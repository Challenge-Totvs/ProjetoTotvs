"""Erros do domínio e corpos de erro do contrato v3 (§8.1)."""
import logging

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


def corpo_erro(codigo: str, mensagem: str, **extras) -> dict:
    return {"codigo": codigo, "mensagem": mensagem, **extras}


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
    logger.info("pedido inválido: %d problema(s)", len(detalhes))
    return JSONResponse(
        status_code=422,
        content=corpo_erro("pedido_invalido", "O pedido não segue o contrato v3.", detalhes=detalhes),
    )
