"""Smoke em falha: código HTTP e tipo do erro do provedor, nunca chave, mensagem, corpo nem transcrição."""
import importlib.util
import json
from pathlib import Path

import pytest

from app.engines import llm_engine
from app.schemas import PedidoAnalise
from test_p2_llm import ClienteAnthropicFalso, ClienteOpenAIFalso, instalar

RAIZ = Path(__file__).resolve().parent.parent
PEDIDO = RAIZ.parent / "docs" / "contrato" / "pedido-v3.json"
SEGREDO = "mensagem-secreta-do-provedor"


# Exceções no formato dos SDKs: nome da classe, `status_code`, `type` e `body` (mensagem nunca deve vazar).
class _ErroDeStatus(Exception):
    def __init__(self, status, corpo, tipo=None):
        super().__init__(SEGREDO)
        self.status_code, self.body, self.message = status, corpo, SEGREDO
        if tipo is not None:
            self.type = tipo


class AuthenticationError(_ErroDeStatus): ...
class NotFoundError(_ErroDeStatus): ...
class PermissionDeniedError(_ErroDeStatus): ...
class BadRequestError(_ErroDeStatus): ...


def _anthropic(classe, status, tipo):
    return classe(status, {"type": "error", "error": {"type": tipo, "message": SEGREDO}})


def _openai(classe, status, tipo):
    return classe(status, {"message": SEGREDO, "type": tipo, "code": None}, tipo=tipo)


@pytest.fixture
def smoke():
    spec = importlib.util.spec_from_file_location("smoke_llm", RAIZ / "scripts" / "smoke_llm.py")
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


@pytest.fixture
def pedido():
    return PedidoAnalise.model_validate(json.loads(PEDIDO.read_text(encoding="utf-8")))


def _sem_vazamento(resultado, pedido):
    texto = json.dumps(resultado, ensure_ascii=False)
    assert SEGREDO not in texto and "chave-ficticia" not in texto
    assert all(t.texto not in texto for t in pedido.turnos)


def test_401_mostra_http_e_authentication_error(smoke, pedido, monkeypatch):
    instalar(monkeypatch, llm1=ClienteAnthropicFalso(erro=_anthropic(AuthenticationError, 401, "authentication_error")))
    resultado = smoke.rodar("llm1", pedido)
    assert resultado["ok"] is False and resultado["erro"] == "autenticacao"
    assert resultado["http"] == 401 and resultado["tipo_erro_provedor"] == "authentication_error"
    _sem_vazamento(resultado, pedido)


def test_404_mostra_http_e_not_found_error(smoke, pedido, monkeypatch):
    instalar(monkeypatch, llm1=ClienteAnthropicFalso(erro=_anthropic(NotFoundError, 404, "not_found_error")))
    resultado = smoke.rodar("llm1", pedido)
    assert resultado["erro"] == "modelo_indisponivel"
    assert resultado["http"] == 404 and resultado["tipo_erro_provedor"] == "not_found_error"
    _sem_vazamento(resultado, pedido)


def test_403_permission_error(smoke, pedido, monkeypatch):
    instalar(monkeypatch, llm1=ClienteAnthropicFalso(erro=_anthropic(PermissionDeniedError, 403, "permission_error")))
    resultado = smoke.rodar("llm1", pedido)
    assert (resultado["erro"], resultado["http"], resultado["tipo_erro_provedor"]) == (
        "autenticacao", 403, "permission_error")


def test_openai_400_invalid_request_error(smoke, pedido, monkeypatch):
    instalar(monkeypatch, llm2=ClienteOpenAIFalso(erro=_openai(BadRequestError, 400, "invalid_request_error")))
    resultado = smoke.rodar("llm2", pedido)
    assert resultado["http"] == 400 and resultado["tipo_erro_provedor"] == "invalid_request_error"
    _sem_vazamento(resultado, pedido)


def test_tipo_com_texto_livre_nao_passa(smoke, pedido, monkeypatch):
    erro = AuthenticationError(401, {"error": {"type": f"tipo com {SEGREDO}"}})
    instalar(monkeypatch, llm1=ClienteAnthropicFalso(erro=erro))
    resultado = smoke.rodar("llm1", pedido)
    assert resultado["http"] == 401 and "tipo_erro_provedor" not in resultado
    _sem_vazamento(resultado, pedido)


def test_erro_sem_status_nao_inventa_campos(smoke, pedido, monkeypatch):
    class APIConnectionError(Exception): ...

    instalar(monkeypatch, llm1=ClienteAnthropicFalso(erro=APIConnectionError(SEGREDO)))
    resultado = smoke.rodar("llm1", pedido)
    assert resultado == {"motor": "llm1", "ok": False, "erro": "erro_provedor", "tempo_s": resultado["tempo_s"]}


def test_diagnostico_nao_chega_a_resposta_da_api(pedido, monkeypatch):
    from app import orchestrator

    instalar(monkeypatch, llm1=ClienteAnthropicFalso(erro=_anthropic(AuthenticationError, 401, "authentication_error")),
             llm2=ClienteOpenAIFalso(erro=_openai(BadRequestError, 400, "invalid_request_error")))
    corpo = orchestrator.analisar(pedido).model_dump(mode="json", exclude_unset=True)
    texto = json.dumps(corpo)
    assert "authentication_error" not in texto and "invalid_request_error" not in texto
    assert all(set(t) <= {"motor", "ok", "erro", "duracaoMs"} for t in corpo["tentativas"])
    assert llm_engine.diagnostico_do_provedor(ValueError("x")) == {"status_http": None, "tipo_provedor": None}
