"""Balanceamento de rações para vacas em lactação — ponto de entrada do Streamlit.

Rodar:  streamlit run app.py
"""
import json

import streamlit as st

st.set_page_config(page_title="Balanceamento de Rações", page_icon="🐄", layout="wide")

import estado  # noqa: E402
from core.formatar import br  # noqa: E402

paginas = [
    st.Page("paginas/1_animal.py", title="Animal e exigências", icon="🐄", default=True),
    st.Page("paginas/2_alimentos.py", title="Alimentos", icon="🌽"),
    st.Page("paginas/6_aditivos.py", title="Aditivos", icon="🧪"),
    st.Page("paginas/3_tentativa_erro.py", title="1. Tentativa e erro", icon="✏️"),
    st.Page("paginas/4_algebrico.py", title="2. Processo algébrico", icon="➗"),
    st.Page("paginas/5_computador.py", title="3. Computador (PL)", icon="💻"),
    st.Page("paginas/7_silo.py", title="Silo e lavoura", icon="🏗️"),
    st.Page("paginas/8_relatorio.py", title="Relatório final", icon="📄"),
]
pg = st.navigation(paginas)
estado.projeto()
pg.run()  # a página roda antes da barra lateral para o resumo já refletir as edições

an, ex = estado.animal(), estado.exig()

with st.sidebar:
    st.markdown("### Lote")
    st.markdown(
        f"**{an.n_vacas} vacas** · {an.peso:g} kg · {an.leite:g} kg leite  \n"
        f"IMS **{br(an.ims_kg, 2)} kg MS**/vaca/dia  \n"
        f"PB {br(ex.pb_kg, 2)} kg · NDT {br(ex.ndt_kg, 2)} kg  \n"
        f"Ca {br(ex.ca_pct, 2)}% · P {br(ex.p_pct, 2)}% · FDN ≥ {br(ex.fdn_min_pct, 0)}%  \n"
        f"EE ≤ {br(ex.ee_max_pct, 0)}% · Amido ≤ {br(ex.amido_max_pct, 0)}% (ração 3)"
    )
    st.divider()
    st.markdown("### Projeto")
    if estado.autosave_ativo():
        st.caption("Salvo automaticamente em `dados/projeto.json`.")
    else:
        st.caption("Versão online: nada fica salvo no servidor. **Baixe o projeto** para guardar o "
                   "trabalho e abra o arquivo depois para continuar.")
    st.download_button("⬇️ Baixar projeto (.json)", estado.para_json(), file_name="projeto_racao.json",
                       mime="application/json", width="stretch")
    arq = st.file_uploader("Abrir projeto (.json)", type=["json"], key="upload_projeto")
    if arq is not None:
        ident = f"{arq.name}-{arq.size}"
        if st.session_state.get("_upload_id") != ident:
            try:
                novo = json.loads(arq.getvalue().decode("utf-8"))
                st.session_state["_upload_id"] = ident
                estado.substituir(novo)
                st.rerun()
            except ValueError:
                st.error("Arquivo inválido.")
    with st.popover("↺ Restaurar exemplo do trabalho", width="stretch"):
        st.write("Apaga as alterações e volta aos dados da folha do trabalho.")
        if st.button("Confirmar restauração", type="primary"):
            estado.substituir(estado.projeto_padrao())
            st.session_state.pop("_upload_id", None)
            st.rerun()

estado.salvar()
