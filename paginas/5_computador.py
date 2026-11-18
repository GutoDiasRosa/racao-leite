import hashlib

import pandas as pd
import streamlit as st

import estado
from comum import (aviso_aditivos, metricas_racao, mostrar_avaliacao, mostrar_checklist, mostrar_df,
                   mostrar_formula, rodar_pl)
from core.formatar import br

st.title("💻 Ração 3 — Computador (programação linear)")
st.caption(
    "O computador escolhe a combinação de **menor custo** que fecha a IMS e respeita todas as restrições: "
    "PB e NDT mínimos, Ca e P mínimos, FDN mínimo, EE máximo e **amido máximo**. Defina quais alimentos ele "
    "pode usar e, se quiser, quantidades mínimas e máximas (por exemplo, mínimo de silagem de milho ou mínimos "
    "para garantir os 4 alimentos).")

p = estado.projeto()
al = estado.alimentos()
pl = p["pl"]
opcoes = estado.nomes_por_categoria()
an = estado.animal()

pl["selecionados"] = [n for n in pl["selecionados"] if n in opcoes]
c1, c2 = st.columns([3, 1])
with c1:
    sel = estado.campo(("pl", "selecionados"), st.multiselect, "Alimentos disponíveis para o otimizador",
                       options=opcoes)
with c2:
    estado.campo(("pl", "incluir_amido"), st.toggle, "Limitar amido", cast=bool,
                 help="Aplica o amido máximo definido em Animal e exigências.")
    lim_min = estado.campo(("pl", "limitar_minerais"), st.toggle, "Limitar excesso de Ca e P", cast=bool,
                           help="Sem esse teto o calcário, barato e sem energia, pode ser usado como "
                                "'enchimento' para fechar a IMS.")
    if lim_min:
        estado.campo(("pl", "tol_minerais"), st.number_input, "Até quanto acima da exigência (%)", cast=float,
                     min_value=0.0, max_value=200.0, step=5.0, format="%.0f")

st.markdown(f"**Limites por alimento** (kg MS/vaca/dia). IMS = {br(an.ims_kg, 2)} kg → 40% = "
            f"{br(0.4 * an.ims_kg, 2)} kg · 50% = {br(0.5 * an.ims_kg, 2)} kg. Máximo vazio (*None*) = sem limite.")
lim = pl["limites"]
base = pd.DataFrame([{
    "Alimento": n, "Preço R$/kg MN": al[n]["preco"],
    "Mín (kg MS)": float(lim.get(n, [0.0, None])[0] or 0.0),
    "Máx (kg MS)": lim.get(n, [0.0, None])[1],
} for n in sel], columns=["Alimento", "Preço R$/kg MN", "Mín (kg MS)", "Máx (kg MS)"])
base["Máx (kg MS)"] = pd.to_numeric(base["Máx (kg MS)"], errors="coerce").astype("float64")
chave = "ed_lim_" + hashlib.md5("|".join(sel).encode()).hexdigest()[:8]
if chave not in st.session_state:
    st.session_state["base_" + chave] = base
if sel:
    ed = st.data_editor(
        st.session_state["base_" + chave], key=chave, hide_index=True, width="stretch",
        disabled=["Alimento", "Preço R$/kg MN"],
        column_config={
            "Preço R$/kg MN": st.column_config.NumberColumn(format="%.2f"),
            "Mín (kg MS)": st.column_config.NumberColumn(min_value=0.0, format="%.2f"),
            "Máx (kg MS)": st.column_config.NumberColumn(min_value=0.0, format="%.2f"),
        })
    novos = {}
    for _, r in ed.iterrows():
        mn = float(r["Mín (kg MS)"]) if pd.notna(r["Mín (kg MS)"]) else 0.0
        mx = float(r["Máx (kg MS)"]) if pd.notna(r["Máx (kg MS)"]) else None
        novos[r["Alimento"]] = [mn, mx]
    # mantém limites de alimentos desmarcados para quando voltarem
    pl["limites"] = {**{k: v for k, v in lim.items() if k not in sel}, **novos}
aviso_aditivos()

res = rodar_pl()
st.divider()
if not res.sucesso:
    st.error(res.mensagem)
    st.stop()
(st.success if not res.nao_atendidas else st.warning)(res.mensagem)
for x in res.nao_atendidas:
    st.markdown(f"- 🔴 {x}")

racao = res.racao
c = st.columns(3)
c[0].metric("Custo R$/vaca/dia", br(res.custo_vaca, 2))
c[1].metric("Custo R$/lote/dia", br(res.custo_lote, 0))
c[2].metric("R$ por kg de leite", br(res.custo_vaca / an.leite, 3) if an.leite else "—")

st.subheader("Fórmula ótima")
mostrar_formula(racao)
metricas_racao(racao)
st.subheader("Avaliação: exigido × fornecido")
mostrar_avaliacao(racao, incluir_amido=bool(pl["incluir_amido"]))
mostrar_checklist(racao, incluir_amido=bool(pl["incluir_amido"]))

st.subheader("Relatório do otimizador")
st.caption("**Ativa** = a restrição está no limite e determina a fórmula. **Valor marginal** = quanto o custo "
           "por vaca/dia muda se o limite aumentar 1 kg (ex.: R$ por kg a mais de PB exigida).")
mostrar_df(pd.DataFrame(res.restricoes), casas={"Limite (kg)": 3, "Obtido (kg)": 3})
st.caption("**Redução de preço p/ entrar** = quanto o preço (R$/kg MN) de um alimento não usado teria de cair "
           "para ele entrar na fórmula.")
mostrar_df(pd.DataFrame(res.alimentos), casas={"kg MS": 3, "kg MN": 3})
