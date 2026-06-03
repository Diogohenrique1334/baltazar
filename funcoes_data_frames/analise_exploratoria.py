import sweetviz as sv
import pandas as pd
from skimpy import skim

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