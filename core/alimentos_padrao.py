"""Biblioteca padrão de alimentos e aditivos.

Composição em % da matéria seca (MS), exceto MS (% da matéria natural).
Preço em R$/kg de matéria natural (MN) — valores de referência, atualize.

Volumosos, concentrados e minerais: médias do CQBAL 4.0 (https://www.cqbal.com.br),
consultadas em 18/11/2026. O NDT é o "NDT_BRCORTE2016" calculado pelo próprio CQBAL.
Atenção: para o caroço de algodão esse NDT calculado (96%) fica bem acima dos
valores usuais de tabela (~77–80%, NRC 2001), por causa do EE alto.
Ureia: composição química (45% N × 6,25). Núcleo e aditivos: usar o rótulo do produto.
"""

CATEGORIAS = [
    "Volumoso",
    "Concentrado energético",
    "Concentrado proteico",
    "Mineral/vitamínico",
    "Aditivo",
]

# Categorias que NÃO contam para a regra "mínimo de 4 alimentos".
CATEGORIAS_NAO_CONTAM = {"Mineral/vitamínico", "Aditivo"}

COLUNAS = ["nome", "categoria", "MS", "PB", "NDT", "FDN", "EE", "Ca", "P", "Amido", "preco", "fonte"]

_CONFERIR = "Típico — conferir no CQBAL"


def _a(nome, categoria, MS, PB, NDT, FDN, EE, Ca, P, Amido, preco, fonte=_CONFERIR):
    return dict(nome=nome, categoria=categoria, MS=MS, PB=PB, NDT=NDT, FDN=FDN, EE=EE,
                Ca=Ca, P=P, Amido=Amido, preco=preco, fonte=fonte)


ALIMENTOS_PADRAO = [
    #  nome                      categoria                 MS     PB     NDT    FDN    EE     Ca     P      Amido  preço
    _a("Silagem de milho", "Volumoso", 31.02, 7.12, 64.86, 52.15, 2.77, 0.28, 0.19, 25.15, 0.30,
       "CQBAL 4.0 — Milho silagem"),
    _a("Silagem de sorgo", "Volumoso", 29.65, 6.45, 61.44, 58.03, 2.58, 0.32, 0.18, 14.85, 0.25,
       "CQBAL 4.0 — Sorgo silagem (amido: n=3)"),
    _a("Feno de Tifton 85", "Volumoso", 88.66, 9.27, 55.44, 77.36, 1.61, 0.41, 0.24, 7.02, 0.90,
       "CQBAL 4.0 — Capim Tifton 85 feno (amido: n=1)"),
    _a("Milho grão moído", "Concentrado energético", 87.88, 8.96, 87.32, 13.42, 4.00, 0.03, 0.26, 73.66, 1.30,
       "CQBAL 4.0 — Milho fubá"),
    _a("Polpa cítrica", "Concentrado energético", 88.38, 6.93, 79.03, 24.47, 3.10, 1.81, 0.13, 6.70, 1.10,
       "CQBAL 4.0 — Citrus polpa"),
    _a("Casca de soja", "Concentrado energético", 90.10, 12.67, 74.14, 66.39, 2.22, 0.52, 0.16, 3.78, 1.00,
       "CQBAL 4.0 — Soja casca"),
    _a("Farelo de trigo", "Concentrado energético", 87.64, 16.68, 78.54, 42.22, 3.56, 0.17, 1.01, 32.48, 1.00,
       "CQBAL 4.0 — Trigo farelo (amido: n=5)"),
    _a("Farelo de soja", "Concentrado proteico", 88.65, 48.85, 80.27, 14.79, 1.93, 0.34, 0.59, 6.18, 2.30,
       "CQBAL 4.0 — Soja farelo"),
    _a("Caroço de algodão", "Concentrado proteico", 90.66, 22.94, 96.35, 45.65, 20.06, 0.27, 0.74, 0.65, 1.40,
       "CQBAL 4.0 — Algodão caroço (NDT calculado alto; tabelas ~77–80%)"),
    _a("Ureia pecuária", "Concentrado proteico", 99.0, 281.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 3.50,
       "Composição química (45% N × 6,25) — não consta no CQBAL"),
    _a("Calcário calcítico", "Mineral/vitamínico", 99.91, 0.11, 0.0, 0.0, 0.0, 37.40, 0.37, 0.0, 0.30,
       "CQBAL 4.0 — Calcário calcítico"),
    _a("Fosfato bicálcico", "Mineral/vitamínico", 98.44, 0.0, 0.0, 0.0, 0.0, 24.12, 18.54, 0.0, 5.00,
       "CQBAL 4.0 — Fosfato bicálcico"),
    _a("Sal comum", "Mineral/vitamínico", 99.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.80, "Sem Ca/P"),
    _a("Núcleo mineral-vitamínico", "Mineral/vitamínico", 99.0, 0.0, 0.0, 0.0, 0.0, 18.0, 6.0, 0.0, 6.00,
       "Exemplo — usar o rótulo do produto"),
    # Aditivos: composição nutricional desprezível para os nutrientes do balanceamento.
    _a("Bicarbonato de sódio", "Aditivo", 99.0, 0, 0, 0, 0, 0, 0, 0, 4.00, "Aditivo"),
    _a("Óxido de magnésio", "Aditivo", 99.0, 0, 0, 0, 0, 0, 0, 0, 6.00, "Aditivo"),
    _a("Monensina sódica (premix 10%)", "Aditivo", 95.0, 0, 0, 0, 0, 0, 0, 0, 60.00, "Aditivo"),
    _a("Levedura viva (S. cerevisiae)", "Aditivo", 93.0, 0, 0, 0, 0, 0, 0, 0, 40.00, "Aditivo"),
    _a("Biotina (premix 2%)", "Aditivo", 95.0, 0, 0, 0, 0, 0, 0, 0, 80.00, "Aditivo"),
]

# Dose de referência (kg de produto, MN, por vaca/dia) e justificativa padrão.
ADITIVOS_INFO = {
    "Bicarbonato de sódio": {
        "dose_kg": 0.200,
        "justificativa": (
            "Tamponante ruminal. Vacas produzindo 40 kg/dia recebem muito concentrado e amido, o que "
            "aumenta a produção de ácidos no rúmen e o risco de acidose ruminal subaguda. O bicarbonato "
            "ajuda a manter o pH ruminal, favorece as bactérias que digerem fibra e contribui para manter "
            "o consumo e o teor de gordura do leite. Dose usual: 0,75 a 1% da MS (≈150–250 g/vaca/dia)."
        ),
    },
    "Óxido de magnésio": {
        "dose_kg": 0.060,
        "justificativa": (
            "Agente alcalinizante e fonte de magnésio. Usado junto com o bicarbonato reforça o efeito "
            "tamponante e ajuda a manter a gordura do leite; também supre Mg, cuja absorção diminui em "
            "dietas ricas em potássio (silagens). Dose usual: 40–90 g/vaca/dia."
        ),
    },
    "Monensina sódica (premix 10%)": {
        "dose_kg": 0.003,
        "justificativa": (
            "Ionóforo que modifica a fermentação ruminal: aumenta a produção de propionato e reduz "
            "acetato, metano e perdas de energia. Melhora a eficiência alimentar e reduz o risco de "
            "cetose e de acidose. Dose usual: 250–450 mg de monensina/vaca/dia (ex.: 3 g de premix a "
            "10% = 300 mg). Atenção: tóxica para equinos."
        ),
    },
    "Levedura viva (S. cerevisiae)": {
        "dose_kg": 0.010,
        "justificativa": (
            "Probiótico que consome o oxigênio presente no rúmen, favorecendo bactérias anaeróbias "
            "celulolíticas e as que utilizam lactato. Estabiliza o pH, melhora a digestão da fibra e "
            "pode aumentar o consumo e a produção de leite em dietas ricas em amido. Dose conforme o "
            "fabricante (geralmente 5–15 g/vaca/dia)."
        ),
    },
    "Biotina (premix 2%)": {
        "dose_kg": 0.001,
        "justificativa": (
            "Vitamina do complexo B que participa da formação da queratina do casco. Melhora a "
            "integridade do casco e reduz problemas de claudicação, comuns em vacas de alta produção "
            "com dietas ricas em concentrado. Dose usual: 20 mg/vaca/dia (ex.: 1 g de premix a 2%)."
        ),
    },
}

ADITIVOS_SELECIONADOS_PADRAO = ["Bicarbonato de sódio", "Monensina sódica (premix 10%)"]
