import pandas as pd
import streamlit as st

import estado
from comum import (aviso_aditivos, metricas_racao, mostrar_avaliacao, mostrar_checklist, mostrar_df,
                   mostrar_formula, resolver_algebrico)
from core.algebrico import DESCRICAO_EQ, EQUACOES_DISPONIVEIS, racao_final
from core.formatar import br
from core.nutricao import composicao

st.title("➗ Ração 2 — Processo algébrico")
st.caption(
    "Escolha **n alimentos incógnitos** e **n equações**. Cada equação diz que a soma do nutriente fornecido "
    "pelos alimentos deve ser igual à exigência, descontando o que os alimentos de quantidade fixa já fornecem. "
    "O sistema é resolvido por eliminação de Gauss-Jordan, com todos os passos mostrados.")

p = estado.projeto()
al = estado.alimentos()
alg = p["algebrico"]
opcoes = estado.nomes_por_categoria()

if st.button("📘 Carregar exemplo clássico (silagem, milho, farelo de soja, calcário e fosfato; MS, PB, NDT, Ca e P)"):
    alg.update({"incognitas": [n for n in estado.INCOGNITAS_CLASSICAS if n in opcoes],
                "equacoes": ["MS", "PB", "NDT", "Ca", "P"], "fixos": {"Caroço de algodão": 1.5}})
    for k in [k for k in st.session_state if str(k).startswith(("w_algebrico", "w_alg_"))]:
        del st.session_state[k]
    st.rerun()

alg["incognitas"] = [n for n in alg["incognitas"] if n in opcoes]
c1, c2 = st.columns(2)
with c1:
    inc = estado.campo(("algebrico", "incognitas"), st.multiselect, "Alimentos incógnitos (x₁, x₂, …)",
                       options=opcoes, max_selections=5,
                       help="O sistema calcula a quantidade destes alimentos.")
with c2:
    eqs = estado.campo(("algebrico", "equacoes"), st.multiselect, "Equações (MS é obrigatória)",
                       options=EQUACOES_DISPONIVEIS, max_selections=5,
                       format_func=lambda e: f"{e} — {DESCRICAO_EQ[e]}")

if "MS" not in eqs:
    st.warning("Inclua a equação de **MS**: é ela que garante que a ração feche a IMS.")
if len(eqs) != len(inc):
    st.info(f"Você tem {len(inc)} incógnita(s) e {len(eqs)} equação(ões). Elas precisam ser em mesmo número.")

st.markdown("**Alimentos com quantidade fixa** (entram no lado direito das equações)")
fixos_opc = [n for n in opcoes if n not in inc]
alg["fixos"] = {k: v for k, v in alg["fixos"].items() if k in fixos_opc}
if "w_alg_fixos_sel" not in st.session_state:
    st.session_state["w_alg_fixos_sel"] = list(alg["fixos"])
fsel = st.multiselect("Alimentos fixos", fixos_opc, key="w_alg_fixos_sel", label_visibility="collapsed")
for n in list(alg["fixos"]):
    if n not in fsel:
        del alg["fixos"][n]
        st.session_state.pop(f"w_algebrico.fixos.{n}", None)
for n in fsel:
    alg["fixos"].setdefault(n, 1.0)
if fsel:
    cols = st.columns(min(4, len(fsel)))
    for i, n in enumerate(fsel):
        with cols[i % len(cols)]:
            estado.campo(("algebrico", "fixos", n), st.number_input, f"{n} (kg MS)", cast=float,
                         min_value=0.0, step=0.1, format="%.2f")
aviso_aditivos()

res, fixos = resolver_algebrico()

st.divider()
if res.mensagem and res.solucao is None:
    st.error(res.mensagem)
    st.stop()

st.subheader("1. Variáveis")
mostrar_df(pd.DataFrame([(v, n, al[n]["MS"], al[n]["PB"], al[n]["NDT"], al[n]["Ca"], al[n]["P"])
                         for v, n in res.variaveis.items()],
                        columns=["Variável (kg MS)", "Alimento", "MS %", "PB %", "NDT %", "Ca %", "P %"]))

st.subheader("2. Montagem do sistema")
mostrar_df(pd.DataFrame(res.equacoes)[["Equação", "Descrição", "Alvo (kg)", "Fornecido pelos fixos (kg)",
                                         "Lado direito (kg)"]], padrao=4)
st.code("\n".join(f"({e['Equação']:>3})  {e['Texto']}" for e in res.equacoes), language=None)


def matriz_df(M):
    n = len(M)
    return pd.DataFrame(M, columns=[f"x{j + 1}" for j in range(n)] + ["= b"],
                        index=[f"L{i + 1}" for i in range(n)])


def mostrar_matriz(M):
    df = matriz_df(M).map(lambda v: br(v, 5))
    st.dataframe(df, width="stretch")


st.subheader("3. Resolução (Gauss-Jordan)")
st.markdown("Matriz aumentada inicial:")
mostrar_matriz(res.matriz_inicial)
with st.expander("Ver o passo a passo da eliminação", expanded=False):
    for passo in res.passos:
        st.markdown(f"**{passo.titulo}** — " + ("; ".join(passo.operacoes) or "nenhuma operação necessária"))
        mostrar_matriz(passo.matriz)

st.subheader("4. Solução")
sol = pd.DataFrame([(v, n, res.solucao[n], res.solucao[n] / (al[n]["MS"] / 100) if al[n]["MS"] else 0)
                    for v, n in res.variaveis.items()],
                   columns=["Variável", "Alimento", "kg MS/vaca/dia", "kg MN/vaca/dia"])
mostrar_df(sol, padrao=3)
(st.success if res.viavel else st.error)(res.mensagem)

if res.viavel:
    racao = racao_final(res, fixos)
    st.subheader("5. Conferência da ração completa")
    metricas_racao(racao)
    mostrar_avaliacao(racao, incluir_amido=False)
    comp = composicao(racao, al)
    ex = estado.exig()
    st.caption(f"FDN, EE e amido não entram como equações: são conferidos depois. Amido = "
               f"{br(comp['pct']['Amido'], 1)}% da MS (limite de {br(ex.amido_max_pct, 0)}% só na ração 3).")
    mostrar_checklist(racao, incluir_amido=False)
    st.subheader("Fórmula")
    mostrar_formula(racao)
