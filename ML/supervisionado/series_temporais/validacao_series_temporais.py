import matplotlib.pyplot as plt
from matplotlib.pyplot import figure

def g_previsoes_series_temporais(df_treino_log,df_valid_log,previsoes, modelo = "ARIMA" ):
    
    # Plot
    figure(figsize = (15, 6))
    plt.plot(df_treino_log, label = 'Dados de Treinamento')
    plt.plot(df_valid_log, label = 'Dados de Validação')
    plt.plot(previsoes, label = 'Previsões')
    plt.title(f'Previsões com Modelo {modelo}')
    plt.legend(loc = 'upper left', fontsize = 12)
    plt.show()
    
    return print("Gráfico gerado!")

def originalVStreino(dados_reais,previsoes ):
    
    figure(figsize = (15, 6))
    plt.plot(dados_reais, label = 'Série Original') 
    plt.plot(previsoes, color = 'orange', label = 'Previsões') 
    plt.legend(loc = 'best') 
    plt.show()
    
    return print("Gráfico gerado!")