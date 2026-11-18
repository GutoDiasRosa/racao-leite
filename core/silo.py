"""Dimensionamento do silo trincheira, fatia diária e área de milho a cultivar."""
from __future__ import annotations

import math
from dataclasses import dataclass, asdict

from .formatar import br


@dataclass
class ParametrosSilo:
    kg_ms_vaca: float = 12.0          # silagem na ração (kg MS/vaca/dia)
    ms_silagem_pct: float = 31.0      # % MS da silagem
    n_vacas: int = 130
    dias: int = 365                   # período de fornecimento
    perdas_pct: float = 15.0          # perdas na ensilagem/armazenamento/desabastecimento
    densidade: float = 600.0          # kg MN/m³
    fatia_m: float = 0.25             # avanço diário do painel (m/dia)
    altura_m: float = 2.5
    formato: str = "trapezoidal"      # "retangular" ou "trapezoidal"
    inclinacao: float = 0.25          # m de abertura horizontal por m de altura, em cada parede
    produtividade_t_ha: float = 45.0  # t MN/ha
    margem_area_pct: float = 10.0     # margem de segurança da lavoura
    comprimento_max_m: float = 60.0   # acima disso sugere dividir em mais silos

    @classmethod
    def de_dict(cls, d: dict) -> "ParametrosSilo":
        return cls(**{k: d[k] for k in cls.__dataclass_fields__ if k in d})

    def para_dict(self) -> dict:
        return asdict(self)


def calcular_silo(p: ParametrosSilo) -> dict:
    """Retorna valores e a lista de passos (descrição, conta, resultado)."""
    passos = []
    alertas = []

    mn_vaca = p.kg_ms_vaca / (p.ms_silagem_pct / 100)
    passos.append(("Silagem por vaca (matéria natural)",
                   f"{br(p.kg_ms_vaca, 2)} kg MS ÷ {br(p.ms_silagem_pct, 1)}%", f"{br(mn_vaca, 2)} kg MN/vaca/dia"))

    diario = mn_vaca * p.n_vacas
    passos.append(("Consumo diário do lote (fatia diária em peso)",
                   f"{br(mn_vaca, 2)} kg × {p.n_vacas} vacas", f"{br(diario, 0)} kg MN/dia"))

    consumo_periodo = diario * p.dias
    passos.append(("Consumo no período", f"{br(diario, 0)} kg × {p.dias} dias",
                   f"{br(consumo_periodo / 1000, 1)} t MN"))

    necessidade = consumo_periodo / (1 - p.perdas_pct / 100)
    passos.append(("Silagem a produzir (com perdas)",
                   f"{br(consumo_periodo / 1000, 1)} t ÷ (1 − {br(p.perdas_pct, 0)}%)", f"{br(necessidade / 1000, 1)} t MN"))

    volume = necessidade / p.densidade
    passos.append(("Volume total do silo", f"{br(necessidade, 0)} kg ÷ {br(p.densidade, 0)} kg/m³", f"{br(volume, 1)} m³"))

    vol_dia = diario / p.densidade
    passos.append(("Volume retirado por dia", f"{br(diario, 0)} kg ÷ {br(p.densidade, 0)} kg/m³", f"{br(vol_dia, 2)} m³/dia"))

    area_painel = vol_dia / p.fatia_m
    passos.append(("Área do painel (seção transversal)",
                   f"{br(vol_dia, 2)} m³ ÷ {br(p.fatia_m, 2)} m", f"{br(area_painel, 2)} m²"))

    H = p.altura_m
    if p.formato == "trapezoidal":
        base_menor = (area_painel - p.inclinacao * H ** 2) / H
        base_maior = base_menor + 2 * p.inclinacao * H
        passos.append(("Base menor (fundo)",
                       f"({br(area_painel, 2)} − {br(p.inclinacao, 2)} × {br(H, 2)}²) ÷ {br(H, 2)}", f"{br(base_menor, 2)} m"))
        passos.append(("Base maior (topo)",
                       f"{br(base_menor, 2)} + 2 × {br(p.inclinacao, 2)} × {br(H, 2)}", f"{br(base_maior, 2)} m"))
        if base_menor <= 0:
            alertas.append("Base menor ≤ 0: diminua a altura ou a inclinação das paredes.")
    else:
        base_menor = base_maior = area_painel / H
        passos.append(("Largura", f"{br(area_painel, 2)} m² ÷ {br(H, 2)} m", f"{br(base_menor, 2)} m"))

    comprimento = volume / area_painel
    passos.append(("Comprimento total", f"{br(volume, 1)} m³ ÷ {br(area_painel, 2)} m²", f"{br(comprimento, 1)} m"))

    n_silos = max(1, math.ceil(comprimento / p.comprimento_max_m)) if p.comprimento_max_m > 0 else 1
    comp_silo = comprimento / n_silos
    if n_silos > 1:
        alertas.append(f"Comprimento de {br(comprimento, 0)} m: sugere-se dividir em {n_silos} silos de "
                       f"≈{br(comp_silo, 0)} m (mesmo painel, abertos um após o outro).")

    area = necessidade / 1000 / p.produtividade_t_ha
    area_rec = area * (1 + p.margem_area_pct / 100)
    passos.append(("Área de milho a cultivar",
                   f"{br(necessidade / 1000, 1)} t ÷ {br(p.produtividade_t_ha, 0)} t/ha", f"{br(area, 1)} ha"))
    passos.append(("Área recomendada (com margem)",
                   f"{br(area, 1)} ha × (1 + {br(p.margem_area_pct, 0)}%)", f"{br(area_rec, 1)} ha"))

    if p.fatia_m < 0.15:
        alertas.append("Fatia abaixo de 15 cm/dia: alto risco de aquecimento e deterioração no painel.")

    return {
        "mn_vaca": mn_vaca, "diario_kg": diario, "consumo_periodo_kg": consumo_periodo,
        "necessidade_kg": necessidade, "volume_m3": volume, "vol_dia_m3": vol_dia,
        "area_painel_m2": area_painel, "base_menor_m": base_menor, "base_maior_m": base_maior,
        "comprimento_m": comprimento, "n_silos": n_silos, "comprimento_silo_m": comp_silo,
        "area_ha": area, "area_recomendada_ha": area_rec, "passos": passos, "alertas": alertas,
    }
