"""Cálculos nutricionais: IMS, exigências, composição e avaliação da dieta.

Convenções:
- Ração = dict {nome do alimento: kg de MS/vaca/dia}.
- Alimentos = dict {nome: {"categoria", "MS", "PB", "NDT", "FDN", "EE", "Ca", "P", "Amido", "preco"}}
  com nutrientes em % da MS, MS em % da MN e preço em R$/kg MN.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, asdict, field

from .alimentos_padrao import CATEGORIAS_NAO_CONTAM
from .formatar import br

NUTRIENTES = ["PB", "NDT", "FDN", "EE", "Ca", "P", "Amido"]


@dataclass
class Animal:
    n_vacas: int = 130
    dias_lactacao: int = 120
    peso: float = 590.0          # kg
    ims_pct_pc: float = 4.12     # % do peso corporal
    leite: float = 40.0          # kg/dia
    gordura: float = 3.7         # %
    proteina: float = 3.3        # %

    @property
    def ims_kg(self) -> float:
        return self.peso * self.ims_pct_pc / 100

    @classmethod
    def de_dict(cls, d: dict) -> "Animal":
        return cls(**{k: d[k] for k in cls.__dataclass_fields__ if k in d})

    def para_dict(self) -> dict:
        return asdict(self)


@dataclass
class Exigencias:
    pb_kg: float = 4.00
    ndt_kg: float = 17.52
    ca_pct: float = 0.61
    p_pct: float = 0.36
    fdn_min_pct: float = 29.0
    ee_max_pct: float = 5.0
    amido_max_pct: float = 26.0

    @classmethod
    def de_dict(cls, d: dict) -> "Exigencias":
        return cls(**{k: d[k] for k in cls.__dataclass_fields__ if k in d})

    def para_dict(self) -> dict:
        return asdict(self)


@dataclass
class Meta:
    """Uma restrição nutricional da dieta, em kg/vaca/dia."""
    nutriente: str
    tipo: str            # "min" ou "max"
    kg: float
    pct_ms: float
    tol_excesso: float | None = None   # fração acima do mínimo considerada excesso (None = sem limite)


def metas(animal: Animal, exig: Exigencias, incluir_amido: bool = True) -> list[Meta]:
    ims = animal.ims_kg
    m = [
        Meta("PB", "min", exig.pb_kg, 100 * exig.pb_kg / ims, 0.10),
        Meta("NDT", "min", exig.ndt_kg, 100 * exig.ndt_kg / ims, 0.10),
        Meta("Ca", "min", exig.ca_pct / 100 * ims, exig.ca_pct, 0.60),
        Meta("P", "min", exig.p_pct / 100 * ims, exig.p_pct, 0.40),
        Meta("FDN", "min", exig.fdn_min_pct / 100 * ims, exig.fdn_min_pct, None),
        Meta("EE", "max", exig.ee_max_pct / 100 * ims, exig.ee_max_pct),
    ]
    if incluir_amido:
        m.append(Meta("Amido", "max", exig.amido_max_pct / 100 * ims, exig.amido_max_pct))
    return m


# ---------------------------------------------------------------- estimativa NRC

def estimativa_nrc(animal: Animal) -> dict:
    """Estimativas de referência (NRC, 2001). Não substituem as exigências informadas."""
    pv075 = animal.peso ** 0.75
    gordura_kg = animal.leite * animal.gordura / 100
    lcg4 = 0.4 * animal.leite + 15 * gordura_kg
    semana = animal.dias_lactacao / 7
    ims_nrc = (0.372 * lcg4 + 0.0968 * pv075) * (1 - math.exp(-0.192 * (semana + 3.67)))
    ell_mant = 0.08 * pv075
    ell_leite_kg = 0.0929 * animal.gordura + 0.0547 * animal.proteina + 0.0395 * 4.85
    ell_lact = animal.leite * ell_leite_kg
    ell_total = ell_mant + ell_lact
    ims = animal.ims_kg
    densidade = ell_total / ims if ims > 0 else 0.0
    # NRC: ELL (Mcal/kg MS) = 0,0245 × NDT(%) − 0,12  →  NDT(%) = (ELL + 0,12) / 0,0245
    ndt_pct = (densidade + 0.12) / 0.0245 if ims > 0 else 0.0
    return {
        "PC^0,75 (kg)": pv075,
        "LCG 4% (kg/dia)": lcg4,
        "IMS prevista NRC 2001 (kg MS/dia)": ims_nrc,
        "ELL mantença (Mcal/dia)": ell_mant,
        "ELL por kg de leite (Mcal/kg)": ell_leite_kg,
        "ELL lactação (Mcal/dia)": ell_lact,
        "ELL total (Mcal/dia)": ell_total,
        "ELL necessária (Mcal/kg MS)": densidade,
        "NDT equivalente (% MS)": ndt_pct,
        "NDT equivalente (kg/dia)": ndt_pct / 100 * ims,
    }


# ---------------------------------------------------------------- composição da dieta

def kg_mn(alimento: dict, kg_ms: float) -> float:
    ms = alimento["MS"]
    return kg_ms / (ms / 100) if ms else 0.0


def com_aditivos(racao: dict, aditivos: dict, alimentos: dict) -> dict:
    """Junta os aditivos selecionados (dose em kg MN) à ração (kg MS)."""
    total = {k: v for k, v in racao.items() if v}
    for nome, info in aditivos.items():
        if nome in alimentos and info.get("dose_kg", 0) > 0:
            total[nome] = info["dose_kg"] * alimentos[nome]["MS"] / 100
    return total


def composicao(racao: dict, alimentos: dict) -> dict:
    """Totais da dieta: kg de MS, MN, cada nutriente e custo por vaca/dia."""
    tot = {"MS": 0.0, "MN": 0.0, "custo": 0.0, **{n: 0.0 for n in NUTRIENTES}}
    for nome, kg in racao.items():
        if not kg or nome not in alimentos:
            continue
        a = alimentos[nome]
        tot["MS"] += kg
        mn = kg_mn(a, kg)
        tot["MN"] += mn
        tot["custo"] += mn * (a.get("preco") or 0)
        for n in NUTRIENTES:
            tot[n] += kg * (a.get(n) or 0) / 100
    tot["pct"] = {n: (100 * tot[n] / tot["MS"] if tot["MS"] else 0.0) for n in NUTRIENTES}
    return tot


def status_meta(meta: Meta, fornecido: float) -> str:
    """'ok', 'perto', 'excesso' ou 'fora'."""
    if meta.kg <= 0:
        return "ok"
    r = fornecido / meta.kg
    if meta.tipo == "min":
        if r >= 1 - 1e-9:
            if meta.tol_excesso is not None and r > 1 + meta.tol_excesso:
                return "excesso"
            return "ok"
        return "perto" if r >= 0.97 else "fora"
    if r <= 1 + 1e-9:
        return "ok"
    return "perto" if r <= 1.03 else "fora"


def status_ims(animal: Animal, ms_total: float) -> str:
    ims = animal.ims_kg
    if ims <= 0:
        return "fora"
    r = abs(ms_total / ims - 1)
    return "ok" if r <= 0.01 else ("perto" if r <= 0.03 else "fora")


def avaliar(racao: dict, alimentos: dict, animal: Animal, exig: Exigencias,
            incluir_amido: bool = True) -> list[dict]:
    """Linhas exigido × fornecido para cada restrição (inclui a linha da IMS)."""
    comp = composicao(racao, alimentos)
    ims = animal.ims_kg
    linhas = [{
        "Nutriente": "MS (IMS)", "Tipo": "=", "Exigido (kg)": ims, "Fornecido (kg)": comp["MS"],
        "Diferença (kg)": comp["MS"] - ims, "Exigido (% MS)": 100.0,
        "Fornecido (% MS)": 100 * comp["MS"] / ims if ims else 0.0,
        "% atendido": 100 * comp["MS"] / ims if ims else 0.0,
        "Status": status_ims(animal, comp["MS"]),
    }]
    for m in metas(animal, exig, incluir_amido):
        f = comp[m.nutriente]
        linhas.append({
            "Nutriente": m.nutriente, "Tipo": "≥" if m.tipo == "min" else "≤",
            "Exigido (kg)": m.kg, "Fornecido (kg)": f, "Diferença (kg)": f - m.kg,
            "Exigido (% MS)": m.pct_ms, "Fornecido (% MS)": comp["pct"][m.nutriente],
            "% atendido": 100 * f / m.kg if m.kg else 0.0,
            "Status": status_meta(m, f),
        })
    return linhas


def tabela_ingredientes(racao: dict, alimentos: dict, n_vacas: int) -> list[dict]:
    """Fórmula: kg MS, kg MN, % MS, kg MN do lote e custo por ingrediente."""
    ms_total = sum(v for v in racao.values() if v)
    linhas = []
    for nome, kg in racao.items():
        if not kg or nome not in alimentos:
            continue
        a = alimentos[nome]
        mn = kg_mn(a, kg)
        linhas.append({
            "Ingrediente": nome, "Categoria": a.get("categoria", ""),
            "kg MN/vaca/dia": mn, "kg MS/vaca/dia": kg,
            "% da MS": 100 * kg / ms_total if ms_total else 0.0,
            "kg MN lote/dia": mn * n_vacas,
            "Custo R$/vaca/dia": mn * (a.get("preco") or 0),
        })
    return linhas


# ---------------------------------------------------------------- ajudas e checklist

def dicas(racao: dict, alimentos: dict, animal: Animal, exig: Exigencias,
          incluir_amido: bool = False) -> list[str]:
    """Sugestões simples para a tentativa e erro."""
    comp = composicao(racao, alimentos)
    usados = [n for n in racao if racao[n] and n in alimentos
              and alimentos[n].get("categoria") != "Aditivo"]
    saida = []
    dif_ms = animal.ims_kg - comp["MS"]
    if abs(dif_ms) > 0.01 * animal.ims_kg:
        saida.append(f"{'Faltam' if dif_ms > 0 else 'Sobram'} {br(abs(dif_ms), 2)} kg de MS para fechar a IMS "
                     f"({br(animal.ims_kg, 2)} kg).")
    for m in metas(animal, exig, incluir_amido):
        f = comp[m.nutriente]
        if m.tipo == "min" and f < m.kg:
            falta = m.kg - f
            cands = [(alimentos[n].get(m.nutriente) or 0, n) for n in usados]
            cands = [c for c in cands if c[0] > 0]
            if cands:
                conc, melhor = max(cands)
                saida.append(f"Faltam {br(falta, 3)} kg de {m.nutriente}: ≈ +{br(falta / (conc / 100), 2)} kg MS "
                             f"de {melhor} ({br(conc, 1)}% de {m.nutriente}).")
            else:
                saida.append(f"Faltam {br(falta, 3)} kg de {m.nutriente}: inclua um alimento rico em {m.nutriente}.")
        elif m.tipo == "max" and f > m.kg:
            saida.append(f"{m.nutriente} passou {br(f - m.kg, 3)} kg do máximo ({br(m.pct_ms, 1)}% da MS): "
                         f"reduza os alimentos mais ricos em {m.nutriente}.")
    return saida


def conta_alimentos(racao: dict, alimentos: dict) -> int:
    return sum(1 for n, kg in racao.items() if kg and n in alimentos
               and alimentos[n].get("categoria") not in CATEGORIAS_NAO_CONTAM)


def tem_silagem_de_milho(racao: dict) -> bool:
    return any(kg and "silagem de milho" in n.lower() for n, kg in racao.items())


def checklist(racao: dict, alimentos: dict, animal: Animal, exig: Exigencias,
              aditivos: dict, incluir_amido: bool) -> list[dict]:
    """Regras do trabalho para uma ração (já com aditivos)."""
    itens = []
    n = conta_alimentos(racao, alimentos)
    itens.append({"Item": "Pelo menos 4 alimentos (sem minerais/vitamínicos e aditivos)",
                  "OK": n >= 4, "Detalhe": f"{n} alimento(s)"})
    itens.append({"Item": "Silagem de milho como volumoso", "OK": tem_silagem_de_milho(racao),
                  "Detalhe": ""})
    adit_ok = [a for a, i in aditivos.items() if racao.get(a) and (i.get("justificativa") or "").strip()]
    itens.append({"Item": "Pelo menos 2 aditivos justificados", "OK": len(adit_ok) >= 2,
                  "Detalhe": ", ".join(adit_ok) or "nenhum"})
    for linha in avaliar(racao, alimentos, animal, exig, incluir_amido):
        ok = linha["Status"] in ("ok", "excesso")
        em_kg = linha["Nutriente"] in ("PB", "NDT", "MS (IMS)")
        alvo = (f"{linha['Tipo']} {br(linha['Exigido (kg)'], 3)} kg" if em_kg
                else f"{linha['Tipo']} {br(linha['Exigido (% MS)'], 2)}% MS")
        forn = (f"{br(linha['Fornecido (kg)'], 3)} kg" if em_kg
                else f"{br(linha['Fornecido (% MS)'], 2)}% MS")
        itens.append({"Item": f"{linha['Nutriente']} {alvo}", "OK": ok, "Detalhe": forn})
    return itens
