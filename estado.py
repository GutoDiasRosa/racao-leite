"""Estado do projeto no Streamlit: valores padrão, autosave e campos persistentes."""
from __future__ import annotations

import copy
import json
import math
import os
from pathlib import Path

import streamlit as st

from core.alimentos_padrao import (ADITIVOS_INFO, ADITIVOS_SELECIONADOS_PADRAO, ALIMENTOS_PADRAO,
                                   COLUNAS)
from core.nutricao import Animal, Exigencias
from core.silo import ParametrosSilo

ARQUIVO = Path(os.environ.get("RACAO_PROJETO") or Path(__file__).parent / "dados" / "projeto.json")

R1, R2, R3 = "Ração 1 — Tentativa e erro", "Ração 2 — Processo algébrico", "Ração 3 — Computador"

INCOGNITAS_CLASSICAS = ["Silagem de milho", "Milho grão moído", "Farelo de soja",
                        "Calcário calcítico", "Fosfato bicálcico"]


def projeto_padrao() -> dict:
    ims = Animal().ims_kg
    return {
        "versao": 1,
        "animal": Animal().para_dict(),
        "exigencias": Exigencias().para_dict(),
        "alimentos": copy.deepcopy(ALIMENTOS_PADRAO),
        "aditivos": {n: dict(ADITIVOS_INFO[n]) for n in ADITIVOS_SELECIONADOS_PADRAO},
        "tentativa": {
            "racao": {"Silagem de milho": 12.0, "Milho grão moído": 5.0, "Farelo de soja": 4.0,
                      "Caroço de algodão": 1.5},
            "historico": [],
        },
        "algebrico": {
            "incognitas": list(INCOGNITAS_CLASSICAS),
            "equacoes": ["MS", "PB", "NDT", "Ca", "P"],
            "fixos": {"Caroço de algodão": 1.5},
        },
        "pl": {
            "selecionados": ["Silagem de milho", "Milho grão moído", "Polpa cítrica", "Casca de soja",
                             "Farelo de soja", "Caroço de algodão", "Calcário calcítico",
                             "Fosfato bicálcico"],
            "limites": {"Silagem de milho": [round(0.40 * ims, 2), None]},
            "incluir_amido": True,
            "limitar_minerais": True,
            "tol_minerais": 15.0,
        },
        "silo": {**ParametrosSilo().para_dict(), "fonte": R3},
    }


# ---------------------------------------------------------------- carregar / salvar

def _completar(dados: dict) -> dict:
    """Garante que um projeto antigo/importado tenha todas as chaves."""
    base = projeto_padrao()
    for k, v in base.items():
        if k not in dados:
            dados[k] = v
        elif isinstance(v, dict) and isinstance(dados[k], dict):
            for k2, v2 in v.items():
                dados[k].setdefault(k2, v2)
    return dados


def projeto() -> dict:
    if "projeto" not in st.session_state:
        dados = None
        if ARQUIVO.exists():
            try:
                dados = json.loads(ARQUIVO.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                dados = None
        st.session_state["projeto"] = _completar(dados or projeto_padrao())
    return st.session_state["projeto"]


def para_json(p: dict | None = None) -> str:
    return json.dumps(p or projeto(), ensure_ascii=False, indent=2, default=_json_default)


def _json_default(o):
    if isinstance(o, float) and math.isnan(o):
        return None
    if hasattr(o, "item"):
        return o.item()
    return str(o)


def salvar() -> None:
    texto = para_json()
    if st.session_state.get("_ultimo_salvo") == texto:
        return
    try:
        ARQUIVO.parent.mkdir(parents=True, exist_ok=True)
        ARQUIVO.write_text(texto, encoding="utf-8")
        st.session_state["_ultimo_salvo"] = texto
    except OSError:
        pass


def limpar_widgets() -> None:
    for k in list(st.session_state.keys()):
        if isinstance(k, str) and k.startswith(("w_", "ed_", "base_")):
            del st.session_state[k]


def substituir(novo: dict) -> None:
    st.session_state["projeto"] = _completar(novo)
    limpar_widgets()


# ---------------------------------------------------------------- acesso conveniente

def animal() -> Animal:
    return Animal.de_dict(projeto()["animal"])


def exig() -> Exigencias:
    return Exigencias.de_dict(projeto()["exigencias"])


def _num(v) -> float:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return 0.0
    return 0.0 if math.isnan(f) else f


def alimentos() -> dict:
    """{nome: dados} com números limpos (NaN → 0)."""
    saida = {}
    for a in projeto()["alimentos"]:
        nome = str(a.get("nome") or "").strip()
        if not nome or nome == "nan":
            continue
        d = {c: a.get(c) for c in COLUNAS}
        for c in ["MS", "PB", "NDT", "FDN", "EE", "Ca", "P", "Amido", "preco"]:
            d[c] = _num(d.get(c))
        d["nome"] = nome
        d["categoria"] = a.get("categoria") or "Concentrado energético"
        saida[nome] = d
    return saida


def nomes_por_categoria(incluir_aditivos: bool = False) -> list[str]:
    return [n for n, a in alimentos().items() if incluir_aditivos or a["categoria"] != "Aditivo"]


# ---------------------------------------------------------------- campos persistentes

def _get(path: tuple):
    d = projeto()
    for p in path[:-1]:
        d = d[p]
    return d, path[-1]


def campo(path: tuple, widget, label: str, cast=None, **kw):
    """Cria um widget ligado a projeto[path...], mantendo o valor entre páginas."""
    key = "w_" + ".".join(map(str, path))
    d, ult = _get(path)
    if key not in st.session_state:
        v = d.get(ult)
        st.session_state[key] = cast(v) if cast and v is not None else v
    valor = widget(label, key=key, **kw)
    d[ult] = valor
    return valor
