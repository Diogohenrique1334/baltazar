# Baltazar

Biblioteca pessoal de funções Python reutilizáveis para análise de dados em telecom (Claro SA).
Cobre ingestão de dados, Machine Learning, séries temporais e visualizações interativas.

---

## Estrutura

```
baltazar/
├── CX_PME.py                   # Customer Experience PME: speech, NPS, portabilidade, churn
├── Inteligencia_OP.py          # Treinamento comercial: turmas, ativos, JUMP
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

## Módulos principais

### CX_PME — Customer Experience PME

Requer que o projeto consumidor tenha uma pasta `Dados/Repositorio_dados/` acessível pelo `os.getcwd()`.

```python
from baltazar.CX_PME import dados_speech, Dimensoes, ps8, qualtrics, portabilidade, churn

# Consolidar speech do mês + histórico
speech = dados_speech(projeto='Movel')
df = speech.speech_consolidado()

# Ranking de variações por hiper-categoria
ranking = speech.Rankin_variacao(df, Hiper_categoria='EU USO')

# Enviar relatório HTML por Outlook
speech.enviar_relatorio_jornadas()

# Dimensões
dim = Dimensoes()
df_clientes = dim.D_clientes()
df_churn    = dim.churn()

# Portabilidade (passe seu caminho de conflitos se diferente do padrão)
port = portabilidade(caminho_conflitos=r'C:\seu\caminho\Conflitos Portabilidade')
df_port = port.portabilidade_consolidada()
port.distribuicao_dias_ativacao(df_port)

# NPS / CSAT / CES
q = qualtrics()
df_nps  = q.tratar_base_nps_j1(df_raw)
nps     = q.calcular_nps(df_nps)
ces     = q.calcula_ces(df_raw)
```

---

### Inteligencia_OP — Treinamento Comercial

Requer que o projeto consumidor seja executado dentro de um path que contenha `\General\`.

```python
from baltazar.Inteligencia_OP import (
    Treinados_consolidados, consolidar_turmas,
    Ativos_consolidados, treinados_por_temas
)

# Histórico de treinados
df_treinados = Treinados_consolidados().gerar_treinados()

# Turmas validadas
df_turmas = consolidar_turmas().gerar_turmas()

# Ativos por canal
df_ativos = Ativos_consolidados().gerar_ativos()

# Ativos treinados por tema
df_tema = treinados_por_temas(df_ativos, df_treinados, df_turmas)
df_resultado = df_tema.Gera_treinados_por_tema()
```

---

### funcoes_data_frames

```python
from baltazar.funcoes_data_frames.leitura_csv import corrigir_csv
from baltazar.funcoes_data_frames.transformacoes import colunas_por_delimitadores, reduz_categorias
from baltazar.funcoes_data_frames.analise_exploratoria import analise_exploratoria

# Ler CSV com encoding ISO-8859-2 e decimais com vírgula
df = corrigir_csv('arquivo.csv')

# Explodir coluna com valores separados por ";"
df_explodido = colunas_por_delimitadores(df, coluna='TAGS', delimitador=';')

# Agrupar categorias com < 5% de frequência em "Other"
df = reduz_categorias(df, coluna='CATEGORIA', cutoff=0.05)

# Relatório HTML exploratório
analise_exploratoria(df, 'relatorio.html')
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
    corr_limite_inferior, alvo_vs_atributosSelecionados, cria_scatter_previsoesVSreais
)

# Matriz de correlação (sem duplicatas)
corr_limite_inferior(df.corr())

# Pairplot features vs alvo
alvo_vs_atributosSelecionados(df, alvo='TARGET', atributos=['A','B','C'], n=3)

# Scatter previsões vs reais
cria_scatter_previsoesVSreais(y_real, y_pred, 'Modelo', 'Previsões', 'Reais')
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
