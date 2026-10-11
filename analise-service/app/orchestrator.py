"""Orquestrador v3: llm1 -> llm2 -> local -> regras -> 503 (SDD §6.1).

Os motores LLM entram por `llms` (item P2); sem eles a cadeia começa no `local`. A mecânica de
`motor`, `tentativas` e erros está em `app/cadeia.py`.
"""
from typing import Sequence

from app.cadeia import Motor, executar_cadeia
from app.engines import modelo_local_engine, regras_engine
from app.schemas import AnaliseResponse, PedidoAnalise


def montar_motores(llms: Sequence[tuple[str, Motor]] = ()) -> list[tuple[str, Motor]]:
    return [*llms, ("local", modelo_local_engine.analisar), ("regras", regras_engine.analisar)]


def analisar(pedido: PedidoAnalise, llms: Sequence[tuple[str, Motor]] = ()) -> AnaliseResponse:
    return executar_cadeia(pedido, montar_motores(llms))
