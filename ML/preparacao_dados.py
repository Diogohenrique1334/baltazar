import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV, KFold, StratifiedKFold
from sklearn.preprocessing import OrdinalEncoder, OneHotEncoder

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

# Função para automatizar a divisão em treino e teste
def split_dataset(data, target_column, test_size, random_state = 42):
    """
    Divide o dataset em conjuntos de treino e teste.

    Parâmetros:
    - data (DataFrame): O DataFrame completo.
    - target_column (str): O nome da coluna alvo (target).
    - test_size (float): A proporção do conjunto de teste.
    - random_state (int): Seed para a geração de números aleatórios (padrão é 42).

    Retorna:
    - X_train (DataFrame): Conjunto de treino para as variáveis independentes.
    - X_test (DataFrame): Conjunto de teste para as variáveis independentes.
    - y_train (Series): Conjunto de treino para a variável alvo.
    - y_test (Series): Conjunto de teste para a variável alvo.
    """

    # Dados de entrada
    X = data.drop(target_column, axis = 1)
    
    # Dados de saída
    y = data[target_column]
    
    # Divisão em treino e teste
    X_train, X_test, y_train, y_test = train_test_split(X, 
                                                        y, 
                                                        test_size = test_size, 
                                                        random_state = random_state)

    return X_train, X_test, y_train, y_test


def codifica_categoricas(
        df: pd.DataFrame,
        colunas_ordinais=None,
        drop_first: bool = True,
        max_cats_ohe: int = 20) -> tuple:

    """
    Codifica automaticamente todas as colunas categóricas (object/category) do DataFrame,
    aplicando a estratégia correta para cada coluna:

    - Coluna com hierarquia (ordinal)   ->OrdinalEncoder com a ordem que você definir
    - Coluna sem hierarquia, 2 valores  ->OneHotEncoder (gera 1 coluna binária)
    - Coluna sem hierarquia, N valores  ->OneHotEncoder (gera N-1 colunas)
    - Coluna com cardinalidade alta     ->pulada com aviso (acima de max_cats_ohe)

    Retorna o DataFrame transformado e um dict de encoders ajustados para reusar
    no conjunto de teste via `aplica_encoders`, sem vazar padrões dos dados.

    Parâmetros:
    - df (DataFrame): DataFrame de treino com as colunas categóricas a codificar.
    - colunas_ordinais (list ou dict): Colunas com hierarquia.
        list  ->['col_a', 'col_b']  : OrdinalEncoder em ordem alfabética.
        dict  ->{'col_a': ['baixo', 'médio', 'alto']}  : OrdinalEncoder com ordem definida.
    - drop_first (bool): Se True, dropa a primeira categoria no OHE (evita multicolinearidade).
    - max_cats_ohe (int): Colunas com mais categorias únicas que este limite são puladas.

    Retorna:
    - df_enc (DataFrame): DataFrame com as colunas categóricas codificadas.
    - encoders (dict): Encoders ajustados no treino, para reusar em `aplica_encoders`.
    """

    # Normaliza colunas_ordinais para dict {col: [categorias_ordenadas]}
    ordinais = {}
    if isinstance(colunas_ordinais, list):
        for col in colunas_ordinais:
            ordinais[col] = sorted(df[col].dropna().unique().tolist())
    elif isinstance(colunas_ordinais, dict):
        ordinais = colunas_ordinais

    # Detecta colunas categóricas automaticamente pelo dtype
    colunas_categoricas = df.select_dtypes(include=['object', 'category']).columns.tolist()

    df_enc = df.copy()
    encoders = {}

    print(f"\n{'='*58}")
    print(f"  codifica_categoricas — {len(colunas_categoricas)} coluna(s) detectada(s)")
    print(f"{'='*58}")

    for col in colunas_categoricas:

        n_unique = df[col].nunique()

        # Coluna com hierarquia ->OrdinalEncoder
        if col in ordinais:

            categorias = ordinais[col]
            enc = OrdinalEncoder(
                categories=[categorias],
                handle_unknown='use_encoded_value',
                unknown_value=-1
            )
            df_enc[col] = enc.fit_transform(df[[col]])
            encoders[col] = {'tipo': 'ordinal', 'encoder': enc}

            print(f"  [ORDINAL ] {col:<28} {n_unique} cat  ->ordem: {categorias}")

        # Cardinalidade alta ->pular
        elif n_unique > max_cats_ohe:

            print(f"  [PULADO  ] {col:<28} {n_unique} cat  ->acima de max_cats_ohe={max_cats_ohe}")

        # Sem hierarquia ->OneHotEncoder
        else:

            drop = 'first' if drop_first else None
            enc = OneHotEncoder(drop=drop, sparse=False, handle_unknown='ignore')
            enc.fit(df[[col]])

            # Nomes das colunas geradas (exclui a categoria dropada se drop_first=True)
            cats_usadas = enc.categories_[0][1:] if drop_first else enc.categories_[0]
            nomes_gerados = [f"{col}_{cat}" for cat in cats_usadas]

            # Transforma e insere as novas colunas, remove a original
            df_enc[nomes_gerados] = enc.transform(df[[col]])
            df_enc = df_enc.drop(columns=[col])

            encoders[col] = {'tipo': 'ohe', 'encoder': enc, 'colunas_geradas': nomes_gerados}

            rotulo = "OHE(bin)" if n_unique == 2 else "OHE     "
            print(f"  [{rotulo}] {col:<28} {n_unique} cat  ->{nomes_gerados}")

    print(f"{'='*58}\n")

    return df_enc, encoders


def aplica_encoders(
        df: pd.DataFrame,
        encoders: dict) -> pd.DataFrame:

    """
    Aplica encoders já ajustados no treino a um novo DataFrame (ex.: conjunto de teste),
    garantindo que a transformação seja idêntica sem vazar padrões dos novos dados.

    Categorias desconhecidas são tratadas de forma segura:
    - OrdinalEncoder  ->valor -1
    - OneHotEncoder   ->zeros em todas as colunas geradas (handle_unknown='ignore')

    Parâmetros:
    - df (DataFrame): Novo DataFrame a transformar (ex.: X_test).
    - encoders (dict): Dict retornado por `codifica_categoricas` no conjunto de treino.

    Retorna:
    - df_enc (DataFrame): DataFrame com as mesmas transformações aplicadas no treino.
    """

    df_enc = df.copy()

    print(f"\n{'='*58}")
    print(f"  aplica_encoders — {len(encoders)} coluna(s) a transformar")
    print(f"{'='*58}")

    for col, info in encoders.items():

        if col not in df_enc.columns:
            print(f"  [AVISO   ] '{col}' não encontrada no DataFrame — pulada")
            continue

        if info['tipo'] == 'ordinal':

            df_enc[col] = info['encoder'].transform(df_enc[[col]])
            print(f"  [ORDINAL ] {col} ->transformado")

        elif info['tipo'] == 'ohe':

            df_enc[info['colunas_geradas']] = info['encoder'].transform(df_enc[[col]])
            df_enc = df_enc.drop(columns=[col])
            print(f"  [OHE     ] {col} ->{info['colunas_geradas']}")

    print(f"{'='*58}\n")

    return df_enc


def compara_modelos_cv(
        modelos: dict,
        X,
        y,
        scoring: str = 'r2',
        cv: int = 5,
        estratificado: bool = None) -> pd.DataFrame:

    """
    Compara múltiplos modelos sklearn via validação cruzada e retorna
    um DataFrame ranqueado por score médio.

    Detecta automaticamente KFold (regressão) ou StratifiedKFold
    (classificação) com base na cardinalidade de y, a menos que
    `estratificado` seja passado explicitamente.

    Parâmetros
    ----------
    modelos : dict
        {'nome': estimador_sklearn, ...}  — aceita qualquer estimador
        compatível com a API fit/predict do sklearn.
    X : array-like
        Features de treino (sem o target).
    y : array-like
        Target.
    scoring : str
        Métrica sklearn. Regressão: 'r2', 'neg_mean_squared_error',
        'neg_root_mean_squared_error'. Classificação: 'accuracy',
        'roc_auc', 'f1', 'f1_weighted'. Padrão 'r2'.
    cv : int
        Número de folds. Padrão 5.
    estratificado : bool ou None
        True  -> StratifiedKFold (mantém proporção de classes por fold).
        False -> KFold simples.
        None  -> detecta automaticamente: usa StratifiedKFold se y
                 tiver <= 20 valores únicos (classificação).

    Retorna
    -------
    pd.DataFrame
        Colunas: modelo, media, desvio_padrao, cv_min, cv_max.
        Ordenado por média decrescente (melhor primeiro).
    """

    import numpy as np

    if estratificado is None:
        estratificado = pd.Series(y).nunique() <= 20

    if estratificado:
        splitter = StratifiedKFold(n_splits=cv, shuffle=True, random_state=42)
        tipo_cv = 'StratifiedKFold'
    else:
        splitter = KFold(n_splits=cv, shuffle=True, random_state=42)
        tipo_cv = 'KFold'

    print(f"\n{'='*64}")
    print(f"  compara_modelos_cv  |  scoring={scoring}  |  cv={cv}  |  {tipo_cv}")
    print(f"{'='*64}")

    resultados = []
    for nome, modelo in modelos.items():
        scores = cross_val_score(modelo, X, y, cv=splitter, scoring=scoring)
        resultados.append({
            'modelo':        nome,
            'media':         scores.mean(),
            'desvio_padrao': scores.std(),
            'cv_min':        scores.min(),
            'cv_max':        scores.max(),
        })
        print(f"  {nome:<32} {scores.mean():+.4f} ± {scores.std():.4f}"
              f"   [{scores.min():+.4f}, {scores.max():+.4f}]")

    print(f"{'='*64}\n")

    return (
        pd.DataFrame(resultados)
        .sort_values('media', ascending=False)
        .reset_index(drop=True)
    )