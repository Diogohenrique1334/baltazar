import numpy as np
import pandas as pd


# Função para gerar dados fictícios
def gerar_dados(seed, n_paises):
    
    np.random.seed(seed)
    
    taxa_vacinacao = np.random.uniform(30, 99, size = n_paises)
    
    expectativa_vida = 50 + 0.5 * taxa_vacinacao + np.random.normal(scale = 5, size = n_paises)
    
    paises = [f"País {i+1}" for i in range(n_paises)]
    
    return pd.DataFrame({"País": paises, 
                         "Taxa de Vacinação": taxa_vacinacao, 
                         "Expectativa de Vida": expectativa_vida})