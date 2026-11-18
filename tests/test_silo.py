import pytest

from core.relatorio import gerar_html, gerar_xlsx, montar_relatorio
from core.silo import ParametrosSilo, calcular_silo


def test_silo_exemplo_do_plano():
    p = ParametrosSilo(kg_ms_vaca=12, ms_silagem_pct=32, n_vacas=130, dias=365, perdas_pct=15,
                       densidade=600, fatia_m=0.25, altura_m=2.5, formato="retangular",
                       produtividade_t_ha=45, comprimento_max_m=200)
    s = calcular_silo(p)
    assert s["diario_kg"] == pytest.approx(4875)
    assert s["necessidade_kg"] == pytest.approx(4875 * 365 / 0.85)
    assert s["volume_m3"] == pytest.approx(3489, abs=1)
    assert s["area_painel_m2"] == pytest.approx(32.5)
    assert s["base_menor_m"] == pytest.approx(13.0)
    assert s["comprimento_m"] == pytest.approx(107.4, abs=0.1)
    assert s["area_ha"] == pytest.approx(46.5, abs=0.1)
    assert s["n_silos"] == 1


def test_silo_trapezoidal_e_divisao():
    p = ParametrosSilo(kg_ms_vaca=12, ms_silagem_pct=32, formato="trapezoidal", inclinacao=0.25,
                       altura_m=2.5, comprimento_max_m=60)
    s = calcular_silo(p)
    H = 2.5
    area = (s["base_menor_m"] + s["base_maior_m"]) / 2 * H
    assert area == pytest.approx(s["area_painel_m2"])
    assert s["base_maior_m"] - s["base_menor_m"] == pytest.approx(2 * 0.25 * H)
    assert s["n_silos"] == 2 and s["alertas"]


def test_exportacoes(alimentos, animal, exig, aditivos):
    racoes = {"Ração 1 — Tentativa e erro": ({"Silagem de milho": 12, "Farelo de soja": 4,
                                              "Bicarbonato de sódio": 0.198}, False)}
    rel = montar_relatorio(racoes, alimentos, animal, exig, aditivos)
    silo = calcular_silo(ParametrosSilo())
    html = gerar_html("Teste", animal, exig, rel, aditivos, silo, None)
    assert "Silagem de milho" in html and "Tamponante" in html and "Comprimento total" in html
    xlsx = gerar_xlsx({"Ingredientes R1": rel["Ração 1 — Tentativa e erro"]["ingredientes"]})
    assert xlsx[:2] == b"PK"
