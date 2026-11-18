import pandas as pd
import streamlit as st

import estado
from comum import mostrar_df
from core.formatar import br
from core.nutricao import estimativa_nrc

st.title("🐄 Animal e exigências")
st.caption("Os campos já vêm com os dados da folha do trabalho. Altere à vontade: tudo é salvo automaticamente.")

st.subheader("Dados dos animais")
c1, c2, c3 = st.columns(3)
with c1:
    estado.campo(("animal", "n_vacas"), st.number_input, "Número de vacas no lote", cast=int,
                 min_value=1, step=1)
    estado.campo(("animal", "dias_lactacao"), st.number_input, "Dias em lactação (DEL)", cast=int,
                 min_value=0, step=1)
with c2:
    estado.campo(("animal", "peso"), st.number_input, "Peso corporal médio (kg)", cast=float,
                 min_value=50.0, step=5.0, format="%.1f")
    estado.campo(("animal", "ims_pct_pc"), st.number_input, "IMS (% do peso corporal)", cast=float,
                 min_value=0.5, max_value=8.0, step=0.01, format="%.2f")
with c3:
    estado.campo(("animal", "leite"), st.number_input, "Produção de leite (kg/dia)", cast=float,
                 min_value=0.0, step=0.5, format="%.1f")
    g1, g2 = st.columns(2)
    with g1:
        estado.campo(("animal", "gordura"), st.number_input, "Gordura (%)", cast=float,
                     min_value=0.0, step=0.1, format="%.2f")
    with g2:
        estado.campo(("animal", "proteina"), st.number_input, "Proteína (%)", cast=float,
                     min_value=0.0, step=0.1, format="%.2f")

an = estado.animal()
m1, m2, m3 = st.columns(3)
m1.metric("IMS por vaca (kg MS/dia)", br(an.ims_kg, 2), help="Peso × IMS% ÷ 100")
m2.metric("IMS do lote (kg MS/dia)", br(an.ims_kg * an.n_vacas, 0))
m3.metric("Leite do lote (kg/dia)", br(an.leite * an.n_vacas, 0))

st.subheader("Exigências e limites da dieta")
st.caption("Valores informados pelo professor. Proteína e energia em kg/vaca/dia; minerais e limites em % da MS.")
c = st.columns(4) + st.columns(4)[:3]
with c[0]:
    estado.campo(("exigencias", "pb_kg"), st.number_input, "PB (kg/dia)", cast=float, min_value=0.0,
                 step=0.05, format="%.2f")
with c[1]:
    estado.campo(("exigencias", "ndt_kg"), st.number_input, "NDT (kg/dia)", cast=float, min_value=0.0,
                 step=0.1, format="%.2f")
with c[2]:
    estado.campo(("exigencias", "ca_pct"), st.number_input, "Ca (% MS)", cast=float, min_value=0.0,
                 step=0.01, format="%.2f")
with c[3]:
    estado.campo(("exigencias", "p_pct"), st.number_input, "P (% MS)", cast=float, min_value=0.0,
                 step=0.01, format="%.2f")
with c[4]:
    estado.campo(("exigencias", "fdn_min_pct"), st.number_input, "FDN mínimo (% MS)", cast=float,
                 min_value=0.0, step=0.5, format="%.1f")
with c[5]:
    estado.campo(("exigencias", "ee_max_pct"), st.number_input, "EE máximo (% MS)", cast=float,
                 min_value=0.0, step=0.5, format="%.1f")
with c[6]:
    estado.campo(("exigencias", "amido_max_pct"), st.number_input, "Amido máx. (% MS)", cast=float,
                 min_value=0.0, step=0.5, format="%.1f", help="Exigido apenas na ração feita no computador.")

ex = estado.exig()
ims = an.ims_kg
tab = pd.DataFrame([
    ("PB", "mínimo", ex.pb_kg, 100 * ex.pb_kg / ims),
    ("NDT", "mínimo", ex.ndt_kg, 100 * ex.ndt_kg / ims),
    ("Cálcio", "mínimo", ex.ca_pct / 100 * ims, ex.ca_pct),
    ("Fósforo", "mínimo", ex.p_pct / 100 * ims, ex.p_pct),
    ("FDN", "mínimo", ex.fdn_min_pct / 100 * ims, ex.fdn_min_pct),
    ("EE", "máximo", ex.ee_max_pct / 100 * ims, ex.ee_max_pct),
    ("Amido (ração 3)", "máximo", ex.amido_max_pct / 100 * ims, ex.amido_max_pct),
], columns=["Nutriente", "Tipo", "kg/vaca/dia", "% da MS"])
tab["kg/dia para o lote"] = tab["kg/vaca/dia"] * an.n_vacas
mostrar_df(tab, casas={"kg/vaca/dia": 3, "kg/dia para o lote": 1})

with st.expander("📐 Estimativa pelo NRC (2001) — apenas referência"):
    st.markdown(
        "Equações usadas: **LCG 4%** = 0,4 × leite + 15 × gordura (kg); "
        "**IMS** = (0,372 × LCG + 0,0968 × PC^0,75) × (1 − e^(−0,192 × (semana + 3,67))); "
        "**ELL mantença** = 0,08 × PC^0,75; **ELL do leite** = 0,0929 × G% + 0,0547 × P% + 0,0395 × 4,85 (lactose); "
        "**NDT equivalente** por ELL (Mcal/kg MS) = 0,0245 × NDT% − 0,12.")
    est = estimativa_nrc(an)
    mostrar_df(pd.DataFrame({"Item": list(est), "Valor": list(est.values())}), padrao=2)
    st.info(f"Comparação: NDT informado {br(ex.ndt_kg, 2)} kg × NDT equivalente NRC "
            f"{br(est['NDT equivalente (kg/dia)'], 2)} kg; IMS informada {br(ims, 2)} kg × IMS prevista NRC "
            f"{br(est['IMS prevista NRC 2001 (kg MS/dia)'], 2)} kg. O balanceamento usa sempre os valores informados.")
