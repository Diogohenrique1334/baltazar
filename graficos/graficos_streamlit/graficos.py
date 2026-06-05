from typing import Sequence, Optional, Dict, Any, List, Union, Iterable
import datetime as dt
import matplotlib.pyplot as plt
import plotly.express as px
import pandas as pd
import numpy as np
from streamlit_echarts import st_echarts,Map, JsCode
import json
import requests
import streamlit as st


def liquid_fill(
        liquidfill_option:list = None, 
        valor:float = 0.40, 
        tamanho = "300px"):
    
    """Retorna o grafico liquid_fill do e_chart.
    
    *Parametrôs:
    
    liquidfill: Lista de valores or None.
    valor: se liquidifil for None, insira o valor do liquidfill"""

    if liquidfill_option is None:
        liquidfill_option = {
            "title": {
                "text": "Top aderencias",
                "left": "center",
                "textStyle": {
                    "fontSize": 20,
                    "fontWeight": "bold",
                    "color": "#ffffff"
                }
            },
            "series": [{
                "type": 'liquidFill',
                "data": valor,
                "center": ['50%', '50%'],
                "radius": '50%',
                "waveAnimation": True,
                "outline": {
                    "show": True,
                    "borderDistance": 8,
                    "itemStyle": {
                        "borderWidth": 4,
                        "borderColor": "#ffffff"
                    }
                },
                "backgroundStyle": {
                    "color": "#ffffff"
                },
                "label": {
                    "normal": {
                        
                        "textStyle": {
                            "fontSize": 20,
                            "color": '#18990b'
                        }
                    }
                },
                "color":['#18990b']
            }]
        }

    return st_echarts(options=liquidfill_option,height=tamanho)

def barras_laterais_sum_qtd(
        data, 
        tamanho = "500px"):
    
    """Use o transformador: options_lista_categorica_sum_count"""

    options1 = {
                "dataset": {
                    "source": data
                },
                "grid": {"containLabel": True},
                "xAxis": {"name": "amount"},
                "yAxis": {"type": "category"},
                "visualMap": {
                    "orient": "horizontal",
                    "left": "center",
                    "min": 10,
                    "max": 100,
                    "text": ["Muitas utilizações", "Poucas utilizações"],
                    "dimension": 0,
                    "inRange": {"color": ["#65B581", "#FFCE34", "#FD665F"]},
                },
                "series": [{"type": "bar", "encode": {"x": "amount", "y": "product"}}],
            }
    return st_echarts(options=options1, height=tamanho)

def grafico_rosca(data, tamanho = "500px"):

    """Use o tranformador: options_lista_categorica_simples"""

    options = {
        "tooltip": {"trigger": "item"},
        "legend": {"top": "5%", "left": "center"},
        "series": [
            {
                "name": "Access From",
                "type": "pie",
                "radius": ["40%", "70%"],
                "avoidLabelOverlap": False,
                "padAngle": 5,
                "itemStyle": {"borderRadius": 10},
                "label": {"show": False, "position": "center"},
                "emphasis": {
                    "label": {"show": True, "fontSize": 40, "fontWeight": "bold"}
                },
                "labelLine": {"show": False},
                "data": data
                ,
            }
        ],
    }
    st_echarts(options=options, height=tamanho)

def meia_rosca(data,tamanho = "300px"):

    """Use o transformados: options_lista_categorica_simples"""

    options = {
        "tooltip": {"trigger": "item"},
        "legend": {"top": "5%", "left": "center"},
        "series": [
            {
                "name": "Access From",
                "type": "pie",
                "radius": ["40%", "70%"],
                "center": ["50%", "70%"],
                "startAngle": 180,
                "endAngle": 360,
                "data": data,
            }
        ],
    }
    return st_echarts(options=options, height=tamanho)

def grefico_calendario(df, anos=None, tamanho=None, cores=None):
    """
    Heatmap de calendário ECharts. Anos detectados automaticamente se não informados.

    df     : DataFrame com colunas 'Data' (datetime) e 'value' (numeric)
    anos   : lista de int com os anos a exibir. Se None, detecta pelos dados.
    tamanho: altura do gráfico (ex: "500px"). Se None, calcula pelo nº de anos.
    cores  : paleta do visualMap [cor_min, cor_max]. Default: ["#cac2c2", "#99251F"]
    """
    cores = cores or ["#cac2c2", "#99251F"]

    df = df.copy()
    df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
    df['value'] = pd.to_numeric(df['value'], errors='coerce')

    datas = (
        df.dropna(subset=['Data'])
        .pivot_table(index='Data', values='value', aggfunc='sum')
        .sort_index()
    )

    if anos is None:
        anos = sorted(datas.index.year.unique().tolist()) if not datas.empty else []

    if not anos:
        return

    def _to_date_str(idx):
        return idx.strftime("%Y-%m-%d")

    def _to_native_val(x):
        return None if pd.isna(x) else int(x)

    def _build_year(y):
        if datas.empty:
            return []
        return [
            [_to_date_str(idx), _to_native_val(val)]
            for idx, val in zip(datas.index, datas['value'].values)
            if isinstance(idx, pd.Timestamp) and not pd.isna(idx) and idx.year == y
        ]

    n = len(anos)
    spacing = 90 / n
    tops = [f"{5 + i * spacing:.0f}%" for i in range(n)]

    vmax_native = 1.0
    if not datas.empty:
        vmax = pd.to_numeric(datas['value'], errors='coerce').max()
        vmax_native = float(vmax) if pd.notna(vmax) else 1.0

    option = {
        "tooltip": {"position": "top"},
        "visualMap": {
            "min": 0, "max": vmax_native,
            "calculable": True, "orient": "horizontal", "left": "center",
            "inRange": {"color": cores},
        },
        "calendar": [
            {
                "range": str(ano),
                "cellSize": ["auto", 14],
                "top": tops[i],
                "splitLine": {"lineStyle": {"color": "#000000"}},
                "itemStyle": {"color": "#ffffff"},
                "dayLabel": {"color": "#ffffff"},
                "monthLabel": {"color": "#ffffff"},
                "yearLabel": {"color": "#cac2c2"},
            }
            for i, ano in enumerate(anos)
        ],
        "series": [
            {
                "type": "heatmap",
                "coordinateSystem": "calendar",
                "calendarIndex": i,
                "data": _build_year(ano),
            }
            for i, ano in enumerate(anos)
        ],
    }

    if tamanho is None:
        tamanho = f"{max(300, n * 175)}px"

    def to_native(obj):
        from datetime import datetime
        if isinstance(obj, np.integer): return int(obj)
        if isinstance(obj, np.floating): return float(obj)
        if isinstance(obj, np.bool_): return bool(obj)
        if isinstance(obj, (pd.Timestamp, datetime)): return obj.isoformat()
        if obj is pd.NaT: return None
        if isinstance(obj, np.ndarray): return [to_native(x) for x in obj.tolist()]
        if isinstance(obj, (list, tuple, set)): return [to_native(x) for x in obj]
        if isinstance(obj, dict): return {str(k): to_native(v) for k, v in obj.items()}
        return obj

    return st_echarts(options=to_native(option), height=tamanho)

def funil(data=None, titulo=None, ordenar="descending", cores=None, tamanho="350px"):

    """Gráfico de funil (pipeline / etapas), estilizado.

    Use o transformador: df_para_lista_dict (com controle='name'),
    gerando uma lista de dicts no formato [{"value": n, "name": "etapa"}].

    *Parâmetros:
    data: lista de {"value": int, "name": str}.
    titulo: título opcional exibido no topo.
    ordenar: 'descending' (default), 'ascending' ou 'none'. Quando ordenado,
        as fatias recebem a paleta em gradiente do topo para a base.
    cores: paleta de cores (lista). Default: tons de verde da marca.
    tamanho: altura do gráfico (ex.: '350px').
    """

    cores = cores or ["#18990b", "#3aa856", "#65b581", "#8fc9a3", "#b9dcc4", "#d9e8dd"]

    # Ordena no Python para aplicar o gradiente na ordem certa e deixa o
    # ECharts respeitar essa ordem (sort='none').
    itens = [dict(x) for x in (data or [])]
    if ordenar == "descending":
        itens.sort(key=lambda d: d.get("value", 0), reverse=True)
    elif ordenar == "ascending":
        itens.sort(key=lambda d: d.get("value", 0))

    for i, item in enumerate(itens):
        item.setdefault("itemStyle", {})
        item["itemStyle"].setdefault("color", cores[i % len(cores)])

    options = {
        "tooltip": {"trigger": "item", "formatter": "{b}: {c}"},
        "legend": {"show": False},
        "series": [{
            "type": "funnel",
            "left": "8%",
            "right": "8%",
            "top": 15,
            "bottom": 10,
            "minSize": "20%",
            "maxSize": "100%",
            "sort": "none",
            "gap": 4,
            "funnelAlign": "center",
            "label": {
                "show": True,
                "position": "inside",
                "color": "#ffffff",
                "fontWeight": "bold",
                "fontSize": 12,
                "formatter": "{b}\n{c}",
            },
            "labelLine": {"show": False},
            "itemStyle": {"borderColor": "#0e1117", "borderWidth": 2, "opacity": 0.95},
            "emphasis": {"label": {"fontSize": 14}, "itemStyle": {"opacity": 1}},
            "data": itens,
        }],
    }

    if titulo:
        options["title"] = {"text": titulo, "left": "center", "textStyle": {"color": "#ffffff"}}

    return st_echarts(options=options, height=tamanho)

def velocimetro(valor=0, titulo=None, sufixo="%", maximo=100, cor="#18990b", tamanho="300px"):

    """Velocímetro (gauge) para exibir um valor único, ex.: taxa de conclusão.

    Usa o tipo 'gauge' nativo do ECharts (não requer extensões).

    *Parâmetros:
    valor: número entre 0 e `maximo`.
    titulo: rótulo exibido abaixo do valor.
    sufixo: texto após o valor no detalhe (default '%').
    maximo: valor máximo da escala (default 100).
    cor: cor do valor em destaque.
    tamanho: altura do gráfico.
    """

    options = {
        "series": [{
            "type": "gauge",
            "startAngle": 210,
            "endAngle": -30,
            "min": 0,
            "max": maximo,
            "progress": {"show": True, "width": 16},
            "axisLine": {"lineStyle": {"width": 16}},
            "axisTick": {"show": False},
            "splitLine": {"length": 10},
            "axisLabel": {"distance": 18, "fontSize": 10},
            "pointer": {"width": 5},
            "detail": {
                "valueAnimation": True,
                "formatter": "{value}" + sufixo,
                "fontSize": 30,
                "color": cor,
            },
            "data": [{"value": valor, "name": titulo or ""}],
            "title": {"fontSize": 13},
        }],
    }

    return st_echarts(options=options, height=tamanho)

def mapa_brasil(dados_estados = None):

    """Use o transformados: options_lista_categorica_simples"""

    if dados_estados is None:
        dados_estados = [
            {"name": "São Paulo", "value": 46649132},
            {"name": "Minas Gerais", "value": 21411923},
            {"name": "Rio de Janeiro", "value": 17366189},
            {"name": "Bahia", "value": 14985284},
            {"name": "Paraná", "value": 11835379},
            {"name": "Rio Grande do Sul", "value": 11466630},
            {"name": "Pernambuco", "value": 9674793},
            {"name": "Ceará", "value": 9240580},
            {"name": "Pará", "value": 8777124},
            {"name": "Santa Catarina", "value": 7610361},
            {"name": "Goiás", "value": 7206589},
            {"name": "Maranhão", "value": 6775805},
            {"name": "Amazonas", "value": 4269995},
            {"name": "Espírito Santo", "value": 4108508},
            {"name": "Paraíba", "value": 4059905},
            {"name": "Rio Grande do Norte", "value": 3560903},
            {"name": "Mato Grosso", "value": 3658813},
            {"name": "Alagoas", "value": 3365351},
            {"name": "Piauí", "value": 3281480},
            {"name": "Distrito Federal", "value": 3094325},
            {"name": "Mato Grosso do Sul", "value": 2839188},
            {"name": "Sergipe", "value": 2338474},
            {"name": "Rondônia", "value": 1815278},
            {"name": "Tocantins", "value": 1607363},
            {"name": "Acre", "value": 906876},
            {"name": "Amapá", "value": 877613},
            {"name": "Roraima", "value": 652713},
        ]

    formatter = JsCode(
        """
        function (params) {
            return params.seriesName + '<br/>' +
                params.name + ': ' +
                params.value.toLocaleString('pt-BR');
        }
    """
    ).js_code

    # GeoJSON do Brasil
    url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
    geo_json = requests.get(url).json()

    # Cria o mapa
    map = Map(
        "Brazil",
        geo_json,
    )

    options = {
        "title": {
            "text": "População dos Estados Brasileiros",
            "subtext": "Dados exemplo",
            "left": "right",
        },
        "tooltip": {
            "trigger": "item",
            "formatter": formatter,
        },
        "visualMap": {
            "min": 500000,
            "max": 50000000,
            "left": "left",
            "top": "bottom",
            "text": ["Maior", "Menor"],
            "calculable": True,
            "inRange": {
                "color": [
                    "#E0F3F8",
                    "#ABD9E9",
                    "#74ADD1",
                    "#4575B4",
                    "#313695",
                ]
            },
        },
        "toolbox": {
            "show": True,
            "orient": "vertical",
            "left": "right",
            "top": "center",
            "feature": {
                "dataView": {"readOnly": False},
                "restore": {},
                "saveAsImage": {},
            },
        },
        "series": [
            {
                "name": "População",
                "type": "map",
                "map": "Brazil",
                "roam": True,
                "emphasis": {
                    "label": {
                        "show": True
                    }
                },
                "data": dados_estados,
            }
        ],
    }

    st_echarts(options=options, map=map, height="700px")

def mapa_sp(dados = None, tamanho = "800px"):

    """Use o transformados: options_lista_categorica_simples"""

    if dados is None:
        dados = [
            {"name": "São Paulo", "value": 12000000},
            {"name": "Campinas", "value": 1200000},
            {"name": "Santos", "value": 430000},
            {"name": "Sorocaba", "value": 720000},
            {"name": "Cotia", "value": 275000},
            {"name": "Osasco", "value": 740000},
        ]

    _max = int(pd.DataFrame(dados).value.max())

    # Formatter brasileiro
    formatter = JsCode(
        """
        function (params) {
            return params.seriesName + '<br/>' +
                params.name + ': ' +
                params.value.toLocaleString('pt-BR');
        }
    """
    ).js_code

    # GeoJSON municípios SP
    url = "https://raw.githubusercontent.com/tbrugz/geodata-br/master/geojson/geojs-35-mun.json"
    geo_json = requests.get(url).json()

    # Cria mapa
    map = Map(
        "SP_Municipios",
        geo_json,
    )

    options = {
    #    "title": {
    #        "text": "Municípios de São Paulo",
    #        "left": "center",
    #    },
        "tooltip": {
            "trigger": "item",
    #        "formatter": formatter,
        },
        "visualMap": {
            "min": 0,
            "max": _max,
            "left": "left",
            "bottom": "10%",
            "text": ["Gasto alto", "Gasto baixo"],
            "calculable": True,
            "inRange": {
                "color": [
                    "#18990B",
                    "#65B581",
                    "#FF6E6B",
                    "#99251F",
                ]
            },
        },
        "series": [
            {
                "name": "Valor gasto",
                "type": "map",
                "map": "SP_Municipios",
                "roam": True,
                "zoom": 1.2,
                "label": {
                    "show": False
                },
                "emphasis": {
                    "label": {
                        "show": True
                    }
                },
                "data": dados,
            }
        ],
    }

    st_echarts(options=options, map=map, height=tamanho)

def barras_empilhadas(raw_data = None, series_names = None, eixo_x = None, tamanho = "500px"):

    """Use o transformados: serie_temporal_dia_semana"""

    if raw_data is None:
        raw_data = [
            [100, 302, 301, 334, 390, 330, 320],
            [320, 132, 101, 134, 90, 230, 210],
            [220, 182, 191, 234, 290, 330, 310],
            [150, 212, 201, 154, 190, 330, 410],
            [820, 832, 901, 934, 1290, 1330, 1320],
        ]

    if series_names is None:
        series_names = ["Direct", "Mail Ad", "Affiliate Ad", "Video Ad", "Search Engine"]

    if eixo_x is None:
        
        eixo_x = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    total_data = []
    for i in range(len(raw_data[0])):
        sum_val = 0
        for j in range(len(raw_data)):
            sum_val += raw_data[j][i]
        total_data.append(sum_val)

    
    series = []
    for sid, name in enumerate(series_names):
        series.append(
            {
                "name": name,
                "type": "bar",
                "stack": "total",
                "barWidth": "60%",
                "label": {
                    "show": True,
                    "formatter": JsCode(
                        "function(params) { return Math.round(params.value * 1000) / 10 + '%'; }"
                    ).js_code,
                },
                "data": [
                    (0 if total_data[did] <= 0 else d / total_data[did])
                    for did, d in enumerate(raw_data[sid])
                ],
            }
        )

    options = {
        "legend": {"selectedMode": False},
        "yAxis": {"type": "value"},
        "xAxis": {
            "type": "category",
            "data": eixo_x,
        },
        "series": series,
    }

    return st_echarts(options=options, height=tamanho)

def barras_empilhadas_laterais(raw_data = None, series_names = None, eixo = None, tamanho = "500px"):

    """Use os transformadores: serie_temporal_dia_semana_complexo, serei_semana_mes_complexo, lista_categorica_complexa"""

    options = {
        "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
        "legend": {
            "data": series_names},
        "grid": {"left": "3%", "right": "4%", "bottom": "3%", "containLabel": True},
        "xAxis": {"type": "value"},
        "yAxis": {
            "type": "category",
            "data": eixo,
        },
        "series": raw_data,
    }

    return st_echarts(options=options, height=tamanho)

def barras_empilhadas_horizontais(raw_data=None, series_names=None, eixo=None, tamanho="500px"):
    
    """Use os transformadores: serie_temporal_dia_semana_complexo, serei_semana_mes_complexo, lista_categorica_complexa"""

    options = {
        "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
        "legend": {
            "data": series_names,
            "textStyle": {
                "color": "#ffffff",  # cor da fonte da legenda
                "fontSize": 11,      # opcional: tamanho da fonte
    #                "fontWeight": "bold" # opcional: negrito
            }},
        "grid": {"left": "3%", "right": "4%", "bottom": "3%", "containLabel": True},
        "xAxis": {"type": "category", 
                  "data": eixo, 
                  "axisLabel": {"interval": 0,
                                "rotate": 15,
                                "fontSize": 12,
                                "overflow": 'break'}
                }, 
        "yAxis": {"type": "value"},                 
        "series": raw_data,
    }

    return st_echarts(options=options, height=tamanho)

def barras_drilldown(drilldown_data,categorias,dados_principais,tamanho ="500px" ):

    """Use os transformadores: top_10_categorias"""

    if "bar_drilldown_group" not in st.session_state:
        st.session_state.bar_drilldown_group = None

    group = st.session_state.bar_drilldown_group

    if group is None:
        options = {
            "xAxis": {"data": categorias},
            "yAxis": {},
            "animationDurationUpdate": 500,
            "series": {
                "type": "bar",
                "id": "sales",
                "data": dados_principais,
                "universalTransition": {"enabled": True, "divideShape": "clone"},
            },
        }
    else:
        sub_data = drilldown_data[group]
        options = {
            "xAxis": {"data": [item[0] for item in sub_data]},
            "axisLabel": {
                "interval": 0,       # mostra todos os labels
                "rotate": 30,        # rotaciona para não sobrepor
                "overflow": "break", # quebra linha se for muito longo
                },
            "yAxis": {},
            "tooltip": {
                "trigger": "axis",   # mostra tooltip ao passar no eixo
                "axisPointer": {"type": "shadow"},
                },
            "animationDurationUpdate": 500,
            "series": {
                "type": "bar",
                "id": "sales",
                "dataGroupId": group,
                "data": [item[1] for item in sub_data],
                #"data": [{"value": item[1], "groupId": item[0]} for item in sub_data],
                "universalTransition": {"enabled": True, "divideShape": "clone"},
            },
        }

    events = {
        "click": "function(params) { return params.data && params.data.groupId ? params.data.groupId : null }",
    }

    if group is not None:
        if st.button("Back", key="bar_drilldown_back"):
            st.session_state.bar_drilldown_group = None
            st.rerun()

    result = st_echarts(
        options=options,
        events=events,
        height=tamanho,
#        replace_merge="series",
        key="render_bar_drilldown",
    )

    group_id = result.get("groupId") if isinstance(result, dict) else result
    if group_id and isinstance(group_id, str) and group_id in drilldown_data and st.session_state.bar_drilldown_group != group_id:
        st.session_state.bar_drilldown_group = group_id
        st.rerun()

def grafico_cachoeira(categorias, valores, aumento, queda, tamanho ="500px"):

    """Use os transformadores: top_10_categorias"""

    options = {
        "title": {"text": "Gastos acumulados por mês"},
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {"type": "shadow"},
            "formatter": JsCode(
                """
                function (params) {
                let tar;
                if (params[1] && params[1].value !== '-') {
                    tar = params[1];
                } else {
                    tar = params[2];
                }
                return tar && tar.name + '<br/>' + tar.seriesName + ' : ' + tar.value;
                }
                """
            ).js_code,
        },
        "legend": {"data": ["queda", "Aumento"]},
        "grid": {"left": "3%", "right": "4%", "bottom": "3%", "containLabel": True},
        "xAxis": {
            "type": "category",
            "data": categorias,
        },
        "yAxis": {"type": "value"},
        "series": [
            {
                "name": "Placeholder",
                "type": "bar",
                "stack": "Total",
                "silent": True,
                "itemStyle": {
                    "borderColor": "transparent",
                    "color": "transparent",
                },
                "emphasis": {
                    "itemStyle": {
                        "borderColor": "transparent",
                        "color": "transparent",
                    }
                },
                "data": valores,
            },
            {
                "name": "Aumento",
                "type": "bar",
                "stack": "Total",
                "label": {"show": True, "position": "top"},
                "data": aumento,
            },
            {
                "name": "queda",
                "type": "bar",
                "stack": "Total",
                "label": {"show": True, "position": "bottom"},
                "data": queda,
            },
        ],
    }
    return st_echarts(options=options, height=tamanho)

def mapa_palavras(data):

    """Use os transformadores: options_lista_categorica_simples"""

    wordcloud_option = {"series": [{"type": "wordCloud", "data": data}]}
    
    return st_echarts(wordcloud_option)

def barras_simples(categorias,valores, tamanho = "300px"):

    """Use os transformadores: options_lista_categorica_simples"""

    options = {
        "title": {"text": "Análise de Gastos"},
        "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
        #"legend": {"data": ["Gastos"]},
        "toolbox": {"feature": {"saveAsImage": {}, "restore": {}, "dataView": {}}},
        "xAxis": {"type": "category", "data": categorias},
        "yAxis": {"type": "value"},
        "series": [{
            "name": "Gastos",
            "data": valores,
            "type": "bar",
            #"label": {"show": True, "position": "top"},
            "markLine": {"data": [{"type": "average", "name": "Média"}]},
            "color":['#18990b']
        }],
    }
    return st_echarts(options=options, height=tamanho)

def mapa_correlacao(table,categorias, tamanho = "500px"):

    corr = table[np.append([x for x in categorias],['Tempo de sono','Humor'])].squeeze().resample('W').mean().asfreq('W').corr()

    data_serialized = corr.fillna(0).round(2).reset_index().melt(id_vars='index').values.tolist()


    option = {
        "tooltip": {"position": "top"},
        "grid": {"height": "50%", "top": "13%"},
        "xAxis": {"type": "category", "data": corr.columns.tolist(), "splitArea": {"show": True},"axisLabel": {"rotate": "20"}},
        "yAxis": {"type": "category", "data": corr.index.tolist(), "splitArea": {"show": True}},
        "visualMap": {
            "min": -1,
            "max": 1,
            "calculable": True,
            "orient": "horizontal",
            "left": "center",
            "top":"top",
            "bottom": "15%",
            "color": ['#18990b', '#cac2c2'],
        },
        "series": [
            {
                "name": "Punch Card",
                "type": "heatmap",
                "data": data_serialized,
                "label": {"show": True},
                "emphasis": {
                    "itemStyle": {
                        "shadowBlur": 10,
                        "shadowColor": "rgba(0, 0, 0, 0.47)",
                        "color": "#000000",  # Cor do item
                        "borderColor": "#000000",  # Cor da borda
                        "borderWidth": 2,  # Largura da borda
                        "borderType": "solid",  # Tipo de borda
                        "shadowOffsetX": 5,  # Deslocamento horizontal da sombra
                        "shadowOffsetY": 5,  # Deslocamento vertical da sombra
                        "opacity": 0.8  # Opacidade do item
                    }
                },
            }
        ],
    }

    return st_echarts(options=option,height=tamanho)

def options_calendário_echart(
    serie_ou_df: Union[pd.Series, pd.DataFrame],
    anos: Sequence[int],
    *,
    value_col: str = 'ativos',     # usado apenas se a entrada for DataFrame
    date_col: str = 'data',        # usado apenas se a entrada for DataFrame
    colors: Optional[List[str]] = None,
    cell_height: int = 14
) -> Dict[str, Any]:
    """
    Constrói o 'option' do ECharts Calendar Heatmap a partir de uma série temporal diária.

    Parâmetros
    ----------
    serie_ou_df : pd.Series | pd.DataFrame
        - Series: índice datetime diário, valores numéricos (contagem de ativos).
        - DataFrame: precisa ter colunas 'data' (datetime) e 'ativos' (numérico), por padrão.
    anos : sequência de int
        Anos que aparecerão (um calendário por ano, na ordem informada).
    value_col : str
        Nome da coluna de valores quando a entrada for DataFrame (default 'ativos').
    date_col : str
        Nome da coluna de datas quando a entrada for DataFrame (default 'data').
    colors : lista[str] | None
        Paleta para o visualMap (claro -> escuro). Default ["#cac2c2", "#18990b"].
    cell_height : int
        Altura da célula do calendário (px).

    Retorno
    -------
    dict
        Dicionário de opções do ECharts, somente com tipos nativos (serializável em JSON).
        
    """
    colors = colors or ["#cac2c2", "#18990b"]

    # --- 1) Normalização para Series diária (index datetime, values numéricos) ---
    if isinstance(serie_ou_df, pd.Series):
        serie = serie_ou_df.copy()
        # Garante datetime no índice e normaliza por dia
        if not isinstance(serie.index, pd.DatetimeIndex):
            serie.index = pd.to_datetime(serie.index, errors='coerce')
        serie = serie[~serie.index.isna()].sort_index()
        serie.index = serie.index.normalize()
        # Se houver frequências faltantes não preenche (mantém apenas dias existentes)
    elif isinstance(serie_ou_df, pd.DataFrame):
        df = serie_ou_df[[date_col, value_col]].copy()
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        df = df.dropna(subset=[date_col]).sort_values(date_col)
        df[date_col] = df[date_col].dt.normalize()
        # Agrega por dia (se já vier único por dia, não muda)
        serie = df.groupby(date_col, as_index=True)[value_col].sum()
    else:
        raise TypeError("Entrada deve ser pd.Series ou pd.DataFrame.")

    # Garante tipo numérico e int nativo quando possível
    serie = pd.to_numeric(serie, errors='coerce')
    # Não preencher NaN -> virarão None no payload do ECharts
    serie.index.name = 'data'
    serie.name = 'ativos'

    # --- 2) Arrays [YYYY-MM-DD, valor] por ano ---
    def _to_date_str(idx: pd.Timestamp) -> str:
        return idx.strftime("%Y-%m-%d")

    def _to_native_val(x):
        if pd.isna(x):
            return None
        return int(x)

    arrays_por_ano: List[List[List]] = []
    for y in anos:
        if serie.empty:
            arrays_por_ano.append([])
            continue
        recorte = serie[serie.index.year == y]
        data_ano = [[_to_date_str(idx), _to_native_val(val)] for idx, val in recorte.items()]
        arrays_por_ano.append(data_ano)

    # --- 3) vmax para visualMap ---
    if serie.empty:
        vmax_native = 1.0
    else:
        vmax_native = float(pd.to_numeric(serie, errors='coerce').max() or 1.0)

    # --- 4) Layout dos calendários (um por ano) ---
    tops_default = ["7%", "33%", "60%"]
    if len(anos) <= 3:
        tops = tops_default[:len(anos)]
    else:
        # Distribuição vertical simples para >3 anos
        step = max(1, int(90 / len(anos)))
        tops = [f"{min(5 + i*step, 90)}%" for i in range(len(anos))]

    calendar_blocks = [
        {
            "range": str(anos[i]),
            "cellSize": ["auto", cell_height],
            "top": tops[i],
            "splitLine": {"lineStyle": {"color": "#000000"}},
            "itemStyle": {"color": "#ffffff"},
            "dayLabel": {"color": "#ffffff"},
            "monthLabel": {"color": "#ffffff"},
            "yearLabel": {"color": "#cac2c2"},
        }
        for i in range(len(anos))
    ]

    series_blocks = [
        {
            "type": "heatmap",
            "coordinateSystem": "calendar",
            "calendarIndex": i,
            "data": arrays_por_ano[i],
        }
        for i in range(len(anos))
    ]

    option = {
        "tooltip": {"position": "top"},
        "visualMap": {
            "min": 0,
            "max": vmax_native,
            "calculable": True,
            "orient": "horizontal",
            "left": "center",
            "inRange": {"color": colors},
        },
        "calendar": calendar_blocks,
        "series": series_blocks,
    }

    # --- 5) Blindagem final para tipos nativos ---
    def to_native(obj):
        from datetime import datetime
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, (np.bool_,)):
            return bool(obj)
        if isinstance(obj, (pd.Timestamp, datetime)):
            return obj.isoformat()
        if obj is pd.NaT:
            return None
        if isinstance(obj, np.ndarray):
            return [to_native(x) for x in obj.tolist()]
        if isinstance(obj, (list, tuple, set)):
            return [to_native(x) for x in obj]
        if isinstance(obj, dict):
            return {str(k): to_native(v) for k, v in obj.items()}
        return obj

    return st_echarts(options=to_native(option))