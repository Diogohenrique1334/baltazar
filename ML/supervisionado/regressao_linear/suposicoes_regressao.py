from scipy.stats import shapiro
import statsmodels.stats.api as sms
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.compat import lzip
import statsmodels
import seaborn as sns

class ValidacaoSuposicoesRegressao:

    def __init__(self, modelo):
        self.modelo = modelo
        self.resultados = {
            "linearidade": self.linearidade(),
            "independencia_erros": self.independencia_erros(),
            "homocedasticidade": self.homocedasticidade(self.modelo.endog, self.modelo.exog),
            "normalizacao_erros": self.normalizacao_erros(self.modelo.resid),
            "multicolinearidade": self.multicolinearidade(pd.DataFrame(self.modelo.exog))
        }

    def linearidade(self):
        lin_p = sms.linear_rainbow(self.modelo, frac=0.5)[1]
        result = "Rejeitamos a H0. Há evidências de heterocedasticidade." if lin_p <= 0.05 else "Sucesso! Falhamos em rejeitar a H0."
        return np.transpose(pd.DataFrame([[lin_p, 0.05, result]], columns=['Valor-p do Rainbow Linearity Test', 'Alfa', 'Resultado']))

    def independencia_erros(self):
        residuos = self.modelo.resid
        valores_previstos = self.modelo.fittedvalues
        plt.figure(figsize=(10, 5))
        sns.residplot(x=valores_previstos, y=residuos, color="green", lowess=True)
        plt.xlabel("Valores Previstos")
        plt.ylabel("Resíduos")
        plt.title("Plot Residual")
        plt.show()
        resultado = statsmodels.stats.stattools.durbin_watson(residuos)
        interpretacao = "Não há evidências de autocorrelação nos erros!" if 1.9 <= resultado <= 2.1 else "Há evidências de autocorrelação nos erros!"
        return resultado, interpretacao
    
    def homocedasticidade(self, y, x):
        estatisticas = ["F statistic", "p-value"]
        teste_goldfeldquandt = sms.het_goldfeldquandt(y, x)
        resultado = dict(zip(estatisticas, teste_goldfeldquandt))
        interpretacao = "Não há evidências de heterocedasticidade." if resultado["p-value"] >= 0.05 else "Há evidências de heterocedasticidade."
        return resultado, interpretacao

    def normalizacao_erros(self, residuos):
        resultado = shapiro(residuos)
        interpretacao = "Os resíduos seguem uma distribuição normal." if resultado.pvalue >= 0.05 else "Os resíduos não seguem uma distribuição normal."
        return resultado.pvalue, interpretacao
    
    def multicolinearidade(self, train):
        vif = pd.DataFrame()
        vif["feature"] = train.columns
        vif["VIF"] = [variance_inflation_factor(train.values, i) for i in range(len(train.columns))]
        return vif
    
