"""RAG-lite do `POST /similares` (PROPOSTA, `docs/contrato/similares.md`): cosseno TF-IDF, sem API e sem estado.

O vetorizador é ajustado a cada pedido sobre `referencias + texto`; nada fica guardado entre pedidos. O scikit-learn é
importado só na hora do uso (o app sobe sem carregar sklearn).
"""
import logging
import unicodedata
from typing import Sequence

logger = logging.getLogger(__name__)

# Decisão do João Paulo (12/10): 0,2 -> 0,25. Frases sintéticas: paráfrases do mesmo assunto ~0,2-0,35, assuntos
# diferentes <= ~0,14; com 0,25 as paráfrases mais distantes deixam de casar. Calibrar com o conjunto ouro (P8).
LIMIAR_SIMILARIDADE = 0.25
CASAS_DECIMAIS = 4


def _sem_acento(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn").lower()


# Lista curta de palavras vazias do português (sem acento, minúsculas: a mesma forma que o vetorizador produz).
STOP_WORDS = sorted({_sem_acento(p) for p in (
    "a o as os um uma uns umas de do da dos das em no na nos nas por pelo pela pelos pelas para pra com sem que se e "
    "ou mas como ao aos à às é era foi ser são está estão estava tem têm ter tinha já não sim eu ele ela nós eles elas "
    "você vocês me te lhe isso isto esse essa esses essas este esta estes estas aquele aquela muito mais menos também "
    "só até quando onde porque então aqui lá gente meu minha seu sua nosso nossa vai vamos ainda bem"
).split()})


def buscar_similares(
    texto: str, referencias: Sequence[tuple[str, str]], top_k: int = 3, limiar: float | None = None
) -> list[tuple[str, float]]:
    """`(id, score)` das referências com cosseno >= limiar, em ordem decrescente (empate: ordem de chegada).

    Sem referências ou sem vocabulário útil => lista vazia, nunca erro.
    """
    limiar = LIMIAR_SIMILARIDADE if limiar is None else limiar
    if not referencias or not texto.strip():
        return []
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import linear_kernel

    vetorizador = TfidfVectorizer(
        lowercase=True, strip_accents="unicode", ngram_range=(1, 2), sublinear_tf=True, stop_words=STOP_WORDS,
    )
    try:
        matriz = vetorizador.fit_transform([t for _, t in referencias] + [texto])
    except ValueError:  # vocabulário vazio (só stop words, números de um dígito, pontuação)
        return []
    scores = linear_kernel(matriz[-1], matriz[:-1])[0]  # vetores já normalizados (l2): produto = cosseno
    pares = [(id_, round(min(1.0, max(0.0, float(s))), CASAS_DECIMAIS)) for (id_, _), s in zip(referencias, scores)]
    acima = [(i, (id_, s)) for i, (id_, s) in enumerate(pares) if s >= limiar and s > 0]
    acima.sort(key=lambda item: (-item[1][1], item[0]))
    return [par for _, par in acima[:top_k]]
