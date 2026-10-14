import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.config import obter_config
from app.mock import carregar_resposta_mock
from app.orchestrator import analisar
from app.saude import MOTORES, calcular_status, estado_dos_motores
from app.schemas import (
    ItemSimilar, PedidoAnalise, PedidoEvidencias, PedidoSimilares, RespostaEvidencias, RespostaSimilares,
)
from app.similares import buscar_similares

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


@router.post("/similares")
def post_similares(pedido: PedidoSimilares) -> dict:
    """RAG-lite (PROPOSTA, docs/contrato/similares.md): só ids e scores, nunca texto."""
    pares = buscar_similares(
        pedido.texto, [(r.id, r.texto) for r in pedido.referencias], top_k=pedido.topK, limiar=pedido.limiar
    )
    logger.info("similares: texto=%d caracteres referencias=%d similares=%d", len(pedido.texto),
                len(pedido.referencias), len(pares))
    resposta = RespostaSimilares(similares=[ItemSimilar(id=i, score=s) for i, s in pares])
    return resposta.model_dump(mode="json")


@router.post("/evidencias")
def post_evidencias(pedido: PedidoEvidencias) -> dict:
    """Busca no histórico do cliente (PROPOSTA, docs/contrato/evidencias.md): só ids e scores, nunca texto."""
    pares = buscar_similares(
        pedido.consulta, [(t.id, t.texto) for t in pedido.trechos], top_k=pedido.topK, limiar=0.0
    )
    logger.info("evidencias: consulta=%d caracteres trechos=%d evidencias=%d", len(pedido.consulta),
                len(pedido.trechos), len(pares))
    resposta = RespostaEvidencias(evidencias=[ItemSimilar(id=i, score=s) for i, s in pares])
    return resposta.model_dump(mode="json")


@router.get("/health")
def get_health() -> dict:
    ok = estado_dos_motores()
    return {
        "status": calcular_status(ok),
        "pipelineVersao": obter_config().pipeline_versao,
        "motores": [{"motor": motor, "ok": ok[motor]} for motor in MOTORES],
    }
