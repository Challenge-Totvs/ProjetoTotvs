"""Configuração do serviço, lida das variáveis de ambiente em um único lugar."""
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

VERSOES_PIPELINE = ("real", "mock")

CAMINHO_MODELO_LOCAL = Path(__file__).resolve().parent / "modelos" / "classificador_risco.joblib"

_VARIAVEIS_LLM = {
    "llm1": ("LLM_PRINCIPAL_API_KEY", "LLM_PRINCIPAL_MODEL"),
    "llm2": ("LLM_SECUNDARIA_API_KEY", "LLM_SECUNDARIA_MODEL"),
}


CAMINHO_ENV = Path(__file__).resolve().parent.parent / ".env"
VARIAVEL_IGNORAR_DOTENV = "INSIGHTCALL_IGNORAR_DOTENV"  # os testes a ligam: nenhum teste lê o .env real


def carregar_dotenv(caminho: Path | None = None) -> bool:
    """Carrega o .env só se existir e sem sobrescrever variáveis já definidas no ambiente.

    Sem `caminho`, usa `analise-service/.env` e respeita VARIAVEL_IGNORAR_DOTENV.
    """
    if caminho is None:
        if os.environ.get(VARIAVEL_IGNORAR_DOTENV):
            return False
        caminho = CAMINHO_ENV
    if not caminho.is_file():
        return False
    from dotenv import load_dotenv

    return load_dotenv(caminho, override=False)


@dataclass(frozen=True)
class Config:
    pipeline_versao: str


@lru_cache
def obter_config() -> Config:
    pipeline_versao = os.environ.get("PIPELINE_VERSAO", "real").strip().lower() or "real"
    if pipeline_versao not in VERSOES_PIPELINE:
        raise ValueError(
            f"PIPELINE_VERSAO inválida: {pipeline_versao!r}. Use um de: {', '.join(VERSOES_PIPELINE)}."
        )
    return Config(pipeline_versao=pipeline_versao)


def llm_configurada(motor: str) -> bool:
    """True se chave e modelo do motor estão definidos. Não chama a API."""
    return all(os.environ.get(variavel, "").strip() for variavel in _VARIAVEIS_LLM[motor])
