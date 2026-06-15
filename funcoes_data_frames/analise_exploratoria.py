import sweetviz as sv
import pandas as pd
import matplotlib.pyplot as plt
from skimpy import skim
from statsmodels.tsa.seasonal import seasonal_decompose

def analise_exploratoria(
        df: pd.DataFrame, 
        nome_analise_exploratória:str = 'Analise_exploratoria'):

    """Cria um mini dash com sweetviz para exploracao dos dados"""

    return sv.analyze(df).show_html(nome_analise_exploratória)

def analise_exploratoria_comparacao(
        df1:pd.DataFrame,
        df2:pd.DataFrame, 
        nome_analise_exploratória: str = 'Analise_exploratoria.html'):
    
    """Cria um mini dash com sweetviz para comparação de dois dataframes identicos"""

    return sv.compare([df1, df2]).show_html(nome_analise_exploratória)

def exploracao_skim(df):

    return skim(df)


def analise_categoria_temporal(df: pd.DataFrame, coluna: str):

    """
    Análise exploratória de uma coluna numérica indexada por data: histograma,
    série temporal e decomposição sazonal (statsmodels.seasonal_decompose).

    Parâmetros
        ----------
        df : pd.DataFrame
            DataFrame com índice de datas (DatetimeIndex) e a coluna a analisar.
        coluna : str
            Nome da coluna numérica a ser analisada.
    """

    if coluna not in df.columns:
        print(f"A coluna '{coluna}' não foi encontrada no DataFrame.")
        return

    serie = df[coluna].dropna()
    print(f"Total de registros na coluna '{coluna}': {len(serie)}")

    # Histograma
    plt.figure(figsize=(10, 4))
    serie.hist(bins=30)
    plt.title(f'Histograma de: {coluna}')
    plt.xlabel('Valor')
    plt.ylabel('Frequência')
    plt.grid(True)
    plt.show()

    # Série temporal
    plt.figure(figsize=(12, 4))
    df[coluna].plot()
    plt.title(f'Série Temporal de: {coluna}')
    plt.xlabel('Data')
    plt.ylabel('Valor')
    plt.grid(True)
    plt.show()

    # Decomposição sazonal
    try:
        decomposicao = seasonal_decompose(df[coluna].asfreq('D').fillna(0), model='additive', extrapolate_trend='freq')
        decomposicao.plot()
        plt.suptitle(f'Decomposição Sazonal de: {coluna}', fontsize=14)
        plt.show()
    except Exception as e:
        print(f"Erro na decomposição sazonal: {e}")