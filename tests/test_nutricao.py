import pytest

from core.nutricao import (avaliar, checklist, com_aditivos, composicao, conta_alimentos, dicas,
                           estimativa_nrc, metas, status_meta, Meta)


def test_ims_e_metas_do_trabalho(animal, exig):
    assert animal.ims_kg == pytest.approx(24.308, abs=1e-3)
    m = {x.nutriente: x for x in metas(animal, exig)}
    assert m["PB"].pct_ms == pytest.approx(16.46, abs=0.01)
    assert m["NDT"].pct_ms == pytest.approx(72.08, abs=0.01)
    assert m["Ca"].kg == pytest.approx(0.1483, abs=1e-4)
    assert m["P"].kg == pytest.approx(0.0875, abs=1e-4)
    assert m["FDN"].kg == pytest.approx(7.049, abs=1e-3)
    assert m["EE"].kg == pytest.approx(1.215, abs=1e-3)
    assert m["Amido"].kg == pytest.approx(6.320, abs=1e-3)
    assert "Amido" not in {x.nutriente for x in metas(animal, exig, incluir_amido=False)}


def test_composicao_soma_nutrientes(alimentos):
    racao = {"Silagem de milho": 10.0, "Farelo de soja": 2.0}
    s, f = alimentos["Silagem de milho"], alimentos["Farelo de soja"]
    c = composicao(racao, alimentos)
    assert c["MS"] == pytest.approx(12.0)
    assert c["PB"] == pytest.approx(10 * s["PB"] / 100 + 2 * f["PB"] / 100)
    assert c["MN"] == pytest.approx(10 / (s["MS"] / 100) + 2 / (f["MS"] / 100))
    assert c["custo"] == pytest.approx(10 / (s["MS"] / 100) * s["preco"] + 2 / (f["MS"] / 100) * f["preco"])
    assert c["pct"]["PB"] == pytest.approx(100 * c["PB"] / 12)


def test_aditivos_entram_em_kg_ms(alimentos, aditivos):
    r = com_aditivos({"Silagem de milho": 10}, aditivos, alimentos)
    assert r["Bicarbonato de sódio"] == pytest.approx(0.2 * alimentos["Bicarbonato de sódio"]["MS"] / 100)
    assert r["Monensina sódica (premix 10%)"] == pytest.approx(
        0.003 * alimentos["Monensina sódica (premix 10%)"]["MS"] / 100)
    assert conta_alimentos(r, alimentos) == 1   # aditivos não contam


def test_status():
    m = Meta("PB", "min", 4.0, 16.46, 0.10)
    assert status_meta(m, 4.0) == "ok"
    assert status_meta(m, 3.9) == "perto"
    assert status_meta(m, 3.0) == "fora"
    assert status_meta(m, 4.5) == "excesso"
    mx = Meta("EE", "max", 1.2, 5)
    assert status_meta(mx, 1.0) == "ok" and status_meta(mx, 1.5) == "fora"


def test_avaliar_e_checklist(alimentos, animal, exig, aditivos):
    racao = com_aditivos({"Silagem de milho": 12, "Milho grão moído": 5, "Farelo de soja": 4.5,
                          "Caroço de algodão": 1.5, "Calcário calcítico": 0.25,
                          "Fosfato bicálcico": 0.05}, aditivos, alimentos)
    linhas = avaliar(racao, alimentos, animal, exig, incluir_amido=False)
    assert linhas[0]["Nutriente"] == "MS (IMS)"
    itens = checklist(racao, alimentos, animal, exig, aditivos, incluir_amido=False)
    assert itens[0]["OK"] is True          # 4 alimentos
    assert itens[1]["OK"] is True          # silagem de milho
    assert itens[2]["OK"] is True          # 2 aditivos


def test_dicas_apontam_falta(alimentos, animal, exig):
    d = dicas({"Silagem de milho": 12, "Farelo de soja": 2}, alimentos, animal, exig)
    assert any("Faltam" in x and "MS" in x for x in d)
    assert any("PB" in x for x in d)


def test_estimativa_nrc(animal):
    e = estimativa_nrc(animal)
    assert e["LCG 4% (kg/dia)"] == pytest.approx(38.2)
    assert e["ELL mantença (Mcal/dia)"] == pytest.approx(0.08 * 590 ** 0.75)
    assert e["ELL por kg de leite (Mcal/kg)"] == pytest.approx(0.7162, abs=1e-3)
    assert 20 < e["IMS prevista NRC 2001 (kg MS/dia)"] < 30
    assert 60 < e["NDT equivalente (% MS)"] < 80
