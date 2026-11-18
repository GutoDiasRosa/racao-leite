"""Formulação por computador: programação linear de mínimo custo (scipy/HiGHS).

Variáveis: kg de MS de cada alimento. Cada restrição nutricional recebe uma folga
com penalidade alta (restrição "elástica"): assim o modelo sempre devolve uma ração
e informa qual exigência não pôde ser atendida e por quanto.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from scipy.optimize import linprog

from .formatar import br
from .nutricao import Animal, Exigencias, Meta, metas

PENALIDADE = 1e4   # R$ por kg de nutriente não atendido


@dataclass
class ResultadoPL:
    sucesso: bool = False
    mensagem: str = ""
    racao: dict[str, float] = field(default_factory=dict)     # kg MS/vaca/dia
    custo_vaca: float = 0.0
    custo_lote: float = 0.0
    restricoes: list[dict] = field(default_factory=list)
    alimentos: list[dict] = field(default_factory=list)
    nao_atendidas: list[str] = field(default_factory=list)


def custo_kg_ms(alimento: dict) -> float:
    ms = alimento.get("MS") or 0
    return (alimento.get("preco") or 0) / (ms / 100) if ms else 0.0


def otimizar(alimentos: dict, selecionados: list[str], limites: dict[str, tuple],
             animal: Animal, exig: Exigencias, incluir_amido: bool = True,
             fixos: dict[str, float] | None = None, penalidade: float = PENALIDADE,
             tol_minerais: float | None = 0.15) -> ResultadoPL:
    """
    selecionados: alimentos que o otimizador pode usar.
    limites: {nome: (mín kg MS, máx kg MS ou None)}.
    fixos: {nome: kg MS} com quantidade fixa (ex.: aditivos).
    tol_minerais: excesso máximo de Ca e P sobre a exigência (0,15 = +15%). Sem esse teto, o
        calcário (barato e sem energia) pode virar "enchimento" para fechar a IMS. None desliga.
    """
    fixos = {k: v for k, v in (fixos or {}).items() if v and k in alimentos}
    nomes = [n for n in selecionados if n in alimentos and n not in fixos] + list(fixos)
    r = ResultadoPL()
    if not [n for n in nomes if n not in fixos]:
        r.mensagem = "Selecione os alimentos que o otimizador pode usar."
        return r

    ims = animal.ims_kg
    ms_list = metas(animal, exig, incluir_amido)
    rotulos = [m.nutriente for m in ms_list]
    if tol_minerais is not None:
        for m in [m for m in ms_list if m.nutriente in ("Ca", "P")]:
            ms_list.append(Meta(m.nutriente, "max", m.kg * (1 + tol_minerais), m.pct_ms * (1 + tol_minerais)))
            rotulos.append(f"{m.nutriente} (máx)")
    nv, ns = len(nomes), len(ms_list)

    c = [custo_kg_ms(alimentos[n]) for n in nomes] + [penalidade] * ns

    A_ub, b_ub = [], []
    for j, m in enumerate(ms_list):
        coefs = [(alimentos[n].get(m.nutriente) or 0) / 100 for n in nomes]
        folga = [0.0] * ns
        folga[j] = -1.0
        if m.tipo == "min":    # Σ a·x + s ≥ b   →   −Σ a·x − s ≤ −b
            A_ub.append([-v for v in coefs] + folga)
            b_ub.append(-m.kg)
        else:                  # Σ a·x − s ≤ b
            A_ub.append(coefs + folga)
            b_ub.append(m.kg)
    A_eq = [[1.0] * nv + [0.0] * ns]
    b_eq = [ims]

    bounds = []
    for n in nomes:
        if n in fixos:
            bounds.append((fixos[n], fixos[n]))
        else:
            lo, hi = limites.get(n, (0.0, None))
            lo = max(0.0, lo or 0.0)
            hi = None if hi in (None, "") or (isinstance(hi, float) and hi != hi) else float(hi)
            if hi is not None and hi < lo:
                r.mensagem = f"Limite máximo de {n} é menor que o mínimo."
                return r
            bounds.append((lo, hi))
    bounds += [(0.0, None)] * ns

    soma_min = sum(b[0] for b in bounds[:nv])
    if soma_min > ims + 1e-9:
        r.mensagem = (f"Os mínimos dos alimentos somam {soma_min:.2f} kg MS, mais que a IMS "
                      f"({ims:.2f} kg). Reduza os mínimos.")
        return r

    res = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method="highs")
    if res.status != 0:
        r.mensagem = ("Não foi possível fechar a IMS com os limites máximos informados: "
                      "aumente os máximos ou inclua mais alimentos. (" + res.message + ")")
        return r

    x = res.x[:nv]
    s = res.x[nv:]
    r.racao = {n: float(v) for n, v in zip(nomes, x) if v > 1e-6}
    r.custo_vaca = float(sum(custo_kg_ms(alimentos[n]) * v for n, v in zip(nomes, x)))
    r.custo_lote = r.custo_vaca * animal.n_vacas
    r.sucesso = True

    marg = list(res.ineqlin.marginals) if res.ineqlin is not None else [0.0] * ns
    for j, m in enumerate(ms_list):
        valor = sum((alimentos[n].get(m.nutriente) or 0) / 100 * v for n, v in zip(nomes, x))
        violada = s[j] > 1e-6
        ativa = (not violada) and abs(valor - m.kg) <= 1e-6 * max(1.0, m.kg)
        # derivada do custo em relação ao limite (R$ por kg de nutriente)
        dual = -marg[j] if m.tipo == "min" else marg[j]
        if violada:
            r.nao_atendidas.append(
                f"{rotulos[j]}: {'faltaram' if m.tipo == 'min' else 'excedeu em'} {br(s[j], 3)} kg "
                f"({br(100 * s[j] / ims, 2)}% da MS)")
        r.restricoes.append({
            "Restrição": rotulos[j], "Tipo": "≥" if m.tipo == "min" else "≤",
            "Limite (kg)": m.kg, "Obtido (kg)": valor, "Limite (% MS)": m.pct_ms,
            "Obtido (% MS)": 100 * valor / ims, "Situação": "NÃO ATENDIDA" if violada else ("ativa" if ativa else "folga"),
            "Valor marginal (R$/kg)": 0.0 if violada or not ativa else float(dual),
        })

    reduz = list(res.lower.marginals) if res.lower is not None else [0.0] * (nv + ns)
    for i, n in enumerate(nomes):
        a = alimentos[n]
        v = float(x[i])
        r.alimentos.append({
            "Alimento": n, "kg MS": v, "kg MN": v / (a["MS"] / 100) if a.get("MS") else 0.0,
            "Mín (kg MS)": bounds[i][0], "Máx (kg MS)": bounds[i][1],
            "Preço R$/kg MN": a.get("preco") or 0,
            # quanto o preço (R$/kg MN) teria de cair para o alimento entrar na fórmula
            "Redução de preço p/ entrar (R$/kg MN)": (float(reduz[i]) * a["MS"] / 100
                                                     if v <= 1e-6 and n not in fixos else 0.0),
        })

    r.mensagem = ("Ração ótima encontrada: todas as restrições foram atendidas." if not r.nao_atendidas
                  else "Não existe combinação que atenda tudo com esses alimentos e limites. "
                       "Melhor ração possível (veja as restrições não atendidas).")
    return r
