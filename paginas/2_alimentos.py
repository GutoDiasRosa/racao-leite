import copy
import io

import pandas as pd
import streamlit as st

import estado
from core.alimentos_padrao import ALIMENTOS_PADRAO, CATEGORIAS, COLUNAS

st.title("🌽 Alimentos")
st.caption("Composição em **% da MS** (exceto MS, em % da matéria natural). Preço em R$/kg de matéria natural. "
           "Edite as células, adicione linhas no fim da tabela ou apague linhas selecionando-as.")
st.info("Composição dos volumosos, concentrados e minerais: médias do [CQBAL 4.0](https://www.cqbal.com.br/#!/) "
        "(NDT = valor calculado BR-Corte 2016 do próprio CQBAL). O NDT do **caroço de algodão** calculado pelo CQBAL "
        "(96%) é bem maior que o de tabelas como o NRC 2001 (~77–80%): ajuste se o professor preferir. "
        "Os **preços** são apenas referência — atualize.", icon="📚")

p = estado.projeto()

if "ed_alimentos" not in st.session_state:
    st.session_state["base_alimentos"] = pd.DataFrame(p["alimentos"], columns=COLUNAS)

num = lambda t, f="%.2f", h=None: st.column_config.NumberColumn(t, format=f, min_value=0.0, help=h)  # noqa: E731
editado = st.data_editor(
    st.session_state["base_alimentos"], key="ed_alimentos", num_rows="dynamic", hide_index=True,
    width="stretch", height=560,
    column_config={
        "nome": st.column_config.TextColumn("Alimento", required=True, width="medium"),
        "categoria": st.column_config.SelectboxColumn("Categoria", options=CATEGORIAS, required=True),
        "MS": num("MS (% MN)", "%.1f"), "PB": num("PB"), "NDT": num("NDT"), "FDN": num("FDN"),
        "EE": num("EE"), "Ca": num("Ca"), "P": num("P"), "Amido": num("Amido"),
        "preco": num("Preço R$/kg MN"), "fonte": st.column_config.TextColumn("Fonte", width="medium"),
    },
)
p["alimentos"] = editado.to_dict("records")

nomes = [str(n).strip() for n in editado["nome"].dropna()]
dup = sorted({n for n in nomes if nomes.count(n) > 1})
if dup:
    st.error(f"Nomes repetidos: {', '.join(dup)}. Cada alimento precisa de um nome único.")
sem_ms = [n for n, a in estado.alimentos().items() if a["MS"] <= 0]
if sem_ms:
    st.error(f"Alimentos sem MS: {', '.join(sem_ms)}. Informe a matéria seca.")

c1, c2, c3 = st.columns(3)
with c1:
    st.download_button("⬇️ Baixar tabela (.csv)", editado.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
                       file_name="alimentos.csv", mime="text/csv", width="stretch")
with c2:
    arq = st.file_uploader("Importar tabela (.csv no mesmo formato)", type=["csv"], key="upload_alimentos")
    if arq is not None and st.session_state.get("_upload_alim") != f"{arq.name}-{arq.size}":
        try:
            df = pd.read_csv(io.BytesIO(arq.getvalue()), sep=";", decimal=",", encoding="utf-8-sig")
            faltam = [c for c in COLUNAS if c not in df.columns]
            if faltam:
                st.error(f"Colunas ausentes: {', '.join(faltam)}")
            else:
                st.session_state["_upload_alim"] = f"{arq.name}-{arq.size}"
                p["alimentos"] = df[COLUNAS].to_dict("records")
                for k in ("ed_alimentos", "base_alimentos"):
                    st.session_state.pop(k, None)
                st.rerun()
        except Exception as e:  # noqa: BLE001
            st.error(f"Não consegui ler o arquivo: {e}")
with c3:
    if st.button("↺ Restaurar alimentos padrão", width="stretch"):
        p["alimentos"] = copy.deepcopy(ALIMENTOS_PADRAO)
        for k in ("ed_alimentos", "base_alimentos"):
            st.session_state.pop(k, None)
        st.rerun()

with st.expander("Como as categorias são usadas"):
    st.markdown(
        "- **Volumoso / Concentrado energético / Concentrado proteico** contam para a regra de *no mínimo "
        "4 alimentos*.\n"
        "- **Mineral/vitamínico** (calcário, fosfato, sal, núcleo) **não contam** para essa regra.\n"
        "- **Aditivo** aparece na página *Aditivos* e entra com dose fixa nas três rações.\n"
        "- A regra da silagem de milho procura um alimento cujo nome contenha \"silagem de milho\".")
