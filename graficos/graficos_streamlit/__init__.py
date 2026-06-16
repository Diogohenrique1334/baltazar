"""Gráficos Streamlit - Baltazar."""

from .mapas_dinamicos import (
    mapa_estado,
    mapa_brasil,
    obter_mapping_municipios_estado,
    obter_estados_unicos,
    obter_mapping_municipios_estado as obter_mapa_municipios,
)

from .graficos import (
    # primitivas reutilizáveis (aceitam cores/cor + key)
    grafico_rosca,
    meia_rosca,
    velocimetro,
    barras_simples,
    # gráficos de dashboard (DataFrame-based, aceitam cor/cores + key)
    barras_horizontais,
    barras_verticais,
    barras_coloridas,
    barras_agrupadas,
    linha_temporal,
    linha_com_rotulos,
    barras_status,
    donut,
    gauge_progresso,
    campo_futebol,
)

__all__ = [
    "mapa_estado",
    "mapa_brasil",
    "obter_mapping_municipios_estado",
    "obter_estados_unicos",
    "obter_mapa_municipios",
    "grafico_rosca",
    "meia_rosca",
    "velocimetro",
    "barras_simples",
    "barras_horizontais",
    "barras_verticais",
    "barras_coloridas",
    "barras_agrupadas",
    "linha_temporal",
    "linha_com_rotulos",
    "barras_status",
    "donut",
    "gauge_progresso",
    "campo_futebol",
]