import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.config import obter_config
from app.erros import AnaliseIndisponivel
from app.mock import carregar_resposta_mock
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

    # O orchestrator ainda fala o contrato v1 (e carrega o .joblib no import), então não é
    # importado aqui: o app sobe sem .joblib e sem chaves (AC7). P2/P4 ligam os motores v3
    # à `cadeia.executar_cadeia`; até lá o handler devolve o 503 estruturado.
    raise AnaliseIndisponivel([])


@router.get("/health")
def get_health() -> dict:
    ok = estado_dos_motores()
    return {
        "status": calcular_status(ok),
        "pipelineVersao": obter_config().pipeline_versao,
        "motores": [{"motor": motor, "ok": ok[motor]} for motor in MOTORES],
    }
