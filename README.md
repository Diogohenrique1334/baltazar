# Baltazar

[![CI](https://github.com/Diogohenrique1334/baltazar/actions/workflows/ci.yml/badge.svg)](https://github.com/Diogohenrique1334/baltazar/actions/workflows/ci.yml)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org)

Biblioteca pessoal de funções Python reutilizáveis para análise de dados em telecom (Claro SA).
Cobre ingestão de dados, Machine Learning, séries temporais e visualizações interativas.

---

## Estrutura

```
baltazar/
├── funcoes_data_frames/        # Leitura CSV, transformações, dados fake, análise exploratória
├── funcoes_so/                 # Operações de sistema e arquivos
├── ML/
│   ├── preparacao_dados.py     # Tratamento de NaN e outliers
│   ├── N_supervisionado/       # Clustering KMeans
│   ├── supervisionado/
│   │   ├── regressao_linear/   # Curva de aprendizado, suposições, Lasso/Ridge
│   │   ├── regressao_logistica/# Métricas de classificação
│   │   └── series_temporais/   # Transformações, suposições (ADF, Granger), validação
│   └── graficos_estatisticos/  # Correlação, pairplot, scatter
└── graficos/
    └── graficos_streamlit/     # Transformadores de dados + 20+ tipos de gráficos ECharts
```

---

## Pré-requisitos

```
pandas numpy scikit-learn statsmodels matplotlib seaborn
sweetviz skimpy selenium pywin32 streamlit streamlit-echarts
```

---

## Testes

A suíte cobre os módulos centrais de ML e transformação de DataFrames
(`ML.preparacao_dados`, `funcoes_data_frames.transformacoes`, séries temporais e
métricas de classificação). Roda automaticamente no **GitHub Actions** (Python 3.9 e 3.11)
a cada push e pull request.

```bash
pip install -r requirements-dev.txt
pytest
```

---

## Módulos principais

### funcoes_data_frames

```python
from baltazar.funcoes_data_frames.leitura_csv import corrigir_csv
from baltazar.funcoes_data_frames.transformacoes import (
    colunas_por_delimitadores, reduz_categorias, normaliza_linha_percentual, trata_data_flexivel
)
from baltazar.funcoes_data_frames.preparacao_dados import converte_colunas_data_numericas
from baltazar.funcoes_data_frames.analise_exploratoria import analise_exploratoria, analise_categoria_temporal

# Ler CSV com encoding ISO-8859-2 e decimais com vírgula
df = corrigir_csv('arquivo.csv')

# Explodir coluna com valores separados por ";"
df_explodido = colunas_por_delimitadores(df, coluna='TAGS', delimitador=';')

# Agrupar categorias com < 5% de frequência em "Other"
df = reduz_categorias(df, coluna='CATEGORIA', cutoff=0.05)

# Normalizar cada linha como % da soma da linha
df_pct = normaliza_linha_percentual(df_numerico)

# Converter valores de data em formatos variados (texto ou serial Excel)
df['DATA'] = df['DATA'].apply(trata_data_flexivel)

# Converter colunas "*data*" numéricas (serial Excel) para datetime
df = converte_colunas_data_numericas(df, padrao='data')

# Relatório HTML exploratório
analise_exploratoria(df, 'relatorio.html')

# Histograma + série temporal + decomposição sazonal de uma coluna
analise_categoria_temporal(df, coluna='VALOR')
```

---

### funcoes_so

```python
from baltazar.funcoes_so.trabalha_arquivos import ultimo_arquivo, mover_arquivo

# Arquivo mais recente em uma pasta
arquivo = ultimo_arquivo(caminho=r'C:\dados\entrada')

# Mover arquivo (cria destino se não existir)
mover_arquivo(r'C:\dados\entrada\file.xlsx', r'C:\dados\saida\file.xlsx')
```

---

### ML — Preparação de Dados

```python
from baltazar.ML.preparacao_dados import trata_valores_ausentes, verifica_outliers

df = trata_valores_ausentes(df)   # mediana (alta assimetria) ou média
outliers = verifica_outliers(df, coluna='VALOR')
```

---

### ML — Regressão Linear

```python
from baltazar.ML.supervisionado.regressao_linear.suposicoes_regressao import ValidacaoSuposicoesRegressao
from baltazar.ML.supervisionado.regressao_linear.avaliacoes_regressao import plotar_curva_aprendizado
from baltazar.ML.supervisionado.regressao_linear.regressao_lasso_ridge.grid_search_manual import (
    grid_search_manual_ridge, grid_search_manual_Lasso
)

# Validar as 5 suposições de regressão linear
validador = ValidacaoSuposicoesRegressao(modelo_statsmodels)
print(validador.resultados)   # linearidade, independência, homocedasticidade, normalidade, VIF

# Curva de aprendizado
plotar_curva_aprendizado(modelo_sklearn, X_train, y_train)

# Tuning manual de Ridge/Lasso
resultado = grid_search_manual_ridge(X_train, y_train, X_val, y_val, alphas=[0.01, 0.1, 1, 10])
```

---

### ML — Regressão Logística

```python
from baltazar.ML.supervisionado.regressao_logistica.avaliacoes_RLG.metricas_modelo import relatorio_metricas

# Relatório completo: AUC, Acurácia, Recall, Precisão, Especificidade
relatorio_metricas(modelo, X_test, y_test)
```

---

### ML — Séries Temporais

```python
from baltazar.ML.supervisionado.series_temporais.suposicoes_series_temporais import (
    testa_estacionaridade, autocorrelation_lag, cross_correlation_lag, teste_causalidade
)
from baltazar.ML.supervisionado.series_temporais.transformacoes_temporais import (
    contagem_ativos_por_dia, Conta_dias_uteis
)
from baltazar.ML.supervisionado.series_temporais.validacao_series_temporais import (
    g_previsoes_series_temporais, originalVStreino
)

# Teste de estacionaridade (Dickey-Fuller)
testa_estacionaridade(serie)

# Lag de máxima autocorrelação
lag = autocorrelation_lag(serie)

# Teste de causalidade de Granger
teste_causalidade(df, coluna_causa='X', coluna_efeito='Y', lags=4)

# Contagem de ativos por dia (vetorizado)
df_serie = contagem_ativos_por_dia(df, col_inicio='DATA_INICIO', col_fim='DATA_FIM')

# Visualizar previsões
g_previsoes_series_temporais(df_treino, df_valid, previsoes, modelo='SARIMA')
```

---

### ML — Clustering KMeans

```python
from baltazar.ML.N_supervisionado.kmeans import (
    metodo_cotovelo, silhuete_metodo, cluster_simples_dois_valores
)

# Escolher k ótimo
metodo_cotovelo(X, k_max=10)
silhuete_metodo(X, k_max=10)

# Clusterizar e plotar
df_clusters = cluster_simples_dois_valores(
    df, coluna_a_clusterizar='LOJA_ID',
    coluna_valor1='QTD_ATIVOS', coluna_vendas='VENDAS_MES'
)
```

---

### ML — Gráficos Estatísticos

```python
from baltazar.ML.graficos_estatisticos.graficos_ml import (
    corr_limite_inferior, alvo_vs_atributosSelecionados, cria_scatter_previsoesVSreais, histograma_com_outliers
)

# Matriz de correlação (sem duplicatas)
corr_limite_inferior(df.corr())

# Pairplot features vs alvo
alvo_vs_atributosSelecionados(df, alvo='TARGET', atributos=['A','B','C'], n=3)

# Scatter previsões vs reais
cria_scatter_previsoesVSreais(y_real, y_pred, 'Modelo', 'Previsões', 'Reais')

# Histograma com clipping de outliers e linhas de referência
histograma_com_outliers(df['DIAS_PARA_ATIVACAO'], titulo='Distribuição de dias para ativação')
```

---

### Gráficos Streamlit (ECharts)

```python
from baltazar.graficos.graficos_streamlit.transformadores import (
    options_lista_categorica_simples, serie_temporal_data, get_delta
)
from baltazar.graficos.graficos_streamlit.graficos import (
    barras_simples, grafico_rosca, barras_empilhadas,
    grefico_calendario, mapa_brasil, grafico_cachoeira,
    barras_drilldown, liquid_fill, mapa_palavras
)

# Preparar dados
data = options_lista_categorica_simples(df, col_categoria='JORNADA', col_valor='QTDE')

# Gráficos básicos
barras_simples(data)
grafico_rosca(data)

# Série temporal
data_ts = serie_temporal_data(df, col_data='DATA', col_valor='VALOR')

# Mapa do Brasil
mapa_brasil(df_estados)   # df com coluna 'UF' e coluna de valor

# Calendar heatmap
grefico_calendario(df, col_data='DATA', col_valor='LIGACOES', anos=[2024, 2025])

# Waterfall
data_wf = dados_grafico_cachoeira(df, col_categoria='JORNADA', col_valor='VARIACAO')
grafico_cachoeira(data_wf)
```
