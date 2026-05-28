import pandas as pd
import numpy as np
import os
import re
import datetime as dt
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import win32com.client as win32

#Melhorias no código:
#Criar o TOO string de todas as minhas funções
#Ajustar contratados e treinados com o PAP indireto
#Crias a classe com os relatórios

#-------------------------------------------------------------------------------------------------------

#Variaveis globais
usuario = os.getcwd().split('General')[0]

#função usada para corrigir as dadtas:

def tratarData(x):

    #cose o formato esteja em data e hora
    if len(str(x).split(' ')) == 2:
        return pd.to_datetime(str(x).split(' ')[0])
    
    elif pd.isnull(x):
        np.nan

    elif x == 'nan':
        np.nan
    
    # Caso o formato seja 'yyyy-mm-dddd'
    elif len(str(x).split('-')) == 3:
        return dt.datetime(int(str(x).split('-')[0]),int(str(x).split('-')[1]), int(str(x).split('-')[2]))
    
    # Caso o formato seja 'dd-mm-yyyy'
    elif len(str(x).split('-')) == 3 and len(str(x).split('-')[0]) == 2:
        return dt.datetime(int(str(x).split('-')[2]),int(str(x).split('-')[1]), int(str(x).split('-')[0]))
    
    # Caso o formato seja 'DD-MM-YY'
    elif len(str(x).split('-')) == 3 and len(str(x).split('-')[2]) == 2:
        return dt.datetime( (2000 + int(str(x).split('-')[2])), int(str(x).split('-')[1]), int(str(x).split('-')[0]))
    
    # Caso o formato seja 'dias desde 1900'
    elif len(str(x).split('/')) == 1:
        return dt.datetime(1900, 1, 1) + dt.timedelta(days=float(x)-2)

    # Caso o formato seja 'DD/MM/YY'
    elif len(str(x).split('/')) == 3 and int(str(x).split('/')[2]) < 2000:
        return dt.datetime( (2000 + int(str(x).split('/')[2])), int(str(x).split('/')[1]), int(str(x).split('/')[0]))

    # Caso o formato seja 'DD/MM/YYYY'
    elif len(str(x).split('/')) == 3:
        return dt.datetime(int(str(x).split('/')[2]),int(str(x).split('/')[1]), int(str(x).split('/')[0]))

    else:
        raise x

    return x


    # Função que retorna turmas por temas em cada linha
def pepilineTotaltemas(df_treinados,df_Turmas,temas_considerados_turma):

    #Unindo a base de turmas com a base de treinados para pegar os temas
    t = pd.merge(df_treinados,df_Turmas.set_index('Número')[['Tema','Instrutor']], left_on='Número', right_index=True, how = 'left').reset_index(drop='index')

    #Para as turmas que não tem tema, eu coloca o tema da base de treinados
    t.Tema_y =  t.Tema_y.fillna(t['Tema_x'].map(lambda x: x))

    #Tratando potenciais colunas vazias
    t.Instrutor = t['Instrutor'].fillna('Treinamento anterior a 2019')

    #Colocando colocando a quantidade de temas escolhidos em colunas
    #t['Tema_y'].astype('str').map(lambda x: str(x).split(',')[:temas_considerados_turma]).apply(pd.Series)

    #
    t = pd.merge(t,t['Tema_y'].astype('str').map(lambda x: str(x).split(',')[:temas_considerados_turma]).apply(pd.Series),
                left_index=True,
                right_index=True)
    

    t = pd.melt(t, id_vars = [x for x in t.columns if not isinstance(x, int)])
    
    t.rename(columns = {'value': 'Tema','variable':'Temas abordados'}, inplace=True)

    t = t.drop(columns = ['Tema_x','Tema_y']).dropna(axis=0, how='any')

    t.Tema = t.Tema.map(lambda x: str(x).replace('_x000D_',''))
    
    return t

class Treinados_consolidados:

    """
        Função que retorna um data frame com todos os treinados.
        A função espera receber o caminho do histórico de treinados e os treinados deste ano.

        Parâmetros
        --------------------
        historico_treinados: parquet com o histórico de treinados

        treinados_atual: planilha de excel que tem os treinados deste ano, se não passado, a função usa o caminho da
        minha máquina.

        Retornos
        ---------------------
        Data frame com o histórico de todas as pessoas treinadas na área de treinamento comercial.

    """

    def __init__(self,historico_treinados = None,treinados_atual = None, colunas = None):

        #se não for passada nenhuma lista para colunas, usar a lista padrão
        if colunas is None:
            self.colunas = ['Número','Login','Data Final','Status','T. dia Treinamento','Frequência','Categoria Tema','Tema']
        else:
            self.colunas = colunas
        
        if historico_treinados is None:

            caminho_local_historico_treinados = 'General\\BASES_TODAS\\Bases Plataformas\\PAINEIS JUMP\\Relatório_de_Treinados\\treinados_limiar.parquet'
            self.historico_treinados = usuario + caminho_local_historico_treinados


        else:
            #Caminho do histórico de treinados    
            self.historico_treinados = historico_treinados
        
        if treinados_atual is None:

            caminho_local_treinados_atual = "General\\BASES_TODAS\\Bases Plataformas\\PAINEIS JUMP\\Relatório_de_Treinados\\Treinados JUMP 2025\\TOTAL DE TREINADOS JUMP 2025.xlsx"
            self.treinados_atual = usuario + caminho_local_treinados_atual
        else:
            #caminho dos treinados que não estão no histórico
            self.treinados_atual = treinados_atual
        
        

    def gerar_treinados(self, per_presenca = True):

        #parquet de treinados consolidados até dia 15/01/2025
        try:
            treinados_consolidados = pd.read_parquet(self.historico_treinados)
        except:
            treinados_consolidados = pd.read_parquet(r'C:\Users\f115523\OneDrive - Claro SA\General\BASES_TODAS\Bases Plataformas\PAINEIS JUMP\Relatório_de_Treinados\treinados_limiar_25-02-2025.parquet')

        #Treinados do ano atual
        try:
            treinados_no_atual = pd.read_excel(self.treinados_atual)
        except:
            treinados_no_atual = pd.read_excel(r'C:\Users\f115523\OneDrive - Claro SA\General\BASES_TODAS\Bases Plataformas\PAINEIS JUMP\Relatório_de_Treinados\Treinados JUMP 2025\TOTAL DE TREINADOS JUMP 2025.xlsx')

        #Corrigindo as datas do fim da formação
        treinados_no_atual['Data Final'] = treinados_no_atual['Data Final'].astype(str).apply(tratarData)
        treinados_no_atual['Data Inicial'] = treinados_no_atual['Data Inicial'].astype(str).apply(tratarData)

        #consolidados dos treinados mais os treinados do ano atual
        df_treinados = pd.concat([treinados_consolidados,treinados_no_atual]).drop_duplicates().reset_index(drop='index')

        #Tratando erros no cpf
        df_treinados['Login'] = df_treinados['Login'].map(lambda x: re.sub(r'\D+', '', str(x).replace('_x000D_','')))

        #Transformando o cpf em inteiro para cruzamento
        df_treinados_com_cpf = df_treinados[~(df_treinados['Login'] == '')]['Login'].map(lambda x: int(x))
        df_treinados.loc[df_treinados_com_cpf.index,'Login'] = df_treinados_com_cpf

        #Criando o %de presença por colaborador
        df_treinados['Presença'] = df_treinados['Frequência'] / df_treinados['T. dia Treinamento']

        if per_presenca:
            self.df_treinados = df_treinados[df_treinados['Presença'] >= 0.75]


        return self.df_treinados[self.colunas].drop_duplicates()

class consolidar_turmas:

    def __init__(self,pasta_das_bases_turmas = None, colunas_turmas = None):

        if colunas_turmas is None: 
            self.colunas_turmas =  ["Número",
                                    "Tipo de Treinamento",
                                    "Data Inicial",
                                    "Data Final",
                                    "Status",
                                    "Instrutor",
                                    "Tipo de Cliente",
                                    "Regional Treinamento",
                                    "Canal",
                                    "Cidade",
                                    "Estado",
                                    "Duração",
                                    "Nº Particip.(Expectativa)",
                                    "Participantes Inscritos",
                                    "Participantes Treinados",
                                    "Categoria Tema",
                                    "Tema",
                                    "Observações",
                                    "Lista",
                                    "Galeria"]
            
        else:
            self.colunas_turmas = colunas_turmas

        if pasta_das_bases_turmas is None:

            caminho_local_pasta_bases_turmas = "General\\BASES_TODAS\\Bases Plataformas\\PAINEIS JUMP\\Relatório_de_Turmas"

            self.pasta_das_bases_turmas = usuario + caminho_local_pasta_bases_turmas
        else:
            self.pasta_das_bases_turmas = pasta_das_bases_turmas

        self.caminho_e_mails = usuario + "General\\BASES_TODAS\\Bases Plataformas\\Bases relatório padrão\\RADAR\\Nome_jump.xlsx"

        try:
            self.E_mails = pd.read_excel(self.caminho_e_mails)
        except:
            self.E_mails = pd.read_excel('C:\\Users\\f115523\\OneDrive - Claro SA\\General\\BASES_TODAS\\Bases Plataformas\\Bases relatório padrão\\RADAR\\Nome_jump.xlsx')

    def funcao_radar(self,table):

        radar = table.copy()

        def validate_lists(cell):
            numbers = re.findall(r"\d+", str(cell))
            if len(numbers) == 0 or not any(len(num) >= 6 for num in numbers):
                return True
            return False

        radar = radar[radar['Data Final'].apply(tratarData) < (dt.datetime.now() - dt.timedelta(days = 1))]

        radar = radar[radar.Status.isin(['Confirmado','Realizado'])]

        Turmas_outros_canal_diferente_De_Analistas = radar[(radar['Tipo de Treinamento'] == 'Outros') & (radar['Canal'] != 'Analista')]

        EAD_presencial_Canal_Analistas = radar[(radar['Tipo de Treinamento'].isin(['EAD','PRESENCIAL'])) & (radar['Canal'] == 'Analista')]

        Sem_Turma_moderacao_obs = radar[radar['Tema'] == 'Moderação de Treinamento']['Observações'].map(validate_lists)
        Sem_numero_da_turma_em_moderacao = radar[radar['Tema'] == 'Moderação de Treinamento'].loc[Sem_Turma_moderacao_obs]

        #Analisar pelo gestor, colaboradores do hub, contaúdo e inteligencia op
        lista_matriz = ['felipe.deoliveira@claro.com.br','MARLUCE.MARQUES@claro.com.br','nadiane.sobral@claro.com.br','vanessa.fernan@claro.com.br']
        pode_matriz = [ x for x in self.E_mails[self.E_mails['e-mail_gestor'].isin(lista_matriz)]['Nome no jump']]
        Ead_presencial_Regional_matriz = radar[(radar['Tipo de Treinamento'].isin(['EAD','PRESENCIAL'])) & (radar['Regional Treinamento'] == 'Matriz') & (~radar.Instrutor.isin(pode_matriz))]

        instrutor_matriz_regional_dif = radar[(radar['Tipo de Treinamento'].isin(['EAD','PRESENCIAL'])) & (radar['Regional Treinamento'] != 'Matriz') & (radar.Instrutor.isin(pode_matriz))]

        participantes_zerados = radar[((radar['Participantes Treinados'] == 0) | (radar['Participantes Treinados'].isnull()) & (radar['Tipo de Treinamento'] != 'Outros')) & ((radar.Lista == "Sem arquivos") | (radar.Galeria == "Sem arquivos"))]

        Formacao_menos_6h = radar[(radar['Categoria Tema'] == 'Formação Inicial') & (radar['Duração'].map(lambda x: int(re.findall(r"\d+", str(x))[0])) < 6)]

        Sem_arquivos = radar[((radar.Lista == "Sem arquivos") | (radar.Galeria == "Sem arquivos")) & (radar['Tipo de Treinamento'] != 'Outros')]

        Erros_do_radar = pd.concat([Turmas_outros_canal_diferente_De_Analistas,
                                    EAD_presencial_Canal_Analistas,
                                    Sem_numero_da_turma_em_moderacao,
                                    Ead_presencial_Regional_matriz,
                                    instrutor_matriz_regional_dif,
                                    participantes_zerados,
                                    Formacao_menos_6h,
                                    Sem_arquivos])

        return Erros_do_radar.drop_duplicates()
    
    def gerar_turmas(self):

        try:
            Turmas_limiar = pd.read_parquet(self.pasta_das_bases_turmas+'\\Turmas_limiar_28_04_25.parquet')
        except:
            Turmas_limiar = pd.read_parquet('C:\\Users\\f115523\\OneDrive - Claro SA\\General\\BASES_TODAS\\Bases Plataformas\\PAINEIS JUMP\\Relatório_de_Turmas\\Turmas_limiar_28_04_25.parquet')

        try:
            turmas_2025 = pd.read_excel(self.pasta_das_bases_turmas+'\\Resumo_Turmas_JUMP_2025\\TOTAL DAS TURMAS JUMP 2025.xlsx')
        except:
            turmas_2025 = pd.read_excel('C:\\Users\\f115523\\OneDrive - Claro SA\\General\\BASES_TODAS\\Bases Plataformas\\PAINEIS JUMP\\Relatório_de_Turmas\\Resumo_Turmas_JUMP_2025\\TOTAL DAS TURMAS JUMP 2025.xlsx')

        turmas_2025['Data Inicial'] = turmas_2025['Data Inicial'].apply(tratarData)
        turmas_2025['Data Final'] = turmas_2025['Data Final'].apply(tratarData)


        pasta_turmas_mes = self.pasta_das_bases_turmas+'\\Resumo_Turmas_JUMP_2025\\TURMAS POR MÊS 2025'

        try:
            turmas_mes_atual = sorted([os.path.join(pasta_turmas_mes, f) for f in os.listdir(pasta_turmas_mes) if f.endswith('.csv')],
                                    key=os.path.getctime,
                                    reverse=True)[0]
            
        except:
            turmas_mes_atual = sorted([os.path.join('C:\\Users\\f115523\\OneDrive - Claro SA\\General\\BASES_TODAS\\Bases Plataformas\\PAINEIS JUMP\\Relatório_de_Turmas\\Resumo_Turmas_JUMP_2025\\TURMAS POR MÊS 2025', f) for f in os.listdir('C:\\Users\\f115523\\OneDrive - Claro SA\\General\\BASES_TODAS\\Bases Plataformas\\PAINEIS JUMP\\Relatório_de_Turmas\\Resumo_Turmas_JUMP_2025\\TURMAS POR MÊS 2025') if f.endswith('.csv')],
                                    key=os.path.getctime,
                                    reverse=True)[0]
        
        turmas_mes_atual = pd.read_csv(turmas_mes_atual,encoding='ISO-8859-1',sep=';')

        turmas_mes_atual['Data Inicial'] = turmas_mes_atual['Data Inicial'].apply(tratarData)
        turmas_mes_atual['Data Final'] = turmas_mes_atual['Data Final'].apply(tratarData)

        turmas_consolidadas = pd.concat([Turmas_limiar,turmas_2025,turmas_mes_atual])

        Turmas_com_erro_radar = self.funcao_radar(turmas_consolidadas)['Número']

        return turmas_consolidadas[~turmas_consolidadas['Número'].isin(Turmas_com_erro_radar)].reset_index(drop='index').drop_duplicates(subset='Número')[self.colunas_turmas]

    def gerar_turmas_v1(self):

        df_treinados = pd.DataFrame()

        for pasta in [x for x in os.listdir(self.pasta_das_bases_turmas) if 'JUMP' in x]:

            print(pasta)
            
            arquivo = [x for x in os.listdir(self.pasta_das_bases_turmas+'/'+pasta) if 'xlsx' in x]

            print(arquivo[0])

            df_temp = pd.read_excel(self.pasta_das_bases_turmas+'/'+pasta+'/'+arquivo[0], usecols=self.colunas_turmas)

            print(df_temp.shape)

            df_treinados = pd.concat([df_treinados,df_temp])

        return df_treinados
    
class Ativos_consolidados:

    def __init__(self,caminho_arquivos_canais = None):

        if caminho_arquivos_canais is None:
            caminho_padrao_arquivos_canais = "General\\BASES_TODAS\\Bases Recebidas de Canais\\Base vigente"
            self.caminho_arquivos = usuario+caminho_padrao_arquivos_canais
        else:
            # Caminho dos arquivos
            self.caminho_arquivos = caminho_arquivos_canais

        # Mapeamento das regionais
        self.da_para_regional = {
            'RBS': 'BA/SE', 'RSC': 'SPC', 'RCO': 'CO', 'RMG': 'MG', 'RNE': 'NE', 'RNO': 'NO', 'RPS': 'PR/SC', 'RRE': 'RJ/ES', 'RRS': 'RS',
            'RSI': 'SPI', 'CO': 'CO', 'PR/SC': 'PR/SC', 'NE': 'NE', 'SP2': 'SPI', 'BA/SE': 'BA/SE', 'RJ/ES': 'RJ/ES', 'RS': 'RS', 'MG': 'MG',
            'SP1': 'SPC', 'NO': 'NO', 'SP': 'SPC', 'SPI': 'SPI'
        }

        self.UF_REGIONAL = \
        {'MG':'MG',
        'PA':'NO',
        'CE':'NE',
        'SC':'PR/SC',
        'PE':'NE',
        'BA':'BA/SE',
        'RN':'NE',
        'MT':'CO',
        'MA':'NO',
        'RS':'RS',
        'PR':'PR/SC',
        'PB':'NE',
        'ES':'RJ/ES',
        'TO':'CO',
        'RO':'CO',
        'RR':'NO',
        'PI':'NE',
        'MS':'CO',
        'AM':'NO',
        'SE':'BA/SE',
        'RJ':'RJ/ES',
        'GO':'CO',
        'AL':'NE',
        'AP':'NO',
        'AC':'CO',
        'DF':'CO'}

        self.Regional_tratada = {'SAO PAULO':'SPC',
                    'Claro Matriz - Matriz São Paulo':'SPC',
                    'TODAS':'SPC',
                    'Claro SP - Regional São Paulo':'SPC', 
                    'Claro SI - São Paulo / Interior':'SPI'}
        
                #colunas consideradas
        
        self.colunas_iw =        ['NOME','CPF','CARGO','REGIONAL','DATA DE ADMISSÃO','Cód. Agente','RAZÃO SOCIAL','CANAL','CIDADE','ESTADO','CNPJ']

        self.colunas_HC =        ["NOME", "DATA DE ADMISSÃO", "CPF", "CARGO", "RAZÃO SOCIAL", "CIDADE", "ESTADO", "REGIONAL", "CNPJ", 'CANAL']

        self.colunas_papind =    ['REGIONAL','CIDADE','RAZÃO SOCIAL','CNPJ','NOME','CPF','CARGO', 'DATA DE ADMISSÃO','CANAL']

        self.colunas_PAPind_AG = ["RAZÃO SOCIAL", "REGIONAL", "CIDADE", "CPF", "NOME", "DATA DE ADMISSÃO", "CANAL","CNPJ"]

        self.Colunas_varejo =    ['RAZÃO SOCIAL', 'CNPJ','CPF','CARGO', 'NOME', 'DATA DE ADMISSÃO','REGIONAL','CIDADE','CANAL']



        try:
        # Carregar as bases de dados
            self.cad_pdv = pd.read_excel(self.caminho_arquivos.replace('Base vigente', 'CAD PDV\\CADASTRO_NACIONAL_PARCEIROS_ATUAL.xlsb'), 
                                        engine='pyxlsb', header=11, dtype={'NUMERO_CNPJ': str})
            self.capilaridade = pd.read_excel(self.caminho_arquivos.replace('Base vigente', 'CAD PDV\\Capilaridade_AA_AAPAP.xlsx'), sheet_name='AA')

        except Exception as e:
            self.cad_pdv = pd.read_excel('C:\\Users\\f115523\\OneDrive - Claro SA\\General\\BASES_TODAS\\Bases Recebidas de Canais\\CAD PDV'+'\\CADASTRO_NACIONAL_PARCEIROS_ATUAL.xlsb', 
                                        engine='pyxlsb', header=11, dtype={'NUMERO_CNPJ': str})
            self.capilaridade = pd.read_excel('C:\\Users\\f115523\\OneDrive - Claro SA\\General\\BASES_TODAS\\Bases Recebidas de Canais\\CAD PDV\\Capilaridade_AA_AAPAP.xlsx', sheet_name='AA')
            print(f"Erro ao carregar dados: {e}")
   
    def base_LOJAS_PAPPremium(self,table = None):
        
        #Se não receber uma tabela como argumento, pega a tabela que fica na base vigente
        if table is None:
            try:
                HC = pd.read_excel(self.caminho_arquivos + '\\HC.xlsb', engine='pyxlsb')
            except:
                HC = pd.read_excel('C:\\Users\\f115523\OneDrive - Claro SA\\General\\BASES_TODAS\\Bases Recebidas de Canais\\Base vigente' + '\\HC.xlsb', engine='pyxlsb')
        else:
            HC = table.copy()

        HC['DATA_ADMISSAO'] = HC.apply(lambda x: dt.datetime(1900, 1, 1) + dt.timedelta(days=x['DATA_ADMISSAO'] - 2), axis=1)

        dict_colunas_HC = {"EMPRESA": "RAZÃO SOCIAL", "EMPRESA_CIDADE": "CIDADE", "EMPRESA_ESTADO": "ESTADO", "DATA_ADMISSAO": "DATA DE ADMISSÃO", "Regional": "REGIONAL"}

        HC['CANAL'] = HC.apply(lambda x: 'PAP PREMIUM' if pd.isnull(x['LP']) else 'LOJAS PRÓPRIAS', axis=1)

        HC = HC[(~HC['LP'].isnull()) | (~HC['PAP premium'].isnull())].rename(columns=dict_colunas_HC)

        cargos_pap_premium = [x for x in HC[HC['CANAL'] == 'PAP PREMIUM']['CARGO'].unique() if 'ALTO VALOR' in x.upper()]

        cargos_lojas = [x for x in HC[HC['CANAL'] == 'LOJAS PRÓPRIAS']['CARGO'].unique()]
        
        return HC[HC['CARGO'].isin(cargos_pap_premium + cargos_lojas)]
    
    def dataadm(self, table, col_data_adm):
        return table.apply(lambda x: dt.datetime(1900, 1, 1) + dt.timedelta(days=x[col_data_adm] - 2) if not np.isnan(x[col_data_adm]) else dt.datetime(1900, 1, 1) + dt.timedelta(days=x['Data Cadastro'] - 2), axis=1)

    def base_AA(self, table = None):

        if table is None:

            try:
                base_aa = pd.read_excel(self.caminho_arquivos + '\\BASE_IW.xlsb', engine='pyxlsb')
            except:
                base_aa = pd.read_excel('C:\\Users\\f115523\\OneDrive - Claro SA\\General\\BASES_TODAS\\Bases Recebidas de Canais\\Base vigente' + '\\BASE_IW.xlsb', engine='pyxlsb')
        else:
            
            base_aa = table.copy()
        
        #Dicionário que renomeia as colunas
        disc_colunas_iw = {"Nome Vendedor":"NOME","Data de Admissão":"DATA DE ADMISSÃO","Cargo":"CARGO","Regional":"REGIONAL","Razão Social":"RAZÃO SOCIAL",'NOME_CIDADE':'CIDADE','NUMERO_CNPJ':'CNPJ'}
        
        #Corrigindo as datas de admissão
        base_aa['Data de Admissão'] = self.dataadm(base_aa,'Data de Admissão')
        
        #Filtrando aa e brand shop no grupo de clientes
        base_aa = base_aa[(base_aa['Grupo de Cliente']=='Agente Autorizado') 
    #                   | (base_aa['Grupo de Cliente']=='Brand Shop')
                        ]
        
        #Filtrando os cargos considerados na análise e tirando os testes que podem aparecer na razão social:
        base_aa = base_aa[base_aa['Cargo'].isin([x for x in base_aa['Cargo'].unique() if 'VENDEDOR' in x.upper() or 'GERENTE' == x.upper()]) & (~base_aa['Razão Social'].isin([x for x in base_aa['Razão Social'].unique() if 'TESTE' in x.upper()]))]
        
        base_aa['CANAL'] = 'AA'

        #Cruzando com a capilaridadde do AA
        #base_aa[base_aa['Cód. Agente'].isin(Capilaridade['CODIGO_AGENTE'].unique())]
        
        
        #Retornando cidade e estado do cad_pdv
        return base_aa[base_aa['Cód. Agente'].isin(self.capilaridade['CODIGO_AGENTE'].unique())].merge(
            self.cad_pdv[['NOME_CIDADE','ESTADO','NUMERO_CNPJ','CODIGO_AGENTE']], 
            left_on='Cód. Agente', 
            right_on='CODIGO_AGENTE', 
            how='left').drop('CODIGO_AGENTE', axis = 1).rename(columns = disc_colunas_iw )

    def base_PME(self, table =  None):

        if table is None:
            try:
                base_pme = pd.read_excel(self.caminho_arquivos + '\\BASE_IW.xlsb', engine='pyxlsb')
            except:
                base_pme = pd.read_excel('C:\\Users\\f115523\\OneDrive - Claro SA\\General\\BASES_TODAS\\Bases Recebidas de Canais\\Base vigente' + '\\BASE_IW.xlsb', engine='pyxlsb')

        else:            
            base_pme = table.copy()
        
        #Dicionário que renomeia as colunas
        disc_colunas_iw = {"Nome Vendedor":"NOME","Data de Admissão":"DATA DE ADMISSÃO","Cargo":"CARGO","Regional":"REGIONAL","Razão Social":"RAZÃO SOCIAL",'NOME_CIDADE':'CIDADE','NUMERO_CNPJ':'CNPJ'}
        
        #Corrigindo as datas de admissão
        base_pme['Data de Admissão'] = self.dataadm(base_pme,'Data de Admissão')
        
        
        #Filtrando os cargos considerados na análise e tirando os testes que podem aparecer na razão social:
        base_pme = base_pme[base_pme['Cargo'].isin([x for x in base_pme['Cargo'].unique() if "CORP VENDEDOR DE AACE" in x.upper() or 'VENDEDOR_PAP INDIRETO PME' == x.upper()]) & (~base_pme['Razão Social'].isin([x for x in base_pme['Razão Social'].unique() if 'TESTE' in x.upper()]))]
        
        base_pme['CANAL'] = 'CLARO EMPRESAS'
        
        
        #Retornando cidade e estado do cad_pdv
        return base_pme.merge(self.cad_pdv[['NOME_CIDADE','ESTADO','NUMERO_CNPJ','CODIGO_AGENTE']], left_on='Cód. Agente', right_on='CODIGO_AGENTE', how='left').drop('CODIGO_AGENTE', axis = 1).rename(columns = disc_colunas_iw )

    def base_varejo_tratada(self, table = None):

        if table is None:
            try:
                base_varejo = pd.read_excel(self.caminho_arquivos + '\\VAREJO.xlsx', header=4)
            except:
                base_varejo = pd.read_excel('C:\\Users\\f115523\\OneDrive - Claro SA\\General\\BASES_TODAS\\Bases Recebidas de Canais\\Base vigente' + '\\VAREJO.xlsx', header=4)
        else:
            base_varejo = table.copy()

        dict_colunas_varejo = {"FUNÇÃO":"CARGO","NOME COMPLETO":"NOME","DATA ADMISSÃO":"DATA DE ADMISSÃO",'CIDADE ':'CIDADE'}

        base_varejo = base_varejo.rename(columns = dict_colunas_varejo)

        return base_varejo

    def PAP_ind(self, table = None):
        
        if table is None:
            try:
                base_PAPind = pd.read_excel(self.caminho_arquivos + '\\PAP INDIRETO.xlsx')
            except:
                base_PAPind = pd.read_excel('C:\\Users\\f115523\\OneDrive - Claro SA\\General\\BASES_TODAS\\Bases Recebidas de Canais\\Base vigente' + '\\PAP INDIRETO.xlsx')

        else: 
            
            base_PAPind = table.copy()

        #Colunas do PAP

        #Cargos_papaind
        cargos_papind = [x for x in base_PAPind['CLASSIFICAÇÃO'].unique() if 'VENDEDOR' in x.upper() or 'VENDEDOR BACK OFFICE' in x.upper()]

        #Canal pap
        base_PAPind['CANAL'] = 'PAP INDIRETO'

        #Nomes de colunas
        dict_colunasPAP = {'CLASSIFICAÇÃO':'CARGO','DATA CADASTRO':'DATA DE ADMISSÃO'}

        return base_PAPind.rename(columns = dict_colunasPAP)

    def base_pap_Ag(self, table = None):

        if table is None:
            try:
                base_PAPind_AG = pd.read_excel(self.caminho_arquivos + '\\PAP INDIRETO AGENCIAS.xlsx', header=1)
            except:
                base_PAPind_AG = pd.read_excel('C:\\Users\\f115523\\OneDrive - Claro SA\\General\\BASES_TODAS\\Bases Recebidas de Canais\\Base vigente' + '\\PAP INDIRETO AGENCIAS.xlsx', header=1)

        else:

            base_PAPind_AG = table.copy()


        dict_papAG = {'DATA ADMISSÃO':'DATA DE ADMISSÃO','AGÊNCIA':'RAZÃO SOCIAL'}

        base_PAPind_AG['CANAL'] = 'PAP INDIRETO'

        return base_PAPind_AG.rename(columns=dict_papAG)

    def base_tlv(self, table = None):
            
        if table is None:
            try:
                tlv = pd.read_excel(self.caminho_arquivos + '\\TELEVENDAS.xlsx')
            except:
                tlv = pd.read_excel('C:\\Users\\f115523\\OneDrive - Claro SA\\General\\BASES_TODAS\\Bases Recebidas de Canais\\Base vigente' + '\\TELEVENDAS.xlsx')
        else:
              
            tlv = table.copy()

        colunas_tlv = {'NOME COMPLETO':'NOME','Data de Admissão':'DATA DE ADMISSÃO','UF':'ESTADO','EPS':'RAZÃO SOCIAL'}
    
        #Encontrando a regional
        tlv.REGIONAL = tlv.REGIONAL.map(self.Regional_tratada).fillna(tlv.UF.map(self.UF_REGIONAL))
    
        #Ajustando o canal
        tlv.CANAL =  tlv.apply(lambda x: 'Televendas ' + x.CANAL, axis = 1)
    
        Status_col_tlv = [x for x in tlv.STATUS.unique() if 'ATIV' in x.upper()]
    
        #retornando somente os ativos
        tlv = tlv[tlv.STATUS.isin(Status_col_tlv)]
    
        #Renomeando as colunas
        tlv.rename(columns = colunas_tlv, inplace = True)

        tlv.CPF = tlv.CPF.map(lambda x: int("".join(map(str,re.findall(r"\d+", str(x))))))
    
        return tlv

    def gerar_ativos(self):

        pap_agencias = self.base_pap_Ag()[self.colunas_PAPind_AG]
        pap_indireto = self.PAP_ind()[self.colunas_papind]
        varejo = self.base_varejo_tratada()[self.Colunas_varejo]
        PME = self.base_PME()[self.colunas_iw]
        AA = self.base_AA()[self.colunas_iw]
        lojas = self.base_LOJAS_PAPPremium()[self.colunas_HC]
        tlv = self.base_tlv()[['RAZÃO SOCIAL','REGIONAL','CIDADE','CPF','NOME','DATA DE ADMISSÃO','CANAL','CNPJ','CARGO','ESTADO']]
        
        try:
            lojas['CPF'] = lojas['CPF'].apply(lambda x: int('{:.0f}'.format(x)))
        except:
            print("Erro ao converter o cpf em números")
        
        consolidado = pd.concat([pap_agencias, pap_indireto, AA, PME, lojas, varejo, tlv]).reset_index(drop='index')
        
        consolidado['DATA DE ADMISSÃO'] = consolidado['DATA DE ADMISSÃO'].map(tratarData)
        
        consolidado['REGIONAL'] = consolidado.REGIONAL.map(self.da_para_regional)
        
        consolidado.CPF = consolidado.CPF.map(lambda x: int("".join(re.findall(r"\d+", str(x)))) if re.findall(r"\d+", str(x)) else None)

        return consolidado
  
class treinados_por_temas:
   
    def __init__(self,historico_treinados = None, treinados_atual = None,pasta_das_bases_turmas = None,caminho_arquivos_canais = None,temas_considerados = None):

        if temas_considerados is None:
            self.temas_considerados = 4
        else:
            self.temas_considerados = temas_considerados

        
        if historico_treinados is None:
            self.Treinados_consolidados = Treinados_consolidados()
            self.Treinados_consolidados = self.Treinados_consolidados.gerar_treinados()
        else:
            self.Treinados_consolidados = Treinados_consolidados(historico_treinados,treinados_atual)
            self.Treinados_consolidados = self.Treinados_consolidados.gerar_treinados()

        if pasta_das_bases_turmas is None:

            self.turmas_consolidadas = consolidar_turmas()
            self.turmas_consolidadas = self.turmas_consolidadas.gerar_turmas()
        else:
            self.turmas_consolidadas = consolidar_turmas(pasta_das_bases_turmas)
            self.turmas_consolidadas = self.turmas_consolidadas.gerar_turmas()
        
        self.treinados_temas = pepilineTotaltemas(self.Treinados_consolidados,self.turmas_consolidadas,self.temas_considerados)

        if caminho_arquivos_canais is None:
            self.df_ativos_treinados = Ativos_consolidados()
            self.df_ativos_treinados = self.df_ativos_treinados.gerar_ativos()
        else:
            self.df_ativos_treinados = Ativos_consolidados(caminho_arquivos_canais)
            self.df_ativos_treinados = self.df_ativos_treinados.gerar_ativos()
       
    def retorna_treinados(self,Ativos, Treinados_por_tema, per_treinados = False):

        def rename_and_drop_columns(ativos_t):
            try:
                new_column_name = ativos_t[~ativos_t.Tema.isnull()].Tema.reset_index().loc[0].values[1]
                ativos_t = ativos_t.rename(columns={'Número': new_column_name}).drop(columns='Tema')
            except Exception as e:
                ativos_t = ativos_t.drop(columns = ['Tema','Número'])
            return ativos_t


        """ 
        Função que retorna os ativos treinados por tema.
        A função espera que o Data Frame tenha a coluna CPF como chave primária.

        Parâmetros
        --------------------
        Ativos: Data Frame com os ativos

        Treinados_por_tema: Data Frame com os treinados de cada tema.

        Retornos
        ---------------------
        Data Frame com os ativos treinados, na coluna o nome do tema e nas linhas o número do treinamento

        """

        self.ativos = Ativos

        self.Treinados_por_tema = Treinados_por_tema

        #retornando o ultimo treinamento de cada tema
        temp = self.Treinados_por_tema.loc[self.Treinados_por_tema.groupby(['Login','Tema'])['Data Final'].idxmax()][['Login','Tema','Número']].set_index('Login')

        ativos_t = pd.merge(self.ativos,temp,left_on='CPF', right_index=True,how='left')

        return rename_and_drop_columns(ativos_t)

       # return ativos_t.rename(columns={'Número':ativos_t[~ativos_t.Tema.isnull()].Tema.reset_index().loc[0].values[1]}).drop(columns='Tema')
        
    def Gera_treinados_por_tema(self, temas_selecionados, Ativos = None):

        if Ativos is None:
            Ativos = self.df_ativos_treinados.copy()

        self.temas_selecionados = temas_selecionados

        if len(self.temas_selecionados) >= 2 and isinstance(self.temas_selecionados,list):

            for x in self.temas_selecionados:

                #código que retorna o tema mais semelhante ao tema escrito pelo usuário
                x = [ y for y in self.treinados_temas.Tema.value_counts().index if x.upper() in y.upper() ][0]

                print(x)

                df_temp = self.treinados_temas[self.treinados_temas.Tema == x]

                Ativos = self.retorna_treinados(Ativos, df_temp,True)

        elif isinstance(self.temas_selecionados,str):
            #Retornando todos os temas que correspondem ao texto incluído. 
            temas_correspondentes = [ y for y in self.treinados_temas.Tema.value_counts().index if self.temas_selecionados.upper() in y.upper() ]

            for x in temas_correspondentes:

                print(x)

                df_temp = self.treinados_temas[self.treinados_temas.Tema == x]

                Ativos = self.retorna_treinados(Ativos, df_temp,True)


        else:

            #código que retorna o tema mais semelhante ao tema escrito pelo usuário
            tema_proximo = [ y for y in self.treinados_temas.Tema.value_counts().index if self.temas_selecionados[0].upper() in y.upper()][0]

            Ativos = self.retorna_treinados(Ativos, self.treinados_temas[self.treinados_temas.Tema == tema_proximo ],True)

        return Ativos

class contratados_vs_treinados:
    
    def __init__(self,caminho_arquivos_canais = None ,historico_treinados = None,treinados_atual = None):

        if historico_treinados is None: 
            self.df_treinados = Treinados_consolidados()
            self.df_treinados = self.df_treinados.gerar_treinados()
        else:
            self.df_treinados = Treinados_consolidados(historico_treinados,treinados_atual)
            self.df_treinados = self.df_treinados.gerar_treinados()

        if caminho_arquivos_canais is None:

            self.consolidado = Ativos_consolidados()
            self.consolidado = self.consolidado.gerar_ativos()
        else:
            self.consolidado = Ativos_consolidados(caminho_arquivos_canais)
            self.consolidado = self.consolidado.gerar_ativos()

    def gera_contratados_vs_treinados(self):

        #Criando a tabela de formados
        treinados_formacao = self.df_treinados[self.df_treinados['Categoria Tema'] == 'Formação Inicial']

        #Retornando a ultima formação de cada colaborador e cruzando com os ativos do canal
        ativos_formados = pd.merge(self.consolidado,
                                treinados_formacao.loc[treinados_formacao.groupby('Login')['Data Final'].idxmax()][['Login','Data Final']],
                                left_on='CPF',
                                right_on='Login',
                                how= 'left')
        
        return ativos_formados

class Extracao_turmas_jump:

    def __init__(self, USERNAME = None,PASSWORD = None,DOWNLOAD_DIR=None, DIAS_EXTRACAO = None):
        
        if DIAS_EXTRACAO is None:
            self.DIAS_EXTRACAO = int(dt.datetime.now().day) 
        else:
            self.DIAS_EXTRACAO = DIAS_EXTRACAO
        
        self.URL_LOGIN = "https://www.jumptargets.com.br/claro/login.php"
        self.URL_DOWNLOAD = "http://www.jumptargets.com.br/claro/twagenda.php"
        self.URL_DOWNLOAD_treinados = "https://www.jumptargets.com.br/claro/twpessoa.php"

        if USERNAME is None:
            self.USERNAME = 'diogo.henrique@claro.com.br'
        else:
            self.USERNAME = USERNAME

        if PASSWORD is None:
            self.PASSWORD = '37846040'
        else:
            self.PASSWORD = PASSWORD

        if DOWNLOAD_DIR is None:
            self.DOWNLOAD_DIR = usuario + 'General\\BASES_TODAS\\Bases Plataformas\\PAINEIS JUMP\\Relatório_de_Turmas\\Resumo_Turmas_JUMP_2025\\TURMAS POR MÊS 2025'
        else:
            self.DOWNLOAD_DIR = DOWNLOAD_DIR
            
        self.DATA_EXTRACAO = (dt.datetime.today() - dt.timedelta(days=self.DIAS_EXTRACAO)).strftime('%d/%m/%Y')
        self.NOVO_NOME = f"relatorio_{dt.datetime.now().strftime('%d%m%Y')}.csv"
        self.NOVO_NOME_treinados = f"relatorio_treinados_{dt.datetime.now().strftime('%d%m%Y')}.csv"

    def download_turmas(self):

        chrome_options = webdriver.ChromeOptions()

        configuracao_chrome = {
            "download.default_directory": self.DOWNLOAD_DIR,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }

        chrome_options.add_experimental_option("prefs", configuracao_chrome)

        navegador = webdriver.Chrome(options=chrome_options)

        try:
            # Etapas de login e navegação
            navegador.get(self.URL_LOGIN)
            navegador.find_element(By.NAME, "email").send_keys(self.USERNAME)
            navegador.find_element(By.NAME, "senha").send_keys(self.PASSWORD)
            navegador.find_element(By.CLASS_NAME, "botao").click()
            
            time.sleep(2)
            # Navegação para a página de download
            navegador.get(self.URL_DOWNLOAD)
            
            # Aplicar filtros
            data_inicial = WebDriverWait(navegador, 20).until(
                EC.element_to_be_clickable((By.NAME, "dt_inicial"))
            )
            data_inicial.clear()
            data_inicial.send_keys(self.DATA_EXTRACAO)
            navegador.find_element(By.NAME, "reset23").click()
            
            # monitoramento de abas (A confirmação do download em andamento acontece quando uma nova guia é aberta)
            abas_originais = navegador.window_handles  # Guarda as abas existentes
            
            time.sleep(3)
            # Iniciar download
            link_excel = WebDriverWait(navegador, 20).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, 'javascript:excel2()')]"))
            )
            link_excel.click()
            
            time.sleep(3)
            # Gatilho principal: nova aba aberta = download iniciado
            try:
                WebDriverWait(navegador, 30).until(
                    lambda d: len(d.window_handles) > len(abas_originais)  # Condição de nova aba
                )
                print("Nova guia detectada! Download iniciado. Fechando navegador...")
                
            except:
                # Fallback: se não abrir nova aba, usar verificação tradicional
                print("Nova guia não detectada. Verificando download via arquivo...")
                start_time = time.time()
                while not any(f.endswith('.crdownload') for f in os.listdir(self.DOWNLOAD_DIR)):
                    if time.time() - start_time > 60:
                        raise TimeoutError("Download não iniciado")
                    time.sleep(1)
                print("Download iniciado via fallback")

            time.sleep(3)
        finally:
            # Fechar navegador imediatamente após o gatilho (nova aba ou fallback)
            navegador.quit()
            print("Navegador fechado com sucesso")

        # Etapa pós-fechamento: renomear arquivo
        arquivos = sorted(
            [os.path.join(self.DOWNLOAD_DIR, f) for f in os.listdir(self.DOWNLOAD_DIR) if f.endswith('.csv')],
            key=os.path.getctime,
            reverse=True
        )

        if arquivos:
            novo_caminho = os.path.join(self.DOWNLOAD_DIR,self.NOVO_NOME)
            if os.path.exists(novo_caminho):
                os.remove(novo_caminho)
            os.rename(arquivos[0], novo_caminho)
            print(f"Arquivo renomeado: {novo_caminho}")

    def download_treinados(self):

        chrome_options = webdriver.ChromeOptions()

        configuracao_chrome = {
            "download.default_directory": self.DOWNLOAD_DIR,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }

        chrome_options.add_experimental_option("prefs", configuracao_chrome)

        navegador = webdriver.Chrome(options=chrome_options)

        try:
            # Etapas de login e navegação
            navegador.get(self.URL_LOGIN)
            navegador.find_element(By.NAME, "email").send_keys(self.USERNAME)
            navegador.find_element(By.NAME, "senha").send_keys(self.PASSWORD)
            navegador.find_element(By.CLASS_NAME, "botao").click()
            
            time.sleep(2)
            # Navegação para a página de download
            navegador.get(self.URL_DOWNLOAD_treinados)
            
            # Aplicar filtros
            data_inicial = WebDriverWait(navegador, 20).until(
                EC.element_to_be_clickable((By.NAME, "dt_inicial"))
            )
            data_inicial.clear()
            data_inicial.send_keys(self.DATA_EXTRACAO)
            navegador.find_element(By.NAME, "reset23").click()
            
            # monitoramento de abas (A confirmação do download em andamento acontece quando uma nova guia é aberta)
            abas_originais = navegador.window_handles  # Guarda as abas existentes
            
            time.sleep(3)
            # Iniciar download
            link_excel = WebDriverWait(navegador, 20).until(
                EC.element_to_be_clickable((By.XPATH, "//input[@value='Gerar Excel']"))
            )
            link_excel.click()
            
            # Gatilho principal: nova aba aberta = download iniciado
            try:
                WebDriverWait(navegador, 30).until(
                    lambda d: len(d.window_handles) > len(abas_originais)  # Condição de nova aba
                )
                print("Nova guia detectada! Download iniciado. Fechando navegador...")
                
            except:
                # Fallback: se não abrir nova aba, usar verificação tradicional
                print("Nova guia não detectada. Verificando download via arquivo...")
                start_time = time.time()
                while not any(f.endswith('.crdownload') for f in os.listdir(self.DOWNLOAD_DIR)):
                    if time.time() - start_time > 30:
                        raise TimeoutError("Download não iniciado")
                    time.sleep(1)
                print("Download iniciado via fallback")

            time.sleep(5)
        finally:
            # Fechar navegador imediatamente após o gatilho (nova aba ou fallback)
            navegador.quit()
            print("Navegador fechado com sucesso")

        # Etapa pós-fechamento: renomear arquivo
        arquivos = sorted(
            [os.path.join(self.DOWNLOAD_DIR, f) for f in os.listdir(self.DOWNLOAD_DIR) if f.endswith('.csv')],
            key=os.path.getctime,
            reverse=True
        )

        if arquivos:
            novo_caminho = os.path.join(self.DOWNLOAD_DIR,self.NOVO_NOME_treinados)
            if os.path.exists(novo_caminho):
                os.remove(novo_caminho)
            os.rename(arquivos[0], novo_caminho)
            print(f"Arquivo renomeado: {novo_caminho}")

class radar:

    def __init__(self, dias = None, data_limite = None):

        #Colunas do radar
        self.Colunas_radar = ["Número",
           "Tipo de Treinamento",
           "Data Inicial",
           "Data Final",
           "Status",
           "Instrutor",
           "Tipo de Cliente",
           "Regional Treinamento",
           "Canal",
           "Cidade",
           "Estado",
           "Duração",
           "Nº Particip.(Expectativa)",
           "Participantes Inscritos",
           "Participantes Treinados",
           "Categoria Tema",
           "Tema",
           "Observações",
           "Lista",
           "Galeria"]  
            
        self._ = dt.datetime.now().strftime('%d_%m_%Y')

        if dias is None:
            instancia_download_turmas = Extracao_turmas_jump()
        else:
            instancia_download_turmas = Extracao_turmas_jump(DIAS_EXTRACAO=dias)

        #Intanciando e gerando as turmas do jump
        instancia_download_turmas.download_turmas()

        instancia_turmas = consolidar_turmas()

        #lista de e-mails
        self.E_mails = instancia_turmas.E_mails

        #Caminho das turmas
        Turmas_atualizadas =  os.path.join(instancia_download_turmas.DOWNLOAD_DIR,instancia_download_turmas.NOVO_NOME)

        #pegando a base de turmas geradas pelo código
        radar = pd.read_csv(Turmas_atualizadas,encoding='ISO-8859-1',sep=';',usecols=self.Colunas_radar)
        
        facilitadores = [ x for x in radar['Instrutor'].unique() if 'Facilitador' in x]
        radar_facilitadores = radar[radar['Instrutor'].isin(facilitadores)]
        radar_instrutores = radar[~radar['Instrutor'].isin(facilitadores)]

        if data_limite is None:
            pass
        else:
            radar_instrutores = radar_instrutores[radar_instrutores['Data Inicial'].map(tratarData) <= tratarData(data_limite)]
            radar_facilitadores = radar_facilitadores[radar_facilitadores['Data Inicial'].map(tratarData) <= tratarData(data_limite)]

        
        self.Erros_do_radar = instancia_turmas.funcao_radar(radar_instrutores)
        self.Erros_do_radar_terceiros = instancia_turmas.funcao_radar(radar_facilitadores)

    def mandar_email(self):

        for y in [x for x in self.Erros_do_radar.Instrutor.unique()]:

            erros_atual = self.Erros_do_radar[self.Erros_do_radar.Instrutor == y ]
            
            print(f' Intrutor(a) {y} tem {erros_atual.shape[0]} erros no radar')
        
            arquivo = usuario + f"General\\BASES_TODAS\\Bases Plataformas\\Bases relatório padrão\\RADAR\\Erros_radar\\Radar_{y}dia{self._}.xlsx"

            #colocar caminho interiro da pasta
            erros_atual.to_excel(arquivo)

            try:

                email_destinatario = f"{self.E_mails[self.E_mails['Nome no jump'] == y]['e-mail'].values[0]};{self.E_mails[self.E_mails['Nome no jump'] == y]['e-mail_gestor'].values[0]}"

            except:
                print(f'Erro ao localizar o e-mail do(a) instrutor {y}')
                email_destinatario = 'diogo.henrique@claro.com.br'
        
            nome = y.split(" ")[0].capitalize()
        
            outlook = win32.Dispatch('outlook.application')

            print(arquivo)
            
            #criando o e-mail
            email = outlook.CreateItem(0)
            email.To = email_destinatario
            email.CC = "Angela.Mauricio@claro.com.br;ketlyn.pereira@claro.com.br"
            email.Subject = 'Radar (e-mail automático, por favor não responda diretamente)'
            email.Attachments.Add(arquivo)
            email.HTMLBody = f"""
            <html>
                <head>
                    <style>
                        body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; }}
                        .corpo {{ max-width: 700px; margin: 0 auto; padding: 20px; }}
                        .header {{ background-color: #AB0A00; color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
                        .content {{ padding: 25px; background-color: #f8f9fa; border-radius: 0 0 8px 8px; }}
                        .texto_alerta {{ border-left: 10px solid #AB0A00; padding: 10px; margin: 10px 0; }}
                        .destaque {{ color: #AB0A00; font-weight: bold; }}
                        .rodape {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; color: #7f8c8d; font-size: 0.9em; }}
                        .button {{ 
                            background-color: #3498db; 
                            color: white; 
                            padding: 10px 20px; 
                            text-decoration: none; 
                            border-radius: 5px; 
                            display: inline-block;
                            margin: 15px 0;
                        }}
                    </style>
                </head>
                <body>
                    <div class="corpo">
                        <div class="header">
                            <h2>🔍 Inconsistências Identificadas - Turmas do Jump</h2>
                        </div>
                        
                        <div class="content">
                            <p>Prezado(a) <strong>{nome}</strong>,</p>
                            
                            <div class="texto_alerta">
                                <p>Identificamos <span class="destaque">{erros_atual.shape[0]} turmas com inconsistências</span> lançadas no Jump que necessitam de sua atenção.</p>
                            </div>
                            
                            <p><strong>Próximos passos:</strong></p>
                            <ol>
                                <li>Analisar a planilha em anexo com os detalhes das inconsistências</li>
                                <li>Realizar as correções necessárias no Jump</li>
                            </ol>
                            
                            <p>Em caso de dúvidas sobre como proceder com as correções, procure seu coordenador.</p>
                            
                            <div class="rodape">
                                <p>Atenciosamente,</p>
                                <p><strong>Time de Treinamento Comercial | Inteligencia Operacional</strong></p>
                                <p style="font-size: 0.8em;">Este é um e-mail automático, por favor não responda diretamente.</p>
                            </div>
                        </div>
                    </div>
                </body>
            </html>
            """
            print('E-mail enviado')

            email.Send()

        return print('instrutores notificados')
    
#Dimensão de produtos vendidos e seus semelhantes.
#Criamos esse arquivo no notebook que avalia a do vetor do nome do tema treinado com o nome do produto vendido.
de_paraProdutos = {'CLARO BOX TV': 'CLARO BOX TV',
 'CLARO BOX TV CONMEBOL TV': 'CLARO BOX TV',
 'CLARO BOX TV GLOBOPLAY': 'CLARO BOX TV',
 'CLARO BOX TV HBO': 'CLARO BOX TV',
 'CLARO BOX TV MERCANTIL': 'CLARO BOX TV',
 'CLARO BOX TV PARAMOUNT+': 'CLARO BOX TV',
 'CLARO BOX TV TOP': 'CLARO BOX TV',
 'CLARO TV MAIS 4K BLACK FRIDAY': 'BLACK FRIDAY 2022',
 'CLARO TV MAIS BOX': 'CLARO BOX TV',
 'CLARO TV MAIS BOX BLACK FRIDAY': 'CLARO BOX TV',
 'CLARO TV MAIS SOUNDBOX': 'CLARO TV+ SOUNDBOX',
 'CLARO TV MAIS SOUNDBOX - CABO': 'CLARO TV+ SOUNDBOX',
 'CLARO TV MAIS SOUNDBOX - CABO BLACK FRIDAY': 'BLACK FRIDAY 2022',
 'CLARO TV MAIS SOUNDBOX - STREAMING': 'CLARO TV+ SOUNDBOX',
 'CLARO TV MAIS SOUNDBOX - STREAMING BLACK FRIDAY': 'BLACK FRIDAY 2022',
 'Claro Controle': 'CONTROLE',
 'Claro Controle Mais 3GB + Ilimitado': 'CONTROLE',
 'Claro Controle ON 10GB (Fácil)': 'CONTROLE',
 'Claro Controle ON 12GB Rentab': 'CONTROLE',
 'Claro Controle ON 15GB': 'CONTROLE',
 'Claro Controle ON 15GB + 5GB Multi': 'CONTROLE',
 'Claro Controle ON 20GB': 'CONTROLE',
 'Claro Controle ON 20GB + 5GB Multi': 'CONTROLE',
 'Claro Controle ON 25GB - Gaming': 'CONTROLE',
 'Claro Controle ON 25GB - Gaming + 5GB Multi': 'CONTROLE',
 'Claro Controle Play 3GB + Minutos Ilimitados': 'CONTROLE',
 'Claro Controle Super 1GB': 'CONTROLE',
 'Claro Controle Super 3GB': 'CONTROLE',
 'Claro Controle Super 4GB': 'CONTROLE',
 'Claro Controle Super 5GB': 'CONTROLE',
 'Claro Controle Super 6GB': 'CONTROLE',
 'Claro Controle+ 10GB': 'CONTROLE',
 'Claro Controle+ 10GB Disney+': 'CONTROLE',
 'Claro Controle+ 10GB Disney+_A': 'CONTROLE',
 'Claro Controle+ 10GB Fácil': 'CONTROLE',
 'Claro Controle+ 10GB Gaming': 'CONTROLE',
 'Claro Controle+ 10GB Gaming_A': 'CONTROLE',
 'Claro Controle+ 10GB Globoplay': 'CONTROLE',
 'Claro Controle+ 10GB Globoplay_A': 'CONTROLE',
 'Claro Controle+ 10GB HBO Max': 'CONTROLE',
 'Claro Controle+ 10GB HBO Max_A': 'CONTROLE',
 'Claro Controle+ 10GB HBO Max_Redutor': 'CONTROLE',
 'Claro Controle+ 10GB Netflix': 'CONTROLE',
 'Claro Controle+ 10GB Netflix_A': 'CONTROLE',
 'Claro Controle+ 10GB SEM SVA': 'CONTROLE',
 'Claro Controle+ 10GB SEM SVA_A': 'CONTROLE',
 'Claro Controle+ 10GB TikTok': 'CONTROLE',
 'Claro Controle+ 10GB TikTok Fácil': 'CONTROLE',
 'Claro Controle+ 10GB_A': 'CONTROLE',
 'Claro Controle+ 10GB_Redutor': 'CONTROLE',
 'Claro Controle+ 13GB (Combo) SEM SVA': 'CONTROLE',
 'Claro Controle+ 13GB (Combo) SEM SVA_A': 'CONTROLE',
 'Claro Controle+ 13GB (Combo) SEM SVA_Redutor': 'CONTROLE',
 'Claro Controle+ 13GB Combo': 'CONTROLE',
 'Claro Controle+ 13GB Combo SEM SVA': 'CONTROLE',
 'Claro Controle+ 15GB': 'CONTROLE',
 'Claro Controle+ 15GB (Combo)': 'CONTROLE',
 'Claro Controle+ 15GB (Combo)_A': 'CONTROLE',
 'Claro Controle+ 15GB (Rentab.)': 'CONTROLE',
 'Claro Controle+ 15GB Combo': 'CONTROLE',
 'Claro Controle+ 15GB Combo Disney+': 'CONTROLE',
 'Claro Controle+ 15GB Combo Gaming': 'CONTROLE',
 'Claro Controle+ 15GB Combo Globoplay': 'CONTROLE',
 'Claro Controle+ 15GB Combo HBO Max': 'CONTROLE',
 'Claro Controle+ 15GB Combo Netflix': 'CONTROLE',
 'Claro Controle+ 15GB Combo TikTok': 'CONTROLE',
 'Claro Controle+ 15GB Disney+ (Combo)': 'CONTROLE',
 'Claro Controle+ 15GB Gaming (Combo)': 'CONTROLE',
 'Claro Controle+ 15GB Gaming (Combo)_A': 'CONTROLE',
 'Claro Controle+ 15GB Globoplay (Combo)': 'CONTROLE',
 'Claro Controle+ 15GB Globoplay (Combo)_A': 'CONTROLE',
 'Claro Controle+ 15GB HBO Max (Combo)': 'CONTROLE',
 'Claro Controle+ 15GB HBO Max (Combo)_A': 'CONTROLE',
 'Claro Controle+ 15GB Netflix (Combo)': 'CONTROLE',
 'Claro Controle+ 15GB Netflix (Combo)_A': 'CONTROLE',
 'Claro Controle+ 15GB TikTok (Combo)': 'CONTROLE',
 'Claro Controle+ 4GB (Rentab.)': 'CONTROLE',
 'Claro Controle+ 6GB (Rentab.)': 'CONTROLE',
 'Claro Controle+ 8GB': 'CONTROLE',
 'Claro Controle+ 8GB Fácil': 'CONTROLE',
 'Claro Controle+ 8GB SEM SVA': 'CONTROLE',
 'Claro Controle+ 8GB SEM SVA_A': 'CONTROLE',
 'Claro Controle+ 8GB_A': 'CONTROLE',
 'Claro Controle+ 8GB_Redutor': 'CONTROLE',
 'Claro Flex 10GB': 'CLARO FLEX',
 'Claro Flex 10GB (8GB + 2GB Bônus)': 'CLARO FLEX',
 'Claro Flex 12GB (8GB + 2GB + 2GB Bônus)': 'CLARO FLEX',
 'Claro Flex 16GB': 'CLARO FLEX',
 'Claro Flex 20GB (15GB + 5GB Bônus)': 'CLARO FLEX',
 'Claro Flex 35GB (30GB + 5GB Bônus)': 'CLARO FLEX',
 'Claro Flex 8GB': 'CLARO FLEX',
 'Claro Internet Mais 120GB': 'INTERNET MAIS',
 'Claro Internet Mais 120GB + Noites em Claro': 'INTERNET MAIS',
 'Claro Internet Mais 20GB': 'INTERNET MAIS',
 'Claro Internet Mais 20GB + Noites em Claro': 'INTERNET MAIS',
 'Claro Internet Mais 40GB': 'INTERNET MAIS',
 'Claro Internet Mais 40GB + Noites em Claro': 'INTERNET MAIS',
 'Claro Internet Móvel 400GB': 'INTERNET MAIS',
 'Claro Internet Móvel 5G+ 200GB': 'BANDA LARGA MÓVEL ',
 'Claro Internet Móvel 5G+ 400GB': 'BANDA LARGA MÓVEL ',
 'Claro Internet Móvel Mais 200GB': 'INTERNET MAIS',
 'Claro Pós': 'CLARO PÓS PAGO',
 'Claro Pós Conectado 100GB': 'CLARO PÓS PAGO',
 'Claro Pós Conectado 100GB - Combo': 'CLARO PÓS PAGO',
 'Claro Pós Conectado 100GB - Combo - Oferta 50%': 'CLARO PÓS PAGO',
 'Claro Pós Conectado 120GB + Conmebol + Netflix': 'CLARO PÓS PAGO',
 'Claro Pós Conectado 120GB - Combo + Conmebol + Netflix': 'CLARO PÓS PAGO',
 'Claro Pós Conectado 15GB': 'CLARO PÓS PAGO',
 'Claro Pós Conectado 2.0 25GB + SVA + GloboPlay': 'CLARO PÓS PAGO',
 'Claro Pós Conectado 200GB - Combo': 'CLARO PÓS PAGO',
 'Claro Pós Conectado 20GB': 'CLARO PÓS PAGO',
 'Claro Pós Conectado 20GB - Combo': 'CLARO PÓS PAGO',
 'Claro Pós Conectado 20GB - Combo - Oferta R$20': 'CLARO PÓS PAGO',
 'Claro Pós Conectado 240GB - Combo + Conmebol + Netflix': 'CLARO PÓS PAGO',
 'Claro Pós Conectado 25GB + Conmebol': 'CLARO PÓS PAGO',
 'Claro Pós Conectado 25GB + Conmebol + Netflix': 'CLARO PÓS PAGO',
 'Claro Pós Conectado 25GB + Futebol e Filmes': 'CLARO PÓS PAGO',
 'Claro Pós Conectado 25GB + Globoplay': 'CLARO PÓS PAGO',
 'Claro Pós Conectado 25GB + HBO Max': 'CLARO PÓS PAGO',
 'Claro Pós Conectado 25GB + Netflix': 'CLARO PÓS PAGO',
 'Claro Pós Conectado 30GB': 'CLARO PÓS PAGO',
 'Claro Pós Conectado 30GB - Combo': 'CLARO PÓS PAGO',
 'Claro Pós Conectado 30GB - Combo - Oferta R$20': 'CLARO PÓS PAGO',
 'Claro Pós Conectado 40GB - Combo': 'CLARO PÓS PAGO',
 'Claro Pós Conectado 40GB - Combo - Oferta R$20': 'CLARO PÓS PAGO',
 'Claro Pós Conectado 50GB': 'CLARO PÓS PAGO',
 'Claro Pós Conectado 50GB - Combo + Conmebol': 'CLARO PÓS PAGO',
 'Claro Pós Conectado 50GB - Combo + Conmebol + Netflix': 'CLARO PÓS PAGO',
 'Claro Pós Conectado 50GB - Combo + Conmebol - Oferta R$20': 'CLARO PÓS PAGO',
 'Claro Pós Conectado 50GB - Combo + Conmebol e Netflix': 'CLARO PÓS PAGO',
 'Claro Pós Conectado 50GB - Combo + Futebol': 'CLARO PÓS PAGO',
 'Claro Pós Conectado 50GB - Combo + Globoplay': 'CLARO PÓS PAGO',
 'Claro Pós Conectado 50GB - Combo + Globoplay - Oferta R$20': 'CLARO PÓS PAGO',
 'Claro Pós Conectado 50GB - Combo + HBO Max': 'CLARO PÓS PAGO',
 'Claro Pós Conectado 50GB - Combo + HBO Max - Oferta R$20': 'CLARO PÓS PAGO',
 'Claro Pós Conectado 50GB - Combo + Netflix': 'CLARO PÓS PAGO',
 'Claro Pós Conectado 60GB + Conmebol + Netflix': 'CLARO PÓS PAGO',
 'Claro Pós Conectado 60GB - Combo': 'CLARO PÓS PAGO',
 'Claro Pós Conectado 60GB - Combo - Oferta 50%': 'CLARO PÓS PAGO',
 'Claro Pós Conectado 70GB': 'CLARO PÓS PAGO',
 'Claro Pós Mais 6GB': 'CLARO PÓS PAGO',
 'Claro Pós ON 100GB Multi': 'CLARO PÓS PAGO',
 'Claro Pós ON 150GB': 'CLARO PÓS PAGO',
 'Claro Pós ON 150GB Multi': 'CLARO PÓS PAGO',
 'Claro Pós ON 25GB': 'CLARO PÓS PAGO',
 'Claro Pós ON 25GB Multi': 'CLARO PÓS PAGO',
 'Claro Pós ON 300GB Multi': 'CLARO PÓS PAGO',
 'Claro Pós ON 50GB': 'CLARO PÓS PAGO',
 'Claro Pós ON 50GB Multi': 'CLARO PÓS PAGO',
 'Claro Pós ON 75GB': 'CLARO PÓS PAGO',
 'Claro Pós Play 20GB': 'CLARO PÓS PAGO',
 'Claro Pós Super 100GB + SVA': 'CLARO PÓS PAGO',
 'Claro Pós Super 10GB + SVA': 'CLARO PÓS PAGO',
 'Claro Pós Super 15GB + SVA': 'CLARO PÓS PAGO',
 'Claro Pós Super 50GB + SVA': 'CLARO PÓS PAGO',
 'Claro Pós Super 8GB + SVA': 'CLARO PÓS PAGO',
 'Claro Pós Tudo 7GB': 'CLARO PÓS PAGO',
 'Claro Pós+ 100GB': 'CLARO PÓS PAGO',
 'Claro Pós+ 100GB Combo': 'CLARO PÓS PAGO',
 'Claro Pós+ 100GB Individual (5G SA)': 'CLARO PÓS PAGO',
 'Claro Pós+ 200GB': 'CLARO PÓS PAGO',
 'Claro Pós+ 200GB Combo': 'CLARO PÓS PAGO',
 'Claro Pós+ 200GB Combo (5G SA)': 'CLARO PÓS PAGO',
 'Claro Pós+ 200GB Individual (5G SA)': 'CLARO PÓS PAGO',
 'Claro Pós+ 25GB': 'CLARO PÓS PAGO',
 'Claro Pós+ 25GB - Combo': 'CLARO PÓS PAGO',
 'Claro Pós+ 25GB Combo': 'CLARO PÓS PAGO',
 'Claro Pós+ 25GB Disney+ e Star+': 'CLARO PÓS PAGO',
 'Claro Pós+ 25GB Disney+ e Star+_A': 'CLARO PÓS PAGO',
 'Claro Pós+ 25GB Fórmula 1': 'FÓRMULA 1',
 'Claro Pós+ 25GB Globoplay': 'CLARO PÓS PAGO',
 'Claro Pós+ 25GB HBO Max': 'CLARO PÓS PAGO',
 'Claro Pós+ 25GB Netflix': 'CLARO PÓS PAGO',
 'Claro Pós+ 400GB Combo': 'CLARO PÓS PAGO',
 'Claro Pós+ 400GB Combo (5G SA)': 'CLARO PÓS PAGO',
 'Claro Pós+ 50GB': 'CLARO PÓS PAGO',
 'Claro Pós+ 50GB Combo': 'CLARO PÓS PAGO',
 'Claro Pós+ 50GB Combo Disney+ e Star+': 'CLARO PÓS PAGO',
 'Claro Pós+ 50GB Combo Disney+ e Star+_A': 'CLARO PÓS PAGO',
 'Claro Pós+ 50GB Combo Globoplay': 'CLARO PÓS PAGO',
 'Claro Pós+ 50GB Combo HBO Max': 'CLARO PÓS PAGO',
 'Claro Pós+ 50GB Combo Netflix': 'CLARO PÓS PAGO',
 'Claro TV MAIS BOX': 'CLARO BOX TV',
 'Controle Conectado 10GB': 'CONTROLE',
 'Controle Conectado 10GB + Conmebol': 'CONTROLE',
 'Controle Conectado 10GB + Gaming': 'CONTROLE',
 'Controle Conectado 10GB + Globoplay': 'CONTROLE',
 'Controle Conectado 10GB + HBO Max': 'CONTROLE',
 'Controle Conectado 10GB + Netflix': 'CONTROLE',
 'Controle Conectado 13GB - Combo': 'CONTROLE',
 'Controle Conectado 15GB - Combo': 'CONTROLE',
 'Controle Conectado 15GB - Combo + Conmebol': 'CONTROLE',
 'Controle Conectado 15GB - Combo + Gaming': 'CONTROLE',
 'Controle Conectado 15GB - Combo + Globoplay': 'CONTROLE',
 'Controle Conectado 15GB - Combo + HBO Max': 'CONTROLE',
 'Controle Conectado 15GB - Combo + Netflix': 'CONTROLE',
 'Controle Conectado 3GB': 'CONTROLE',
 'Controle Conectado 4GB': 'CONTROLE',
 'Controle Conectado 6GB': 'CONTROLE',
 'Controle Conectado 6GB - Combo': 'CONTROLE',
 'Controle Conectado 8GB': 'CONTROLE',
 'Controle Plus 3GB': 'CONTROLE',
 'Controle Plus 4GB': 'CONTROLE',
 'Controle Plus 5GB': 'CONTROLE',
 'Controle R$  49,89 (Fácil)': 'CONTROLE',
 'Controle R$  59,89 (Fácil)': 'CONTROLE',
 'Controle R$ 49,89 (Controle Fácil)': 'CONTROLE',
 'Controle R$ 59,89 (Controle Fácil)': 'CONTROLE',
 'Dependente Banda Larga': 'BANDA LARGA MÓVEL ',
 'EXTENSOR MESH COMODATO': 'EXTENSOR WI-FI MESH',
 'EXTENSOR WI-FI MESH COMODATO': 'EXTENSOR WI-FI MESH',
 'NET BOX TV': 'CLARO BOX TV',
 'NET BOX TV CONMEBOL TV': 'CLARO BOX TV',
 'NET BOX TV GLOBOPLAY': 'CLARO BOX TV',
 'NET BOX TV HBO': 'CLARO BOX TV',
 'NET BOX TV PARAMOUNT+': 'CLARO BOX TV',
 'NET BOX TV TOP': 'CLARO BOX TV',
 'NET TV MAIS BOX': 'CLARO BOX TV',
 'VIRTUA 1 GB': 'NET VIRTUA',
 'VIRTUA 1 GB - (IP FIXO)': 'NET VIRTUA',
 'VIRTUA 1 GB - PME': 'NET VIRTUA',
 'VIRTUA 10 MB': 'NET VIRTUA',
 'VIRTUA 120 MB': 'NET VIRTUA',
 'VIRTUA 125 MB': 'NET VIRTUA',
 'VIRTUA 15 MB': 'NET VIRTUA',
 'VIRTUA 150 MB - (IP FIXO)': 'NET VIRTUA',
 'VIRTUA 150 MB - PME': 'NET VIRTUA',
 'VIRTUA 240 MB': 'NET VIRTUA',
 'VIRTUA 240 MB - PME': 'NET VIRTUA',
 'VIRTUA 250 MB': 'NET VIRTUA',
 'VIRTUA 250 MB Globoplay': 'NET VIRTUA',
 'VIRTUA 250 MB Netflix': 'NET VIRTUA',
 'VIRTUA 30 MB - PME': 'NET VIRTUA',
 'VIRTUA 300 MB - (IP FIXO)': 'NET VIRTUA',
 'VIRTUA 300 MB - PME': 'NET VIRTUA',
 'VIRTUA 35 MB': 'NET VIRTUA',
 'VIRTUA 350 MB': 'NET VIRTUA',
 'VIRTUA 350 MB - PME': 'NET VIRTUA',
 'VIRTUA 5 MB': 'NET VIRTUA',
 'VIRTUA 50 MB': 'NET VIRTUA',
 'VIRTUA 50 MB (R$ 49,99)': 'NET VIRTUA',
 'VIRTUA 50 MB - PME': 'NET VIRTUA',
 'VIRTUA 500 MB': 'NET VIRTUA',
 'VIRTUA 500 MB Conmebol': 'NET VIRTUA',
 'VIRTUA 500 MB Globoplay': 'NET VIRTUA',
 'VIRTUA 500 MB Netflix': 'NET VIRTUA',
 'VIRTUA 60 MB': 'NET VIRTUA',
 'VIRTUA 60 MB - PME': 'NET VIRTUA',
 'VIRTUA 600 MB - PME': 'NET VIRTUA',
 'VIRTUA 750 MB': 'NET VIRTUA',
 'WI-FI MESH COMODATO': 'EXTENSOR WI-FI MESH',
 'CLARO TV ILIMITADO BRASIL TOTAL':'CLARO TV+',
 'CLARO TV ILIMITADO BRASIL':'CLARO TV+',
 'CLARO TV HBO':'CLARO TV+',
 'FUTEBOL SÓCIO PFC A + B + 5 EST.':'CLARO TV+',
 'CLARO TV TELECINE':'CLARO TV+',
 'CONMEBOL TV':'CLARO TV+',
 'CLARO TV ILIMITADO MUNDO TOTAL':'CLARO TV+',
 'CLARO TV ILIMITADO LOCAL':'CLARO TV+',
 'CLARO NET CONMEBOL TV':'CLARO TV+',
 'CLARO NET COMBATE':'CLARO TV+',
 'CLARO TV COMBATE':'CLARO TV+',
 'NET TV MAIS APP':'CLARO TV+',
 'NET TV MAIS 4K':'CLARO TV+',
 'CLARO TV MAIS APP':'CLARO TV+',
 'NET TV MAIS HD':'CLARO TV+',
 'TV INICIAL HD':'CLARO TV+',
 'CLARO TV MAIS HD':'CLARO TV+',
 'TELECINE':'CLARO TV+',
 'CLARO TV MAIS 4K':'CLARO TV+',
 'COMBATE':'CLARO TV+',
 'FUTEBOL':'CLARO TV+',
 'TOP 4K PREMIUM':'CLARO TV+',
 'FÁCIL SD':'CLARO TV+',
 'PREMIERE':'CLARO TV+',
 'Claro Pós Conectado 20GB  Combo':'CLARO PÓS PAGO',
 'Claro Pós Conectado 60GB  Combo  Oferta 50%':'CLARO PÓS PAGO',
 'Claro Pós Conectado 60GB  Combo':'CLARO PÓS PAGO',
 'Claro Internet Mais 20GB + Promoção Noites em Claro':'INTERNET MAIS',
 'Claro Internet Mais 120GB + Promoção Noites em Claro':'INTERNET MAIS',
 'Claro Pós Conectado 20GB  Combo  Oferta R$20':'CLARO PÓS PAGO',
 'Controle Conectado 13GB  Combo':'CONTROLE',
 'Claro Pós Conectado 100GB  Combo':'CLARO PÓS PAGO',
 'Claro Pós Conectado 40GB  Combo':'CLARO PÓS PAGO',
 'Controle Conectado 15GB  Combo':'CONTROLE',
 'Claro Pós Conectado 30GB  Combo':'CLARO PÓS PAGO',
 'Claro Pós Conectado 100GB  Combo  Oferta 50%':'CLARO PÓS PAGO',
 'Claro Pós Conectado 200GB  Combo':'CLARO PÓS PAGO',
 'Controle R$ 4989 (Controle Fácil)':'CONTROLE',
 'Claro Pós Conectado 40GB  Combo  Oferta R$20':'CLARO PÓS PAGO',
 'Claro Pós Conectado 120GB  Combo + Conmebol + Netflix':'CLARO PÓS PAGO',
 'Controle Conectado 15GB  Combo + Gaming':'CONTROLE',
 'Claro Internet Mais 40GB + Promoção Noites em Claro':'INTERNET MAIS',
 'Claro Pós Conectado 30GB  Combo  Oferta R$20':'CLARO PÓS PAGO',
 'Claro Pós Conectado 50GB  Combo + Globoplay  Oferta R$20':'CLARO PÓS PAGO',
 'Claro Pós Conectado 50GB  Combo + Conmebol  Oferta R$20':'CLARO PÓS PAGO',
 'Controle R$ 5989 (Controle Fácil)':'CONTROLE',
 'Claro Pós Conectado 50GB  Combo + HBO Max  Oferta R$20':'CLARO PÓS PAGO',
 'Claro Pós Conectado 240GB  Combo + Conmebol + Netflix':'CLARO PÓS PAGO',
 'Controle Conectado 15GB  Combo + Netflix':'CONTROLE',
 'Claro Pós Conectado 50GB  Combo + Conmebol':'CLARO PÓS PAGO',
 'Controle Conectado 15GB  Combo + Globoplay':'CONTROLE',
 'Claro Pós Conectado 50GB  Combo + Globoplay':'CLARO PÓS PAGO',
 'Controle Conectado 15GB  Combo + Conmebol':'CONTROLE',
 'Claro Pós Conectado 50GB  Combo + HBO Max':'CLARO PÓS PAGO',
 'VIRTUA 600 MB  PME':'NET VIRTUA',
 'VIRTUA 350 MB  PME':'NET VIRTUA',
 'VIRTUA 150 MB  PME':'NET VIRTUA',
 'VIRTUA 300 MB  PME':'NET VIRTUA',
 'VIRTUA 50 MB  PME':'NET VIRTUA',
 'VIRTUA 60 MB  PME':'NET VIRTUA',
 'VIRTUA 1 GB  PME':'NET VIRTUA',
 'Claro Pós Conectado 50GB  Combo + Futebol':'CLARO PÓS PAGO',
 'VIRTUA 50 MB (R$ 4999)':'NET VIRTUA',
 'VIRTUA 30 MB  PME':'NET VIRTUA',
 'VIRTUA 240 MB  PME':'NET VIRTUA',
 'Claro Pós Conectado 50GB  Combo + Conmebol + Netflix':'CLARO PÓS PAGO',
 'Claro Pós Conectado 50GB  Combo + Conmebol e Netflix':'CLARO PÓS PAGO',
 'Claro Pós+ 25GB  Combo':'CLARO PÓS PAGO',
 'Claro Pós Conectado 50GB  Combo + Netflix':'CLARO PÓS PAGO',
 'Controle Conectado 15GB  Combo + HBO Max':'CONTROLE',
 'Claro Pós Conectado 20 25GB + SVA + GloboPlay':'CLARO PÓS PAGO',
 'Claro Controle+ 15GB (Rentab)':'CONTROLE',
 'Claro Controle+ 4GB (Rentab)':'CONTROLE',
 'Claro Controle+ 6GB (Rentab)':'CONTROLE',
 'Controle Conectado 6GB  Combo':'CONTROLE',
 'VIRTUA 300 MB  (IP FIXO)':'NET VIRTUA',
 'Controle R$  4989 (Fácil)':'CONTROLE',
 'Controle R$  5989 (Fácil)':'CONTROLE',
 'VIRTUA 1 GB  (IP FIXO)':'NET VIRTUA',
 'CLARO TV MAIS SOUNDBOX  STREAMING':'CLARO TV+',
 'CLARO TV MAIS SOUNDBOX  CABO':'CLARO TV+',
 'VIRTUA 150 MB  (IP FIXO)':'NET VIRTUA',
 'CLARO TV MAIS SOUNDBOX  STREAMING BLACK FRIDAY':'CLARO TV+',
 'CLARO TV MAIS SOUNDBOX  CABO BLACK FRIDAY':'CLARO TV+',
 'Claro Internet Mais 120GB_R + Noites em Claro':'INTERNET MAIS',
 'Claro Internet Mais 20GB_R':'INTERNET MAIS',
 'Claro Internet Mais 40GB_R':'INTERNET MAIS',
 'Claro Internet Mais 40GB_R + Noites em Claro':'INTERNET MAIS',
 'Claro Internet Mais 120GB_R':'INTERNET MAIS',
 'Claro Controle ON 25GB  Gaming':'CONTROLE',
 'Claro Controle ON 25GB  Gaming + 5GB Multi':'CONTROLE',
 'Claro Controle ON 12GB':'CONTROLE',
 'Claro Controle Flex 25GB (20GB + 5GB Bônus)':'CONTROLE',
 'Claro Controle ON+ 15GB':'CONTROLE',
 'Claro Controle ON+ 20GB':'CONTROLE',
 'Claro Controle ON+ 15GB + 5GB Multi':'CONTROLE',
 'Claro Controle ON+ 20GB + 5GB Multi':'CONTROLE',
 'Claro Controle ON+ 25GB + 5GB Multi  Gaming':'CONTROLE',
 'Claro Controle Flex 20GB (15GB + 5GB Bônus)':'CONTROLE',
 'Claro Controle Flex 10GB (8GB + 2GB Bônus)':'CONTROLE',
 'Claro Controle Flex 35GB (30GB + 5GB Bônus)':'CONTROLE',
 'Claro Controle ON+ 12GB':'CONTROLE',
 'Claro Controle ON+ 25GB  Gaming':'CONTROLE',
 'Claro Controle Fácil ON+ 20GB + 5GB':'CONTROLE',
 'Claro Controle Fácil ON+ 15GB + 3GB':'CONTROLE',
 'Claro Pós ON 30GB + Cloud Gaming':'CLARO PÓS PAGO',
 'Claro Controle+ 15GB SEM SVA':'CONTROLE',
  'Claro Flex 25GB (20GB + 5GB Bônus)':'CLARO FLEX',
 'Claro Controle ON+ 25GB + 5GB Multi - Gaming':'CONTROLE',
 'Claro Controle ON+ 25GB - Gaming':'CONTROLE',
 'VIRTUA 600 MB - (IP FIXO)':'NET VIRTUA',
 'Claro Internet Móvel Mais 400GB':'INTERNET MAIS',
 'Claro Internet Mais 200GB':'INTERNET MAIS',
 'Claro Internet Mais 400GB':'INTERNET MAIS',
 'Claro Pós ON 25GB Multi Epico':'CLARO PÓS PAGO',
 'Claro Controle ON+ 20GB +5GB Redes Epico':'CONTROLE',
 'Claro Internet Móvel 200GB':'INTERNET MAIS',
 'Claro Controle 2025 ON+ 15GB':'CONTROLE',
 'Claro Controle 2025 ON+ 20GB + 5GB Multi':'CONTROLE',
 'Claro Controle 2025 ON+ 20GB':'CONTROLE',
 'Claro Controle 2025 ON+ 15GB + 5GB':'CONTROLE'
}

dicTemas = {'Cabo e Fibra – Brownfield': 'CLARO FIBRA PF',
 'Claro Fibra PF': 'CLARO FIBRA PF',
 'Banda Larga': 'BANDA LARGA',
 'Banda Larga + Netflix': 'BANDA LARGA',
 'Banda Larga Rede GPON e SVAS': 'BANDA LARGA',
 'Banda Larga Rede HFC e SVAS': 'BANDA LARGA',
 'Banda Larga Tecnologia Rede GPON': 'BANDA LARGA',
 'Banda Larga Tecnologia Rede HFC': 'BANDA LARGA',
 'Banda Larga rede HFC e GPON': 'BANDA LARGA',
 'Gpon': 'GPON',
 "SVA's - Cabo": "SVA'S - CABO",
 'CLARO TV+ SOUNDBOX CABO': 'CLARO TV+ SOUNDBOX',
 'Claro tv+ Soundbox': 'CLARO TV+ SOUNDBOX',
 'Claro Box TV': 'CLARO BOX TV',
 'ENTREGA CLARO TV+ BOX EM LP': 'CLARO BOX TV',
 'Claro Energia': 'CLARO ENERGIA',
 'Claro Fone': 'NET FONE',
 'Net Fone': 'NET FONE',
 'Claro TV Pré Pago': 'CLARO TV PRÉ PAGO',
 'TV - DTH': 'TV - DTH',
 'Extensor Wi-fi Mesh': 'EXTENSOR WI-FI MESH',
 'WI-FI 6': 'EXTENSOR WI-FI MESH',
 'Redes Neutras': 'REDES NEUTRAS',
 'MDU': 'MDU',
 'Net Virtua': 'NET VIRTUA',
 'Now - Cabo': 'NOW - CABO',
 'Ponto Ultra': 'PONTO ULTRA',
 'Processos - Cabo': 'PROCESSOS - CABO',
 'Smart Home': 'SMART HOME',
 'INTERNET MAIS': 'INTERNET MAIS',
 'Portabilidade': 'TOKEN DE PORTABILIDADE',
 'Token de Portabilidade': 'TOKEN DE PORTABILIDADE',
 'Token de Portabilidade Pré Pago': 'TOKEN DE PORTABILIDADE',
 'Aparelhos': 'APARELHOS',
 'Banda Larga Móvel ': 'BANDA LARGA MÓVEL ',
 'Claro internet móvel 5G+ Consumo': 'BANDA LARGA MÓVEL ',
 'Claro internet móvel 5G+ PME': 'BANDA LARGA MÓVEL ',
 'Portfólio Móvel (Pré Controle e Pós)': 'PORTFÓLIO MÓVEL (PRÉ CONTROLE E PÓS)',
 'Proteção Móvel': 'PROTEÇÃO MÓVEL',
 'SVAs Móvel': 'SVAS MÓVEL',
 'COMBATE TIM APPLE ONE': 'COMBATE TIM APPLE ONE',
 'Chip Flex -  Dist Massivo': 'CLARO FLEX',
 'Claro Flex': 'CLARO FLEX',
 'Claro Pay': 'CLARO PAY',
 'Claro Pós Pago': 'CLARO PÓS PAGO',
 'Pré Pago': 'PRÉ PAGO',
 'Claro SYNC': 'CLARO SYNC',
 'Claro Troca': 'CLARO TROCA',
 'Controle': 'CONTROLE',
 'Controle Fácil': 'CONTROLE',
 'Fórmula 1': 'FÓRMULA 1',
 'Prezão + Starbem': 'PREZÃO + STARBEM',
 'Passaportes': 'PASSAPORTES',
 'Tarifação e Roaming': 'TARIFAÇÃO E ROAMING',
 'Backoffice': 'BACKOFFICE',
 'Cabo e Fibra': 'CABO E FIBRA',
 'Minha Claro Móvel/Minha Claro Residencial': 'MINHA CLARO MÓVEL/MINHA CLARO RESIDENCIAL',
 'Combo Multi - AC': 'COMBO MULTI - AC',
 'Combo Multi - AC + ANC': 'COMBO MULTI - AC',
 'Combo Multi - ANC': 'COMBO MULTI - AC',
 'Especialista Combo Multi': 'COMBO MULTI - AC',
 'Concorrência': 'CONCORRÊNCIA',
 'Integração Produtos': 'INTEGRAÇÃO PRODUTOS',
 'MPlay': 'MPLAY',
 'Outage': 'OUTAGE',
 'PAP': 'PAP',
 'Claro TV+':'Claro TV+',
 'Pós Pago ':'CLARO PÓS PAGO',
 'Net TV':'Claro TV+',
 '5G':'BANDA LARGA'
}