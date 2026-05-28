import pandas as pd
from io import StringIO
import re

@staticmethod
def corrigir_csv(file_path, encoding='iso-8859-2'):
    """
    Corrige o CSV substituindo vírgulas decimais por pontos ANTES do pandas ler
    """
    linhas_corrigidas = []
    
    # Função de substituição (definida uma vez fora do loop)
    def substituir_virgula(match):
        # Substitui a vírgula decimal por ponto
        return match.group(1) + '.' + match.group(2)
    
    with open(file_path, 'r', encoding=encoding) as f:  # CORRIGIDO: encoding=encoding
        for linha in f:
            # Padrão para identificar números com vírgula decimal
            # Captura padrões como: 520,23 ou 1471,91 etc.
            padrao = r'(\d+),(\d+)'
            
            # Aplica a correção em toda a linha
            linha_corrigida = re.sub(padrao, substituir_virgula, linha)
            linhas_corrigidas.append(linha_corrigida)
    
    # Junta todas as linhas corrigidas
    csv_corrigido = ''.join(linhas_corrigidas)  # CORRIGIDO: ''.join
    
    # Agora sim, carrega no pandas
    return pd.read_csv(StringIO(csv_corrigido), sep=',', on_bad_lines='skip')

