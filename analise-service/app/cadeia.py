"""Cadeia de motores v3: tenta cada motor em ordem e escreve motor, tentativas e versaoContrato.

Os motores são funções `pedido -> dict` (campos da resposta). A cadeia não conhece a LLM:
`motor`, `tentativas` e `versaoContrato` são sempre escritos aqui, nunca pelo motor (regra 3).
`descartados` vem do motor porque é calculado pelo código dele (conferência de citações).
"""
import logging
import time
from typing import Any, Callable, Sequence

from pydantic import ValidationError

from app.erros import AnaliseIndisponivel, ErroMotor
from app.schemas import AnaliseResponse, Tentativa

logger = logging.getLogger(__name__)

Motor = Callable[[Any], dict]

_AVISO_DE_CONTINGENCIA = {"local": "contingencia_modelo_local", "regras": "contingencia_regras"}


def _codigo_do_erro(e: Exception) -> str:
    if isinstance(e, ErroMotor):
        return e.codigo
    if isinstance(e, TimeoutError):
        return "timeout"
    if isinstance(e, ValidationError):
        return "schema_invalido"
    return "erro_interno"


def _ms_desde(inicio: float) -> int:
    return round((time.perf_counter() - inicio) * 1000)


def executar_cadeia(pedido: Any, motores: Sequence[tuple[str, Motor]]) -> AnaliseResponse:
    tentativas: list[Tentativa] = []
    for nome, motor in motores:
        inicio = time.perf_counter()
        try:
            campos = dict(motor(pedido))
            for reservado in ("motor", "tentativas", "versaoContrato"):
                campos.pop(reservado, None)
            campos.setdefault("descartados", [])
            avisos = list(campos.pop("avisos", None) or [])
            if nome in _AVISO_DE_CONTINGENCIA:
                avisos.append(_AVISO_DE_CONTINGENCIA[nome])
            return AnaliseResponse(
                **campos,
                motor=nome,
                tentativas=[*tentativas, Tentativa(motor=nome, ok=True, duracaoMs=_ms_desde(inicio))],
                versaoContrato="v3",
                avisos=avisos,
            )
        except Exception as e:  # um motor pode falhar de qualquer forma; a cadeia segue
            codigo = _codigo_do_erro(e)
            logger.warning("motor %s falhou: %s", nome, codigo)
            tentativas.append(Tentativa(motor=nome, ok=False, erro=codigo, duracaoMs=_ms_desde(inicio)))
    raise AnaliseIndisponivel(tentativas)
