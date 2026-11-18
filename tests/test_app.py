"""Teste de fumaça: abre cada página do app sem navegador e verifica que não há exceções."""
import os
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

RAIZ = Path(__file__).resolve().parent.parent
PAGINAS = ["1_animal", "2_alimentos", "6_aditivos", "3_tentativa_erro", "4_algebrico", "5_computador",
           "7_silo", "8_relatorio"]


@pytest.fixture(autouse=True)
def projeto_temporario(tmp_path, monkeypatch):
    monkeypatch.setenv("RACAO_PROJETO", str(tmp_path / "projeto.json"))
    monkeypatch.chdir(RAIZ)
    import estado
    monkeypatch.setattr(estado, "ARQUIVO", tmp_path / "projeto.json")


@pytest.mark.parametrize("pagina", PAGINAS)
def test_pagina_abre_sem_erro(pagina):
    at = AppTest.from_file(str(RAIZ / "app.py"), default_timeout=60)
    at.run()
    at.switch_page(f"paginas/{pagina}.py").run()
    assert not at.exception, [e.value for e in at.exception]
    assert at.title, "a página deveria ter título"


def test_tentativa_reage_a_edicao():
    at = AppTest.from_file(str(RAIZ / "app.py"), default_timeout=60)
    at.run()
    at.switch_page("paginas/3_tentativa_erro.py").run()
    campo = at.number_input(key="w_tentativa.racao.Farelo de soja")
    campo.set_value(4.5).run()
    assert not at.exception
    assert at.session_state["projeto"]["tentativa"]["racao"]["Farelo de soja"] == 4.5
    at.button[0].click().run()   # Salvar tentativa
    assert len(at.session_state["projeto"]["tentativa"]["historico"]) == 1
