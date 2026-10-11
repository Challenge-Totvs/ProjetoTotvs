"""Orquestrador v3: llm1 -> llm2 -> local -> regras -> 503 (SDD §6.1).

A mecânica de `motor`, `tentativas` e erros está em `app/cadeia.py`. As duas LLMs dividem um
`Prazo` por requisição (D6). `llms=()` desliga as LLMs (usado em testes).
"""
import time
from typing import Callable, Sequence

from app.cadeia import Motor, Prazo, executar_cadeia
from app.engines import llm_engine, modelo_local_engine, regras_engine
from app.schemas import AnaliseResponse, PedidoAnalise


def motores_llm(prazo: Prazo) -> list[tuple[str, Motor]]:
    return [(motor, llm_engine.criar_motor(motor, prazo)) for motor in ("llm1", "llm2")]


def montar_motores(llms: Sequence[tuple[str, Motor]]) -> list[tuple[str, Motor]]:
    return [*llms, ("local", modelo_local_engine.analisar), ("regras", regras_engine.analisar)]


def analisar(
    pedido: PedidoAnalise,
    llms: Sequence[tuple[str, Motor]] | None = None,
    relogio: Callable[[], float] = time.monotonic,
) -> AnaliseResponse:
    if llms is None:
        llms = motores_llm(Prazo(relogio=relogio))
    return executar_cadeia(pedido, montar_motores(llms))
