import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np


def corr_limite_inferior(df, dropDuplicates = True, xrot = 70, yrot = 0, label = 'Variable'):

    # Excluir correlações duplicadas mascarando os valores superiores à direita
    if dropDuplicates:
        mask = np.zeros_like(df, dtype = np.bool_)
        mask[np.triu_indices_from(mask)] = True

    # Definir cor do plano de fundo / estilo do gráfico
    sns.set_style(style = 'dark')
    fig, ax = plt.subplots(figsize = (14, 12))

    # Adiciona mapa de cores do vermelho ao azul
    plt.title("Matriz de Correlação")

    # Desenha gráfico de correlação com ou sem duplicatas
    if dropDuplicates:
        sns.heatmap(df, mask = mask, square = True, linewidth = .5, cbar_kws = {"shrink": .5}, ax = ax, annot=True)
        plt.xlabel(label)
        plt.ylabel(label)
        plt.xticks(rotation=xrot)
        plt.yticks(rotation=yrot)

    else:
        sns.heatmap(df, square = True, linewidth = .5, cbar_kws = {"shrink": .5}, ax = ax, annot=True)
        plt.xlabel(label)
        plt.ylabel(label)
        plt.xticks(rotation = xrot)
        plt.yticks(rotation = yrot)
        
    return

def alvo_vs_atributosSelecionados(data, alvo, atributos, n):
        
    # Grupos de linhas com 3 (n) gráficos por linha
    row_groups = [atributos[i:i+n] for i in range(0, len(atributos), n)]

    # Loop pelos grupos de linhas para criar cada pair plot
    for ind in row_groups:
        plot = sns.pairplot(x_vars = ind, y_vars = alvo, data = data, kind = "reg", height = 3)

    return

def cria_scatter_previsoesVSreais(x, y, title, xlabel, ylabel):

    """# Plot das previsões
        cria_scatter(df_previsoes.Valor_Real, df_previsoes.Valor_Previsto, 'Modelo', 'Previsões', 'Reais')"""
    
    # Figura e subplots
    fig, ax = plt.subplots(figsize = (10, 6))
    
    # Scatter
    ax.scatter(x, y, color = "green", alpha = 0.3)

    # Labels
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    return