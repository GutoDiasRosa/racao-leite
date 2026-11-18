import pytest

from core.alimentos_padrao import ALIMENTOS_PADRAO, ADITIVOS_INFO
from core.nutricao import Animal, Exigencias


@pytest.fixture
def alimentos():
    return {a["nome"]: dict(a) for a in ALIMENTOS_PADRAO}


@pytest.fixture
def animal():
    return Animal()


@pytest.fixture
def exig():
    return Exigencias()


@pytest.fixture
def aditivos():
    return {n: dict(ADITIVOS_INFO[n]) for n in ["Bicarbonato de sódio", "Monensina sódica (premix 10%)"]}
