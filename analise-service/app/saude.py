"""Estado de cada motor para o GET /health (contrato v3 §8.3). Nunca chama a API de uma LLM."""
import logging
import time
from functools import lru_cache

from app import config

logger = logging.getLogger(__name__)

MOTORES = config.MOTORES_VALIDOS
JANELA_FALHA_S = 300.0  # uma falha derruba o `ok` do motor por 5 minutos

relogio = time.monotonic
_ultimas: dict[str, tuple[float, bool]] = {}  # motor -> (instante, ok) da última tentativa real; em memória


def registrar_tentativa(motor: str, ok: bool) -> None:
    _ultimas[motor] = (relogio(), ok)


def limpar_estado() -> None:
    _ultimas.clear()


def falhou_recentemente(motor: str) -> bool:
    ultima = _ultimas.get(motor)
    return ultima is not None and not ultima[1] and relogio() - ultima[0] <= JANELA_FALHA_S


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
    """ok = configurado E não forçado a falhar E a última tentativa real não falhou nos últimos 5 minutos."""
    configurado = {
        "llm1": config.llm_configurada("llm1"),
        "llm2": config.llm_configurada("llm2"),
        "local": modelo_local_carrega(),
        "regras": True,
    }
    forcados = config.motores_forcados()
    return {m: configurado[m] and m not in forcados and not falhou_recentemente(m) for m in MOTORES}


def calcular_status(ok: dict[str, bool]) -> str:
    if ok.get("llm1") or ok.get("llm2"):
        return "ok"
    if ok.get("local") or ok.get("regras"):
        return "degradado"
    return "indisponivel"
