"""Motor `local`: classificador sklearn (risco ou neutro por trecho) + expressões por padrão.

O classificador contribui com `score` e `interesse`; os temas vêm das expressões por padrão
(contrato v3 §5). Mapear o classificador aos 14 padrões é Release 2 (A3). O trecho é o TURNO,
"por ora" (A5). O .joblib é carregado de forma preguiçosa, nunca no import.
O `interesse` pode vir de um classificador próprio (P8), DESLIGADO por padrão: ver `prever_interesse`.
"""
import logging
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any

from app import config
from app.citacoes import TAMANHO_MINIMO, conferir_citacoes
from app.engines import regras_engine
from app.erros import ErroMotor

logger = logging.getLogger(__name__)

LIMIAR_RISCO = 0.6  # probabilidade de risco a partir da qual o trecho conta como risco
LIMIAR_INTERESSE = 0.3  # [proposta] só vira interesse o turno que o classificador vê como de baixo risco
# [proposta] classificador de interesse (P8): turno com p(interesse) >= limiar vira interesse. Calibrar no portão.
LIMIAR_P_INTERESSE = 0.5
TEXTO_DO_INTERESSE_MODELO = "Sinal de interesse (modelo local)"


@lru_cache
def _carregar(caminho: Path) -> Any:
    import joblib

    return joblib.load(caminho)  # artefato do próprio repo (joblib é pickle)


def carregar_pipeline(caminho: Path | None = None) -> Any:
    caminho = caminho or config.CAMINHO_MODELO_LOCAL
    if not caminho.is_file():
        raise ErroMotor("modelo_indisponivel")
    try:
        return _carregar(caminho)
    except Exception as e:
        logger.warning("modelo local não carrega: %s", type(e).__name__)
        raise ErroMotor("modelo_indisponivel") from e


def prever_interesse(trechos: list[tuple[int, str]]) -> dict[int, float] | None:
    """p(interesse) por turno, a partir de `(n, texto NFC)`. None = usar o filtro atual (regex v2 + veto de risco).

    Desligado por padrão: só roda com INTERESSE_MODELO=1 E o artefato promovido em `app/modelos/`. Artefato ausente,
    que não carrega ou que falha na predição nunca derruba o motor: cai no filtro atual (log só com o tipo do erro).
    """
    if not config.interesse_modelo_ligado():
        return None
    caminho = config.CAMINHO_MODELO_INTERESSE
    if not caminho.is_file():
        logger.warning("local: INTERESSE_MODELO=1 sem artefato de interesse; usando o filtro atual")
        return None
    try:
        modelo = _carregar(caminho)  # artefato promovido do próprio repo (joblib é pickle)
        probabilidades = modelo.predict_proba([texto for _, texto in trechos])[:, 1]
    except Exception as e:
        logger.warning("local: modelo de interesse falhou (%s); usando o filtro atual", type(e).__name__)
        return None
    return {n: float(p) for (n, _), p in zip(trechos, probabilidades)}


def _interesse_do_modelo(pedido: Any, p_interesse: dict[int, float]) -> tuple[list[dict], list[dict]]:
    """Turnos com p >= LIMIAR_P_INTERESSE (até MAX_INTERESSE, os de maior p), citação conferida como sempre."""
    textos = {t.n: unicodedata.normalize("NFC", t.texto).strip() for t in pedido.turnos}
    escolhidos = sorted(
        (n for n, p in p_interesse.items() if p >= LIMIAR_P_INTERESSE and len(textos[n]) >= TAMANHO_MINIMO),
        key=lambda n: -p_interesse[n],
    )[: regras_engine.MAX_INTERESSE]
    candidatos = [
        {"texto": TEXTO_DO_INTERESSE_MODELO, "turno": n, "citacao": textos[n][: regras_engine.TAMANHO_MAXIMO_TEXTO].strip()}
        for n in sorted(escolhidos)
    ]
    return conferir_citacoes(pedido.turnos, candidatos, origem="interesse", campo_texto="citacao")


def analisar(pedido: Any) -> dict:
    trechos = [
        (t.n, unicodedata.normalize("NFC", t.texto).strip()) for t in pedido.turnos if t.texto.strip()
    ]
    if not trechos:
        raise ErroMotor("entrada_sem_trechos")

    pipeline = carregar_pipeline()
    probabilidades = pipeline.predict_proba([texto for _, texto in trechos])[:, 1]

    em_risco = sum(1 for p in probabilidades if p >= LIMIAR_RISCO)
    score = round((1 - em_risco / len(trechos)) * 100)
    baixo_risco = [n for (n, _), p in zip(trechos, probabilidades) if p < LIMIAR_INTERESSE]

    temas, descartados_temas = regras_engine.extrair_temas(pedido)
    p_interesse = prever_interesse(trechos)
    if p_interesse is None:  # filtro atual: palavra-chave v2 E risco < LIMIAR_INTERESSE
        interesse, descartados_interesse = regras_engine.extrair_interesse(pedido, turnos_permitidos=baixo_risco)
    else:
        interesse, descartados_interesse = _interesse_do_modelo(pedido, p_interesse)
    logger.info("local: trechos=%d risco=%d temas=%d interesse=%d", len(trechos), em_risco, len(temas), len(interesse))
    return {
        "score": score,
        "sentimento": regras_engine.sentimento_do_score(score),
        "interesse": interesse,
        "temas": temas,
        "descartados": [*descartados_temas, *descartados_interesse],
    }
