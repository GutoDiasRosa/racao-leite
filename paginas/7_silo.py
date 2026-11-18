import pandas as pd
import streamlit as st

import estado
from comum import mostrar_df, parametros_silo
from core.formatar import br
from core.silo import calcular_silo

st.title("🏗️ Silagem de milho: silo, fatia diária e área a cultivar")
st.caption("Dimensiona um silo trincheira a partir do consumo de silagem de milho da ração escolhida.")

p = estado.projeto()
s = p["silo"]

fontes = [estado.R1, estado.R2, estado.R3, "Manual"]
estado.campo(("silo", "fonte"), st.radio, "Consumo de silagem vem da", options=fontes, horizontal=True)
prm, msg = parametros_silo()
if msg:
    st.info(msg)

if s["fonte"] == "Manual" or "não tem silagem" in msg:
    c1, c2 = st.columns(2)
    with c1:
        estado.campo(("silo", "kg_ms_vaca"), st.number_input, "Silagem (kg MS/vaca/dia)", cast=float,
                     min_value=0.0, step=0.1, format="%.2f")
    with c2:
        estado.campo(("silo", "ms_silagem_pct"), st.number_input, "MS da silagem (%)", cast=float,
                     min_value=1.0, step=0.5, format="%.1f")

st.subheader("Parâmetros")
c = st.columns(4)
with c[0]:
    estado.campo(("silo", "dias"), st.number_input, "Período de fornecimento (dias)", cast=int, min_value=1, step=1)
    estado.campo(("silo", "perdas_pct"), st.number_input, "Perdas (%)", cast=float, min_value=0.0,
                 max_value=60.0, step=1.0, format="%.0f",
                 help="Perdas de fermentação, efluente, superfície e desabastecimento (usual 10–20%).")
with c[1]:
    estado.campo(("silo", "densidade"), st.number_input, "Densidade (kg MN/m³)", cast=float, min_value=200.0,
                 step=10.0, format="%.0f", help="Silagem bem compactada: 550–700 kg MN/m³.")
    estado.campo(("silo", "fatia_m"), st.number_input, "Fatia retirada por dia (m)", cast=float,
                 min_value=0.05, step=0.05, format="%.2f",
                 help="Recomendado ≥ 0,15–0,20 m/dia no inverno e ≥ 0,25–0,30 m/dia no verão.")
with c[2]:
    estado.campo(("silo", "altura_m"), st.number_input, "Altura do silo (m)", cast=float, min_value=0.5,
                 step=0.1, format="%.2f")
    estado.campo(("silo", "formato"), st.selectbox, "Formato do painel", options=["trapezoidal", "retangular"])
    if s["formato"] == "trapezoidal":
        estado.campo(("silo", "inclinacao"), st.number_input, "Inclinação das paredes (m/m)", cast=float,
                     min_value=0.0, step=0.05, format="%.2f",
                     help="Abertura horizontal de cada parede por metro de altura.")
with c[3]:
    estado.campo(("silo", "produtividade_t_ha"), st.number_input, "Produtividade (t MN/ha)", cast=float,
                 min_value=1.0, step=1.0, format="%.0f")
    estado.campo(("silo", "margem_area_pct"), st.number_input, "Margem de área (%)", cast=float,
                 min_value=0.0, step=5.0, format="%.0f")
    estado.campo(("silo", "comprimento_max_m"), st.number_input, "Comprimento máx. por silo (m)", cast=float,
                 min_value=0.0, step=5.0, format="%.0f")

prm, _ = parametros_silo()
r = calcular_silo(prm)

st.divider()
m = st.columns(4)
m[0].metric("Silagem a produzir (t MN)", br(r["necessidade_kg"] / 1000, 0))
m[1].metric("Volume do silo (m³)", br(r["volume_m3"], 0))
m[2].metric("Fatia diária (cm)", br(prm.fatia_m * 100, 0), f"{br(r['diario_kg'], 0)} kg MN/dia", delta_color="off")
m[3].metric("Área a cultivar (ha)", br(r["area_recomendada_ha"], 1), f"mínimo {br(r['area_ha'], 1)} ha",
            delta_color="off")

dims = (f"{br(r['base_menor_m'], 2)} m (fundo) × {br(r['base_maior_m'], 2)} m (topo)"
        if prm.formato == "trapezoidal" else f"{br(r['base_menor_m'], 2)} m de largura")
st.markdown(f"**Dimensões sugeridas:** {dims} × {br(prm.altura_m, 2)} m de altura × "
            f"{br(r['comprimento_m'], 1)} m de comprimento total"
            + (f" — dividido em **{r['n_silos']} silos de ≈ {br(r['comprimento_silo_m'], 1)} m**."
               if r["n_silos"] > 1 else "."))
for a in r["alertas"]:
    st.warning(a)

st.subheader("Memória de cálculo")
mostrar_df(pd.DataFrame(r["passos"], columns=["Etapa", "Cálculo", "Resultado"]))
