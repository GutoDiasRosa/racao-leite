"""Cálculos compartilhados entre páginas e componentes de exibição."""
from __future__ import annotations

import pandas as pd
import streamlit as st

import estado
from core.algebrico import racao_final, resolver
from core.formatar import br
from core.nutricao import avaliar, checklist, com_aditivos, composicao
from core.otimizacao import otimizar
from core.relatorio import df_ingredientes
from core.silo import ParametrosSilo

STATUS_ROTULO = {"ok": "🟢 Atende", "excesso": "🟡 Atende (excesso)", "perto": "🟡 Quase",
                 "fora": "🔴 Não atende"}


# ---------------------------------------------------------------- rações

def fixos_aditivos() -> dict:
    p = estado.projeto()
    return com_aditivos({}, p["aditivos"], estado.alimentos())


def racao_tentativa() -> dict:
    p = estado.projeto()
    return com_aditivos(p["tentativa"]["racao"], p["aditivos"], estado.alimentos())


def resolver_algebrico():
    p = estado.projeto()
    al = estado.alimentos()
    fixos = com_aditivos(p["algebrico"]["fixos"], p["aditivos"], al)
    res = resolver(p["algebrico"]["incognitas"], p["algebrico"]["equacoes"], fixos, al,
                   estado.animal(), estado.exig())
    return res, fixos


def racao_algebrica() -> dict:
    res, fixos = resolver_algebrico()
    return racao_final(res, fixos) if res.viavel else {}


def rodar_pl():
    p = estado.projeto()
    lim = {n: (v[0], v[1]) for n, v in p["pl"]["limites"].items()}
    tol = float(p["pl"]["tol_minerais"]) / 100 if p["pl"].get("limitar_minerais", True) else None
    return otimizar(estado.alimentos(), p["pl"]["selecionados"], lim, estado.animal(), estado.exig(),
                    incluir_amido=bool(p["pl"]["incluir_amido"]), fixos=fixos_aditivos(), tol_minerais=tol)


def racoes_finais() -> dict:
    """{título: (ração com aditivos, aplica limite de amido?)}"""
    p = estado.projeto()
    return {
        estado.R1: (racao_tentativa(), False),
        estado.R2: (racao_algebrica(), False),
        estado.R3: (rodar_pl().racao, bool(p["pl"]["incluir_amido"])),
    }


def parametros_silo() -> tuple[ParametrosSilo, str]:
    """Parâmetros do silo com a silagem de milho vinda da ração escolhida."""
    p = estado.projeto()
    s = dict(p["silo"])
    fonte = s.get("fonte", estado.R3)
    msg = ""
    if fonte != "Manual":
        racao = racoes_finais().get(fonte, ({}, False))[0]
        al = estado.alimentos()
        nomes = [n for n in racao if "silagem de milho" in n.lower()]
        if nomes:
            s["kg_ms_vaca"] = sum(racao[n] for n in nomes)
            s["ms_silagem_pct"] = al[nomes[0]]["MS"]
            msg = (f"Silagem de milho da {fonte}: {br(s['kg_ms_vaca'], 2)} kg MS/vaca/dia "
                   f"com {br(s['ms_silagem_pct'], 1)}% de MS.")
        else:
            msg = f"A {fonte} não tem silagem de milho (ou ainda não foi montada). Usando os valores manuais."
    return ParametrosSilo.de_dict(s), msg


# ---------------------------------------------------------------- exibição

def mostrar_df(df: pd.DataFrame, casas: dict | None = None, progresso: list | None = None,
               padrao: int = 2, **kw) -> None:
    if df is None or df.empty:
        st.caption("Sem dados.")
        return
    casas = casas or {}
    progresso = progresso or []
    out = df.copy()
    for c in out.columns:
        if c in progresso:
            continue
        if pd.api.types.is_float_dtype(out[c]):
            k = casas.get(c, padrao)
            out[c] = out[c].map(lambda v, k=k: "" if pd.isna(v) else br(v, k))
    cfg = {c: st.column_config.ProgressColumn(c, min_value=0, max_value=150, format="%.0f%%")
           for c in progresso}
    st.dataframe(out, hide_index=True, width="stretch", column_config=cfg, **kw)


def mostrar_avaliacao(racao: dict, incluir_amido: bool) -> None:
    linhas = avaliar(racao, estado.alimentos(), estado.animal(), estado.exig(), incluir_amido)
    df = pd.DataFrame(linhas)
    df["Status"] = df["Status"].map(STATUS_ROTULO)
    mostrar_df(df[["Nutriente", "Tipo", "Exigido (kg)", "Fornecido (kg)", "Diferença (kg)",
                   "Exigido (% MS)", "Fornecido (% MS)", "% atendido", "Status"]],
               casas={"Exigido (kg)": 3, "Fornecido (kg)": 3, "Diferença (kg)": 3},
               progresso=["% atendido"])


def mostrar_formula(racao: dict) -> None:
    df = df_ingredientes(racao, estado.alimentos(), estado.animal().n_vacas)
    mostrar_df(df, casas={"kg MN/vaca/dia": 3, "kg MS/vaca/dia": 3, "kg MN lote/dia": 1})


def mostrar_checklist(racao: dict, incluir_amido: bool) -> bool:
    itens = checklist(racao, estado.alimentos(), estado.animal(), estado.exig(),
                      estado.projeto()["aditivos"], incluir_amido)
    tudo = all(i["OK"] for i in itens)
    with st.expander(("✅ Checklist do trabalho: tudo certo" if tudo
                      else "⚠️ Checklist do trabalho: há itens pendentes"), expanded=not tudo):
        for i in itens:
            st.markdown(f"{'✅' if i['OK'] else '❌'} {i['Item']}"
                        + (f" — *{i['Detalhe']}*" if i["Detalhe"] else ""))
    return tudo


def metricas_racao(racao: dict) -> None:
    comp = composicao(racao, estado.alimentos())
    an, ex = estado.animal(), estado.exig()
    c = st.columns(5)
    c[0].metric("MS (kg)", br(comp["MS"], 2), f"{br(comp['MS'] - an.ims_kg, 2)} vs IMS", delta_color="off")
    c[1].metric("PB (kg)", br(comp["PB"], 2), br(comp["PB"] - ex.pb_kg, 3))
    c[2].metric("NDT (kg)", br(comp["NDT"], 2), br(comp["NDT"] - ex.ndt_kg, 2))
    c[3].metric("FDN (% MS)", br(comp["pct"]["FDN"], 1), f"mín. {br(ex.fdn_min_pct, 0)}", delta_color="off")
    c[4].metric("R$/vaca/dia", br(comp["custo"], 2), f"lote R$ {br(comp['custo'] * an.n_vacas, 0)}",
                delta_color="off")


def aviso_aditivos() -> None:
    adit = estado.projeto()["aditivos"]
    if adit:
        txt = ", ".join(f"{n} ({br(i['dose_kg'] * 1000, 0)} g)" for n, i in adit.items())
        st.caption(f"Aditivos incluídos automaticamente (página Aditivos): {txt}.")
    else:
        st.caption("Nenhum aditivo selecionado — escolha pelo menos 2 na página Aditivos.")
