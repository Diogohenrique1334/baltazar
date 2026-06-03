import pandas as pd
import numpy as np

def contagem_ativos_por_dia(
    dados: pd.DataFrame,
    col_inicio: str = 'data_criacao',
    col_fim: str = 'Data_status_atual',
    inclusivo: bool = True,
    freq: str = 'D',
    retornar_dataframe: bool = True
):
    if not isinstance(dados, pd.DataFrame):
        raise TypeError(
            f"Parâmetro 'dados' deve ser um pandas.DataFrame. Recebido: {type(dados)}"
        )

    """
    Gera a série temporal de quantidade de projetos ativos por dia,
    usando o método de eventos + soma cumulativa (eficiente).

    Parâmetros
    ----------
    df : pd.DataFrame
        DataFrame com, no mínimo, as colunas de início e fim.
    col_inicio : str
        Nome da coluna de data de início (ex.: 'data_criacao').
    col_fim : str
        Nome da coluna de data de fim (ex.: 'Data_status_atual').
    inclusivo : bool
        Se True, o dia do fim é contado como ativo (default).
        Se False, conta até o dia anterior ao fim.
    freq : str
        Frequência temporal para o índice final (default 'D' para diário).
    retornar_dataframe : bool
        Se True, retorna DataFrame com colunas ['data','ativos'].
        Se False, retorna uma Series com índice datetime e nome 'ativos'.

    Retorno
    -------
    pd.DataFrame ou pd.Series
    """
    # Garantir datetime normalizados para data (sem hora)
    ini = pd.to_datetime(dados[col_inicio]).dt.normalize()
    fim = pd.to_datetime(dados[col_fim]).dt.normalize()

    # Faixa total do índice temporal
    start = ini.min()
    end = fim.max()

    # Série de eventos: +1 no início, -1 no fim (ajustado conforme inclusivo)
    eventos = {}

    if inclusivo:
        # Conta o dia do fim; portanto, removemos 1 no dia seguinte
        for s, e in zip(ini, fim):
            eventos[s] = eventos.get(s, 0) + 1
            day_after_end = e + pd.Timedelta(days=1)
            eventos[day_after_end] = eventos.get(day_after_end, 0) - 1
        # O índice final precisa ir até o máximo 'day_after_end - 1',
        # então mantemos end como fim original; o reindex por cumsum cuida disso.
        index = pd.date_range(start=start, end=end, freq=freq)
    else:
        # Não conta o dia do fim; remove 1 no próprio fim
        for s, e in zip(ini, fim):
            eventos[s] = eventos.get(s, 0) + 1
            eventos[e] = eventos.get(e, 0) - 1
        # Como tiramos no próprio dia do fim, o índice também vai até 'end'
        index = pd.date_range(start=start, end=end, freq=freq)

    # Constrói série de eventos e acumula
    eventos = pd.Series(eventos, dtype='int64').sort_index()

    # Garante todos os dias no índice
    eventos = eventos.reindex(
        pd.date_range(start=start, end=end + (pd.Timedelta(days=1) if inclusivo else pd.Timedelta(0)), freq=freq),
        fill_value=0
    )

    ativos = eventos.cumsum()

    if inclusivo:
        # Quando inclusivo, o último ponto (end+1 dia) é o retorno a zero; cortamos
        ativos = ativos.loc[start:end]

    ativos.name = 'ativos'
    ativos.index.name = 'data'

    if retornar_dataframe:
        return ativos.reset_index()
    else:
        return ativos

def Conta_dias_uteis(
        start_series: pd.Series,
        end_series: pd.Series,
        holidays=None,
        include_end: bool = False) -> pd.Series:
    
    """
    Calcula a diferença em DIAS ÚTEIS entre duas séries de datas (start e end),
    desconsiderando sábados e domingos e, opcionalmente, uma lista de feriados.

    Parâmetros
    ----------
    start_series : pd.Series
        Série com as datas de início (ex.: DATA_BILHETE_EA).
    end_series : pd.Series
        Série com as datas de fim (ex.: DAT_ATIVACAO).
    holidays : list-like | None, opcional
        Lista de feriados (strings 'YYYY-MM-DD' ou objetos de data).
        Ex.: ["2026-01-01", "2026-04-21"].
    include_end : bool, opcional (default=False)
        Se True, soma 1 quando a data final for dia útil e end >= start.

    Retorna
    -------
    pd.Series
        Série com a contagem de dias úteis (float, com NaN para casos inválidos).
        Regras de NaN:
        - Se start ou end forem inválidas (NaT) -> NaN
        - Se end < start -> NaN

    Observações
    -----------
    - Usa np.busday_count, que conta dias úteis entre start (INCLUSIVO) e end (EXCLUSIVO).
    - Se include_end=True, soma 1 quando end for dia útil e end >= start.
    """
    # 1) Normaliza para datetime
    s = pd.to_datetime(start_series, errors='coerce')
    e = pd.to_datetime(end_series,   errors='coerce')

    # 2) Converte para numpy datetime64[D] — substitui NaT por sentinela para não travar o busday_count
    _SENTINELA = np.datetime64('2000-01-01', 'D')
    mask_invalid_pre = s.isna() | e.isna()
    s_np = np.where(mask_invalid_pre, _SENTINELA, s.values.astype('datetime64[D]'))
    e_np = np.where(mask_invalid_pre, _SENTINELA, e.values.astype('datetime64[D]'))

    # 3) Prepara feriados para o numpy
    hol = []
    if holidays is not None and len(holidays) > 0:
        hol = np.array(pd.to_datetime(holidays, errors='coerce').dropna().values, dtype='datetime64[D]')

    # 4) Conta dias úteis (s incluído, e excluído)
    base = np.busday_count(s_np, e_np, holidays=hol)

    # 5) Ajuste opcional para incluir o dia final, se útil
    if include_end:
        is_end_bd = np.is_busday(e_np, holidays=hol)
        base = base + (is_end_bd & (e_np >= s_np)).astype(int)

    # 6) Converte para Series e aplica máscaras de validade
    out = pd.Series(base, index=start_series.index, dtype='float')
    mask_invalid = mask_invalid_pre | (e_np < s_np)
    out = out.mask(mask_invalid, other=np.nan)

    return out