import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.config import obter_config
from app.erros import corpo_erro
from app.mock import carregar_resposta_mock
from app.schemas import PedidoAnalise

logger = logging.getLogger(__name__)

router = APIRouter()

MOTORES = ("llm1", "llm2", "local", "regras")


@router.post("/analisar")
def post_analisar(pedido: PedidoAnalise) -> JSONResponse:
    versao = obter_config().pipeline_versao
    cabecalho = {"X-Insightcall-Pipeline": versao}
    logger.info("analisar: pipeline=%s turnos=%d", versao, len(pedido.turnos))

    if versao == "mock":
        return JSONResponse(content=carregar_resposta_mock(), headers=cabecalho)

    # O orchestrator ainda fala o contrato v1 (e carrega o .joblib no import), então não é
    # importado aqui: o app sobe sem .joblib e sem chaves (AC7). P1/P2 religam o pipeline real.
    return JSONResponse(
        status_code=503,
        content=corpo_erro(
            "analise_indisponivel",
            "O pipeline real ainda não foi migrado para o contrato v3.",
            tentativas=[],
        ),
        headers=cabecalho,
    )


@router.get("/health")
def get_health() -> dict:
    # P5 troca o ok fixo pelo estado real de cada motor.
    return {
        "status": "ok",
        "pipelineVersao": obter_config().pipeline_versao,
        "motores": [{"motor": motor, "ok": True} for motor in MOTORES],
    }
