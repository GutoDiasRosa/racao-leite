import pytest

from core.nutricao import avaliar, checklist, com_aditivos, composicao
from core.otimizacao import otimizar

SEL = ["Silagem de milho", "Milho grão moído", "Polpa cítrica", "Casca de soja", "Farelo de soja",
       "Caroço de algodão", "Calcário calcítico", "Fosfato bicálcico"]


def test_pl_atende_tudo_com_amido(alimentos, animal, exig, aditivos):
    fixos = com_aditivos({}, aditivos, alimentos)
    lim = {"Silagem de milho": (0.40 * animal.ims_kg, None)}
    r = otimizar(alimentos, SEL, lim, animal, exig, incluir_amido=True, fixos=fixos)
    assert r.sucesso and not r.nao_atendidas, r.mensagem
    racao = r.racao
    assert racao["Silagem de milho"] >= 0.40 * animal.ims_kg - 1e-6
    comp = composicao(racao, alimentos)
    ims = animal.ims_kg
    assert comp["MS"] == pytest.approx(ims)
    assert comp["PB"] >= exig.pb_kg - 1e-6
    assert comp["NDT"] >= exig.ndt_kg - 1e-6
    assert comp["Ca"] >= exig.ca_pct / 100 * ims - 1e-6
    assert comp["P"] >= exig.p_pct / 100 * ims - 1e-6
    assert comp["FDN"] >= exig.fdn_min_pct / 100 * ims - 1e-6
    assert comp["EE"] <= exig.ee_max_pct / 100 * ims + 1e-6
    assert comp["Amido"] <= exig.amido_max_pct / 100 * ims + 1e-6
    # teto padrão de +15% para Ca e P (evita calcário como "enchimento")
    assert comp["Ca"] <= 1.15 * exig.ca_pct / 100 * ims + 1e-6
    assert comp["P"] <= 1.15 * exig.p_pct / 100 * ims + 1e-6
    assert r.custo_vaca == pytest.approx(comp["custo"], rel=1e-6)
    assert r.custo_lote == pytest.approx(r.custo_vaca * animal.n_vacas)
    assert all(l["Status"] in ("ok", "excesso") for l in avaliar(racao, alimentos, animal, exig, True))


def test_minimos_garantem_quatro_alimentos(alimentos, animal, exig, aditivos):
    fixos = com_aditivos({}, aditivos, alimentos)
    lim = {"Silagem de milho": (9.7, None), "Milho grão moído": (1.0, None),
           "Farelo de soja": (1.0, None), "Caroço de algodão": (1.0, None)}
    r = otimizar(alimentos, SEL, lim, animal, exig, incluir_amido=True, fixos=fixos)
    itens = checklist(r.racao, alimentos, animal, exig, aditivos, True)
    assert itens[0]["OK"]


def test_inviavel_aponta_restricao(alimentos, animal, exig):
    # só silagem e milho: impossível atingir 16,5% de PB
    r = otimizar(alimentos, ["Silagem de milho", "Milho grão moído"], {}, animal, exig, True)
    assert r.sucesso
    assert any(x.startswith("PB") for x in r.nao_atendidas)
    sit = {x["Restrição"]: x["Situação"] for x in r.restricoes}
    assert sit["PB"] == "NÃO ATENDIDA"


def test_sem_teto_calcario_vira_enchimento(alimentos, animal, exig, aditivos):
    """Documenta por que o teto de minerais existe."""
    fixos = com_aditivos({}, aditivos, alimentos)
    lim = {"Silagem de milho": (0.40 * animal.ims_kg, None)}
    sem = otimizar(alimentos, SEL, lim, animal, exig, True, fixos, tol_minerais=None)
    com = otimizar(alimentos, SEL, lim, animal, exig, True, fixos)
    ca = lambda r: composicao(r.racao, alimentos)["pct"]["Ca"]  # noqa: E731
    assert ca(com) <= 1.15 * exig.ca_pct + 1e-6
    assert ca(sem) >= ca(com)
    assert any(x["Restrição"] == "Ca (máx)" for x in com.restricoes)


def test_minimos_maiores_que_ims(alimentos, animal, exig):
    r = otimizar(alimentos, ["Silagem de milho", "Farelo de soja"],
                 {"Silagem de milho": (20, None), "Farelo de soja": (10, None)}, animal, exig)
    assert not r.sucesso and "mínimos" in r.mensagem
