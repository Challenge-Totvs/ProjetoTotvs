import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.config import obter_config
from app.mock import carregar_resposta_mock
from app.orchestrator import analisar
from app.saude import MOTORES, calcular_status, estado_dos_motores
from app.schemas import PedidoAnalise

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/analisar")
def post_analisar(pedido: PedidoAnalise) -> JSONResponse:
    versao = obter_config().pipeline_versao
    logger.info("analisar: pipeline=%s turnos=%d", versao, len(pedido.turnos))

    if versao == "mock":
        return JSONResponse(content=carregar_resposta_mock(), headers={"X-Insightcall-Pipeline": versao})

    resposta = analisar(pedido)
    return JSONResponse(
        content=resposta.model_dump(mode="json", exclude_unset=True),
        headers={"X-Insightcall-Pipeline": versao},
    )


@router.get("/health")
def get_health() -> dict:
    ok = estado_dos_motores()
    return {
        "status": calcular_status(ok),
        "pipelineVersao": obter_config().pipeline_versao,
        "motores": [{"motor": motor, "ok": ok[motor]} for motor in MOTORES],
    }
