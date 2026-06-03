import matplotlib
matplotlib.use('Agg')  # evita janelas de plot durante os testes

import sys
import os
import pytest
import numpy as np
import pandas as pd

# Garante que a raiz do projeto está no path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# ---------------------------------------------------------------------------
# ML.preparacao_dados
# ---------------------------------------------------------------------------
from ML.preparacao_dados import trata_valores_ausentes, verifica_outliers


class TestTrataValoresAusentes:

    def test_preenche_com_mediana_quando_assimetria_alta(self, capsys):
        # Distribuição muito assimétrica (skew > 1): deve usar mediana
        df = pd.DataFrame({'x': [1, 1, 1, 1, 100, np.nan]})
        trata_valores_ausentes(df)
        assert df['x'].isna().sum() == 0
        # Mediana de [1,1,1,1,100] = 1.0
        assert df['x'].iloc[-1] == pytest.approx(1.0)

    def test_preenche_com_media_quando_assimetria_moderada(self, capsys):
        # Distribuição moderadamente assimétrica (0.5 < skew < 1)
        df = pd.DataFrame({'x': [1.0, 2.0, 3.0, 4.0, 6.0, np.nan]})
        skew_antes = df['x'].skew()
        assert 0.5 < skew_antes < 1.0, "fixture esperava assimetria moderada"
        media_esperada = df['x'].mean()
        trata_valores_ausentes(df)
        assert df['x'].isna().sum() == 0
        assert df['x'].iloc[-1] == pytest.approx(media_esperada)

    def test_sem_nans_nao_altera_dataframe(self, capsys):
        df = pd.DataFrame({'x': [1.0, 2.0, 3.0]})
        df_original = df.copy()
        trata_valores_ausentes(df)
        pd.testing.assert_frame_equal(df, df_original)


class TestVerificaOutliers:

    def test_retorna_apenas_outliers(self):
        # IQR não-nulo: Q1=2, Q3=4, IQR=2 → bounds [-1, 7] → 100 é o único outlier
        df = pd.DataFrame({'x': [1.0, 2.0, 3.0, 4.0, 5.0, 100.0]})
        resultado = verifica_outliers(df)
        assert len(resultado) == 1
        assert resultado['x'].iloc[0] == 100.0

    def test_sem_outliers_retorna_vazio(self):
        df = pd.DataFrame({'x': [1.0, 2.0, 3.0, 4.0, 5.0]})
        resultado = verifica_outliers(df)
        assert len(resultado) == 0

    def test_distancia_customizada(self):
        # Com distância = 0.1 (muito restrita), valores moderados já são outlier
        df = pd.DataFrame({'x': [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]})
        resultado_restrito = verifica_outliers(df, distancia_media=0.1)
        resultado_padrao = verifica_outliers(df, distancia_media=1.5)
        assert len(resultado_restrito) >= len(resultado_padrao)


# ---------------------------------------------------------------------------
# funcoes_data_frames.transformacoes
# ---------------------------------------------------------------------------
from funcoes_data_frames.transformacoes import colunas_por_delimitadores, reduz_categorias


class TestColunasporDelimitadores:

    def test_expande_valores_separados_por_ponto_virgula(self):
        df = pd.DataFrame({
            'id':  [1, 2],
            'tags': ['A;B;C', 'X;Y']
        })
        resultado = colunas_por_delimitadores(df, coluna='tags', delimitador=';')
        # Cada combinação id x tag deve virar uma linha com 'value' preenchido
        valores = resultado['value'].tolist()
        assert 'A' in valores
        assert 'B' in valores
        assert 'C' in valores
        assert 'X' in valores
        assert 'Y' in valores

    def test_sem_delimitador_mantem_valor_original(self):
        df = pd.DataFrame({'id': [1], 'cat': ['UNICO']})
        resultado = colunas_por_delimitadores(df, coluna='cat', delimitador=';')
        assert 'UNICO' in resultado['value'].tolist()


class TestReduzCategorias:

    def test_mapeia_pequenas_categorias_para_other(self):
        contagens = pd.Series({'A': 500, 'B': 300, 'C': 10})
        mapa = reduz_categorias(contagens, cutoff=50)
        assert mapa['A'] == 'A'
        assert mapa['B'] == 'B'
        assert mapa['C'] == 'Other'

    def test_todas_acima_do_cutoff_mantem_original(self):
        contagens = pd.Series({'A': 100, 'B': 200})
        mapa = reduz_categorias(contagens, cutoff=50)
        assert mapa == {'A': 'A', 'B': 'B'}

    def test_todas_abaixo_do_cutoff_viram_other(self):
        contagens = pd.Series({'A': 5, 'B': 3})
        mapa = reduz_categorias(contagens, cutoff=10)
        assert all(v == 'Other' for v in mapa.values())


# ---------------------------------------------------------------------------
# ML.supervisionado.series_temporais.transformacoes_temporais
# ---------------------------------------------------------------------------
from ML.supervisionado.series_temporais.transformacoes_temporais import (
    contagem_ativos_por_dia,
    Conta_dias_uteis,
)


class TestContagemAtivosPorDia:

    def _make_df(self, starts, ends):
        return pd.DataFrame({
            'inicio': pd.to_datetime(starts),
            'fim':    pd.to_datetime(ends),
        })

    def test_um_ativo_por_dois_dias(self):
        df = self._make_df(['2024-01-01'], ['2024-01-02'])
        resultado = contagem_ativos_por_dia(df, col_inicio='inicio', col_fim='fim')
        assert set(resultado.columns) == {'data', 'ativos'}
        assert resultado['ativos'].max() == 1
        assert len(resultado) == 2  # 01 e 02

    def test_dois_ativos_sobrepostos(self):
        df = self._make_df(
            ['2024-01-01', '2024-01-01'],
            ['2024-01-03', '2024-01-02']
        )
        resultado = contagem_ativos_por_dia(df, col_inicio='inicio', col_fim='fim')
        # Em 2024-01-01, ambos estão ativos
        ativos_01 = resultado.loc[resultado['data'] == '2024-01-01', 'ativos'].values[0]
        assert ativos_01 == 2

    def test_type_error_quando_nao_dataframe(self):
        with pytest.raises(TypeError):
            contagem_ativos_por_dia([1, 2, 3])

    def test_retornar_series_quando_flag_false(self):
        df = self._make_df(['2024-01-01'], ['2024-01-01'])
        resultado = contagem_ativos_por_dia(df, col_inicio='inicio', col_fim='fim', retornar_dataframe=False)
        assert isinstance(resultado, pd.Series)


class TestContaDiasUteis:

    def test_contagem_simples_sem_feriados(self):
        starts = pd.Series(pd.to_datetime(['2024-01-01']))  # segunda-feira
        ends   = pd.Series(pd.to_datetime(['2024-01-06']))  # sábado
        # busday_count: 01 (seg) até 06 (sab) exclusivo = 5 dias úteis (seg-sex)
        resultado = Conta_dias_uteis(starts, ends)
        assert resultado.iloc[0] == 5

    def test_nan_quando_end_antes_de_start(self):
        starts = pd.Series(pd.to_datetime(['2024-01-10']))
        ends   = pd.Series(pd.to_datetime(['2024-01-05']))
        resultado = Conta_dias_uteis(starts, ends)
        assert pd.isna(resultado.iloc[0])

    def test_nan_quando_start_invalido(self):
        starts = pd.Series([pd.NaT])
        ends   = pd.Series(pd.to_datetime(['2024-01-10']))
        resultado = Conta_dias_uteis(starts, ends)
        assert pd.isna(resultado.iloc[0])

    def test_com_feriado(self):
        # 01/01 é segunda; sem feriados: 01→05 = 4 dias úteis
        # com feriado em 02/01: 3 dias úteis
        starts = pd.Series(pd.to_datetime(['2024-01-01']))
        ends   = pd.Series(pd.to_datetime(['2024-01-05']))
        sem_feriado = Conta_dias_uteis(starts, ends)
        com_feriado = Conta_dias_uteis(starts, ends, holidays=['2024-01-02'])
        assert com_feriado.iloc[0] == sem_feriado.iloc[0] - 1


# ---------------------------------------------------------------------------
# ML.supervisionado.regressao_logistica — métricas
# ---------------------------------------------------------------------------
from ML.supervisionado.regressao_logistica.avaliacoes_RLG.metricas_modelo import (
    calc_specificity,
    relatorio_metricas,
)


class TestCalcSpecificity:

    def test_todos_negativos_corretos(self):
        y_actual = np.array([0, 0, 0])
        y_pred   = np.array([0.1, 0.2, 0.3])
        assert calc_specificity(y_actual, y_pred, thresh=0.5) == pytest.approx(1.0)

    def test_nenhum_negativo_correto(self):
        y_actual = np.array([0, 0, 0])
        y_pred   = np.array([0.9, 0.8, 0.7])
        assert calc_specificity(y_actual, y_pred, thresh=0.5) == pytest.approx(0.0)


class TestRelatorioMetricas:

    def test_retorna_cinco_metricas(self, capsys):
        y_actual = np.array([0, 0, 1, 1])
        y_pred   = np.array([0.1, 0.4, 0.6, 0.9])
        resultado = relatorio_metricas(y_actual, y_pred, thresh=0.5)
        assert len(resultado) == 5

    def test_auc_perfeito(self, capsys):
        y_actual = np.array([0, 0, 1, 1])
        y_pred   = np.array([0.1, 0.2, 0.8, 0.9])
        auc, *_ = relatorio_metricas(y_actual, y_pred, thresh=0.5)
        assert auc == pytest.approx(1.0)
