import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Função para checar a assimetria dos dados e então tratar valores ausentes
def trata_valores_ausentes(df: pd.DataFrame) -> pd.DataFrame:

    """Função que trata valores ausentes com base na assimetria da varíavel"""
    
    # Lista de variáveis com assimetria alta
    assimetria_alta = []
    
    # Lista de variáveis com assimetria moderada
    assimetria_moderada = []
    
    # Loop
    for i, j in df.skew().items():
        
        # Condição para assimetria alta
        if (j < -1) or (j > 1):
            
            # Coloca o nome da variável na lista
            assimetria_alta.append(i)
            
            # Preenche valores ausentes com a mediana
            # Reatribuição (em vez de inplace em Series destacada) p/ compatibilidade
            # com o Copy-on-Write padrão do pandas >= 3.0
            df[i] = df[i].fillna(df[i].median())
            
        # Condição para assimetria moderada
        elif (-1 > j > -0.5) or (0.5 < j <  1):
            
            # Coloca o nome da variável na lista
            assimetria_moderada.append(i)
            
            # Preenche valores ausentes com a média (CoW-safe, ver acima)
            df[i] = df[i].fillna(df[i].mean())
        else:
            pass
        
    print("\nVariáveis com assimetria alta:\n")
    print(assimetria_alta)
    print("\nVariáveis com assimetria moderada:\n")
    print(assimetria_moderada)
    print("\nValores ausentes:\n")
    print(df.isnull().sum())

def verifica_outliers(
        df_dsa: pd.DataFrame,
        distancia_media = 1.5) -> pd.DataFrame:
    
    """Função que análisa todas as colunas do Data frame e retorna um data frame limpo sem outliers"""

    # Visualizando outliers para cada variável no DataFrame
    for column in df_dsa.columns:
        if df_dsa[column].dtype in ['int64', 'float64']:  
            plt.figure(figsize = (5, 5))
            sns.boxplot(x = df_dsa[column])
            plt.title(column)
            plt.show()

    # Define o Intervalo Interquartil
    Q1 = df_dsa.quantile(0.25)
    Q3 = df_dsa.quantile(0.75)
    IQR = Q3 - Q1
    print(IQR)

    # Vamos checar os valores que estão 1.5 acima ou abaixo do IQR. Esses valores são considerados outliers.
    outliers = ((df_dsa < (Q1 - distancia_media * IQR)) | (df_dsa > (Q3 + distancia_media * IQR))).any(axis = 1)
    df_outliers = df_dsa[outliers]
    
    return df_outliers