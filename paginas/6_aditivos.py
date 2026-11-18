import streamlit as st

import estado
from core.alimentos_padrao import ADITIVOS_INFO
from core.formatar import br

st.title("🧪 Aditivos")
st.caption("O trabalho pede pelo menos **dois aditivos** em cada ração, com justificativa. Os escolhidos aqui "
           "entram com dose fixa nas três rações (o trabalho permite usar os mesmos).")

p = estado.projeto()
al = estado.alimentos()
opcoes = [n for n, a in al.items() if a["categoria"] == "Aditivo"]
if not opcoes:
    st.error("Nenhum alimento com a categoria **Aditivo** na página Alimentos.")
    st.stop()

if "w_aditivos_sel" not in st.session_state:
    st.session_state["w_aditivos_sel"] = [n for n in p["aditivos"] if n in opcoes]
sel = st.multiselect("Aditivos usados", opcoes, key="w_aditivos_sel")

novos = {}
for nome in sel:
    atual = p["aditivos"].get(nome) or dict(ADITIVOS_INFO.get(nome, {"dose_kg": 0.01, "justificativa": ""}))
    kd, kj = f"w_adit_dose_{nome}", f"w_adit_just_{nome}"
    if kd not in st.session_state:
        st.session_state[kd] = float(atual.get("dose_kg", 0)) * 1000
    if kj not in st.session_state:
        st.session_state[kj] = atual.get("justificativa", "")
    with st.container(border=True):
        c1, c2 = st.columns([1, 3])
        with c1:
            st.markdown(f"**{nome}**")
            dose_g = st.number_input("Dose (g de produto/vaca/dia)", min_value=0.0, step=1.0, format="%.1f", key=kd)
            ms = al[nome]["MS"]
            st.caption(f"= {br(dose_g / 1000 * ms / 100, 4)} kg MS/vaca/dia · "
                       f"{br(dose_g / 1000 * estado.animal().n_vacas, 2)} kg/dia para o lote")
        with c2:
            just = st.text_area("Justificativa", key=kj, height=130)
    novos[nome] = {"dose_kg": dose_g / 1000, "justificativa": just}
p["aditivos"] = novos

if len(novos) < 2:
    st.warning("Selecione pelo menos 2 aditivos.")
elif any(not v["justificativa"].strip() for v in novos.values()):
    st.warning("Há aditivo sem justificativa.")
elif any(v["dose_kg"] <= 0 for v in novos.values()):
    st.warning("Há aditivo com dose zero.")
else:
    st.success(f"{len(novos)} aditivos com dose e justificativa. ✔")

st.caption("As doses e textos padrão são referências de literatura e bula; confira a concentração do produto "
           "comercial que for usar.")
