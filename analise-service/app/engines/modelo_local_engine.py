"""Motor `local`: classificador sklearn (risco ou neutro por trecho) + expressões por padrão.

O classificador contribui com `score` e `interesse`; os temas vêm das expressões por padrão
(contrato v3 §5). Mapear o classificador aos 14 padrões é Release 2 (A3). O trecho é o TURNO,
"por ora" (A5). O .joblib é carregado de forma preguiçosa, nunca no import.
"""
import logging
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any

from app import config
from app.engines import regras_engine
from app.erros import ErroMotor

logger = logging.getLogger(__name__)

LIMIAR_RISCO = 0.6  # probabilidade de risco a partir da qual o trecho conta como risco
LIMIAR_INTERESSE = 0.3  # [proposta] só vira interesse o turno que o classificador vê como de baixo risco


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
    interesse, descartados_interesse = regras_engine.extrair_interesse(pedido, turnos_permitidos=baixo_risco)
    logger.info("local: trechos=%d risco=%d temas=%d interesse=%d", len(trechos), em_risco, len(temas), len(interesse))
    return {
        "score": score,
        "sentimento": regras_engine.sentimento_do_score(score),
        "interesse": interesse,
        "temas": temas,
        "descartados": [*descartados_temas, *descartados_interesse],
    }
