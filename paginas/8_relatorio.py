from dataclasses import asdict

import pandas as pd
import streamlit as st

import estado
from comum import mostrar_df, parametros_silo, racoes_finais, rodar_pl
from core.formatar import br
from core.relatorio import df_animal, gerar_html, gerar_xlsx, montar_relatorio
from core.silo import calcular_silo

st.title("📄 Relatório final")
st.caption("Reúne as três rações, os aditivos e o silo. Baixe em **HTML** (abra no navegador e use Imprimir → "
           "Salvar como PDF) ou em **Excel** para copiar as tabelas para o modelo do professor.")

p = estado.projeto()
al = estado.alimentos()
an, ex = estado.animal(), estado.exig()
if "w_rel_titulo" not in st.session_state:
    st.session_state["w_rel_titulo"] = p.get("titulo_relatorio", "Balanceamento de rações — vacas em lactação")
titulo = st.text_input("Título do relatório", key="w_rel_titulo")
p["titulo_relatorio"] = titulo

racoes = racoes_finais()
rel = montar_relatorio(racoes, al, an, ex, p["aditivos"])
pl = rodar_pl()
prm, _ = parametros_silo()
silo = calcular_silo(prm)
hist = pd.DataFrame(p["tentativa"]["historico"]).fillna(0.0) if p["tentativa"]["historico"] else None

faltando = [t for t in racoes if t not in rel]
if faltando:
    st.warning("Ainda sem ração válida: " + "; ".join(faltando))

st.subheader("Resumo")
resumo = []
for t, tabs in rel.items():
    ck = tabs["checklist"]
    pend = ck[ck["OK"] == "✘"]["Item"].tolist()
    resumo.append({"Ração": t, "Custo R$/vaca/dia": tabs["custo"], "Custo R$/lote/dia": tabs["custo"] * an.n_vacas,
                   "Checklist": "✅ completo" if not pend else "⚠️ " + "; ".join(pend)})
mostrar_df(pd.DataFrame(resumo))

abas = st.tabs(["Animal"] + list(rel) + ["Aditivos", "Silo"])
with abas[0]:
    st.dataframe(df_animal(an, ex).astype(str), hide_index=True, width="stretch")
for aba, (t, tabs) in zip(abas[1:], rel.items()):
    with aba:
        st.markdown("**Fórmula**")
        mostrar_df(tabs["ingredientes"], casas={"kg MN/vaca/dia": 3, "kg MS/vaca/dia": 3, "kg MN lote/dia": 1})
        st.markdown("**Nutrientes**")
        mostrar_df(tabs["nutrientes"], casas={"Exigido (kg)": 3, "Fornecido (kg)": 3, "Diferença (kg)": 3})
        st.markdown("**Checklist**")
        st.dataframe(tabs["checklist"], hide_index=True, width="stretch")
with abas[-2]:
    for n, i in p["aditivos"].items():
        st.markdown(f"**{n}** — {br(i['dose_kg'] * 1000, 1)} g/vaca/dia")
        st.write(i["justificativa"])
with abas[-1]:
    mostrar_df(pd.DataFrame(silo["passos"], columns=["Etapa", "Cálculo", "Resultado"]))

html = gerar_html(titulo, an, ex, rel, p["aditivos"], silo, asdict(pl) if pl.sucesso else None, hist)

planilhas = {"Animal": df_animal(an, ex)}
for i, (t, tabs) in enumerate(rel.items(), start=1):
    n = t.split(" — ")[0].replace("Ração ", "R")
    planilhas[f"{n} Formula"] = tabs["ingredientes"]
    planilhas[f"{n} Nutrientes"] = tabs["nutrientes"]
    planilhas[f"{n} Checklist"] = tabs["checklist"]
if hist is not None:
    planilhas["R1 Tentativas"] = hist
if pl.sucesso:
    planilhas["R3 Restricoes"] = pd.DataFrame(pl.restricoes)
    planilhas["R3 Alimentos"] = pd.DataFrame(pl.alimentos)
planilhas["Aditivos"] = pd.DataFrame([{"Aditivo": n, "Dose (g/vaca/dia)": i["dose_kg"] * 1000,
                                       "Justificativa": i["justificativa"]} for n, i in p["aditivos"].items()])
planilhas["Silo"] = pd.DataFrame(silo["passos"], columns=["Etapa", "Cálculo", "Resultado"])
planilhas["Alimentos"] = pd.DataFrame(list(al.values()))

c1, c2 = st.columns(2)
c1.download_button("⬇️ Relatório (HTML → imprimir em PDF)", html.encode("utf-8"), file_name="relatorio_racao.html",
                   mime="text/html", type="primary", width="stretch")
c2.download_button("⬇️ Tabelas (Excel .xlsx)", gerar_xlsx(planilhas), file_name="relatorio_racao.xlsx",
                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", width="stretch")
