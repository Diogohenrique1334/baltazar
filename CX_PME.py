import os
import warnings
warnings.filterwarnings('ignore')
import pandas as pd
import numpy as np
import datetime as dt
from sklearn.preprocessing import MinMaxScaler
from statsmodels.tsa.seasonal import seasonal_decompose
import matplotlib.pyplot as plt
import datetime as dt
import baltazar as btz
import win32com.client as win32
import seaborn as sns
import shutil
from pathlib import Path

pd.set_option('display.float_format', '{:.6f}'.format)

_RAIZ_DADOS = os.getcwd().split('Dados')[0]

class funcoes_globais:

    def __init__(self):
        pass

    def ultimo_arquivo(self,caminho):
        return fr'{caminho}/{max(os.listdir(caminho), key=lambda f: os.path.getmtime(os.path.join(caminho, f)))}'

    def mover_arquivo(self, caminho_origem: str, caminho_destino: str):
        """
        Move um arquivo de um caminho para outro.

        Parameters
        ----------
        caminho_origem : str
            Caminho completo do arquivo atual.
        caminho_destino : str
            Caminho completo onde o arquivo deve ser movido (incluindo o novo nome, se quiser).

        Exemplo:
            mover_arquivo("C:/entrada/arquivo.xlsx", "C:/saida/arquivo.xlsx")
        """
        origem = Path(caminho_origem)
        destino = Path(caminho_destino)

        # Garante que a pasta destino exista
        destino.parent.mkdir(parents=True, exist_ok=True)

        shutil.move(str(origem), str(destino))
        print(f"Arquivo movido com sucesso para: {destino}")

class dados_speech:

    def __init__(self, colunas=None, caminho=None, projeto = None, caminho_historico = None):

        caminho_local_parte1 = _RAIZ_DADOS

        if colunas is None:
            self.colunas = ['% de Tempo de Conversação',
                            '% de Tempo de Fala do Cliente',
                            '% de Tempo de Fala do Funcionário',
                            '% Tempo de Silêncio',
                            'Agrupamento',
                            'ANI',
                            'Call ID',
                            'Direção',
                            'CSPLogin',
                            'Funcionário',
                            'Hora de Início Local',
                            'Segmento',
                            'Skill',
                            'MSISDN',
                            'Protocolo_Nice']
        else:
            self.colunas = colunas
            
        if projeto is None:

            self.projeto = 'Movel'

        else:
            self.projeto = projeto

        if caminho is None:
            caminho_local_parte2 = fr"Dados\Repositorio_dados\Speech_mes\{self.projeto}"
            self.caminho = caminho_local_parte1 + caminho_local_parte2

        else: 
            self.caminho = caminho


        if caminho_historico is None:
            caminho_historico_local_parte2 = fr"Dados\Repositorio_dados\Speech\{self.projeto}"
            self.caminho_historico = caminho_local_parte1 + caminho_historico_local_parte2

        else: 
            self.caminho_historico = caminho_historico
        
    def Pipe_speech(self, caminho_planilha, coluna_referencia='Pontuação'):
        """Função que lê a planilha extraída do speech e prepara ela para ser utilizada nos relatórios"""

        # Lê a planilha inteira sem cabeçalho
        df_raw = pd.read_excel(caminho_planilha, header=None)

        # Detecta a linha do cabeçalho
        linha_cabecalho = df_raw[df_raw.apply(lambda row: coluna_referencia in row.values, axis=1)].index[0]

        # Define os nomes das colunas
        df_raw.columns = df_raw.iloc[linha_cabecalho]

        # Remove as linhas acima do cabeçalho
        df = df_raw.iloc[linha_cabecalho + 1:].reset_index(drop=True)

        Colunas_indesejadas = [ x for x in df.columns if 'E -' in str(x) ] + [ x for x in df.columns if 'E-' in str(x) ] + ['I - Improdutivas','Uncategorized']

        Colunas_indesejadas.append('MACRO - NÃO EXCLUIR')

        # Remove colunas indesejadas
        df = df.dropna(how='all', axis=1).drop(columns=Colunas_indesejadas, errors='ignore')

        df.rename(columns= {"E":"Cliente_estressado(a)"}, inplace=True)

        df.loc[df['Cliente_estressado(a)'] == "E", 'Cliente_estressado(a)'] = 1

        # Cria coluna E com valor 0 para não excluir ligacoes sem registros
        df['E'] = 0

        # Realiza o melt e filtra todos registros com a direcao 'Entrada'
        df = df[df['Direção'] == 'Entrada'].melt(
            id_vars=self.colunas,
            value_vars=df.loc[:, 'Pontuação':'% de Tempo de Conversação'].columns[1:-1],
            var_name='Categoria',
            value_name='Confiança'
        ).dropna(subset=['Confiança']).reset_index(drop=True)

        return self.limpeza_speech_engenharia_features(df)

        #return df
    
    def limpeza_speech_engenharia_features(self,df):
    
        #Identificando a hiper categoria da categoiria
        Hiper_categoria = dict(df.Categoria.map(lambda x: x.split('-')[0].split('_')[0].strip()))
        df['Hiper_categoria'] = df.index.map(Hiper_categoria)

        #Ajuste nas categorias
        df.loc[df['Categoria'] == 'E', 'Hiper_categoria'] = 'Não categorizado'
        df.loc[df.Hiper_categoria == 'Finan', 'Hiper_categoria'] = 'Financeiro'

        #Engenharia de features
        #Limpando ligacoes que estão como E e estão em mais de uma categoria.
        df['Ranking_reclamacao'] = df.groupby('Call ID')['Confiança'].rank(method = 'first', ascending= False)
        df_filtrado = df[~((df.Categoria == 'E') & (df.Ranking_reclamacao > 1))]
        
        df_filtrado['DDD'] = df_filtrado.ANI.map(lambda x: str(x)[:4][2:])

        df_filtrado['Protocolo_Nice'] = df_filtrado.Protocolo_Nice.map(lambda x: str(x) if str(x).isdigit() else None)

        return df_filtrado.reset_index(drop = 'index').merge(Dimensoes().D_Hiper_categoria(planilha = self.projeto).drop(columns = 'Hiper_categoria'),left_on='Categoria', right_index=True, how='left')
    
    def consolidar_bases_speech(self, pasta=None):
        """Função que consolida todas as bases de speech em um único data frame"""

        if pasta is None:
            pasta = self.caminho

        temp = pd.DataFrame()
        for planilha in [ x for x in os.listdir(pasta) if '.xlsx' in x ]:
            print(f'Lendo a planilha: {planilha}')
            temp = pd.concat([temp, self.Pipe_speech(os.path.join(pasta, planilha))]).drop_duplicates()
            print(temp.shape)

        return temp.reset_index(drop=True)
    
    def pipe_ligacoes_dia(self,df = None,agrupador = None, retorno = 'Representatividade dia'):

        """Bloco que transforma o speech em uma série temporal com a representatividade de cada categoria por dia ou com o percentual de ligaçoes por dia."""

        if df is None:

            df = dados_speech(projeto=self.projeto).speech_consolidado()

        if agrupador is None:

            agrupador = 'Categoria'

        self.dicionario_ligacoes_dia = df.pivot_table(
            index = pd.to_datetime(df['Hora de Início Local'].dt.strftime('%D')).dt.date,
            values = 'Call ID',
            aggfunc= lambda x: len(x.unique())).to_dict()['Call ID']
        
        #Função que tranforma a quantidade de Ligações com aquela categoria em % de ligações do dia
        def normalizar_por_per_ligacoes(df):
            return df.apply(lambda linha: (linha / self.dicionario_ligacoes_dia.get(linha.name.date())) * 100,axis=1)

        #Função que tranforma a quantidade de Ligações com aquela categoria em % derepresentatividade
        def normalizar_por_dia(df):
            return df.apply(lambda linha: (linha / linha.sum()) * 100, axis=1)
        
        #Cria um dataFrame com a quantidade unica de call ID por dia por categoria.
        ligacoes_categorias_dia = df.pivot_table(index = [pd.to_datetime(df['Hora de Início Local'].dt.strftime('%D')),agrupador ],
                values = 'Call ID',
                aggfunc= lambda x: len(x.unique())).reset_index().pivot(index='Hora de Início Local', columns = agrupador, values = 'Call ID' )
        
        ligacoes_categorias_dia.columns.name = None

        if retorno == "Representatividade dia":

            ligacoes_categorias_dia_norm = normalizar_por_dia(ligacoes_categorias_dia.fillna(0))
        else:
            ligacoes_categorias_dia_norm = normalizar_por_per_ligacoes(ligacoes_categorias_dia.fillna(0))

        return ligacoes_categorias_dia_norm
    
    def speech_consolidado(self):
        """Função que consolida todo o histórico do speech e retorna um data frame"""

        Mes_atual = dados_speech(projeto=self.projeto).consolidar_bases_speech(self.caminho)

        temp = pd.DataFrame()

        for planilha in [ x for x in os.listdir(self.caminho_historico) if '.parquet' in x]:
            print(f'Lendo a planilha: {planilha}')
            temp = pd.concat([temp, pd.read_parquet(os.path.join(self.caminho_historico, planilha))]).drop_duplicates()
            print(temp.shape)

        return pd.concat([temp,Mes_atual]).reset_index(drop=True)

    def Consolida_historico_speech(self):

        """Fanção que consolida o histórico de extrações do speech e salva-o na pasta."""

        #lendo todas as planilhas de bkp (Código aponta para a pasta de bkp)
        caminho_bkp = self.caminho.replace('\\Speech_mes\\','\\Speech_mes\\bkp\\')

        #consolida o que está na pasta de bkp
        #df = self.consolidar_bases_speech(pasta=caminho_bkp)

        #Consolida o que está na pasta de mês atual
        #Mes_atual = dados_speech(projeto=self.projeto).consolidar_bases_speech(self.caminho)

        #consolida o que está no hitórico com o que está na pasta mês atual
        df_consolidado = dados_speech(projeto=self.projeto).consolidar_bases_speech(self.caminho)

        for x in os.listdir(self.caminho):

            funcoes_globais().mover_arquivo(rf'{self.caminho}\{x}',rf'{caminho_bkp}\{x}')

        #df_consolidado = pd.concat([df,Mes_atual]).reset_index(drop=True)

        #Salva o que está na pasta do mês atual na pasta de bkp
        
        # Salva o arquivo consolidado no repositório speech
        arquivo = f"Dados_speech_limiar_{str(df_consolidado['Hora de Início Local'].max()).split(' ')[0]}.parquet"
        caminho_consolidado = fr"{self.caminho_historico}\{arquivo}"

        return df_consolidado.to_parquet(caminho_consolidado)

    def Rankin_variacao(self,df = None,Fator_temporal = 'M', agrupador = 'Etapa da Jornada' ,Hiper_categoria = 'EU USO',n_ranking = 10, ordem = False, retorno = "Representatividade dia"):

        """Ranking de variações das categorias de ligações por hiper categoria \n
        
        args** df: Dataframe do speech \n Fator_temporal: Tipo de variação temporal (M = Mês, W = Semana, Y = Ano)\n Agrupador: Hiper categoria agrupadora da variaçao\n Hiper categoria: Categoria do agrupador para ser usada\n n_ranking: quantidade de linhas retorndas no ranking\n ordem: True para mostrar as variações negativas, False para mostrar as positivas\nju """

        if df is None:

            df = dados_speech(projeto=self.projeto).speech_consolidado()

        dicionario_hiper_categoria = df[['Categoria',agrupador]].drop_duplicates().set_index('Categoria').to_dict()[agrupador]

        df_serie_temporal = dados_speech().pipe_ligacoes_dia(df,retorno=retorno)

        # Ajustando a série temporal para retornar apenas os dados da data maxima da comparação.
        df_serie_temporal = df_serie_temporal.reset_index().loc[df_serie_temporal.reset_index()['Hora de Início Local'].dt.day <= df_serie_temporal.reset_index()['Hora de Início Local'].max().day].set_index('Hora de Início Local')

        #df_serie_temporal = df_serie_temporal.reset_index().loc[df_serie_temporal.reset_index()['Hora de Início Local'].dt.day <= df_serie_temporal.reset_index()['Hora de Início Local'].max().day].set_index('Hora de Início Local')

        df_serie_temporal_variacao = (df_serie_temporal.resample(Fator_temporal).apply(lambda x: x[x != 0].mean()).pct_change() * 100).reset_index().melt(id_vars = 'Hora de Início Local', var_name = 'Categoria', value_name = 'Variação mês atual')

        df_serie_temporal_variacao_ranking = df_serie_temporal_variacao.loc[df_serie_temporal_variacao.groupby(['Categoria'])['Hora de Início Local'].idxmax()]

        ranking = df_serie_temporal_variacao_ranking[\
        (df_serie_temporal_variacao_ranking.Categoria.map(dicionario_hiper_categoria) == Hiper_categoria) & \
        (~df_serie_temporal_variacao_ranking['Variação mês atual'].isnull()) &\
        (~np.isinf(df_serie_temporal_variacao_ranking['Variação mês atual']))\
        ].sort_values('Variação mês atual', ascending = ordem).head(n_ranking)

        #Retornando os ultimos dois meses de variação.
        ultimos2meses = df_serie_temporal_variacao.pivot_table(index = 'Categoria',
                                              values = 'Variação mês atual',
                                              columns = 'Hora de Início Local'
                                              ).iloc[:,-3:-1]
        
        ultimos2meses.rename(columns = {ultimos2meses.columns[0]: f'Variação mês {ultimos2meses.columns[0].strftime("%m.%Y")}',
                                        ultimos2meses.columns[1]: f'Variação mês {ultimos2meses.columns[1].strftime("%m.%Y")}'}, inplace = True)
        
        return ranking.merge(ultimos2meses, left_on='Categoria', right_index=True, how='left') 
    #Formata os verbatins colocando-o em seqência
    def formatar_verbatins(self,texto):
        partes = texto.split("\n")
        return " - ".join([f"{i+1}° {parte}" for i, parte in enumerate(partes)])
    
    def Per_ligacoes(self,df):
        Per_ligacoes_categoria = (
            df.pivot_table(
                index=['Categoria','Nomenclatura para apresentação','Exemplo de verbalização'],
                columns = df['Hora de Início Local'].dt.strftime('%m/%y'),
                values = 'Call ID', 
                aggfunc = lambda x: len(x.unique())).reset_index().set_index('Categoria')
        )

        De_para_mes = {Per_ligacoes_categoria.columns[-1]: f'Ligações transcritas no mês {Per_ligacoes_categoria.columns[-1]}'}

        Per_ligacoes_categoria[Per_ligacoes_categoria.columns[-1]] = Per_ligacoes_categoria[Per_ligacoes_categoria.columns[-1]].map(lambda x: f"{x:.0f}" )

        Per_ligacoes_categoria['Exemplo de verbalização'] = Per_ligacoes_categoria['Exemplo de verbalização'].apply(self.formatar_verbatins)
        
        return Per_ligacoes_categoria.rename(columns = De_para_mes)

    def resumo_jornada(self,df = None,jornada = "EU USO",retorno = "%",n_ranking = 10):

        """
        Tranforma o Dataframe do speech em uma tabela de jornada 

        args:
            df: Data Frame do speech
            jornada: Jornada da análise
            retorno: Formato de análise, representatividade dia por padrão.
        """

        if df is None:

            df = dados_speech(projeto=self.projeto).speech_consolidado()

        #    mesees = [df['Hora de Início Local'].dt.month.max(), 12 if df['Hora de Início Local'].dt.month.max() == 1 else df['Hora de Início Local'].dt.month.max() - 1]

        #Encontra o mês maximo da tabela
        mesees = [df['Hora de Início Local'].max().strftime("%m/%y")]
        
        #Filtra o data frame para contar a quantidade de ligações no mês
        df_mes = df[df['Hora de Início Local'].dt.strftime("%m/%y").isin(mesees)]
    
        # [['Nomenclatura para apresentação','Exemplo de verbalização','Variação mês atual']]
    
        #Calcula a quantidade de ligações por dia e me retorna as colunas que vou usar na tabela de jornada
        def Per_ligacoes(df):
            Per_ligacoes_categoria = (
                df.pivot_table(
                    index=['Categoria','Nomenclatura para apresentação','Exemplo de verbalização'],
                    columns = df['Hora de Início Local'].dt.strftime('%m/%y'),
                    values = 'Call ID', 
                    aggfunc = lambda x: len(x.unique())).reset_index().set_index('Categoria')
            )
    
            De_para_mes = {Per_ligacoes_categoria.columns[-1]: f'Ligações transcritas no mês {Per_ligacoes_categoria.columns[-1]}'}
    
            Per_ligacoes_categoria[Per_ligacoes_categoria.columns[-1]] = Per_ligacoes_categoria[Per_ligacoes_categoria.columns[-1]].map(lambda x: f"{x:.0f}" )

            Per_ligacoes_categoria['Exemplo de verbalização'] = Per_ligacoes_categoria['Exemplo de verbalização'].apply(self.formatar_verbatins)
            
            return Per_ligacoes_categoria.rename(columns = De_para_mes)
        
        #filtra as categorias que estão acima do 2º quartil
        Per_ligacoes_ = self.Per_ligacoes(df_mes)
        coluna = Per_ligacoes_.iloc[:,-1:].columns.values[0]
        mediana_pariodo = Per_ligacoes_[coluna].astype(int).median()
        Per_ligacoes_ = Per_ligacoes_[Per_ligacoes_[coluna].astype(int) >= mediana_pariodo]
    
        df_email = dados_speech().Rankin_variacao(df = df[df.Categoria.isin(Per_ligacoes_.reset_index()['Categoria'].unique())],
                                                  Hiper_categoria = jornada, 
                                                  retorno=retorno,
                                                  n_ranking = n_ranking
                                                  ).merge(self.Per_ligacoes(df_mes),left_on='Categoria', right_index=True, how='left')

        Nomes_atualizados = {'Nomenclatura para apresentação':'Categoria','Exemplo de verbalização':'Exemplos de verbatins'}
    
        return df_email[['Nomenclatura para apresentação',df_email.columns[-5],df_email.columns[-4],'Variação mês atual',df_email.columns[-1],'Exemplo de verbalização']].rename(columns = Nomes_atualizados)
    
    def enviar_relatorio_jornadas(self,df=None,email_destinatario='diogo.henrique@claro.com.br',n_ranking_email = 10):
        """
        Envia relatório com múltiplas jornadas
        
        Args:
            email_destinatario: E-mail do destinatário
            dataframes_jornadas: Dicionário com {nome_jornada: dataframe}
        """

        if df is None:

            df = dados_speech(projeto=self.projeto).speech_consolidado()


        dataframes_jornadas = {
        "Categorias Experiência do Cliente":self.resumo_jornada(df, "Experiência do Cliente","Per de ligacoes",n_ranking = n_ranking_email),
        "Categorias Jornada de Uso":self.resumo_jornada(df, "EU USO","Per de ligacoes",n_ranking = n_ranking_email),
        "Categorias Jornada de Compra":self.resumo_jornada(df, "EU COMPRO","Per de ligacoes",n_ranking = n_ranking_email),
        "Categorias Jornada de Pagamento":self.resumo_jornada(df, "EU PAGO","Per de ligacoes",n_ranking = n_ranking_email),
        "Categorias Jornada de Cancelamento":self.resumo_jornada(df, "EU CANCELO","Per de ligacoes",n_ranking = n_ranking_email),
        "Categorias Jornada de Alteracao":self.resumo_jornada(df, "EU MUDO","Per de ligacoes",n_ranking = n_ranking_email)
        }

        df_jornadas = pd.DataFrame()
        for x in dataframes_jornadas.keys():

            # Formatar percentuais
            temp = dataframes_jornadas.get(x).copy()

            temp['Jornada'] = x
            
            df_jornadas = pd.concat([df_jornadas,temp])
    
        data_atual = df['Hora de Início Local'].max().strftime('%d/%m/%Y')
        
        outlook = win32.Dispatch('outlook.application')
        email = outlook.CreateItem(0)
        email.To = email_destinatario
        email.Subject = f'Desvios categorias speech ({self.projeto}) - {data_atual}'
        
        # Converter DataFrames para HTML
        tabelas_html = {}
        for nome_jornada, df_email in dataframes_jornadas.items():
            # Formatar percentuais
            #if 'Percentual de ligações' in df_email.columns:
            #    df_email['Percentual de ligações'] = df_email['Percentual de ligações'].apply(lambda x: f"{x:.2f}%")
            #if 'Variação mês atual' in df_email.columns:
            #    for a in [x for x in df_email.columns if 'ariação' in x ]:
            #        df_email[a] = df_email[a].apply(lambda x: f"{x:.2f}%")
            for a in [x for x in df_email.columns if 'VARIAÇÃO' in x.upper() ]:
                    df_email[a] = df_email[a].apply(lambda x: f"{x:.2f}%")
            
            tabelas_html[nome_jornada] = df_email.to_html(index=False, border=0, escape=False)
        
        # Calcular métricas gerais
        total_ligacoes = len(df[df['Hora de Início Local'].dt.month == df['Hora de Início Local'].dt.month.max()]['Call ID'].unique()) 
        jornadas_analisadas = len(dataframes_jornadas)
        categorias_ativas = sum(len(df_email) for df_email in dataframes_jornadas.values())
        total_ligacoes_joranas_analisadas = df_jornadas[[ x for x in df_jornadas.columns if 'Ligações transcritas no mês' in x ][0]].dropna().astype(int).sum()
        resumo_variacao_jornada = df_jornadas.pivot_table(index = 'Jornada', values = 'Variação mês atual', aggfunc='mean').to_html(border=0, escape=False)

        
        email.HTMLBody = f"""
        <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 1000px; margin: 20px auto; padding: 30px; background: #f8f9fa; }}
                    .header {{ color: #2c3e50; border-bottom: 3px solid #AB0A00; padding-bottom: 10px; }}
                    .section {{ margin: 25px 0; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                    .highlight {{ color: #AB0A00; font-size: 1.2em; font-weight: bold; }}
                    table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
                    th {{ background-color: #AB0A00; color: white; padding: 12px; text-align: left; }}
                    td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
                    .signature {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; }}
                    .jornada-title {{ color: #2c3e50; border-left: 4px solid #AB0A00; padding-left: 10px; margin-top: 30px; }}
                    .metric-box {{ 
                        display: flex; 
                        justify-content: space-around; 
                        margin: 20px 0; 
                        text-align: center;
                    }}
                    .metric-item {{ 
                        background: white; 
                        padding: 15px; 
                        border-radius: 6px; 
                        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                        flex: 1;
                        margin: 0 10px;
                    }}
                    .metric-value {{ 
                        font-size: 1.8em; 
                        font-weight: bold; 
                        color: #AB0A00; 
                    }}
                    .metric-label {{ 
                        color: #7f8c8d; 
                        font-size: 0.9em; 
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h2>Top {n_ranking_email} Desvios categorias speech por jornada - {data_atual}</h2>
                    </div>
                    
                    <div class="section">
                        <p>Prezado(a),</p>
                        <p>Boa tarde.</p>
                        <p>Segue abaixo o relatório das jornadas, apresentando o percentual de ligações e suas variações por categoria.</p>
                        <p>Neste e-mail, analisamos a representatividade média das {n_ranking_email} categorias com maior aumento percentual (mês contra mês) em cada jornada.</p>
                        <p><strong>Como calculamos a variação:</strong></p>
                        <p>Para cada categoria, comparamos a representatividade média das ligações entre:</p>
                        <ul>
                            <li>Mês atual (acumulado até o dia de hoje);</li>
                            <li>Mês anterior (mesmo intervalo de dias);</li>
                            <li>Dois meses atrás (mesmo intervalo de dias).</li>
                        </ul>
                        <p><strong>Exemplo ilustrativo:</strong></p>
                        <p>Supondo que hoje seja <strong>10/03/2026</strong>:</p> 
                        <ul>
                            <li>Representatividade média da categoria “Segunda via de fatura” nos dias 1-10 de março: <strong>10%</strong>;</li>
                            <li>Nos dias 1-10 de fevereiro: <strong>15%</strong>;</li>
                            <li>Nos dias 1-10 de janeiro: <strong>12%</strong>.</li>
                        </ul>
                        <p> Sendo assim, Variação mês 02.2026 = diferença mês atual - mês anterior (15% - 12%) / resultado do mês anterior (12%) que resulta em uma majoração de 25% nesta categoria.</p>
                        <p>A partir desses valores, calculamos a variação percentual entre os períodos (M-1 e M-2). As categorias listadas são aquelas que apresentaram os maiores aumentos percentuais.</p>

                    </div>

                    <div class="section">
                        <h3>📊 Visão Geral</h3>
                        <div class="metric-box">

                            <div class="metric-item">
                                <div class="metric-value">{total_ligacoes}</div>
                                <div class="metric-label">Total de Ligações transcritas neste mês</div>
                            </div>

                            <div class="metric-item">
                                <div class="metric-value">{total_ligacoes_joranas_analisadas}</div>
                                <div class="metric-label">Total de Ligações transcritas nas categorias analisadas</div>
                            </div>
                            
                            <div class="metric-item">
                                <div class="metric-value">{categorias_ativas}</div>
                                <div class="metric-label">Categorias com majoração analisadas</div>
                            </div>

                            <div class="metric-item">
                                <div class="metric-value">{jornadas_analisadas}</div>
                                <div class="metric-label">Jornadas Analisadas</div>
                            </div>
                        </div>
                    </div>

                    {''.join([f'''
                    <div class="section">
                        <h3 class="jornada-title">{nome_jornada}</h3>
                        {tabela_html}
                    </div>
                    ''' for nome_jornada, tabela_html in tabelas_html.items()])}

                    <div class="signature">
                        <p>Atenciosamente,</p>
                        <p><strong>Diogo Oliveira</strong></p>
                        <p style="color: #7f8c8d;">(E-mail automático - favor não responder)</p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        email.Send()

        return print("Relatório de jornadas enviado com sucesso")
    
    def analise_categorias(self,base_dados, categoria,agrupador = 'Categoria'):

        """
        Realiza uma análise exploratória de séries temporais para uma categoria específica em um DataFrame.
        
        args:
            df (pd.DataFrame): DataFrame contendo os dados.
            categoria (str): Nome da coluna a ser analisada.
        """

        df = self.pipe_ligacoes_dia(base_dados,agrupador)

        # Verifica se a categoria existe no DataFrame
        if categoria not in df.columns:
            print(f"A categoria '{categoria}' não foi encontrada no DataFrame.")
            return

        # Remove valores nulos e conta os registros
        serie = df[categoria].dropna()
        print(f"Total de dias com o registro de ligações na categoria '{categoria}': {len(serie)}")
        print('---')

        # Histograma
        plt.figure(figsize=(10, 4))
        serie.hist(bins=30)
        plt.title(f'Histograma da categoria: {categoria}')
        plt.xlabel('Valor')
        plt.ylabel('Frequência')
        plt.grid(True)
        plt.show()
        print('---')

        # Série temporal
        plt.figure(figsize=(12, 4))
        df[categoria].plot()
        plt.title(f'Série Temporal da categoria: {categoria}')
        plt.xlabel('Data')
        plt.ylabel('Valor')
        plt.grid(True)
        plt.show()
        print('---')

        # Decomposição sazonal
        try:
            decomposicao = seasonal_decompose(df[categoria].asfreq('D').fillna(0), model='additive', extrapolate_trend='freq')
            decomposicao.plot()
            plt.suptitle(f'Decomposição Sazonal da categoria: {categoria}', fontsize=14)
            plt.show()
        except Exception as e:
            print(f"Erro na decomposição sazonal: {e}")

        return print('Concluído')

class Dimensoes:

    def __init__(self):

        self.pasta_dimensoes = _RAIZ_DADOS + r'Dados\Repositorio_dados\D_'

    def D_clientes(self,D_clientes = '\\D_clientes'):

        """Função que retorna todos os clientes ativos da base PME"""

        arquivo_clientes = fr'{self.pasta_dimensoes}{D_clientes}'

        clientes_ativos = pd.read_parquet(funcoes_globais().ultimo_arquivo(arquivo_clientes))

        return clientes_ativos
    
    def D_Hiper_categoria(self,categoria = '\\D_hiperCategoria.xlsx',planilha = 'Movel'):

        """Função que retorna a dimensão de categorias do speech"""

        arquivo_categoria = self.pasta_dimensoes+categoria

        df_categorias = pd.read_excel(arquivo_categoria, sheet_name=planilha, header=1, index_col='CATEGORIAS').drop(columns = 'Unnamed: 0')

        return df_categorias
    
    def Linhas_ativas_cnpj(self, linhas_ativas_caminho = None, Colunas_df = None):

        if Colunas_df is None:

            Colunas_df = [
                'NUM_CNPJ',
                'DW_NUM_NTC',
                'NUM_NTC',
                'NUM_DDD',
                'DSC_SEGMENTO',
                'DSC_TERRITORIO',
                'DSC_GRUPO_SEGMENTO',
                'DSC_SUBGRUPO_SEGMENTO',
                'COD_PLATAFORMA',
                'DSC_REGIONAL',
                'DAT_ATIVACAO'
                ]

        if linhas_ativas_caminho is None:
            linhas_ativas_caminho =  self.pasta_dimensoes + '\\Ativacoes'

        linhas_ativas = pd.read_parquet(funcoes_globais().ultimo_arquivo(linhas_ativas_caminho))

        linhas_ativas.DAT_ATIVACAO = pd.to_datetime(linhas_ativas.DAT_ATIVACAO, format='%d/%m/%y')

        linhas_ativas = linhas_ativas[Colunas_df].drop_duplicates()

        linhas_ativas['SEQ_ATIVACAO'] = linhas_ativas.groupby('NUM_CNPJ')['DAT_ATIVACAO'].rank(method = 'first', ascending= True)

        return linhas_ativas
    
    def agg_linhas_ativas_cnpj(self, df = None):

        if df == None:

            df = self.Linhas_ativas_cnpj()

        qtd_linhas_cnpj = df.pivot_table(index= 'NUM_CNPJ',
                         values = 'NUM_NTC',
                         aggfunc= lambda x: len(x.unique()))
        
        qtd_linhas_cnpj['RANGE'] = pd.cut(qtd_linhas_cnpj.NUM_NTC, bins = [0,1,2,5,10,99681], labels = ['1 Linha','2 Linhas','3 a 5 linhas','6 a 10 Linhas','Mais de 10 Linhas'])

        return qtd_linhas_cnpj
        
    def churn(self, D_clientes = '\\Churn'):
                
        """Função que retorna todos os clientes sairam da base PME"""

        arquivo_clientes = fr'{self.pasta_dimensoes}{D_clientes}'

        clientes_ativos = pd.read_parquet(funcoes_globais().ultimo_arquivo(arquivo_clientes))

        clientes_ativos = clientes_ativos.loc[clientes_ativos.groupby('NUM_CNPJ')['DAT_REFERENCIA'].idxmax()]

        clientes_ativos.IND_CNPJ_CLARO = 'NÃO'

        return clientes_ativos

    def port_out(self, caminho_portab = '\Portabilidade\Port_out' ):

        caminho = fr'{self.pasta_dimensoes}{caminho_portab}'

        arquivo = funcoes_globais().ultimo_arquivo(caminho)

        print(arquivo)

        port_out = pd.read_parquet(arquivo)

        return port_out

    def D_clientes_eng_atributos(self, df = None):

        if df == None:

            df = pd.concat( [self.D_clientes(),self.churn()] ).reset_index(drop='index')
        
        De_para_mix_servicos = {'FIXA':'FIXA',
            'FIXA + MOBILIDADE':'CONVERGENTE',
            'MOBILIDADE':'MOBILIDADE',
            'CONECTIVIDADE':'CONECTIVIDADE',
            'CONECTIVIDADE + FIXA':'FIXA',
            'CONECTIVIDADE + MOBILIDADE':'MOBILIDADE',
            'FIXA + MOBILIDADE + SOLUCOES DIGITAIS':'CONVERGENTE',
            'FIXA + SOLUCOES DIGITAIS':'FIXA',
            'CONECTIVIDADE + FIXA + MOBILIDADE':'CONVERGENTE',
            'CONECTIVIDADE + FIXA + MOBILIDADE + SOLUCOES DIGITAIS':'CONVERGENTE',
            'SOLUCOES DIGITAIS':'SOLUCOES DIGITAIS',
            'CONECTIVIDADE + MOBILIDADE + SOLUCOES DIGITAIS':'MOBILIDADE',
            'MOBILIDADE + SOLUCOES DIGITAIS':'MOBILIDADE',
            'CONECTIVIDADE + SOLUCOES DIGITAIS':'CONECTIVIDADE',
            'CONECTIVIDADE + FIXA + SOLUCOES DIGITAIS':'FIXA'}
        
        df['QTD_LISTA_SERVICOS'] = df.MIX_SERVICOS.map(lambda x: len(x.split(' + ')) )

        df['QTD_LISTA_PRODUTOS'] = df.MIX_PRODUTO.map(lambda x: len(x.split(' + ')) )

        df['TIPO_CLIENTE'] = df.MIX_SERVICOS.map(
            lambda x: De_para_mix_servicos.get(' + '.join(sorted(x.split(' + '))))
        )

        df['MIX_SERVICOS'] = df.MIX_SERVICOS.map(
            lambda x: ' + '.join(sorted(x.split(' + ')))
            )

        return df.loc[df.reset_index().groupby('NUM_CNPJ')['index'].idxmax()].reset_index(drop='index')
    
    def D_clientes_distribuicao_clientes(self, mix = False):

        d_clientes = self.D_clientes_eng_atributos()

        if mix:

            df = d_clientes.pivot_table(index='DSC_SEGMENTACAO',
                       columns = 'MIX_SERVICOS', 
                      values = 'NUM_CNPJ',
                      aggfunc= 'count').fillna(0).astype(int).reset_index()
        else: 

            df = d_clientes.pivot_table(index='DSC_SEGMENTACAO',
                       columns = 'TIPO_CLIENTE', 
                      values = 'NUM_CNPJ',
                      aggfunc= 'count').fillna(0).astype(int).reset_index()
            
        return df

class ps8:

    def __init__(self):

        self.pasta_ps8 = _RAIZ_DADOS + r'Dados\Repositorio_dados\PS8'

        self.De_para_colunas = {"MOTIVO1":"MOTIVO_CONTATO","MOTIVO3":"CATEGORIA_CONTATO","MOTIVO4":"SUB_CATEGORIA_CONTATO"}

        self.tipagem = {"CRIADO_POR":"str","FECHADO_POR":"str"}

        self.colunas = ['NIVEL',
           'TORRE',
           'DT_CRIACAO',
           'DT_CONCLUSAO',
           'NUM_NTC',
           'NUM_PROTOCOLO_ATENDIMENTO',
           'QUEM_ATENDEU',
           'MOTIVO1',
           'MOTIVO3',
           'MOTIVO4',
           'STATUS',
           'METODO_CONTATO',
           'CNPJ',
           'PORTE',
           'CRIADO_POR',
           'REGIONAL']
        
    def carrega_dados_ps8(self):

        caminho_consolidado = rf'{self.pasta_ps8}\Consolidado'

        arquiso_parquet = os.listdir(caminho_consolidado)

        df_ps8 = pd.DataFrame()

        for x in  arquiso_parquet:

            temp = pd.read_parquet(rf'{caminho_consolidado}\{x}')

            df_ps8 = pd.concat([df_ps8,temp])

        return df_ps8

    def limpeza_ps8(self, df = None):

        if df is None:
            df = self.carrega_dados_ps8()

        df.DT_CRIACAO = pd.to_datetime(df.DT_CRIACAO, format='%d/%m/%y %H:%M:%S')
        df.DT_CONCLUSAO = pd.to_datetime(df.DT_CONCLUSAO, format='%d/%m/%y %H:%M:%S')
        df['NUM_NTC'] = df.NUM_NTC.map(lambda x: str(x).split('.')[0])
        df['NUM_PROTOCOLO_ATENDIMENTO'] = df['NUM_PROTOCOLO_ATENDIMENTO'].astype(str)
        df['CNPJ'] = df['CNPJ'].astype(str)
        df['NIVEL'] = df['NIVEL'].astype('category')
        df['TORRE'] = df['TORRE'].astype('category')
        df['MOTIVO1'] = df['MOTIVO1'].astype('category')
        df['REGIONAL'] = df['REGIONAL'].astype('category')

        df = df.loc[df.CRIADO_POR.map(lambda x: len(x) == 8)]

        df_tratado = df[self.colunas].rename(columns = self.De_para_colunas).drop_duplicates()

        return df_tratado.reset_index(drop='index')
    
    def ligacoes_ps8(self):

        ps8 = self.limpeza_ps8()

        ps8 = ps8[ps8.METODO_CONTATO == 'Telefonema Recebido']

        ps8['Chave_ligacao'] = (ps8.DT_CRIACAO.astype('str') + ' - ' + ps8.NUM_NTC.astype('str'))

        ps8['sub_categora_ajustada'] = np.where(ps8["SUB_CATEGORIA_CONTATO"].eq("(Em branco)"),ps8["CATEGORIA_CONTATO"],ps8["SUB_CATEGORIA_CONTATO"])

        return ps8.reset_index(drop='index')
    
    def ps8_dias_primeira_ativacao(self):

       ps8 = self.limpeza_ps8()

       ativacoes = Dimensoes().Linhas_ativas_cnpj()

       df_primeira_ativacao_cnpj = ativacoes[ativacoes.SEQ_ATIVACAO == 1]

       atendimento_ps8_primeira_ativacao = ps8.merge(
           df_primeira_ativacao_cnpj[['NUM_CNPJ','DAT_ATIVACAO']].set_index('NUM_CNPJ'), 
           left_on='CNPJ', 
           right_index=True, 
           how='left')

       atendimento_ps8_primeira_ativacao['dif_dias'] = (atendimento_ps8_primeira_ativacao.DT_CRIACAO - atendimento_ps8_primeira_ativacao.DAT_ATIVACAO).dt.days

       return atendimento_ps8_primeira_ativacao

class qualtrics:
    
    def __init__(self):

        self.caminho_local_parte1 = _RAIZ_DADOS

        self.caminho_parte2 = r'Dados/Repositorio_dados/Qualtrics'

        self.caminho = fr'{self.caminho_local_parte1}/{self.caminho_parte2}'

    def canal_pesquisado_tratado(self,df):
        f_pesquisas = df.copy()
        cond1 = f_pesquisas['DSC_CANAL_PESQUISADO'].eq('Outage') & \
            f_pesquisas['DSC_SUB_CANAL_PESQUISADO'].isin(['App', 'Site','App_unificado'])

        cond2 = f_pesquisas['DSC_CANAL_PESQUISADO'].eq('Outage') & \
                f_pesquisas['DSC_SUB_CANAL_PESQUISADO'].eq('URA')

        f_pesquisas['canal_pesquisado_tratado'] = np.select(
            condlist=[cond1, cond2],
            choicelist=[
                f_pesquisas['DSC_CANAL_PESQUISADO'] + ' Digital',
                f_pesquisas['DSC_CANAL_PESQUISADO'] + ' URA'
            ],
            default=f_pesquisas['DSC_CANAL_PESQUISADO']
        )

        f_pesquisas['DATA_PESQUISA_AJUSTADA'] = pd.to_datetime(df.DATA_PESQUISA_AJUSTADA) 

        return f_pesquisas

    def tratar_base_nps_j1(self,df = None, jornada = 'Suporte BL' ):

        if df is None:

            df = pd.read_parquet(rf'{self.caminho}/Qualtrics_j1/J1_02_2026.parquet')

        colunas_numericas = ["NUM_NOTA_NPS",
                            "NUM_CSAT_01",
                            "NUM_CSAT_02",
                            "NUM_CSAT_03",
                            "NUM_CSAT_04",
                            "NUM_CSAT_05",
                            "NUM_CSAT_06",
                            "NUM_CSAT_07",
                            "NUM_CSAT_08"]

        df_filtrado = df[(~df.NUM_NOTA_NPS.isnull()) & (df.DSC_JORNADA_PESQUISADA == jornada) & (df.DSC_IDENTIFICACAO_QUALTRICS == 'Live') & (df.NUM_CSAT_09.isin(['PURPLE PME PF','PME']))]

        df_filtrado[colunas_numericas] = df_filtrado[colunas_numericas].apply(pd.to_numeric, errors="coerce")

        df_filtrado['Mes'] = df_filtrado.DATA_PESQUISA_AJUSTADA.dt.strftime('%m/%y')
        
        return self.canal_pesquisado_tratado(df_filtrado)

    def calcular_nps(self,df, coluna = 'NUM_NOTA_NPS'):

        #if df == None:

        #    df = self.tratar_base_nps_j1()

        # Contagem total
        total = len(df[coluna])
        
        # Contagem de promotores (9 ou 10)
        promotores = df[df[coluna].between(9, 10)].shape[0]
        
        # Contagem de detratores (0 a 6)
        detratores = df[df[coluna].between(0, 6)].shape[0]
        
        # Fórmula do NPS
        nps = ((promotores - detratores) / total) * 100
        return round(nps, 2)
    
    def calcula_taxa_resolutividade(self,df, coluna = 'IND_RESOLUCAO_PROBLEMA'):

        taxa_resolucao = df[coluna].value_counts(normalize = True)[[ x for x in df.IND_RESOLUCAO_PROBLEMA.unique() if 'SIM' in str(x).upper()]].sum()

        return round(taxa_resolucao, 4)
    
    def calcula_ces(self,df, coluna = 'DSC_DRIVER_CES'):

        dic_ces_num = {'Muito fácil':5,'Fácil':4 , 'Nem difícil, nem fácil':3 , 'Difícil':2, 'Muito difícil':1}

        ces_jornada = df[coluna].map(dic_ces_num).mean()

        #ces_jornada = dac.dropna(subset = coluna)[coluna].map(dic_ces_num).mean()

        return round(ces_jornada, 2)
    
    def distribuicao_tnps(self,df):

        return round(pd.cut(df.NUM_NOTA_NPS, bins = [-1,6,8,10], labels = ['Detrator','Neutro','Promotor']).value_counts(normalize = True),2)*100
    
    def aceita_contato(self,df): 

        return round(df.IND_SOBRE_OPT_IN.map({'Sim':1,'Não':0}).fillna(0).mean(),2)*100

class portabilidade:

    def __init__(self, caminho_conflitos=None):

        self.caminho_local_parte1 = _RAIZ_DADOS

        self.caminho_parte2 = r'Dados\Repositorio_dados\Portabilidade'

        # Pasta de conflitos de portabilidade (Teams/SharePoint). Passe o caminho da sua máquina.
        self.caminho = caminho_conflitos or r'C:\Users\f115523\Claro SA\USER-Operações PME - Conflitos Portabilidade'

    def portabilidade_consolidada(self, ano = None, mes = None):
        
        """
        Docstring for portabilidade_consolidada: 
        Função que consolida o histórico de todas as extrações feitas de portabilidade. 
        
        :param ano: nome da pasta que vamos consolidar
        :param mes: mês que vamos consolidar.
        """

        colunas = ['CNPJ_CLIENTE', 'RAZAO_SOCIAL', 'UF_CLIENTE', 'REGIONAL', 'SEGMENTO',
        'COD_AACE', 'NOME_AACE', 'LOGIN_GERENTE_DA_CONTA',
        'NOME_GERENTE_DA_CONTA', 'DATA_COTACAO', 'ID_COTACAO',
        'MSISDN ', 'Bilhete EA', 'STATUS_PORTABILIDADE_EA',
        'COD_MOTIVO_RECUSA', 'DATA_BILHETE_EA',
        'DATA_INICIO_JANELA', 'DATA_FIM_JANELA',
        'COD_MOTIVO_REJEICAO','BILHETE_AGRUPADOR_EA', 'REGIONAL - SIGLA',
        'STATUS V2','RECUSA V2','CANAL DE VENDA','REASON']

        if ano is None:
            ano = dt.datetime.today().year

        if mes is None:
            mes = dt.datetime.today().strftime("%m.%Y")

        caminho = rf"{self.caminho}\{ano}\{mes}"

        caminho_salvamento = rf"{self.caminho}\log\historico_portabilidade_mes_{mes}.parquet"

        log_portabiliadde = pd.DataFrame()


        for x in [ a for a in os.listdir(rf'{caminho}') if 'xlsx' in a ]:

            temp = pd.read_excel(rf'{caminho}\{x}', sheet_name='BASE PORT IW')

            temp['Nome do arquivo'] = x
        
            print(f"lendo {x}")
        
            log_portabiliadde = pd.concat([log_portabiliadde,temp]).drop_duplicates()
        
            print(log_portabiliadde.shape)

        log_portabiliadde = log_portabiliadde[colunas].drop_duplicates().reset_index(drop = 'index')

        log_portabiliadde["RAZAO_SOCIAL"] = log_portabiliadde["RAZAO_SOCIAL"].astype(str)

                    
        return log_portabiliadde.to_parquet(caminho_salvamento)

    def pipe_log(self, df = None):

        """
        Docstring for pipe_log:
        Função que trata a base de portabilidades consolidadas e faz o tratamento da base unificada.
        
        :param df: Base com as portabilidades consolidadas.
        """

        correcoes_status = {
            'CNuloPJS DIFERENuloTES':'CNPJS DIFERENTES',
            'CPFS DIFERENuloTES':'CPFS DIFERENTES',
            'ASSINuloANuloTE NuloÃO ENuloCONuloTRADO OU CANuloCELADO':'ASSINANTE NÃO ENCONTRADO OU CANCELADO',
            'TIPO CLIENuloTE DIFERENuloTE':'TIPO CLIENTE DIFERENTE',
            'REJEICAO ESTORNuloO POR FRAUDE':'REJEICAO ESTORNO POR FRAUDE',
            'SEM RESPOSTA DE SMS':'SEM RESPOSTA DE SMS',
            'CNPJS DIFERENTES':'CNPJS DIFERENTES',
            'ASSINANTE NÃO ENCONTRADO OU CANCELADO':'ASSINANTE NÃO ENCONTRADO OU CANCELADO',
            'TIPO CLIENTE DIFERENTE':'TIPO CLIENTE DIFERENTE',
            'REJEICAO ESTORNO POR FRAUDE':'REJEICAO ESTORNO POR FRAUDE',
            'ASSINANTE NÃO ENCONTRADO OU CANCELADO':'ASSINANTE NÃO ENCONTRADO OU CANCELADO',
            'N':'SEM CONFLITO',
            'Nulo':'SEM CONFLITO',
            None:'SEM CONFLITO',
            np.nan:'SEM CONFLITO',
            'CPFS DIFERENTES':'CPFS DIFERENTES',
            'Sem resposta de SMS':'SEM RESPOSTA DE SMS',
            'REJEITADO':'REJEITADO',
            'Resposta negativa SMS':'RESPOSTA NEGATIVA SMS',
            'ASSINANTE NÃO ENCONTRADO OU CANCELADO':'ASSINANTE NÃO ENCONTRADO OU CANCELADO',
            'FALHA SISTÊMICA':'FALHA SISTÊMICA'}
        
        dE_PARA_CANCELADOS = { x:'CANCELADO' for x in df['STATUS_PORTABILIDADE_EA'].unique() if 'cancela' in x}
        dE_PARA_REJEITADOS = { x:'REJEITADO' for x in df['STATUS_PORTABILIDADE_EA'].unique() if 'rejeitad' in x }
        dE_PARA_FALHA = { x:'Falha' for x in df['STATUS_PORTABILIDADE_EA'].unique() if 'falha' in x }
        dE_PARA_SUSPENSO = { x:'Suspenso' for x in df['STATUS_PORTABILIDADE_EA'].unique() if 'suspenso' in x }
        dE_PARA_STATUS = {
            **dE_PARA_CANCELADOS,
            **dE_PARA_REJEITADOS,
            **dE_PARA_FALHA,
            **dE_PARA_SUSPENSO}
        
        df['COD_MOTIVO_RECUSA'] = df.apply(lambda x: x['RECUSA V2'] if x['COD_MOTIVO_RECUSA'] in ['Nulo','N'] else x['COD_MOTIVO_RECUSA'] , axis = 1)

        #corrigindo_status
        #Converter não-escalares (list/dict/ndarray) para NaN, para não quebrar o map
        is_scalar = df['COD_MOTIVO_RECUSA'].map(pd.api.types.is_scalar)
        df.loc[~is_scalar, 'COD_MOTIVO_RECUSA'] = np.nan

        
        #Normalizar: manter NaN, padronizar strings
        s = df['COD_MOTIVO_RECUSA']
        s = s.where(s.isna(), s.astype(str).str.strip())

        df['COD_MOTIVO_RECUSA'] = s.replace(correcoes_status).fillna('SEM CONFLITO')

        df['CNPJ_CLIENTE'] = df.CNPJ_CLIENTE.map(lambda x: int(''.join(ch for ch in str(x) if ch.isdigit())))

        df['Chave'] = df.CNPJ_CLIENTE.astype('str') + " - " + df['MSISDN '].map(lambda x: str(x).split('.')[0])

        log_2025 = df[['CNPJ_CLIENTE','MSISDN ','Bilhete EA','Chave','COD_MOTIVO_RECUSA']].drop_duplicates()

        log_2025['Ranking'] = log_2025.groupby('Chave')['Bilhete EA'].rank(method='first')

        #Colunas do log:
        quantidade_bilhetes_chave = log_2025.pivot_table(index = 'Chave',
                    values = 'Bilhete EA',
                    aggfunc= lambda x: len(x.unique())).rename(columns = {'Bilhete EA':'Quantidade_bilhetes'})
        
        quantidade_motivos = log_2025.pivot_table(index = 'Chave',
                    values = 'COD_MOTIVO_RECUSA',
                    aggfunc= lambda x: len(x.unique())).rename(columns = {'COD_MOTIVO_RECUSA':'Quantidade_status'})
        
        Lista_motivos = log_2025.pivot_table(index = 'Chave',
                    values = 'COD_MOTIVO_RECUSA',
                    aggfunc= lambda x: list(pd.unique(pd.Series(x).dropna()))
                    ).rename(columns={'COD_MOTIVO_RECUSA': 'Hist_status'})

        
        Lista_status = df.pivot_table(index = 'Bilhete EA',
                    values = 'STATUS_PORTABILIDADE_EA',
                    aggfunc = lambda x: list(pd.unique(pd.Series(x).dropna()))).rename(columns={'STATUS_PORTABILIDADE_EA': 'Hist_status_EA'})

        
        df['STATUS V2'] = df['STATUS V2'].fillna(df['STATUS_PORTABILIDADE_EA'].map(dE_PARA_CANCELADOS))

        lista_status_linha = df.sort_values('STATUS V2', ascending=False)[~df['STATUS V2'].isnull()].pivot_table(index = 'Chave',
                    values = 'STATUS V2',
                    aggfunc= lambda x: list(pd.unique(pd.Series(x).dropna()))).rename(columns = {'STATUS V2':'Hist_status_linha'})
        
        log_2025 = log_2025.merge(quantidade_bilhetes_chave, left_on='Chave', right_index=True, how = 'left'
              ).merge(quantidade_motivos, left_on='Chave', right_index=True, how = 'left'
                     ).merge(Lista_motivos, left_on='Chave', right_index=True, how = 'left'
                            ).merge(Lista_status, left_on='Bilhete EA', right_index=True, how = 'left'
                                    ).merge(lista_status_linha, left_on='Chave', right_index=True, how = 'left'
                                           )
        
        return log_2025

    def historico_bilhetes(self,caminho = None):

        if caminho is None:

            caminho = self.caminho

        df = pd.DataFrame()

        for x in [a for a in os.listdir(rf'{caminho}\log') if '.parquet' in a ]:

            temp = pd.read_parquet(rf"{caminho}\log\{x}")

            print(f'lendo a planilha {x}')

            df = pd.concat([df,temp])

        return df.reset_index(drop='index')

    def carregar_log(self,caminho = None,ano = None, mes = None):

        """
        Docstring for carregar_log:
        Função que carrega log de portabilidade consolidada na pasta log e passa pela função pipe_log para tratamento.
        
        :param caminho: Caminho da pasta consolidada, se NONE ela pega a pasta configurada no construtor.
        :param ano: Ano da consolidação
        :param mes: mês da consolidação
        """

        if caminho is None:

            caminho = self.caminho

        self.portabilidade_consolidada(ano = ano, mes = mes)

        df = self.historico_bilhetes()

        return self.pipe_log(df.reset_index(drop='index'))

    def pipe_portabilidade_hist(self,df,log_portabiliadde_ = None, columns = None,ano = None, mes = None):
        """
        Docstring for pipe_portabilidade_hist:
        Função que retorna as variaveis enriquecedoras da base consolidada no log de portabilidade.
        
    
        :param df: Base atual que vamos enriquecer
        :param log_portabiliadde_: Log consolidado com as variaveis enriquecida, se none chama o método carregar log
        :param columns: Colunas que deseja retornar da base atual
        :param ano: Ano da consolidação do log
        :param mes: mês da consolidação do log
        """
        if columns is None:
            columns = [
                'CNPJ_CLIENTE',
                'REGIONAL - SIGLA',
                'NOME_AACE',
                'COD_AACE',
                'ID_COTACAO',
                'MSISDN ',
                'Bilhete EA',
                'STATUS_PORTABILIDADE_EA',
                'COD_MOTIVO_RECUSA',
                'DATA_BILHETE_EA',
                'DATA_INICIO_JANELA',
                'BILHETE_AGRUPADOR_EA',
                'STATUS V2',
                'RECUSA V2',
                'CANAL DE VENDA',   
                'REASON'
                ]

        df = df[columns].drop_duplicates()

        if log_portabiliadde_ is None:

            log_portabiliadde_ = self.carregar_log(ano = ano, mes = mes)

        Bilhetes_com_conflito = log_portabiliadde_[log_portabiliadde_['COD_MOTIVO_RECUSA']!='SEM CONFLITO'].drop_duplicates('Bilhete EA').set_index('Bilhete EA')

        df = df.merge(Bilhetes_com_conflito.rename(columns = {'COD_MOTIVO_RECUSA':'COD_MOTIVO_RECUSA_HISTORICO'})[
            ['COD_MOTIVO_RECUSA_HISTORICO',
             'Quantidade_bilhetes',
             'Quantidade_status',
             'Hist_status',
             'Hist_status_EA',
             'Hist_status_linha',
             'Ranking']], left_on='Bilhete EA', right_index=True, how = 'left')

        de_para_motivo_recusa = {'N':'Sem conflito',
                                 'SEM RESPOSTA DE SMS':'Com conflito',
                                 'CNPJS DIFERENTES':'Com conflito',
                                 'CPFS DIFERENTES':'Com conflito',
                                 'ASSINANTE NÃO ENCONTRADO OU CANCELADO':'Com conflito',
                                 'TIPO CLIENTE DIFERENTE':'Com conflito',
                                 'REJEICAO ESTORNO POR FRAUDE':'Com conflito',
                                 "REJEITADO":"Com conflito",
                                 "FALHA SISTÊMICA":"Com conflito",
                                 "RESPOSTA NEGATIVA SMS":"Com conflito"}

        df['Satatus_agrupado'] = df.COD_MOTIVO_RECUSA.map(de_para_motivo_recusa)

        df['Satatus_agrupado_hist'] = df.COD_MOTIVO_RECUSA_HISTORICO.map(de_para_motivo_recusa)

        df['CNPJ_CLIENTE'] = df.CNPJ_CLIENTE.map(lambda x: int(''.join(ch for ch in x if ch.isdigit())))

        df['Chave'] = df.CNPJ_CLIENTE.astype('str') + " - " + df['MSISDN '].map(lambda x: str(x).split('.')[0])

        def Preenche_infos_bilhete(df,log):

            print(df.shape)

            dict_chave_Hist_status_linha = log[['Chave','Hist_status_linha']].drop_duplicates('Chave').set_index('Chave').to_dict().get('Hist_status_linha')
            dict_chave_Hist_qtd_bilhetes_linha = log[['Chave','Quantidade_bilhetes']].drop_duplicates('Chave').set_index('Chave').to_dict().get('Quantidade_bilhetes')
            dict_bilhete_ranking = log[['Bilhete EA','Ranking']].drop_duplicates('Bilhete EA').set_index('Bilhete EA').to_dict().get('Ranking')

            df['Hist_status_linha'] = df.Hist_status_linha.fillna(df.Chave.map(dict_chave_Hist_status_linha))
            df['Quantidade_bilhetes'] = df.Quantidade_bilhetes.fillna(df.Chave.map(dict_chave_Hist_qtd_bilhetes_linha))
            df['Ranking'] = df.Ranking.fillna(df['Bilhete EA'].map(dict_bilhete_ranking))

            print(df.shape)

            return df

        return Preenche_infos_bilhete(df[df['REGIONAL - SIGLA'] != 'Brasil'].reset_index(drop = 'index'),log_portabiliadde_)

    def dias_uteis(self, df, col_inicio, col_fim, feriados=None, include_end=False):
        """
        Calcula dias úteis entre col_inicio (incl.) e col_fim (excl. por padrão).
        - Exclui sábados e domingos automaticamente.
        - Aceita lista de feriados (opcional).
        - Linhas com datas inválidas (NaT) ou fim < início retornam NaN.
        - Se include_end=True, soma 1 quando o dia final for dia útil e fim >= início.

        Retorna: np.ndarray (float), alinhado ao df.index.
        """

        # 1) Converter para datetime (seguro)
        s = pd.to_datetime(df[col_inicio], errors='coerce').dt.date
        e = pd.to_datetime(df[col_fim],    errors='coerce').dt.date

        # 2) Máscara de linhas válidas
        valid = (~s.isna()) & (~e.isna()) & (e >= s)

        # 3) Pré-alocar resultado com NaN
        out = np.full(len(df), np.nan, dtype=float)

        if valid.any():
            # 4) Preparar arrays APENAS para as linhas válidas
            s_valid = s[valid].values.astype('datetime64[D]')
            e_valid = e[valid].values.astype('datetime64[D]')

            # 5) Feriados (opcional)
            hol = None
            if feriados:
                hol = pd.to_datetime(feriados, errors='coerce').dropna().values.astype('datetime64[D]')

            # 6) Calcular dias úteis somente nas linhas válidas
            base = np.busday_count(s_valid, e_valid)

            # 7) Incluir o dia final útil? (opcional)
            if include_end:
                is_end_bd = np.is_busday(e_valid)
                base = base + is_end_bd.astype(int)

            # 8) Escrever no array de saída
            out[valid.to_numpy()] = base.astype(float)

        return out

    def portabilidades_data_ativacao(self, df_linhas = None, df_portabilidade = True,ano = None, mes = None):

        """
        Docstring for portabilidades_data_ativacao:
        Função que consolida todo o processo de enriquecimento da base com as informações do log
        
        :param df_linhas: Base com a data de ativação de todos as linhas ativas por cnpj
        :param df_portabilidade: df enriquecido com as variaveis do log, se none chama o método pipe_portabilidade_hist
        :param ano: Description
        :param mes: Description
        """

        if df_portabilidade:

            ano_ = dt.datetime.today().year

            mes_ = dt.datetime.today().strftime("%m.%Y")

            caminho_ultimo_arquivo = rf"{self.caminho}\{ano_}\{mes_}"

            df_portabilidade = fr'{caminho_ultimo_arquivo}\{max(os.listdir(caminho_ultimo_arquivo), key=lambda f: os.path.getmtime(os.path.join(caminho_ultimo_arquivo, f)))}'

            df_portabilidade = pd.read_excel(df_portabilidade, sheet_name='BASE PORT IW')

        else:

            df_portabilidade = self.historico_bilhetes()

            df_portabilidade = df_portabilidade.loc[df_portabilidade.reset_index().groupby('Bilhete EA')['index'].idxmax()].reset_index(drop='index')


        df_portabilidade = self.pipe_portabilidade_hist(df_portabilidade,ano = ano, mes = mes)

        if df_linhas is None:

            df_linhas = Dimensoes().Linhas_ativas_cnpj()
        else:
            df_linhas = Dimensoes().Linhas_ativas_cnpj(linhas_ativas_caminho = df_linhas)

        df_linhas['Chave'] = df_linhas['NUM_CNPJ'].astype('str') + " - " + df_linhas['NUM_NTC'].astype('str')

        df_linhas = df_linhas[(~df_linhas.DAT_ATIVACAO.isnull())]

        df_linhas = df_linhas.loc[df_linhas.groupby('Chave')['SEQ_ATIVACAO'].idxmax()]

        data_aticao_linha = df_linhas[['Chave','DAT_ATIVACAO','DSC_SEGMENTO']].set_index('Chave')

        df_data_ativacao = df_portabilidade.merge(data_aticao_linha, left_on= 'Chave', right_index = True, how = 'left')

        
        #df_data_ativacao['Dias para ativacao'] = (df_data_ativacao.DAT_ATIVACAO.dt.date - df_data_ativacao.DATA_BILHETE_EA.dt.date).map(lambda x: np.nan if pd.isna(x) or getattr(x, 'days', -1) < 0 else x.days)
        
        #Apenas dias uteis
        df_data_ativacao['Dias para ativacao'] = self.dias_uteis(df_data_ativacao,'DATA_BILHETE_EA','DAT_ATIVACAO')

        df_data_ativacao.loc[
            df_data_ativacao['STATUS V2'].str.strip().str.upper() != 'ATIVAÇÃO',
            'Dias para ativacao'
        ] = np.nan

        return df_data_ativacao

    def distribuicao_dias_ativacao(self,df_data_ativacao, Titulo = "Sem conflito"):
    
        serie = df_data_ativacao['Dias para ativacao'].astype(float)

        mean_val   = serie.mean()
        
        median_val = serie.median()
        q1, q2, q3 = serie.quantile([0.25, 0.50, 0.75])  # q2 == mediana
        iqr        = q3 - q1

        lim_inferior = q1 - 3*iqr
        lim_superior = q3 + 3*iqr
        serie_plot = serie.clip(lower=lim_inferior, upper=lim_superior)
        #serie_plot = serie

        n = len(serie_plot)
        data_range = serie_plot.max() - serie_plot.min()
        bin_width = 2 * iqr / (n ** (1/3)) if iqr > 0 else data_range / 30
        bins = int(np.clip(np.ceil(data_range / bin_width), 10, 100))  # entre 10 e 100 bins

        
        # série já filtrada: serie_plot
        xmin = int(np.floor(serie_plot.min()))
        xmax = int(np.ceil(serie_plot.max()))
        
        plt.figure(figsize=(12, 6))
        sns.histplot(
            serie_plot,
            discrete=True,                 # trata como discreto (inteiro)
            color="#530B03",
            edgecolor="white",
            alpha=0.9,
            shrink=0.9                     # deixa as barras um pouco mais finas
        )
        
        # Linhas de referência
        plt.axvline(mean_val,   color="#FF6E00", linestyle="--", linewidth=2, label=f"Média: {mean_val:.2f}")
        plt.axvline(median_val, color="#9467BD", linestyle="--", linewidth=2, label=f"Mediana: {median_val:.2f}")
        plt.axvline(q1,         color="#31681E", linestyle="--", linewidth=2, label=f"Q1: {q1:.2f}")
        plt.axvline(q3,         color="#530B03", linestyle="--", linewidth=2, label=f"Q3: {q3:.2f}")
        
        # Mostra TODOS os inteiros no eixo X
        plt.xticks(np.arange(xmin, xmax + 1, 1))

        # Barra adicional "15+"
        count_maiores = (serie > lim_superior).sum()
        x_15plus = xmax + 1  # posição da barra extra
        plt.bar([x_15plus], [count_maiores], width=0.9, color="#000000", edgecolor="white")
        plt.text(x_15plus, count_maiores*1.02, f"{count_maiores}", ha="center", va="bottom", fontsize=10)
        
        # Ajustes visuais
        plt.title(f"Distribuição de Dias para Ativação ({Titulo})", fontsize=16, fontweight="bold")
        plt.xlabel("Dias para ativação", fontsize=14)
        plt.ylabel("Contagem", fontsize=14)
        plt.grid(True, linestyle=":", alpha=0.4)
        plt.legend(loc="upper right", fontsize=10)
        plt.tight_layout()
        plt.show()

        return print("Gráfico pronto")

    def protocolos_com_conflitos(df,linhas = 'mes'):

        """
        Docstring for protocolos_com_conflitos

        Função que mostra quantos protocolos gerados foram cancelados ou foram ativados.
        
        :param df: Data frame de portabilidade.
        :param linhas: Modelo de visualização.
        """

        if linhas in 'mes':
            linhas = df.DATA_INICIO_JANELA.dt.month
        else:
            linhas = df[linhas]

        tabela = pd.crosstab(index = linhas,
                columns = df['STATUS V2'],
                values= df['Bilhete EA'],
                aggfunc = lambda x: len(x.unique()),
    #            normalize= 'index'
            )

        return tabela

    def calc_bilhetes_conflit(df_data_ativacao):

        """
        Docstring for calc_bilhetes_conflit:

        Função que calcula quantos bilhetes tiveram conflitos e não tiveram.
        
        :param df_data_ativacao: Description
        """

        return pd.crosstab(
                index = df_data_ativacao.DATA_INICIO_JANELA.dt.month,
                columns = df_data_ativacao['Satatus_agrupado_hist'].fillna('Sem conflito'),
                values = df_data_ativacao['Bilhete EA'],
                aggfunc = lambda x: len(x.unique()),
                )

    def analise_conflitos(df,linhas,colunas,status = 'Cancelados'):

        """
        Docstring for analise_conflitos
        
        :param df: Df de portabilidade
        :param linhas: Linhas da analise
        :param colunas: Status agrupado ou tipo de conflito;
        :param status: Ativados ou cancelados, padrão cacelados
        """

        cancelados = ['Processo cancelamento efetivado EA', 'Processo cancelamento não aceito EA','Processo cancelado automaticamente']

        if status == 'Cancelados':

            df = df[df['STATUS_PORTABILIDADE_EA'].isin(cancelados)]

        else:
            df = df[df['STATUS V2'] == 'ATIVAÇÃO']
        
        return pd.crosstab(
            index=df[linhas],
            columns=df[colunas].fillna('Sem conflito'),
            normalize = 'index'
            )

    def dias_para_ativacao(df,linha,coluna):

        return pd.crosstab(
            index=df[linha],
            columns=df[coluna].fillna('SEM CONFLITO'),
            values = df['Dias para ativacao'],
            aggfunc = 'mean',
            )

    def calcular_percentual_reabertura(df, status_reabertura = 'ATIVAÇÃO',agrupamento = 'Mes'):

        """
        Docstring for calcular_percentual_reabertura
        Função que calcula o percentual de reabertura dos bilhetes cancelados.

        :param df: Data frame de portabilidade
        :param status_reabertura: Status da próxima tentativa de ativação de uma linha, padrão é Ativado
        :param agrupamento: Modelo de agrupamento, padrão é mês.
        """

        # Filtrar bilhetes que foram ativados após cancelamento
        bilhetes_reabertos = df[
        #(~df['COD_MOTIVO_RECUSA_HISTORICO'].isnull()) &
            (df.Quantidade_bilhetes > 1) &
            (df['STATUS V2'] == 'CANCELADO')
        ].loc[df['Hist_status_linha'].map(lambda x: pd.Series(x)[len(x)-1]) == status_reabertura].copy()

        print(bilhetes_reabertos.shape)

        
        # Passo 2: Contagem por mês
        bilhetes_reabertos['Mes'] = bilhetes_reabertos['DATA_INICIO_JANELA'].dt.month
        qtd_reabertos = bilhetes_reabertos.groupby(agrupamento)['Bilhete EA'].nunique().reset_index().rename(columns = {'Bilhete EA':'Reabertos'})
        
        # Passo 3: Contagem de bilhetes cancelados por mês
        bilhetes_cancelados = df[(df['STATUS V2'] == 'CANCELADO')].copy()
        bilhetes_cancelados['Mes'] = bilhetes_cancelados['DATA_INICIO_JANELA'].dt.month
        qtd_cancelados = bilhetes_cancelados.groupby(agrupamento)['Bilhete EA'].nunique().reset_index().rename(columns = {'Bilhete EA':'Cancelados'})
        
        # Passo 4: Calcular percentual
        resultado = pd.merge(qtd_cancelados, qtd_reabertos, left_on= agrupamento, right_on=agrupamento, how = 'left').fillna(0)

        
        resultado['Percentual_Reabertos'] = (resultado['Reabertos'] / resultado['Cancelados']) * 100
        
        return resultado.sort_index()

    def calcular_percentual_reabertura_conflito(df, status_reabertura = 'ATIVAÇÃO',agrupamento = 'Mes'):

        """
        Docstring for calcular_percentual_reabertura
        Função que calcula o percentual de reabertura dos bilhetes cancelados com conflito.

        :param df: Data frame de portabilidade
        :param status_reabertura: Status da próxima tentativa de ativação de uma linha, padrão é Ativado
        :param agrupamento: Modelo de agrupamento, padrão é mês.

        """

        # Filtrar bilhetes que foram ativados após cancelamento
        bilhetes_reabertos = df[
            (~df['COD_MOTIVO_RECUSA_HISTORICO'].isnull()) &
            (df.Quantidade_bilhetes > 1) &
            (df['STATUS V2'] == 'CANCELADO')
        ].loc[df[(~df.COD_MOTIVO_RECUSA_HISTORICO.isnull())]['Hist_status_linha'].map(lambda x: pd.Series(x)[len(x)-1]) == status_reabertura].copy()

        print(bilhetes_reabertos.shape)

        
        # Passo 2: Contagem por mês
        bilhetes_reabertos['Mes'] = bilhetes_reabertos['DATA_INICIO_JANELA'].dt.month
        qtd_reabertos = bilhetes_reabertos.groupby(agrupamento)['Bilhete EA'].nunique().reset_index().rename(columns = {'Bilhete EA':'Reabertos'})
        
        # Passo 3: Contagem de bilhetes cancelados por mês
        bilhetes_cancelados = df[(df['STATUS V2'] == 'CANCELADO') & (~df['COD_MOTIVO_RECUSA_HISTORICO'].isnull())].copy()
        bilhetes_cancelados['Mes'] = bilhetes_cancelados['DATA_INICIO_JANELA'].dt.month
        qtd_cancelados = bilhetes_cancelados.groupby(agrupamento)['Bilhete EA'].nunique().reset_index().rename(columns = {'Bilhete EA':'Cancelados'})
        
        # Passo 4: Calcular percentual
        resultado = pd.merge(qtd_cancelados, qtd_reabertos, left_on= agrupamento, right_on=agrupamento, how = 'left').fillna(0)

        
        resultado['Percentual_Reabertos'] = (resultado['Reabertos'] / resultado['Cancelados']) * 100
        
        return resultado.sort_index()

class churn:

    def __init__(self):

        self.df_port = Dimensoes().port_out()

        self.portabilidade_por_mes_cnpj = self.df_port.pivot_table(index='NUM_CNPJ',
                                                         columns= 'DSC_ANO_MES',
                                                         values= 'NUM_NTC',
                                                         aggfunc= 'count')

        self.colunas_meses_port_mes = self.portabilidade_por_mes_cnpj.columns

    def qtd_meses_ultima_portabilidade(self,df):

        df = df.reset_index().melt(id_vars='NUM_CNPJ').dropna()
        
        # transforma ano/mês em data
        df['DSC_ANO_MES'] = pd.to_datetime(df['variable'], format='%Y_%m')
        
        # pega o último mês com portabilidade
        ultimo_mes = (df[df['value'] > 0]
                    .groupby('NUM_CNPJ')['DSC_ANO_MES']
                    .max()
                    .reset_index()
                    .rename(columns={'DSC_ANO_MES': 'ULTIMO_MES_PORTABILIDADE'}))
        
        # Data maxima para calculo de meses da ultima portbilidade
        data_ref = df['DSC_ANO_MES'].max()
        
        # diferença em meses
        ultimo_mes['MESES_DESDE_ULTIMA_PORT'] = (
            (data_ref.year - ultimo_mes['ULTIMO_MES_PORTABILIDADE'].dt.year) * 12 +
            (data_ref.month - ultimo_mes['ULTIMO_MES_PORTABILIDADE'].dt.month)
        )
        
        return ultimo_mes.set_index('NUM_CNPJ')

    def saida_gradual_meses(self, df = None, coluna = None, normalize = False):

        if df is None:
            
            df = self.churn_port_out()

        if coluna is None:

            coluna = 'DSC_SEGMENTACAO'

        df_ = df[df.QTD_LINHAS_ATIVAS.isnull()]

        dictt = df_[coluna].value_counts(normalize = normalize).to_dict()

        df_ = (pd.crosstab(index = df_[coluna],
            values = df_['NUM_CNPJ'],
            columns = df_['FORMATO_CHURN'],
            aggfunc = lambda x: len(x.unique()),
            normalize = 'index')*100).reset_index()

        df_['Total_clientes'] = df_[coluna].map(dictt)

        return df_.set_index(coluna)
    
    def normalizar_por_dia(self,df):
    
        return df.apply(lambda linha: (linha / linha.sum()) * 100, axis=1)

    def churn_port_out(self):

        clientes_ativos_portab = Dimensoes().D_clientes_eng_atributos()[['NUM_CNPJ','IND_CNPJ_CLARO','DSC_SEGMENTACAO','MIX_SERVICOS','QTD_LISTA_SERVICOS','QTD_LISTA_PRODUTOS','TIPO_CLIENTE']].set_index('NUM_CNPJ')

        linhas_ativas = Dimensoes().agg_linhas_ativas_cnpj()
        
        # Engenharia de atributos

        qtd_meses_portab = self.portabilidade_por_mes_cnpj.reset_index().melt(id_vars = 'NUM_CNPJ').dropna().NUM_CNPJ.value_counts().to_dict()

        self.portabilidade_por_mes_cnpj['LINHAS_PORTADAS'] = self.portabilidade_por_mes_cnpj.apply(lambda x: x.sum(), axis = 1)

        #Informações sobre as linhas
        self.portabilidade_por_mes_cnpj = self.portabilidade_por_mes_cnpj.merge(linhas_ativas, left_index=True, right_index=True, how='left').rename(columns = {'NUM_NTC':'QTD_LINHAS_ATIVAS','RANGE':'CATEGORIA_LINHAS'})

        #Informações sobre os clientes
        self.portabilidade_por_mes_cnpj = self.portabilidade_por_mes_cnpj.merge(clientes_ativos_portab,left_index=True, right_index=True, how = 'left' )

        #Informações sobre as linhas
        self.portabilidade_por_mes_cnpj = self.portabilidade_por_mes_cnpj.merge(
            self.qtd_meses_ultima_portabilidade(self.portabilidade_por_mes_cnpj[self.colunas_meses_port_mes]),
            left_index=True, 
            right_index=True, 
            how = 'left')

        #informações sobre a portabilidade
        self.portabilidade_por_mes_cnpj = self.portabilidade_por_mes_cnpj.merge(
            self.df_port.pivot_table(index = 'NUM_CNPJ',
                   values = 'DSC_RECEPTORA',
                   aggfunc= lambda x: ', '.join(list(pd.unique(pd.Series(x).dropna())) ))
                   ,left_index=True, right_index=True, how = 'left' 
                )
        
        self.portabilidade_por_mes_cnpj = self.portabilidade_por_mes_cnpj.merge(
            self.df_port.pivot_table(index = 'NUM_CNPJ',
                   values = 'CANAL_PLAN',
                   aggfunc= lambda x: ', '.join(list(pd.unique(pd.Series(x).dropna()))))
                   ,left_index=True, right_index=True, how = 'left' 
                )

        self.portabilidade_por_mes_cnpj['ATIVO_MOBILIDADE'] = self.portabilidade_por_mes_cnpj.QTD_LINHAS_ATIVAS.map(lambda x: 1 if x >= 1 else 0)

        self.portabilidade_por_mes_cnpj.reset_index(inplace=True)

        self.portabilidade_por_mes_cnpj['PARCELAS_SAIDA'] = self.portabilidade_por_mes_cnpj.reset_index().NUM_CNPJ.map(qtd_meses_portab)

        self.portabilidade_por_mes_cnpj['FORMATO_CHURN'] = pd.cut(self.portabilidade_por_mes_cnpj.PARCELAS_SAIDA, bins = [0,1,10000000000], labels = ['Saida_total', 'Saida_gradual'])

        self.portabilidade_por_mes_cnpj['CATEGORIA_LINHAS_PORTADAS'] = pd.cut(self.portabilidade_por_mes_cnpj.LINHAS_PORTADAS, bins = [0,1,2,5,10,99681], labels = ['1 Linha','2 Linhas','3 a 5 linhas','6 a 10 Linhas','Mais de 10 Linhas'])

        return self.portabilidade_por_mes_cnpj.drop(columns = self.colunas_meses_port_mes)
