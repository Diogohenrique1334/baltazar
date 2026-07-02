"""KNN de regressão ponderado por similaridade (genérico, sem domínio).

Ideia: dado um item-alvo descrito por um conjunto de *tags* (ex.: skills,
gêneros, categorias de produto) e uma *categoria* opcional (ex.: tipo de
projeto), encontrar entre itens históricos os K mais parecidos que já têm um
*valor* conhecido (ex.: horas, preço, duração) e prever o valor do alvo como a
**média ponderada pela similaridade** desses vizinhos.

A "distância" do KNN clássico é substituída por uma **similaridade** [0, 1]:

    similaridade = peso_tags * Jaccard(tags) + (bonus se a categoria coincide)

Quanto maior, mais perto. Funciona com features categóricas/conjuntos (onde a
distância euclidiana não faz sentido) e ainda dá um piso para itens da mesma
categoria mesmo sem overlap de tags.

Reutilizável: o chamador converte seus objetos de domínio em `ItemHistorico`
(rótulo + tags + valor + categoria) e decide o que fazer no cold start (quando
não há vizinhos), tipicamente um fallback heurístico próprio.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Hashable


# --- Defaults do modelo (ajustáveis pelo chamador) ---
K_PADRAO = 5
PESO_TAGS_PADRAO = 0.6          # quanto a similaridade de tags contribui
BONUS_MESMA_CATEGORIA_PADRAO = 0.4   # piso de similaridade quando a categoria coincide


@dataclass
class ItemHistorico:
    """Item histórico (com valor conhecido) usado como possível vizinho."""

    rotulo: str
    tags: set
    valor: float | None
    categoria: Hashable | None = None


@dataclass
class VizinhoSimilar:
    """Um vizinho selecionado, com sua similaridade e valor."""

    rotulo: str
    similaridade: float
    valor: float


@dataclass
class ResultadoKNN:
    """Resultado da estimativa. `valor` é None quando não há vizinhos válidos."""

    valor: float | None
    vizinhos: list[VizinhoSimilar] = field(default_factory=list)
    explicacao: str = ""


def jaccard(a: Iterable[Hashable], b: Iterable[Hashable]) -> float:
    """Índice de Jaccard entre dois conjuntos: |A ∩ B| / |A ∪ B|. Vazio↔vazio = 0."""
    sa, sb = set(a), set(b)
    uniao = sa | sb
    if not uniao:
        return 0.0
    return len(sa & sb) / len(uniao)


def similaridade_jaccard_categoria(
    tags_a: Iterable[Hashable],
    tags_b: Iterable[Hashable],
    categoria_a: Hashable | None = None,
    categoria_b: Hashable | None = None,
    peso_tags: float = PESO_TAGS_PADRAO,
    bonus_mesma_categoria: float = BONUS_MESMA_CATEGORIA_PADRAO,
) -> float:
    """Similaridade [0, 1] combinando Jaccard de tags + bônus de mesma categoria.

    - Tags: contribuem com `peso_tags * jaccard`.
    - Mesma categoria: soma o piso `bonus_mesma_categoria` (itens da mesma
      categoria já são parecidos, mesmo sem overlap de tags).
    """
    sim = peso_tags * jaccard(tags_a, tags_b)
    if categoria_a is not None and categoria_a == categoria_b:
        sim += bonus_mesma_categoria
    return min(sim, 1.0)


def knn_regressao_similaridade(
    tags_alvo: Iterable[Hashable],
    categoria_alvo: Hashable | None,
    historico: Iterable[ItemHistorico],
    k: int = K_PADRAO,
    peso_tags: float = PESO_TAGS_PADRAO,
    bonus_mesma_categoria: float = BONUS_MESMA_CATEGORIA_PADRAO,
    sim_minima: float = 0.0,
) -> ResultadoKNN:
    """Prevê o valor do alvo pela média ponderada por similaridade dos K vizinhos.

    Itens com `valor` None são ignorados. Retorna `ResultadoKNN.valor = None`
    quando nenhum item histórico atinge `sim_minima` — cabe ao chamador aplicar
    o fallback (ex.: heurística de domínio).

    Parâmetros
    ----------
    tags_alvo, categoria_alvo : descrição do item a estimar.
    historico : itens com valor conhecido (candidatos a vizinho).
    k : número máximo de vizinhos a considerar.
    peso_tags, bonus_mesma_categoria : pesos da função de similaridade.
    sim_minima : similaridade mínima (exclusiva) para um item virar candidato.
    """
    tags_alvo = set(tags_alvo)
    candidatos: list[VizinhoSimilar] = []
    for item in historico:
        if item.valor is None:
            continue
        sim = similaridade_jaccard_categoria(
            tags_alvo, item.tags, categoria_alvo, item.categoria,
            peso_tags, bonus_mesma_categoria,
        )
        if sim > sim_minima:
            candidatos.append(VizinhoSimilar(item.rotulo, sim, float(item.valor)))

    if not candidatos:
        return ResultadoKNN(
            valor=None,
            explicacao="Nenhum item semelhante com valor disponível.",
        )

    candidatos.sort(key=lambda v: v.similaridade, reverse=True)
    vizinhos = candidatos[:k]

    soma_pesos = sum(v.similaridade for v in vizinhos)
    valor = sum(v.valor * v.similaridade for v in vizinhos) / soma_pesos

    nomes = ", ".join(v.rotulo for v in vizinhos)
    explicacao = (
        f"Média ponderada por similaridade de {len(vizinhos)} item(ns) "
        f"semelhante(s): {nomes}."
    )
    return ResultadoKNN(valor=valor, vizinhos=vizinhos, explicacao=explicacao)