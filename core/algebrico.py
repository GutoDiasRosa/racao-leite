"""Processo algébrico: sistema de equações lineares resolvido por Gauss-Jordan,
registrando cada operação para que o aluno possa apresentar os passos."""
from __future__ import annotations

import copy
from dataclasses import dataclass, field

from .nutricao import Animal, Exigencias

EQUACOES_DISPONIVEIS = ["MS", "PB", "NDT", "Ca", "P", "FDN"]

DESCRICAO_EQ = {
    "MS": "Matéria seca total = IMS",
    "PB": "Proteína bruta = exigência de PB",
    "NDT": "NDT = exigência de NDT",
    "Ca": "Cálcio = exigência de Ca",
    "P": "Fósforo = exigência de P",
    "FDN": "FDN = mínimo de FDN",
}


def num(x: float, casas: int = 4) -> str:
    """Número no formato brasileiro, sem zeros desnecessários."""
    s = f"{x:.{casas}f}".rstrip("0").rstrip(".")
    if s in ("-0", ""):
        s = "0"
    return s.replace(".", ",")


def alvo_equacao(eq: str, animal: Animal, exig: Exigencias) -> float:
    ims = animal.ims_kg
    return {
        "MS": ims,
        "PB": exig.pb_kg,
        "NDT": exig.ndt_kg,
        "Ca": exig.ca_pct / 100 * ims,
        "P": exig.p_pct / 100 * ims,
        "FDN": exig.fdn_min_pct / 100 * ims,
    }[eq]


def coeficiente(eq: str, alimento: dict) -> float:
    return 1.0 if eq == "MS" else (alimento.get(eq) or 0) / 100


@dataclass
class Passo:
    titulo: str
    operacoes: list[str]
    matriz: list[list[float]]


@dataclass
class ResultadoAlgebrico:
    variaveis: dict[str, str] = field(default_factory=dict)      # "x1" -> nome do alimento
    equacoes: list[dict] = field(default_factory=list)
    matriz_inicial: list[list[float]] = field(default_factory=list)
    passos: list[Passo] = field(default_factory=list)
    solucao: dict[str, float] | None = None                      # nome -> kg MS
    viavel: bool = False
    mensagem: str = ""


def gauss_jordan(A: list[list[float]], b: list[float]):
    """Resolve A·x = b com pivoteamento parcial. Retorna (x | None, passos, mensagem)."""
    n = len(A)
    M = [list(map(float, A[i])) + [float(b[i])] for i in range(n)]
    passos: list[Passo] = []
    for k in range(n):
        ops = []
        p = max(range(k, n), key=lambda i: abs(M[i][k]))
        if abs(M[p][k]) < 1e-12:
            return None, passos, (f"O sistema não tem solução única (coluna x{k + 1} sem pivô). "
                                  "Há alimentos com composição proporcional ou equações redundantes: "
                                  "troque um alimento ou uma equação.")
        if p != k:
            M[k], M[p] = M[p], M[k]
            ops.append(f"L{k + 1} ↔ L{p + 1}")
        piv = M[k][k]
        if abs(piv - 1) > 1e-15:
            M[k] = [v / piv for v in M[k]]
            ops.append(f"L{k + 1} ← L{k + 1} ÷ {num(piv, 5)}")
        for i in range(n):
            if i == k:
                continue
            f = M[i][k]
            if abs(f) > 1e-15:
                M[i] = [M[i][j] - f * M[k][j] for j in range(n + 1)]
                ops.append(f"L{i + 1} ← L{i + 1} − ({num(f, 5)})·L{k + 1}")
        passos.append(Passo(f"Coluna {k + 1} (x{k + 1})", ops, copy.deepcopy(M)))
    return [M[i][n] for i in range(n)], passos, ""


def resolver(incognitas: list[str], equacoes: list[str], fixos: dict[str, float],
             alimentos: dict, animal: Animal, exig: Exigencias) -> ResultadoAlgebrico:
    """Monta e resolve o sistema. `fixos` = {alimento: kg MS} (aditivos incluídos)."""
    r = ResultadoAlgebrico()
    if len(incognitas) < 2:
        r.mensagem = "Escolha pelo menos 2 alimentos como incógnitas."
        return r
    if len(equacoes) != len(incognitas):
        r.mensagem = (f"O número de equações ({len(equacoes)}) precisa ser igual ao número de "
                      f"incógnitas ({len(incognitas)}).")
        return r
    faltando = [n for n in incognitas if n not in alimentos]
    if faltando:
        r.mensagem = f"Alimento(s) não encontrado(s) na biblioteca: {', '.join(faltando)}."
        return r

    fixos = {k: v for k, v in fixos.items() if v and k not in incognitas and k in alimentos}
    r.variaveis = {f"x{i + 1}": nome for i, nome in enumerate(incognitas)}

    A, b = [], []
    for eq in equacoes:
        coefs = [coeficiente(eq, alimentos[n]) for n in incognitas]
        total = alvo_equacao(eq, animal, exig)
        contrib = sum(coeficiente(eq, alimentos[n]) * kg for n, kg in fixos.items())
        rhs = total - contrib
        termos = " + ".join(f"{num(c)}·x{i + 1}" for i, c in enumerate(coefs))
        r.equacoes.append({
            "Equação": eq, "Descrição": DESCRICAO_EQ[eq], "Alvo (kg)": total,
            "Fornecido pelos fixos (kg)": contrib, "Lado direito (kg)": rhs,
            "Texto": f"{termos} = {num(rhs)}",
        })
        A.append(coefs)
        b.append(rhs)
    r.matriz_inicial = [A[i] + [b[i]] for i in range(len(A))]

    x, passos, msg = gauss_jordan(A, b)
    r.passos = passos
    if x is None:
        r.mensagem = msg
        return r
    x = [0.0 if abs(v) < 1e-9 else v for v in x]
    r.solucao = {nome: x[i] for i, nome in enumerate(incognitas)}
    negativos = [n for n, v in r.solucao.items() if v < 0]
    if negativos:
        r.viavel = False
        r.mensagem = ("Solução matematicamente correta, mas inviável: quantidade negativa para "
                      f"{', '.join(negativos)}. Troque alimentos, mude as quantidades fixas ou as equações.")
    else:
        r.viavel = True
        r.mensagem = "Solução viável: todas as quantidades são positivas."
    return r


def racao_final(res: ResultadoAlgebrico, fixos: dict[str, float]) -> dict:
    """Ração completa (fixos + incógnitas) em kg MS."""
    racao = {k: v for k, v in fixos.items() if v}
    if res.solucao:
        for nome, kg in res.solucao.items():
            racao[nome] = kg
    return racao
