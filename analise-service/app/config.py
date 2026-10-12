"""Configuração do serviço, lida das variáveis de ambiente em um único lugar."""
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

VERSOES_PIPELINE = ("real", "mock")
MOTORES_VALIDOS = ("llm1", "llm2", "local", "regras")

CAMINHO_MODELO_LOCAL = Path(__file__).resolve().parent / "modelos" / "classificador_risco.joblib"

_VARIAVEIS_LLM = {
    "llm1": ("LLM_PRINCIPAL_API_KEY", "LLM_PRINCIPAL_MODEL"),
    "llm2": ("LLM_SECUNDARIA_API_KEY", "LLM_SECUNDARIA_MODEL"),
}

VARIAVEL_WORKSPACE_LLM1 = "LLM_PRINCIPAL_WORKSPACE_ID"  # opcional: cabeçalho anthropic-workspace-id


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


PRAZO_TOTAL_S = 100.0  # D6: total <= 100 s, o Java espera 120 s
RESERVA_S = 10.0
TIMEOUT_LLM_S = {"llm1": 55.0, "llm2": 35.0}


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


def chave_llm(motor: str) -> str | None:
    return os.environ.get(_VARIAVEIS_LLM[motor][0], "").strip() or None


def workspace_llm1() -> str | None:
    """ID do workspace da Anthropic (opcional). Ausente ou vazio => nenhum cabeçalho extra."""
    return os.environ.get(VARIAVEL_WORKSPACE_LLM1, "").strip() or None


def credenciais_llm(motor: str) -> tuple[str, str] | None:
    """(chave, modelo) do motor, ou None se faltar um dos dois."""
    chave = chave_llm(motor)
    modelo = os.environ.get(_VARIAVEIS_LLM[motor][1], "").strip()
    return (chave, modelo) if chave and modelo else None


def llm_configurada(motor: str) -> bool:
    """True se chave e modelo do motor estão definidos. Não chama a API."""
    return credenciais_llm(motor) is not None


def motores_forcados() -> frozenset[str]:
    """Motores que devem falhar de propósito (FORCAR_FALHA="llm1,llm2"): só para a demo. Vazia por padrão."""
    itens = (item.strip().lower() for item in os.environ.get("FORCAR_FALHA", "").split(","))
    return frozenset(item for item in itens if item in MOTORES_VALIDOS)
