import numpy as np
import pytest

from core.algebrico import gauss_jordan, racao_final, resolver
from core.nutricao import avaliar, com_aditivos, composicao


def test_gauss_jordan_confere_com_numpy():
    rng = np.random.default_rng(1)
    A = rng.uniform(0, 1, (5, 5))
    b = rng.uniform(0, 10, 5)
    x, passos, msg = gauss_jordan(A.tolist(), b.tolist())
    assert msg == ""
    assert np.allclose(x, np.linalg.solve(A, b))
    assert len(passos) == 5


def test_gauss_jordan_detecta_sistema_singular():
    x, _, msg = gauss_jordan([[1, 2], [2, 4]], [3, 6])
    assert x is None and "solução única" in msg


def test_exemplo_classico_5x5(alimentos, animal, exig, aditivos):
    fixos = com_aditivos({"Caroço de algodão": 1.5}, aditivos, alimentos)
    inc = ["Silagem de milho", "Milho grão moído", "Farelo de soja", "Calcário calcítico", "Fosfato bicálcico"]
    res = resolver(inc, ["MS", "PB", "NDT", "Ca", "P"], fixos, alimentos, animal, exig)
    assert res.viavel, res.mensagem
    racao = racao_final(res, fixos)
    comp = composicao(racao, alimentos)
    # o sistema fecha exatamente MS, PB, NDT, Ca e P
    assert comp["MS"] == pytest.approx(animal.ims_kg)
    assert comp["PB"] == pytest.approx(exig.pb_kg)
    assert comp["NDT"] == pytest.approx(exig.ndt_kg)
    assert comp["Ca"] == pytest.approx(exig.ca_pct / 100 * animal.ims_kg)
    assert comp["P"] == pytest.approx(exig.p_pct / 100 * animal.ims_kg)
    # ordem de grandeza esperada no planejamento
    assert 9 < res.solucao["Silagem de milho"] < 15
    assert 3 < res.solucao["Milho grão moído"] < 8
    assert 3 < res.solucao["Farelo de soja"] < 6
    # FDN e EE atendem; amido passa de 26% (motivo da ração 3)
    linhas = {l["Nutriente"]: l for l in avaliar(racao, alimentos, animal, exig, incluir_amido=True)}
    assert linhas["FDN"]["Status"] == "ok"
    assert linhas["EE"]["Status"] == "ok"
    assert linhas["Amido"]["Fornecido (% MS)"] > 26


def test_solucao_negativa_e_inviavel(alimentos, animal, exig):
    # muito caroço de algodão fixo: sobra pouca MS e o sistema pede quantidade negativa
    res = resolver(["Silagem de milho", "Farelo de soja"], ["MS", "PB"],
                   {"Caroço de algodão": 20.0}, alimentos, animal, exig)
    assert res.solucao is not None
    assert not res.viavel and "negativa" in res.mensagem


def test_numero_de_equacoes_diferente(alimentos, animal, exig):
    res = resolver(["Silagem de milho", "Farelo de soja"], ["MS", "PB", "NDT"], {}, alimentos, animal, exig)
    assert res.solucao is None and "igual" in res.mensagem
