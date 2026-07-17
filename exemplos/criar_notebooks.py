"""
Gera os 6 notebooks de exemplos do baltazar.
Execute uma vez: python exemplos/criar_notebooks.py
"""
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))


def nb(cells):
    return {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "version": "3.9.0"},
        },
        "cells": cells,
    }


def md(cid, text):
    return {"cell_type": "markdown", "id": cid, "metadata": {}, "source": text}


def code(cid, src):
    return {
        "cell_type": "code",
        "execution_count": None,
        "id": cid,
        "metadata": {},
        "outputs": [],
        "source": src,
    }


SETUP = """\
import sys, os
sys.path.insert(0, os.path.abspath('..'))

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')
"""

# ============================================================
# 01 — Preparação de Dados
# ============================================================

NB01 = nb([
    md("01-00", (
        "# 01 — Preparação de Dados\n\n"
        "Funções: `trata_valores_ausentes`, `verifica_outliers`, "
        "`split_dataset`, `codifica_categoricas`, `aplica_encoders`, "
        "`compara_modelos_cv`"
    )),
    code("01-01", SETUP),

    md("01-02", (
        "## 1. `trata_valores_ausentes`\n\n"
        "Preenche NaN de colunas numéricas: **mediana** quando |skew| > 1 "
        "(distribuição muito assimétrica) ou **média** quando skew moderado."
    )),
    code("01-03", """\
from ML.preparacao_dados import trata_valores_ausentes

np.random.seed(0)
df_nan = pd.DataFrame({
    'preco':    [10, 12, 11, np.nan, 13, 250],        # skew alto (outlier 250) -> mediana
    'desconto': [0.1, 0.2, np.nan, 0.15, 0.18, 0.12], # skew moderado -> media
})

print("Antes:")
print(df_nan)
print(f"\\nSkew: {df_nan.skew().to_dict()}")

trata_valores_ausentes(df_nan)

print("\\nDepois:")
print(df_nan)
"""),

    md("01-04", (
        "## 2. `verifica_outliers`\n\n"
        "Exibe boxplot de cada coluna numérica e retorna as linhas "
        "do DataFrame que contêm outliers pela regra IQR."
    )),
    code("01-05", """\
from ML.preparacao_dados import verifica_outliers

df_out = pd.DataFrame({
    'vendas':  [100, 110, 105, 98, 112, 108, 850],  # 850 e outlier
    'visitas': [200, 210, 205, 195, 215, 208, 220],
})

df_outliers = verifica_outliers(df_out, distancia_media=1.5)
print(f"\\nLinhas com outliers encontradas:\\n{df_outliers}")
"""),

    md("01-06", (
        "## 3. `split_dataset`\n\n"
        "Divide o dataset em X_train, X_test, y_train, y_test separando a coluna alvo."
    )),
    code("01-07", """\
from ML.preparacao_dados import split_dataset

np.random.seed(1)
df_modelo = pd.DataFrame({
    'feature_1': np.random.randn(100),
    'feature_2': np.random.randint(0, 10, 100),
    'target':    np.random.randint(0, 2, 100),
})

X_train, X_test, y_train, y_test = split_dataset(
    data=df_modelo,
    target_column='target',
    test_size=0.2,
    random_state=42,
)

print(f"Treino: X={X_train.shape}, y={y_train.shape}")
print(f"Teste:  X={X_test.shape},  y={y_test.shape}")
"""),

    md("01-08", (
        "## 4. `codifica_categoricas` + `aplica_encoders`\n\n"
        "Encoding automático sem *data leakage*: o fit ocorre **apenas no treino**; "
        "o teste é transformado com os encoders já ajustados.\n\n"
        "| Tipo de coluna | Estratégia |\n"
        "|---|---|\n"
        "| Hierarquia definida | `OrdinalEncoder` — ordem que você controla |\n"
        "| 2 valores únicos | `OneHotEncoder` → 1 coluna binária (drop_first) |\n"
        "| N valores sem hierarquia | `OneHotEncoder` → N-1 colunas |\n"
        "| Cardinalidade > max_cats_ohe | Pulada com aviso |"
    )),
    code("01-09", """\
from ML.preparacao_dados import split_dataset, codifica_categoricas, aplica_encoders

np.random.seed(42)
n = 200
df_enc = pd.DataFrame({
    'genero':        np.random.choice(['M', 'F'], n),
    'canal_venda':   np.random.choice(['Loja', 'Online', 'Televendas', 'Parceiro'], n),
    'nivel_plano':   np.random.choice(['Basico', 'Intermediario', 'Premium'], n),
    'risco_credito': np.random.choice(['Alto', 'Baixo', 'Medio'], n),
    'cidade':        [f'Cidade_{i}' for i in np.random.randint(1, 60, n)],  # alta cardinalidade
    'idade':         np.random.randint(18, 65, n),
    'churn':         np.random.randint(0, 2, n),
})

X_train, X_test, y_train, y_test = split_dataset(df_enc, 'churn', test_size=0.2)

# Fit somente no treino
X_train_enc, encoders = codifica_categoricas(
    df=X_train,
    colunas_ordinais={
        'nivel_plano':   ['Basico', 'Intermediario', 'Premium'],   # 0, 1, 2
        'risco_credito': ['Baixo', 'Medio', 'Alto'],               # 0, 1, 2
    },
    drop_first=True,
    max_cats_ohe=20,
)

# Transform no teste com os mesmos encoders — sem vazar padrao dos dados
X_test_enc = aplica_encoders(X_test, encoders)

print(f"Colunas: {X_train_enc.columns.tolist()}")
print(f"\\nColunas treino == Colunas teste: {X_train_enc.columns.tolist() == X_test_enc.columns.tolist()}")
X_train_enc.head()
"""),

    md("01-10", (
        "## 5. `compara_modelos_cv`\n\n"
        "Avalia N modelos com validação cruzada e retorna um DataFrame "
        "ranqueado por score médio.\n\n"
        "- Detecta automaticamente **KFold** (regressão) ou **StratifiedKFold** "
        "(classificação) pela cardinalidade de `y`  \n"
        "- Aceita qualquer métrica sklearn via `scoring`  \n"
        "- Exibe `média ± desvio` e intervalo `[min, max]` por fold"
    )),
    code("01-11", """\
from ML.preparacao_dados import compara_modelos_cv
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.tree import DecisionTreeClassifier

np.random.seed(42)
n = 500
X_cmp = np.random.randn(n, 5)
y_cmp = ((X_cmp[:, 0] + X_cmp[:, 1] * 0.8 - X_cmp[:, 2] * 0.5) > 0).astype(int)

# y com 2 valores unicos -> StratifiedKFold detectado automaticamente
modelos_clf = {
    'Regressao Logistica': LogisticRegression(max_iter=500),
    'Arvore de Decisao':   DecisionTreeClassifier(max_depth=4),
    'Random Forest':       RandomForestClassifier(n_estimators=100, random_state=42),
    'Gradient Boosting':   GradientBoostingClassifier(n_estimators=100, random_state=42),
}

resultado = compara_modelos_cv(modelos_clf, X_cmp, y_cmp, scoring='roc_auc', cv=5)
resultado
"""),

    code("01-12", """\
# Exemplo com regressao: KFold detectado automaticamente
from sklearn.linear_model import LinearRegression, Lasso
from sklearn.ensemble import RandomForestRegressor

np.random.seed(0)
X_reg = np.random.randn(300, 4)
y_reg = 3 * X_reg[:, 0] - 1.5 * X_reg[:, 1] + np.random.randn(300) * 0.5

modelos_reg = {
    'Regressao Linear': LinearRegression(),
    'Lasso':            Lasso(alpha=0.1),
    'Random Forest':    RandomForestRegressor(n_estimators=100, random_state=42),
}

resultado_reg = compara_modelos_cv(modelos_reg, X_reg, y_reg, scoring='r2', cv=5)
resultado_reg
"""),
])

# ============================================================
# 02 — Transformações de DataFrames e Datas
# ============================================================

NB02 = nb([
    md("02-00", (
        "# 02 — Transformações de DataFrames e Datas\n\n"
        "Funções: `trata_data_flexivel`, `normaliza_linha_percentual`, "
        "`converte_colunas_data_numericas`, `colunas_por_delimitadores`, "
        "`reduz_categorias`, `Conta_dias_uteis`, `contagem_ativos_por_dia`"
    )),
    code("02-01", SETUP),

    md("02-02", (
        "## 1. `trata_data_flexivel`\n\n"
        "Converte um único valor para `pd.Timestamp` aceitando: "
        "`DD/MM/YYYY`, `DD/MM/YY`, `YYYY-MM-DD`, data com hora, "
        "e serial numérico do Excel (dias desde 1899-12-30)."
    )),
    code("02-03", """\
from funcoes_data_frames.transformacoes import trata_data_flexivel

exemplos = pd.Series([
    '15/06/2026',        # DD/MM/YYYY
    '15/06/26',          # DD/MM/YY
    '2026-06-15',        # YYYY-MM-DD
    '2026-06-15 14:30',  # com hora -> mantem so a data
    45823,               # serial Excel
    None,                # nulo -> NaT
])

resultado = exemplos.apply(trata_data_flexivel)
pd.DataFrame({'original': exemplos, 'convertido': resultado})
"""),

    md("02-04", (
        "## 2. `normaliza_linha_percentual`\n\n"
        "Normaliza cada linha de um DataFrame numérico como % da soma da linha. "
        "Ideal para transformar contagens absolutas em representatividade diária."
    )),
    code("02-05", """\
from funcoes_data_frames.transformacoes import normaliza_linha_percentual

df_lig = pd.DataFrame({
    'EU_USO':     [150, 200, 130],
    'EU_PAGO':    [ 80,  90,  70],
    'EU_CANCELO': [ 20,  15,  25],
}, index=['2026-06-01', '2026-06-02', '2026-06-03'])

print("Contagens absolutas:")
print(df_lig)

df_pct = normaliza_linha_percentual(df_lig)
print("\\nRepresentatividade por dia (%):")
print(df_pct.round(1))
print(f"\\nSoma de cada linha: {df_pct.sum(axis=1).values}")  # deve ser [100, 100, 100]
"""),

    md("02-06", (
        "## 3. `converte_colunas_data_numericas`\n\n"
        "Detecta colunas cujo nome contenha um padrão (default `'data'`) e converte para datetime. "
        "Colunas numéricas são tratadas como serial do Excel; as demais via `pd.to_datetime`."
    )),
    code("02-07", """\
from funcoes_data_frames.preparacao_dados import converte_colunas_data_numericas

df_excel = pd.DataFrame({
    'data_pedido':  [45823, 45824, 45825],   # seriais Excel
    'data_entrega': [45830, 45831, 45832],   # seriais Excel
    'valor':        [100.0, 200.0, 150.0],   # numerica normal: nao toca
    'status':       ['OK', 'OK', 'Pendente'],
})

print("Tipos antes:")
print(df_excel.dtypes)

df_conv = converte_colunas_data_numericas(df_excel, padrao='data')

print("\\nDepois:")
print(df_conv)
print(df_conv.dtypes)
"""),

    md("02-08", (
        "## 4. `colunas_por_delimitadores`\n\n"
        "Explode uma coluna com valores concatenados por delimitador, "
        "gerando uma linha por valor (útil para colunas de tags ou serviços múltiplos)."
    )),
    code("02-09", """\
from funcoes_data_frames.transformacoes import colunas_por_delimitadores

df_tags = pd.DataFrame({
    'cliente_id': [1, 2, 3],
    'servicos':   ['internet;fixo;tv', 'movel', 'internet;movel'],
    'valor_mes':  [150.0, 80.0, 120.0],
})

print("Antes (1 linha por cliente):")
print(df_tags)

df_exp = colunas_por_delimitadores(df_tags, coluna='servicos', delimitador=';')
print("\\nDepois (1 linha por servico):")
print(df_exp[['cliente_id', 'value', 'valor_mes']].rename(columns={'value': 'servico'}))
"""),

    md("02-10", (
        "## 5. `reduz_categorias`\n\n"
        "Recebe uma Series de contagens e retorna um dicionário mapeando "
        "categorias com frequência abaixo do `cutoff` para `'Other'`."
    )),
    code("02-11", """\
from funcoes_data_frames.transformacoes import reduz_categorias

freq = pd.Series({
    'Loja':       450,
    'Online':     320,
    'Televendas': 180,
    'Parceiro':    45,
    'WhatsApp':    22,
    'Email':        8,
})

mapeamento = reduz_categorias(freq, cutoff=50)
print("Mapeamento (< 50 ocorrencias -> 'Other'):")
print(mapeamento)

df_canais = pd.DataFrame({'canal': freq.index.repeat(freq.values)})
df_canais['canal_reduzido'] = df_canais['canal'].map(mapeamento)
print(f"\\nDistribuicao final:\\n{df_canais['canal_reduzido'].value_counts()}")
"""),

    md("02-12", (
        "## 6. `Conta_dias_uteis`\n\n"
        "Calcula dias úteis entre duas séries de datas (exclui sábados, domingos "
        "e feriados opcionais). Retorna `NaN` para datas inválidas ou `fim < inicio`."
    )),
    code("02-13", """\
from ML.supervisionado.series_temporais.transformacoes_temporais import Conta_dias_uteis

df_sla = pd.DataFrame({
    'protocolo': ['P001',       'P002',       'P003',       'P004'],
    'abertura':  ['2026-06-02', '2026-06-05', None,         '2026-06-10'],
    'resolucao': ['2026-06-08', '2026-06-04', '2026-06-15', '2026-06-09'],
    # P001: seg->seg excluindo sab(06) + feriado(07) -> 4 dias uteis
    # P002: fim < inicio -> NaN
    # P003: abertura None -> NaN
    # P004: 1 dia util
})

feriados = ['2026-06-07']  # Corpus Christi

df_sla['dias_uteis'] = Conta_dias_uteis(
    pd.to_datetime(df_sla['abertura']),
    pd.to_datetime(df_sla['resolucao']),
    holidays=feriados,
    include_end=True,
)

print(df_sla)
"""),

    md("02-14", (
        "## 7. `contagem_ativos_por_dia`\n\n"
        "Gera a série temporal de quantos itens (contratos, projetos, chamados) "
        "estão ativos em cada dia usando soma cumulativa de eventos de abertura e fechamento."
    )),
    code("02-15", """\
from ML.supervisionado.series_temporais.transformacoes_temporais import contagem_ativos_por_dia

df_contratos = pd.DataFrame({
    'id':    ['C1',          'C2',          'C3',          'C4'],
    'inicio':['2026-06-01', '2026-06-03', '2026-06-02', '2026-06-05'],
    'fim':   ['2026-06-05', '2026-06-07', '2026-06-06', '2026-06-09'],
})

df_serie = contagem_ativos_por_dia(df_contratos, col_inicio='inicio', col_fim='fim')

print(df_serie)

df_serie.plot(x='data', y='ativos', title='Contratos ativos por dia',
              figsize=(9, 3), marker='o', color='steelblue')
plt.tight_layout()
plt.show()
"""),
])

# ============================================================
# 03 — Análise Exploratória
# ============================================================

NB03 = nb([
    md("03-00", (
        "# 03 — Análise Exploratória\n\n"
        "Funções: `analise_exploratoria`, `analise_exploratoria_comparacao`, "
        "`exploracao_skim`, `analise_categoria_temporal`\n\n"
        "> **Dependências extras:** `pip install sweetviz skimpy statsmodels`"
    )),
    code("03-01", SETUP),

    md("03-02", (
        "## Dataset base\n\nDataset sintético usado nos exemplos abaixo."
    )),
    code("03-03", """\
np.random.seed(0)
df_eda = pd.DataFrame({
    'idade':   np.random.randint(18, 65, 200),
    'salario': np.random.exponential(3000, 200),
    'plano':   np.random.choice(['Basico', 'Medio', 'Premium'], 200),
    'churn':   np.random.randint(0, 2, 200),
})

print(df_eda.head())
print(f"\\nShape: {df_eda.shape}")
"""),

    md("03-04", (
        "## 1. `analise_exploratoria`\n\n"
        "Gera um relatório HTML interativo com sweetviz cobrindo distribuições, "
        "correlações e valores ausentes. Abre no navegador ao final."
    )),
    code("03-05", """\
from funcoes_data_frames.analise_exploratoria import analise_exploratoria

# Gera analise.html na pasta exemplos/
analise_exploratoria(df_eda, 'analise.html')
"""),

    md("03-06", (
        "## 2. `analise_exploratoria_comparacao`\n\n"
        "Compara dois DataFrames com a mesma estrutura (ex: grupo A vs grupo B)."
    )),
    code("03-07", """\
from funcoes_data_frames.analise_exploratoria import analise_exploratoria_comparacao

df_churn     = df_eda[df_eda['churn'] == 1].drop(columns='churn')
df_nao_churn = df_eda[df_eda['churn'] == 0].drop(columns='churn')

analise_exploratoria_comparacao(df_churn, df_nao_churn, 'comparacao_churn.html')
"""),

    md("03-08", (
        "## 3. `exploracao_skim`\n\n"
        "Sumário estatístico rápido com histogramas inline (skimpy). "
        "Alternativa mais leve ao sweetviz."
    )),
    code("03-09", """\
from funcoes_data_frames.analise_exploratoria import exploracao_skim

exploracao_skim(df_eda)
"""),

    md("03-10", (
        "## 4. `analise_categoria_temporal`\n\n"
        "EDA de uma coluna numérica com índice datetime: histograma, "
        "série temporal e decomposição sazonal (statsmodels). "
        "Útil para explorar antes de modelar."
    )),
    code("03-11", """\
from funcoes_data_frames.analise_exploratoria import analise_categoria_temporal

datas = pd.date_range('2024-01-01', periods=120, freq='D')
np.random.seed(1)
tendencia    = np.linspace(100, 160, 120)
sazonalidade = 15 * np.sin(np.linspace(0, 4 * np.pi, 120))
ruido        = np.random.normal(0, 5, 120)

df_ts = pd.DataFrame({'ligacoes': tendencia + sazonalidade + ruido}, index=datas)

analise_categoria_temporal(df_ts, coluna='ligacoes')
"""),
])

# ============================================================
# 04 — Gráficos Estatísticos
# ============================================================

NB04 = nb([
    md("04-00", (
        "# 04 — Gráficos Estatísticos\n\n"
        "Funções: `corr_limite_inferior`, `histograma_com_outliers`, "
        "`alvo_vs_atributosSelecionados`, `cria_scatter_previsoesVSreais`"
    )),
    code("04-01", SETUP),

    md("04-02", (
        "## 1. `corr_limite_inferior`\n\n"
        "Heatmap de correlação exibindo apenas o triângulo inferior (elimina duplicatas)."
    )),
    code("04-03", """\
from ML.graficos_estatisticos.graficos_ml import corr_limite_inferior

np.random.seed(0)
df_corr = pd.DataFrame(
    np.random.randn(150, 5),
    columns=['Preco', 'Volume', 'Desconto', 'NPS', 'Churn']
)
df_corr['Volume'] = df_corr['Preco'] * 0.8 + np.random.randn(150) * 0.3  # correlacionado

corr_limite_inferior(df_corr.corr(), label='Feature')
plt.show()
"""),

    md("04-04", (
        "## 2. `histograma_com_outliers`\n\n"
        "Histograma discreto com clipping Q1/Q3 ± 3·IQR, linhas de referência "
        "(média, mediana, Q1, Q3) e uma barra extra agregando os valores além do limite superior."
    )),
    code("04-05", """\
from ML.graficos_estatisticos.graficos_ml import histograma_com_outliers

np.random.seed(2)
dias_sla = pd.Series(
    list(np.random.randint(1, 8, 180)) + [30, 45, 60, 90, 120]  # outliers propositais
)

histograma_com_outliers(
    dias_sla,
    titulo='Distribuicao de Dias para Resolucao de Chamados',
    cor_principal='#1f6aa5',
)
"""),

    md("04-06", (
        "## 3. `alvo_vs_atributosSelecionados`\n\n"
        "Pairplot de features selecionadas versus a variável alvo. "
        "Parâmetro `n` define quantas features por linha de gráficos."
    )),
    code("04-07", """\
from ML.graficos_estatisticos.graficos_ml import alvo_vs_atributosSelecionados

np.random.seed(3)
df_ml = pd.DataFrame({
    'idade':       np.random.randint(18, 65, 150),
    'renda':       np.random.exponential(3000, 150),
    'uso_mb':      np.random.exponential(5000, 150),
    'antiguidade': np.random.randint(1, 120, 150),
    'churn':       np.random.randint(0, 2, 150),
})

alvo_vs_atributosSelecionados(
    df_ml,
    alvo='churn',
    atributos=['idade', 'renda', 'uso_mb', 'antiguidade'],
    n=2,
)
plt.show()
"""),

    md("04-08", (
        "## 4. `cria_scatter_previsoesVSreais`\n\n"
        "Scatter plot de valores previstos versus reais. "
        "Quanto mais próximos de uma reta diagonal, melhor o modelo."
    )),
    code("04-09", """\
from ML.graficos_estatisticos.graficos_ml import cria_scatter_previsoesVSreais

np.random.seed(4)
y_real = np.linspace(500, 5000, 100)
y_pred = y_real + np.random.normal(0, 400, 100)

cria_scatter_previsoesVSreais(
    y_real, y_pred,
    'Previsao de Valor de Contrato',
    'Previsto (R$)',
    'Real (R$)',
)
plt.show()
"""),
])

# ============================================================
# 05 — Séries Temporais
# ============================================================

NB05 = nb([
    md("05-00", (
        "# 05 — Séries Temporais\n\n"
        "Funções: `testa_estacionaridade`, `autocorrelation_lag`, "
        "`cross_correlation_lag`, `teste_causalidade`, "
        "`g_previsoes_series_temporais`, `originalVStreino`"
    )),
    code("05-01", SETUP),

    md("05-02", (
        "## 1. `testa_estacionaridade`\n\n"
        "Plota a média e o desvio padrão móveis (janela 12) e executa o "
        "**Teste Dickey-Fuller Aumentado**: valor-p < 0.05 indica série estacionária."
    )),
    code("05-03", """\
from ML.supervisionado.series_temporais.suposicoes_series_temporais import testa_estacionaridade

np.random.seed(0)
datas = pd.date_range('2022-01-01', periods=120, freq='ME')

# Serie NAO estacionaria (tendencia crescente)
serie_trend = pd.Series(
    np.linspace(100, 200, 120) + np.random.normal(0, 5, 120),
    index=datas, name='com_tendencia'
)
print("=== Serie com tendencia (nao estacionaria) ===")
testa_estacionaridade(serie_trend)

# Serie estacionaria (sem tendencia)
serie_flat = pd.Series(
    150 + np.random.normal(0, 5, 120),
    index=datas, name='estacionaria'
)
print("\\n=== Serie estacionaria ===")
testa_estacionaridade(serie_flat)
"""),

    md("05-04", (
        "## 2. `autocorrelation_lag`\n\n"
        "Calcula a autocorrelação e retorna o **lag de máxima autocorrelação** "
        "(excluindo lag=0). Útil para identificar sazonalidade e ordem de modelos AR."
    )),
    code("05-05", """\
from ML.supervisionado.series_temporais.suposicoes_series_temporais import autocorrelation_lag

np.random.seed(1)
t = np.arange(150)

# Serie com sazonalidade semanal (lag esperado proximo de 7)
serie_saz = pd.Series(50 + 10 * np.sin(2 * np.pi * t / 7) + np.random.normal(0, 2, 150))

lag_max, _ = autocorrelation_lag(serie_saz, plot=True)
print(f"\\nLag de maxima autocorrelacao: {lag_max}")
plt.show()
"""),

    md("05-06", (
        "## 3. `cross_correlation_lag`\n\n"
        "Calcula a **correlação cruzada** entre duas séries e retorna o lag "
        "em que a correlação é máxima. Útil para medir o atraso de resposta "
        "de uma série em relação a outra (ex: marketing -> vendas)."
    )),
    code("05-07", """\
from ML.supervisionado.series_temporais.suposicoes_series_temporais import cross_correlation_lag

np.random.seed(2)
x = pd.Series(np.random.randn(100))

# y reage a x com lag 5 (com ruido)
y = x.shift(5).fillna(0) + np.random.normal(0, 0.3, 100)

lag_max, _ = cross_correlation_lag(x, y, plot=True)
print(f"\\nLag de maxima correlacao cruzada: {lag_max}")
plt.show()
"""),

    md("05-08", (
        "## 4. `teste_causalidade` (Granger)\n\n"
        "Testa se a série `X` **Granger-causa** a série `Y` para cada lag de 1 a `max_lag`. "
        "Valor-p < 0.05 sugere que X contém informação preditiva sobre Y."
    )),
    code("05-09", """\
from ML.supervisionado.series_temporais.suposicoes_series_temporais import teste_causalidade

np.random.seed(3)
n = 120
marketing = np.cumsum(np.random.randn(n))
vendas    = np.cumsum(np.random.randn(n))

# Adiciona causalidade artificial: vendas reage ao marketing com lag 2
vendas += pd.Series(marketing).shift(2).fillna(0).values * 0.6

resultados = teste_causalidade(marketing, vendas, max_lag=5)
"""),

    md("05-10", (
        "## 5. Visualizações de previsões\n\n"
        "- `g_previsoes_series_temporais`: plota treino, validação e previsões no mesmo gráfico  \n"
        "- `originalVStreino`: compara a série original completa com as previsões"
    )),
    code("05-11", """\
from ML.supervisionado.series_temporais.validacao_series_temporais import (
    g_previsoes_series_temporais,
    originalVStreino,
)

np.random.seed(0)
datas_treino = pd.date_range('2024-01-01', periods=80, freq='D')
datas_valid  = pd.date_range('2024-03-21', periods=20, freq='D')

df_treino = pd.Series(np.cumsum(np.random.randn(80)) + 100, index=datas_treino)
df_valid  = pd.Series(np.cumsum(np.random.randn(20)) + 110, index=datas_valid)
previsoes  = df_valid + np.random.normal(0, 3, 20)

g_previsoes_series_temporais(df_treino, df_valid, previsoes, modelo='SARIMA')
originalVStreino(pd.concat([df_treino, df_valid]), previsoes)
"""),
])

# ============================================================
# 06 — ML Supervisionado
# ============================================================

NB06 = nb([
    md("06-00", (
        "# 06 — ML Supervisionado\n\n"
        "Funções: `ValidacaoSuposicoesRegressao`, `plotar_curva_aprendizado`, "
        "`grid_search_manual_ridge`, `grid_search_manual_Lasso`, "
        "`relatorio_metricas`, `metodo_cotovelo`, `silhuete_metodo`"
    )),
    code("06-01", (
        SETUP
        + "\nfrom sklearn.linear_model import LinearRegression, LogisticRegression\n"
        + "from sklearn.model_selection import train_test_split\n"
        + "import statsmodels.api as sm\n"
    )),

    md("06-02", (
        "## 1. `ValidacaoSuposicoesRegressao`\n\n"
        "Valida as 5 suposições da regressão linear em um modelo **statsmodels.OLS**:\n\n"
        "| Suposição | Teste |\n"
        "|---|---|\n"
        "| Linearidade | Rainbow Test |\n"
        "| Independência dos erros | Durbin-Watson |\n"
        "| Homocedasticidade | Goldfeld-Quandt |\n"
        "| Normalidade dos resíduos | Shapiro-Wilk |\n"
        "| Multicolinearidade | VIF |"
    )),
    code("06-03", """\
from ML.supervisionado.regressao_linear.suposicoes_regressao import ValidacaoSuposicoesRegressao

np.random.seed(42)
n = 200
X_raw = np.random.randn(n, 3)
y_raw = 3 * X_raw[:, 0] + 1.5 * X_raw[:, 1] - 0.5 * X_raw[:, 2] + np.random.normal(0, 1, n)

X_sm = sm.add_constant(X_raw)
modelo_ols = sm.OLS(y_raw, X_sm).fit()

print(modelo_ols.summary())

validacao = ValidacaoSuposicoesRegressao(modelo_ols)
print("\\n=== Resultados das suposicoes ===")
for suposicao, resultado in validacao.resultados.items():
    print(f"\\n{suposicao.upper()}:")
    print(resultado)

plt.show()
"""),

    md("06-04", (
        "## 2. `plotar_curva_aprendizado`\n\n"
        "Plota RMSE de treino e validação em função do tamanho do conjunto de treino. "
        "Curvas próximas e baixas = modelo bem calibrado. "
        "Curvas altas = underfitting. Curvas afastadas = overfitting."
    )),
    code("06-05", """\
from ML.supervisionado.regressao_linear.avaliacoes_regressao import plotar_curva_aprendizado

np.random.seed(0)
X_lc = np.random.randn(300, 3)
y_lc = 2 * X_lc[:, 0] - X_lc[:, 1] + np.random.randn(300) * 0.5

plotar_curva_aprendizado(LinearRegression(), X_lc, y_lc)
plt.title('Curva de Aprendizado — Regressao Linear')
plt.xlabel('Tamanho do conjunto de treino')
plt.ylabel('RMSE')
plt.show()
"""),

    md("06-06", (
        "## 3. `grid_search_manual_ridge` + `grid_search_manual_Lasso`\n\n"
        "Busca manual do melhor `alpha` via validação cruzada (R²). "
        "Retorna o alpha com maior R² médio."
    )),
    code("06-07", """\
from ML.supervisionado.regressao_linear.regressao_lasso_ridge.grid_search_manual import (
    grid_search_manual_ridge,
    grid_search_manual_Lasso,
)

np.random.seed(1)
X_reg = np.random.randn(300, 5)
y_reg = 2 * X_reg[:, 0] - X_reg[:, 2] + np.random.randn(300) * 0.8

alphas = [0.001, 0.01, 0.1, 1, 10, 100]

print("=== Ridge ===")
grid_search_manual_ridge(alphas, X_reg, y_reg)

print("\\n=== Lasso ===")
grid_search_manual_Lasso(alphas, X_reg, y_reg)
"""),

    md("06-08", (
        "## 4. `relatorio_metricas` — Classificação Binária\n\n"
        "Imprime AUC, Acurácia, Recall, Precisão e Especificidade. "
        "O parâmetro `thresh` define o limiar de decisão — útil para ajustar "
        "o trade-off entre recall e precisão."
    )),
    code("06-09", """\
from ML.supervisionado.regressao_logistica.avaliacoes_RLG.metricas_modelo import relatorio_metricas

np.random.seed(42)
X_clf = np.random.randn(400, 4)
y_clf = ((X_clf[:, 0] + X_clf[:, 1]) > 0).astype(int)

X_tr_c, X_te_c, y_tr_c, y_te_c = train_test_split(X_clf, y_clf, test_size=0.3, random_state=42)

modelo_log = LogisticRegression()
modelo_log.fit(X_tr_c, y_tr_c)
y_proba = modelo_log.predict_proba(X_te_c)[:, 1]

print("Threshold = 0.5 (padrao)")
relatorio_metricas(y_te_c, y_proba, thresh=0.5)

print("Threshold = 0.3  (aumenta recall, reduz precisao)")
relatorio_metricas(y_te_c, y_proba, thresh=0.3)
"""),

    md("06-10", (
        "## 5. KMeans — `metodo_cotovelo` + `silhuete_metodo`\n\n"
        "Dois auxiliares para escolha do **k ideal**:\n\n"
        "- **Cotovelo**: procure o 'joelho' na curva de SSE  \n"
        "- **Silhueta**: maior score = clusters mais bem separados"
    )),
    code("06-11", """\
from ML.N_supervisionado.kmeans import metodo_cotovelo, silhuete_metodo

np.random.seed(0)
c1 = np.random.randn(60, 2) + [0,  0]
c2 = np.random.randn(60, 2) + [6,  6]
c3 = np.random.randn(60, 2) + [0, 10]
X_km = pd.DataFrame(np.vstack([c1, c2, c3]), columns=['x', 'y'])

print("=== Metodo do Cotovelo (procure o 'joelho' em k=3) ===")
metodo_cotovelo(X_km)
plt.show()

print("\\n=== Metodo da Silhueta (maior score em k=3) ===")
silhuete_metodo(X_km)
plt.show()
"""),
])

# ============================================================
# encoding_exemplo — fluxo completo de encoding sem data leakage
# ============================================================

NB_ENC = nb([
    md("enc-00", (
        "# Encoding sem Data Leakage — Fluxo Completo\n\n"
        "Demonstra o uso de `codifica_categoricas` + `aplica_encoders` do início ao fim:\n\n"
        "1. Criação do dataset com diferentes tipos de colunas categóricas  \n"
        "2. Split treino/teste **antes** de qualquer encoding  \n"
        "3. Fit dos encoders **apenas no treino**  \n"
        "4. Transform do teste com os encoders já ajustados  \n"
        "5. Verificação de consistência e inspeção dos encoders\n\n"
        "| Tipo de coluna | Comportamento |\n"
        "|---|---|\n"
        "| Binária (2 valores) | OneHotEncoder `drop_first` → 1 coluna 0/1 |\n"
        "| Nominal sem hierarquia (N valores) | OneHotEncoder → N-1 colunas |\n"
        "| Ordinal com hierarquia definida | OrdinalEncoder → 0, 1, 2… |\n"
        "| Alta cardinalidade (> max_cats_ohe) | Pulada com aviso |"
    )),
    code("enc-01", SETUP),

    md("enc-02", "## 1. Dataset sintético"),
    code("enc-03", """\
from ML.preparacao_dados import split_dataset, codifica_categoricas, aplica_encoders

np.random.seed(42)
n = 200

df = pd.DataFrame({
    # Binaria (2 valores) -> OHE gera 1 coluna
    'genero':        np.random.choice(['M', 'F'], n),

    # Nominal sem hierarquia (4 valores) -> OHE gera 3 colunas
    'canal_venda':   np.random.choice(['Loja', 'Online', 'Televendas', 'Parceiro'], n),

    # Ordinal com hierarquia clara -> OrdinalEncoder com ordem definida
    'nivel_plano':   np.random.choice(['Basico', 'Intermediario', 'Premium'], n),

    # Ordinal com hierarquia -> passada como lista (ordem alfabetica)
    'risco_credito': np.random.choice(['Alto', 'Baixo', 'Medio'], n),

    # Alta cardinalidade -> sera pulada automaticamente
    'cidade':        [f'Cidade_{i}' for i in np.random.randint(1, 60, n)],

    # Numericas (passam sem alteracao)
    'idade':             np.random.randint(18, 65, n),
    'valor_mensalidade': np.round(np.random.uniform(50, 300, n), 2),

    'churn': np.random.randint(0, 2, n),
})

print(f"Shape: {df.shape}")
df.head()
"""),

    md("enc-04", (
        "## 2. Split treino / teste\n\n"
        "> O split acontece **antes** de qualquer encoding. "
        "Fazer ao contrário causaria data leakage: o encoder aprenderia "
        "estatísticas do conjunto de teste."
    )),
    code("enc-05", """\
X_train, X_test, y_train, y_test = split_dataset(
    data=df,
    target_column='churn',
    test_size=0.2,
    random_state=42,
)

print(f"Treino: {X_train.shape}  |  Teste: {X_test.shape}")
"""),

    md("enc-06", (
        "## 3. Encoding no treino\n\n"
        "O fit dos encoders acontece aqui.  \n"
        "- `colunas_ordinais` como **dict** → você controla a ordem exata  \n"
        "- `drop_first=True` → evita dummy variable trap  \n"
        "- `max_cats_ohe=20` → colunas com mais categorias são ignoradas"
    )),
    code("enc-07", """\
X_train_enc, encoders = codifica_categoricas(
    df=X_train,
    colunas_ordinais={
        'nivel_plano':   ['Basico', 'Intermediario', 'Premium'],   # 0 -> 1 -> 2
        'risco_credito': ['Baixo', 'Medio', 'Alto'],               # 0 -> 1 -> 2
    },
    drop_first=True,
    max_cats_ohe=20,
)

print(f"Shape apos encoding: {X_train_enc.shape}")
X_train_enc.head()
"""),

    md("enc-08", (
        "## 4. Encoding no teste\n\n"
        "`aplica_encoders` usa os encoders ajustados no treino — **sem refazer o fit**.  \n"
        "Categorias desconhecidas no teste são tratadas com segurança:  \n"
        "- OHE: preenche com 0 em todas as colunas geradas  \n"
        "- OrdinalEncoder: retorna -1"
    )),
    code("enc-09", """\
X_test_enc = aplica_encoders(df=X_test, encoders=encoders)

print(f"Shape apos encoding: {X_test_enc.shape}")
X_test_enc.head()
"""),

    md("enc-10", "## 5. Verificação de consistência"),
    code("enc-11", """\
colunas_ok = X_train_enc.columns.tolist() == X_test_enc.columns.tolist()
print(f"Colunas treino == Colunas teste: {colunas_ok}")
print(f"\\nColunas finais: {X_train_enc.columns.tolist()}")
"""),

    md("enc-12", (
        "## 6. Inspecionando os encoders\n\n"
        "O dict `encoders` retornado por `codifica_categoricas` guarda tudo que "
        "`aplica_encoders` precisa para repetir a transformação em qualquer conjunto futuro."
    )),
    code("enc-13", """\
print("Encoders ajustados:")
for col, info in encoders.items():
    if info['tipo'] == 'ordinal':
        ordem = info['encoder'].categories_[0].tolist()
        print(f"  {col:<20} ORDINAL   | ordem: {ordem}")
    elif info['tipo'] == 'ohe':
        print(f"  {col:<20} OHE       | colunas: {info['colunas_geradas']}")
"""),
])

# ============================================================
# Escreve todos os notebooks
# ============================================================

notebooks = [
    ("encoding_exemplo.ipynb",        NB_ENC),
    ("01_preparacao_dados.ipynb",     NB01),
    ("02_transformacoes.ipynb",       NB02),
    ("03_analise_exploratoria.ipynb", NB03),
    ("04_graficos_estatisticos.ipynb", NB04),
    ("05_series_temporais.ipynb",     NB05),
    ("06_ml_supervisionado.ipynb",    NB06),
]

for fname, notebook in notebooks:
    path = os.path.join(BASE, fname)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(notebook, f, ensure_ascii=False, indent=1)
    print(f"Criado: {fname}")
