import pandas as pd
import streamlit as st

import estado
from comum import (aviso_aditivos, metricas_racao, mostrar_avaliacao, mostrar_checklist, mostrar_df,
                   mostrar_formula, racao_tentativa)
from core.formatar import br
from core.nutricao import avaliar, composicao, dicas, kg_mn

st.title("✏️ Ração 1 — Tentativa e erro")
st.caption("Escolha os alimentos e ajuste as quantidades (kg de MS por vaca/dia) até fechar a IMS e atender às "
           "exigências. A tabela de avaliação atualiza a cada alteração. Use **Salvar tentativa** para registrar "
           "o caminho até a ração final.")

p = estado.projeto()
al = estado.alimentos()
t = p["tentativa"]
opcoes = estado.nomes_por_categoria()

t["racao"] = {k: v for k, v in t["racao"].items() if k in opcoes}
if "w_tent_sel" not in st.session_state:
    st.session_state["w_tent_sel"] = list(t["racao"])
sel = st.multiselect("Alimentos da ração", opcoes, key="w_tent_sel")
for n in list(t["racao"]):
    if n not in sel:
        del t["racao"][n]
        st.session_state.pop(f"w_tentativa.racao.{n}", None)
for n in sel:
    t["racao"].setdefault(n, 0.0)

if sel:
    cols = st.columns(min(4, len(sel)))
    for i, n in enumerate(sel):
        with cols[i % len(cols)]:
            kg = estado.campo(("tentativa", "racao", n), st.number_input, f"{n} (kg MS)", cast=float,
                              min_value=0.0, step=0.1, format="%.2f")
            st.caption(f"= {br(kg_mn(al[n], kg), 2)} kg MN · {br(al[n]['PB'], 1)}% PB · {br(al[n]['NDT'], 0)}% NDT")
aviso_aditivos()

racao = racao_tentativa()
an, ex = estado.animal(), estado.exig()

st.divider()
metricas_racao(racao)
st.subheader("Avaliação: exigido × fornecido")
mostrar_avaliacao(racao, incluir_amido=False)
comp = composicao(racao, al)
st.caption(f"Amido da ração: {br(comp['pct']['Amido'], 1)}% da MS (o limite de "
           f"{br(ex.amido_max_pct, 0)}% só é exigido na ração 3).")

d = dicas(racao, al, an, ex)
if d:
    st.info("**Dicas para a próxima tentativa**\n\n" + "\n".join(f"- {x}" for x in d))

mostrar_checklist(racao, incluir_amido=False)

st.subheader("Fórmula")
mostrar_formula(racao)

st.subheader("Histórico de tentativas")
c1, c2 = st.columns([1, 1])
if c1.button("💾 Salvar tentativa", type="primary", width="stretch"):
    linhas = avaliar(racao, al, an, ex, incluir_amido=False)
    reg = {"Tentativa": len(t["historico"]) + 1}
    reg.update({n: round(kg, 3) for n, kg in t["racao"].items() if kg})
    reg["MS (kg)"] = round(comp["MS"], 3)
    reg["PB (kg)"] = round(comp["PB"], 3)
    reg["NDT (kg)"] = round(comp["NDT"], 3)
    reg["Ca (%)"] = round(comp["pct"]["Ca"], 3)
    reg["P (%)"] = round(comp["pct"]["P"], 3)
    reg["FDN (%)"] = round(comp["pct"]["FDN"], 2)
    reg["EE (%)"] = round(comp["pct"]["EE"], 2)
    reg["Atende tudo"] = "Sim" if all(l["Status"] in ("ok", "excesso") for l in linhas) else "Não"
    t["historico"].append(reg)
    st.toast(f"Tentativa {reg['Tentativa']} salva.")
if c2.button("🗑️ Limpar histórico", width="stretch", disabled=not t["historico"]):
    t["historico"] = []
    st.rerun()
if t["historico"]:
    h = pd.DataFrame(t["historico"]).fillna(0.0)
    mostrar_df(h, padrao=3)
else:
    st.caption("Nenhuma tentativa salva ainda.")
