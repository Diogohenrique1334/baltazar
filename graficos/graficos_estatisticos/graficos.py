import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np


def Corr_limite_inferior(df, dropDuplicates = True, xrot = 70, yrot = 0, label = 'Variable'):

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

def Alvo_vs_atributosSelecionados(data, alvo, atributos, n):
        
    # Grupos de linhas com 3 (n) gráficos por linha
    row_groups = [atributos[i:i+n] for i in range(0, len(atributos), n)]

    # Loop pelos grupos de linhas para criar cada pair plot
    for ind in row_groups:
        plot = sns.pairplot(x_vars = ind, y_vars = alvo, data = data, kind = "reg", height = 3)

    return

# Análise Exploratória de Dados (EDA)
# Análise Exploratória de Dados (EDA)
def eda(dados, alvo):
    
    for column in dados.columns:
        
        # Se a coluna for numérica
        if dados[column].dtype in ['int64', 'float64']:
            
            # Histograma e Boxplot
            fig, axes = plt.subplots(1, 2)
            sns.histplot(dados[column], kde = True, ax = axes[0])
            sns.boxplot(x = alvo, y = column, data = dados, ax = axes[1])
            axes[0].set_title(f'Distribuição de {column}')
            axes[1].set_title(f'{column} vs {alvo}')
            plt.tight_layout()
            plt.show()
            
        # Se a coluna for categórica
        else:
            
            # Contagem de frequência e relação com Churn
            fig, axes = plt.subplots(1, 2)
            sns.countplot(x = column, data = dados, ax = axes[0])
            sns.countplot(x = column, hue = alvo, data = dados, ax = axes[1])
            axes[0].set_title(f'Distribuição de {column}')
            axes[1].set_title(f'{column} vs {alvo}')
            plt.tight_layout()
            plt.show()