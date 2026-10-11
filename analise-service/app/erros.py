"""Erros do domínio e corpos de erro do contrato v3 (§8.1). Nada de stack nem texto de transcrição."""
import logging
from typing import get_args

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.config import obter_config
from app.schemas import ErroTentativa, Tentativa

logger = logging.getLogger(__name__)


class ErroMotor(Exception):
    """Falha de um motor, identificada só por um código do contrato (§6.5), nunca por mensagem livre."""

    def __init__(self, codigo: str):
        if codigo not in get_args(ErroTentativa):
            raise ValueError(f"código de erro fora do contrato: {codigo!r}")
        super().__init__(codigo)
        self.codigo = codigo


class AnaliseIndisponivel(Exception):
    """Nenhum motor respondeu (503 `analise_indisponivel`)."""

    def __init__(self, tentativas: list[Tentativa]):
        super().__init__("analise_indisponivel")
        self.tentativas = tentativas


def corpo_erro(codigo: str, mensagem: str, **extras) -> dict:
    return {"codigo": codigo, "mensagem": mensagem, **extras}


def _cabecalho() -> dict[str, str]:
    return {"X-Insightcall-Pipeline": obter_config().pipeline_versao}


def _problema(erro: dict) -> str:
    tipo = erro.get("type", "")
    if tipo == "missing":
        return "ausente"
    if tipo in ("too_short", "string_too_short"):
        return "vazio"
    return "invalido"


async def tratar_pedido_invalido(request: Request, exc: RequestValidationError) -> JSONResponse:
    # Só o caminho do campo e o tipo do problema: nunca o valor recebido (pode ser texto da transcrição).
    detalhes = []
    for erro in exc.errors():
        caminho = [str(parte) for parte in erro.get("loc", ()) if parte != "body"]
        detalhes.append({"campo": ".".join(caminho) or "corpo", "problema": _problema(erro)})
    padrao_desconhecido = any(
        erro.get("type") == "literal_error" and "padroes" in erro.get("loc", ()) for erro in exc.errors()
    )
    logger.info("pedido inválido: %d problema(s)", len(detalhes))
    codigo, mensagem = (
        ("padrao_desconhecido", "O pedido tem um padrão fora da lista dos 14.")
        if padrao_desconhecido
        else ("pedido_invalido", "O pedido não segue o contrato v3.")
    )
    return JSONResponse(status_code=422, content=corpo_erro(codigo, mensagem, detalhes=detalhes))


async def tratar_analise_indisponivel(request: Request, exc: AnaliseIndisponivel) -> JSONResponse:
    logger.warning("análise indisponível: %d tentativa(s)", len(exc.tentativas))
    corpo = corpo_erro(
        "analise_indisponivel",
        "Nenhum motor de análise respondeu dentro do prazo.",
        tentativas=[t.model_dump(exclude_none=True) for t in exc.tentativas],
    )
    return JSONResponse(status_code=503, content=corpo, headers=_cabecalho())


async def tratar_erro_interno(request: Request, exc: Exception) -> JSONResponse:
    # Só o tipo da exceção: a mensagem pode conter texto da transcrição.
    logger.error("erro interno: %s", type(exc).__name__)
    return JSONResponse(
        status_code=500,
        content=corpo_erro("erro_interno", "Erro interno do serviço de análise."),
        headers=_cabecalho(),
    )


def registrar_handlers(app: FastAPI) -> None:
    app.add_exception_handler(RequestValidationError, tratar_pedido_invalido)
    app.add_exception_handler(AnaliseIndisponivel, tratar_analise_indisponivel)
    app.add_exception_handler(Exception, tratar_erro_interno)
