"""Estado de cada motor para o GET /health (contrato v3 §8.3). Nunca chama a API de uma LLM."""
import logging
from functools import lru_cache

from app import config

logger = logging.getLogger(__name__)

MOTORES = ("llm1", "llm2", "local", "regras")


@lru_cache
def modelo_local_carrega() -> bool:
    """O artefato existe e carrega. Carregado só aqui (preguiçoso), nunca no import do app."""
    caminho = config.CAMINHO_MODELO_LOCAL
    if not caminho.is_file():
        return False
    try:
        import joblib

        joblib.load(caminho)  # artefato do próprio repo (joblib é pickle)
    except Exception as e:
        logger.warning("modelo local não carrega: %s", type(e).__name__)
        return False
    return True


def estado_dos_motores() -> dict[str, bool]:
    return {
        "llm1": config.llm_configurada("llm1"),
        "llm2": config.llm_configurada("llm2"),
        "local": modelo_local_carrega(),
        "regras": True,
    }


def calcular_status(ok: dict[str, bool]) -> str:
    if ok.get("llm1") or ok.get("llm2"):
        return "ok"
    if ok.get("local") or ok.get("regras"):
        return "degradado"
    return "indisponivel"
