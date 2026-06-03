import matplotlib.pyplot as plt
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.stattools import grangercausalitytests
import pandas as pd
import numpy as np

# Função para testar a estacionaridade
def testa_estacionaridade(serie):
    
    # Calcula estatísticas móveis
    rolmean = serie.rolling(window = 12).mean()
    rolstd = serie.rolling(window = 12).std()

    # Plot das estatísticas móveis
    orig = plt.plot(serie, color = 'blue', label = 'Original')
    mean = plt.plot(rolmean, color = 'red', label = 'Média Móvel')
    std = plt.plot(rolstd, color = 'black', label = 'Desvio Padrão')
    
    # Plot
    plt.legend(loc = 'best')
    plt.title('Estatísticas Móveis - Média e Desvio Padrão')
    plt.show()
    
    # Teste Dickey-Fuller:
    # Print
    print('\nResultado do Teste Dickey-Fuller:\n')

    # Teste
    dfteste = adfuller(serie, autolag = 'AIC')

    # Formatando a saída
    dfsaida = pd.Series(dfteste[0:4], index = ['Estatística do Teste',
                                               'Valor-p',
                                               'Número de Lags Consideradas',
                                               'Número de Observações Usadas'])

    # Loop por cada item da saída do teste
    for key, value in dfteste[4].items():
        dfsaida['Valor Crítico (%s)'%key] = value

    # Print
    print (dfsaida)
    
    # Testa o valor-p
    print ('\nConclusão:')
    if dfsaida[1] > 0.05:
        print('\nO valor-p é maior que 0.05 e, portanto, não temos evidências para rejeitar a hipótese nula.')
        print('Essa série provavelmente não é estacionária.')
    else:
        print('\nO valor-p é menor que 0.05 e, portanto, temos evidências para rejeitar a hipótese nula.')
        print('Essa série provavelmente é estacionária.')

def autocorrelation_lag(x, plot=True):

    """
    Calcula a autocorrelação de uma série temporal
    e retorna o lag de máxima autocorrelação (excluindo lag=0).

    Parâmetros:
    -----------
    x : array-like
        Série temporal
    plot : bool
        Se True, plota a curva de autocorrelação

    Retorna:
    --------
    lag_max_corr : int
        Lag correspondente à máxima autocorrelação (≠ 0)
    autocorr : np.ndarray
        Vetor da autocorrelação normalizada
    """
    # Centralizando a série
    x_centered = x - np.mean(x)

    # Autocorrelação
    autocorr = np.correlate(x_centered, x_centered, mode='same')

    # Normalização
    autocorr = autocorr / (np.var(x) * len(x))

    # Ajustando eixo de lags
    lags = np.arange(-len(x)//2, len(x)//2)

    # Encontrando lag de máxima autocorrelação (ignorando lag=0)
    lag_max_corr = np.argmax(autocorr[np.where(lags != 0)])

    # Plot opcional
    if plot:
        plt.figure(figsize=(10, 5))
        plt.plot(autocorr)
        plt.axvline(lag_max_corr, color='r', linestyle='--')
        plt.title('Autocorrelação')
        plt.xlabel('Lag')
        plt.ylabel('Autocorrelação')
        plt.show()

    return lag_max_corr, autocorr

def cross_correlation_lag(x, y, plot=True):
    """
    Calcula a correlação cruzada entre duas séries temporais
    e retorna o lag de máxima correlação.

    Parâmetros:
    -----------
    x : array-like
        Série temporal de referência
    y : array-like
        Série temporal a ser comparada
    plot : bool
        Se True, plota a curva de correlação cruzada

    Retorna:
    --------
    lag_max_corr : int
        Lag correspondente à máxima correlação
    correlation : np.ndarray
        Vetor da correlação cruzada normalizada
    """
    # Centralizando as séries
    x_centered = x - np.mean(x)
    y_centered = y - np.mean(y)

    # Correlação cruzada
    correlation = np.correlate(y_centered, x_centered, mode='same')

    # Normalização
    correlation = correlation / (np.std(y) * np.std(x) * len(x))

    # Encontrando o lag de máxima correlação
    lag_max_corr = np.argmax(correlation)

    # Plot opcional
    if plot:
        plt.figure(figsize=(10, 5))
        plt.plot(correlation)
        plt.axvline(lag_max_corr, color='r', linestyle='--')
        plt.title('Correlação Cruzada')
        plt.xlabel('Lag')
        plt.ylabel('Correlação')
        plt.show()

    return lag_max_corr, correlation

def teste_causalidade(X, Y, max_lag=3, verbose=True):
    """
    Teste de causalidade de Granger entre duas séries temporais.

    Parâmetros:
    -----------
    X : array-like
        Série temporal candidata a causar Y
    Y : array-like
        Série temporal dependente
    max_lag : int
        Número máximo de lags a serem testados
    verbose : bool
        Se True, mostra os resultados detalhados

    Retorna:
    --------
    resultados : dict
        Dicionário com lag e valor-p do teste
    """
    # Reorganizar em DataFrame (ordem: Y depois X)
    data = pd.DataFrame({'Y': Y, 'X': X})

    # Executar o teste de Granger
    gc_res = grangercausalitytests(data[['Y', 'X']], maxlag=max_lag, verbose=verbose)

    resultados = {}
    for lag, result in gc_res.items():
        pvalue = result[0]['ssr_ftest'][1]
        resultados[lag] = pvalue
        if verbose:
            print(f'Lag: {lag}, Valor-p: {pvalue:.4f}')

    return resultados
    