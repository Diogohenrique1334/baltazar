import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

def metodo_cotovelo(df):

    # Lista para calcular o SSE
    sse = []

    # Range de valores de k a serem testados
    k_range = range(1, 11)

    # Testando os valores
    for k in k_range:
        kmeans = KMeans(n_clusters = k)
        kmeans.fit(df)
        sse.append(kmeans.inertia_)

    # Plot
    plt.plot(k_range, sse, 'bx-')
    plt.xlabel('k')
    plt.ylabel('Soma dos Quadrados Intra-Cluster')
    plt.title('Método do Cotovelo para Ótimo k')
    plt.show()

    return print('Método do Cotovelo para Ótimo k')

def silhuete_metodo(df_scaled):

    k_range = range(1, 11)

    # Lista para o Silhouette score
    sil_score = []

    # Loop pelo range de valores de k a serem testados
    for k in k_range:
        kmeans = KMeans(n_clusters = k)
        kmeans.fit(df_scaled)
        
        # Silhouette score não é definido para k = 1
        if k != 1:
            sil_score.append(silhouette_score(df_scaled, kmeans.labels_))

    # Plot
    plt.plot(k_range[1:], sil_score, 'bx-')
    plt.xlabel('k')
    plt.ylabel('Coeficiente de Silhueta')
    plt.title('Método da Silhueta para Ótimo k')
    plt.show()

def grafico_clusters(df_dsa_cleaned, cluster = 'cluster'):

    # Criando um mapa de cores baseado na paleta 'Dark2'
    palette = sns.color_palette('Dark2', n_colors = len(df_dsa_cleaned[cluster].unique()))
    color_map = dict(zip(df_dsa_cleaned[cluster].unique(), palette))
    
    # Plotando o gráfico de grid com os clusters e mostrando o mapa de cores
    g = sns.PairGrid(df_dsa_cleaned, hue = cluster, palette = color_map, diag_sharey = False)
    g.map_upper(sns.scatterplot)
    g.map_lower(sns.kdeplot)
    g.map_diag(sns.kdeplot, lw = 2)
    plt.show()
    
    # Mostrando o mapa de cores
    for cluster, color in color_map.items():
        plt.scatter([], [], c = [color], label = f'Cluster {cluster}')
    plt.legend(title = 'Legenda de Cores dos Clusters')
    plt.axis('off')
    plt.show()

    return print('Plotagem de separação')

def cluster_simples_dois_valores(
        df: pd.DataFrame,
        coluna_a_clusterizar: str,
        coluna_valor1: str,
        coluna_regional: str,
        coluna_data: str,
        coluna_vendas: str,
        nclusters: int = 3):

    """ Função que clusteriza as lojas com base na média de vendas e média de colaboradores ativos por mês.
    ** ARGS:
        table: Dataframe que contém os dados analisados;
        coluna_a_clusterizar: Coluna do dataframe com o identificador da clusterização;
        coluna_valor1: coluna do dataframe com o identificador de cada vendedor;
        coluna_regional: Coluna com a regional de cada loja;
        coluna_data: Coluna com as datas de cada venda;
        coluna_vendas: Coluna das vendas;
        vendas_valor: True se o valor for um float
        nclusters: Quantidade de clusters que deseja retornar na função.
        
    """

    table = df.copy()

    if table[coluna_vendas].dtype == float or table[coluna_vendas].dtype == int:
        agg = 'sum'
    else:
        agg = 'count'

    df_lojasCluster = table.pivot_table(values=[coluna_valor1,coluna_vendas],\
                    index=[coluna_a_clusterizar,coluna_regional,table[coluna_data].dt.month.astype('str') + table[coluna_data].dt.year.astype('str')], \
                    aggfunc={coluna_valor1:lambda x: len(x.unique()),coluna_vendas:agg}).reset_index().pivot_table(index = [coluna_a_clusterizar,coluna_regional],
                                                                                                                            values = [coluna_vendas,coluna_valor1],
                                                                                                                            aggfunc = 'mean').reset_index()

    df_lojasCluster = df_lojasCluster.dropna()

    # Função para ordenar os clusters
    def ordenar_clusters(df, col_cluster, col_ordenacao):
        
        cluster_means = df.groupby(col_cluster)[col_ordenacao].mean().sort_values().index
        cluster_map = {antiga: nova for nova, antiga in enumerate(cluster_means)}
        df[col_cluster] = df[col_cluster].map(cluster_map)
        return df


    #Retornando os cluster por regional
    df_t = pd.DataFrame()
    for reg in df_lojasCluster[coluna_regional].unique():

        v_regional = df_lojasCluster[df_lojasCluster[coluna_regional]==reg]
        kmeans5 = KMeans(n_clusters=nclusters, random_state=42).fit(v_regional[[coluna_valor1,coluna_vendas]])
        
        
        v_regional['CATEGORIA LOJA'] = kmeans5.labels_
        
        # Ordenando os clusters
        v_regional = ordenar_clusters(v_regional, 'CATEGORIA LOJA', coluna_vendas)
        
        
        df_t = pd.concat([df_t,v_regional])

    #Vizualizando a distribuição das lojas
    fig, ax = plt.subplots()
    
    ax.scatter(df_t[coluna_vendas],df_t[coluna_valor1], c = df_t['CATEGORIA LOJA'])

    plt.xlabel('Média vendas mês')
    plt.ylabel('Média ativos mês')
    
    plt.show()
    
    
    table['CATEGORIA LOJA'] = table[coluna_a_clusterizar].map(df_t[[coluna_a_clusterizar,'CATEGORIA LOJA']].set_index(coluna_a_clusterizar).to_dict().get('CATEGORIA LOJA'))

    return table