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

def histograma_com_outliers(serie, titulo="", cor_principal="#1f77b4", cor_destaque="#000000"):

    """
    Histograma discreto de uma série numérica, com clipping de outliers (Q1/Q3 ± 3*IQR),
    linhas de referência (média, mediana, Q1, Q3) e uma barra extra agregando os
    valores acima do limite superior.

    Útil para distribuições de contagens/dias (ex.: lead time, SLA) onde poucos
    valores extremos distorceriam a escala do gráfico.

    Parâmetros
        ----------
        serie : pd.Series
            Série numérica a ser plotada.
        titulo : str
            Texto exibido no título do gráfico.
        cor_principal : str
            Cor das barras do histograma.
        cor_destaque : str
            Cor da barra que agrega os valores acima do limite superior.
    """

    serie = serie.astype(float).dropna()

    mean_val = serie.mean()
    median_val = serie.median()
    q1, q3 = serie.quantile([0.25, 0.75])
    iqr = q3 - q1

    lim_superior = q3 + 3 * iqr
    lim_inferior = q1 - 3 * iqr
    serie_plot = serie.clip(lower=lim_inferior, upper=lim_superior)

    xmin = int(np.floor(serie_plot.min()))
    xmax = int(np.ceil(serie_plot.max()))

    plt.figure(figsize=(12, 6))
    sns.histplot(serie_plot, discrete=True, color=cor_principal, edgecolor="white", alpha=0.9, shrink=0.9)

    plt.axvline(mean_val, color="#FF6E00", linestyle="--", linewidth=2, label=f"Média: {mean_val:.2f}")
    plt.axvline(median_val, color="#9467BD", linestyle="--", linewidth=2, label=f"Mediana: {median_val:.2f}")
    plt.axvline(q1, color="#31681E", linestyle="--", linewidth=2, label=f"Q1: {q1:.2f}")
    plt.axvline(q3, color=cor_principal, linestyle="--", linewidth=2, label=f"Q3: {q3:.2f}")

    plt.xticks(np.arange(xmin, xmax + 1, 1))

    # Barra adicional agregando valores acima do limite superior
    count_maiores = (serie > lim_superior).sum()
    if count_maiores > 0:
        x_extra = xmax + 1
        plt.bar([x_extra], [count_maiores], width=0.9, color=cor_destaque, edgecolor="white")
        plt.text(x_extra, count_maiores * 1.02, f"{count_maiores}", ha="center", va="bottom", fontsize=10)

    plt.title(titulo, fontsize=16, fontweight="bold")
    plt.ylabel("Contagem", fontsize=14)
    plt.grid(True, linestyle=":", alpha=0.4)
    plt.legend(loc="upper right", fontsize=10)
    plt.tight_layout()
    plt.show()


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