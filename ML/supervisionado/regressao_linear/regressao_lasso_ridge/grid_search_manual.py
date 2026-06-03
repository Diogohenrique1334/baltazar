from sklearn.linear_model import Ridge
from sklearn.model_selection import cross_val_score
from sklearn.linear_model import Lasso
from sklearn.kernel_ridge import KernelRidge
import numpy as np

def grid_search_manual_ridge(alphas, X, y):
    
    scores = []

    # Iteração sobre os valores de alpha e calculando o R² usando a validação cruzada
    for alpha in alphas:
        modelo = Ridge(alpha = alpha)
        score = cross_val_score(modelo, X, y, cv = 5, scoring = 'r2')
        scores.append(np.mean(score))
        
        idx = np.argmax(scores)
        
    return print("O valor ideal de alpha é:", alphas[idx])

def grid_search_manual_Lasso(alphas, X, y):
    
    scores = []

    # Iteração sobre os valores de alpha e calculando o R² usando a validação cruzada
    for alpha in alphas:
        modelo = Lasso(alpha = alpha)
        score = cross_val_score(modelo, X, y, cv = 5, scoring = 'r2')
        scores.append(np.mean(score))
        
        idx = np.argmax(scores)
        
    return print("O valor ideal de alpha é:", alphas[idx])

def grid_search_manual_Loess(alphas, X, y, gama = None):
    
    """grid_search_manual_Loess(alphas=[-4, 4, 9], X = X, y = y)"""

    scores = []

    if gama is None:
        gamma = 0.1

    # Iteração sobre os valores de alpha e calculando o R² usando a validação cruzada
    for alpha in alphas:
        modelo = KernelRidge(alpha = alpha, kernel = 'rbf', gamma = gamma)
        score = cross_val_score(modelo, X, y, cv = 5, scoring = 'r2')
        scores.append(np.mean(score))
        
        idx = np.argmax(scores)
        
    return print("O valor ideal de alpha é:", alphas[idx])