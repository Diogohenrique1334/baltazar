import pandas as pd
import numpy as np
import re


def normaliza_linha_percentual(df: pd.DataFrame) -> pd.DataFrame:

    """
    Normaliza cada linha de um DataFrame como percentual da soma da linha (0-100).

    Útil para transformar contagens absolutas por categoria em representatividade
    percentual dentro de cada linha (ex.: cada linha soma 100%).

    Parâmetros
        ----------
        df : pd.DataFrame
            DataFrame numérico, onde cada linha será normalizada pela própria soma.

        Retorno
        -------
        pd.DataFrame
    """

    return df.apply(lambda linha: (linha / linha.sum()) * 100, axis=1)


def trata_data_flexivel(x):

    """
    Converte um valor de data em formatos variados para pd.Timestamp.

    Aceita: datas com hora embutida (mantém só a parte da data), formatos
    textuais 'DD/MM/YYYY', 'DD/MM/YY', 'YYYY-MM-DD' (via pandas, dayfirst=True)
    e seriais numéricos do Excel (dias desde 1899-12-30).

    Parâmetros
        ----------
        x
            Valor de data em qualquer um dos formatos aceitos.

        Retorno
        -------
        pd.Timestamp ou pd.NaT (se não for possível converter)
    """

    if pd.isnull(x):
        return pd.NaT

    texto = str(x).strip()

    # Datas com hora embutida: mantém apenas a parte da data
    if ' ' in texto:
        texto = texto.split(' ')[0]

    # Serial numérico do Excel (dias desde 1899-12-30)
    if re.fullmatch(r'\d+(\.\d+)?', texto):
        return pd.to_datetime('1899-12-30') + pd.to_timedelta(float(texto), unit='D')

    return pd.to_datetime(texto, dayfirst=True, errors='coerce')


def colunas_por_delimitadores(
    df: pd.DataFrame,
    coluna: str,
    delimitador: str) -> pd.DataFrame:

    """
    Função que explode um data frame com colunas que possuim valores agrupados em uma coluna

    Parâmetros
        ----------
        df : pd.DataFrame
            DataFrame com, uma coluna que tem uma lista dentro de cada linha.
        coluna : str
            Nome da coluna com as listas (ex.: 'eventos').
        delimitados : str
            delimitador que separa os valores da lista (ex.: ';')
        Retorno
        -------
        pd.DataFrame
        
    """    
    
    novas_colunas = df[coluna].map(lambda x: str(x).split(delimitador)).apply(pd.Series)

    df_novo = pd.merge(df,novas_colunas, left_index=True, right_index=True)

    df_novo_expandido = pd.melt(df_novo, id_vars = [x for x in df_novo.columns if not isinstance(x, int)]).reset_index(drop='index')
    
    return df_novo_expandido.dropna(axis=0, how='any')

def reduz_categorias(categories, cutoff):
        
    """
    Exemplo: Aplica a função filtrando categorias com mais de 100 registros
    dev_map = dsa_reduz_categorias(df['DevType'].value_counts(), 100)
    """
    # Inicializa um dicionário vazio para mapear as categorias
    categorical_map = {}
    
    # Inicia um loop que percorre todos os elementos da série 'categories'
    for i in range(len(categories)):
        
        # Verifica se o valor da categoria atual é maior ou igual ao limite (cutoff).
        if categories.values[i] >= cutoff:
            
            # Se verdadeiro, mapeia a categoria para ela mesma no dicionário.
            categorical_map[categories.index[i]] = categories.index[i]
        else:
            
            # Se falso, mapeia a categoria para 'Other'.
            categorical_map[categories.index[i]] = 'Other'
    
    # Após o loop, retorna o dicionário com o mapeamento das categorias.
    return categorical_map
