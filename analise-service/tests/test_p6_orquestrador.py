"""Cenários do orquestrador (SDD §12, AC5) com clients simulados e relógio simulado: nada dorme de verdade."""
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import orchestrator
from app.engines import modelo_local_engine, regras_engine
from app.erros import AnaliseIndisponivel, ErroMotor
from app.main import app
from app.schemas import PedidoAnalise, SaidaLLM
from test_p2_llm import (
    APITimeoutError, AuthenticationError, ClienteAnthropicFalso, ClienteOpenAIFalso, RateLimitError, instalar,
    resposta_anthropic, saida_valida,
)

CONTRATO = Path(__file__).resolve().parents[2] / "docs" / "contrato"
LIMITE_S = 100.0


@pytest.fixture
def pedido():
    return PedidoAnalise.model_validate(json.loads((CONTRATO / "pedido-v3.json").read_text(encoding="utf-8")))


class Relogio:
    def __init__(self):
        self.agora = 0.0

    def __call__(self):
        return self.agora

    def passar(self, segundos):
        self.agora += segundos


class ClienteLento(ClienteAnthropicFalso):
    """Gasta `gasto` segundos do relógio simulado e então falha (ou responde)."""

    def __init__(self, relogio, gasto, erro=None, resposta=None):
        super().__init__(resposta=resposta, erro=erro)
        self._relogio, self._gasto = relogio, gasto

    def _create(self, **kwargs):
        self._relogio.passar(self._gasto)
        return super()._create(**kwargs)


class ClienteLentoOpenAI(ClienteOpenAIFalso):
    def __init__(self, relogio, gasto, erro=None, saida=None):
        super().__init__(saida=saida, erro=erro)
        self._relogio, self._gasto = relogio, gasto

    def _parse(self, **kwargs):
        self._relogio.passar(self._gasto)
        return super()._parse(**kwargs)


def _saida():
    return SaidaLLM.model_validate(saida_valida())


def test_llm1_ok(pedido, monkeypatch):
    instalar(monkeypatch, llm1=ClienteAnthropicFalso(resposta_anthropic(saida_valida())))
    r = orchestrator.analisar(pedido)
    assert r.motor == "llm1" and [t.ok for t in r.tentativas] == [True]


def test_llm1_falha_e_llm2_responde(pedido, monkeypatch):
    instalar(monkeypatch, llm1=ClienteAnthropicFalso(erro=RateLimitError()), llm2=ClienteOpenAIFalso(saida=_saida()))
    r = orchestrator.analisar(pedido)
    assert r.motor == "llm2" and [(t.motor, t.erro) for t in r.tentativas] == [("llm1", "limite_requisicoes"), ("llm2", None)]


def test_duas_llms_fora_responde_o_local(pedido, monkeypatch):
    instalar(monkeypatch, llm1=ClienteAnthropicFalso(erro=APITimeoutError()), llm2=ClienteOpenAIFalso(erro=AuthenticationError()))
    r = orchestrator.analisar(pedido)
    assert r.motor == "local" and r.avisos == ["contingencia_modelo_local"] and r.temas
    assert [t.motor for t in r.tentativas] == ["llm1", "llm2", "local"]


def test_llms_e_local_fora_responde_as_regras(pedido, monkeypatch):
    instalar(monkeypatch, llm1=ClienteAnthropicFalso(erro=APITimeoutError()), llm2=ClienteOpenAIFalso(erro=AuthenticationError()))
    monkeypatch.setattr(modelo_local_engine, "analisar", lambda p: (_ for _ in ()).throw(ErroMotor("modelo_indisponivel")))
    r = orchestrator.analisar(pedido)
    assert r.motor == "regras" and r.avisos == ["contingencia_regras"] and r.temas


def test_tudo_fora_e_503_estruturado_pelo_router(pedido, monkeypatch, pipeline_versao):
    pipeline_versao("real")
    instalar(monkeypatch, llm1=ClienteAnthropicFalso(erro=APITimeoutError()), llm2=ClienteOpenAIFalso(erro=AuthenticationError()))
    for modulo, codigo in ((modelo_local_engine, "modelo_indisponivel"), (regras_engine, "erro_interno")):
        monkeypatch.setattr(modulo, "analisar", lambda p, c=codigo: (_ for _ in ()).throw(ErroMotor(c)))
    with pytest.raises(AnaliseIndisponivel):
        orchestrator.analisar(pedido)
    r = TestClient(app).post("/analisar", json=json.loads((CONTRATO / "pedido-v3.json").read_text(encoding="utf-8")))
    assert r.status_code == 503
    assert [(t["motor"], t["erro"]) for t in r.json()["tentativas"]] == [
        ("llm1", "timeout"), ("llm2", "autenticacao"), ("local", "modelo_indisponivel"), ("regras", "erro_interno")]


def test_llm_lenta_estoura_o_timeout_e_o_total_fica_abaixo_de_100_s(pedido, monkeypatch):
    relogio = Relogio()
    llm1 = ClienteLento(relogio, gasto=55.0, erro=APITimeoutError())
    llm2 = ClienteLentoOpenAI(relogio, gasto=35.0, erro=APITimeoutError())
    instalar(monkeypatch, llm1=llm1, llm2=llm2)
    r = orchestrator.analisar(pedido, relogio=relogio)
    assert llm1.chamadas[0]["timeout"] == 55.0 and llm2.chamadas[0]["timeout"] == 35.0
    assert r.motor == "local" and [t.erro for t in r.tentativas] == ["timeout", "timeout", None]
    assert relogio.agora == 90.0 and relogio.agora <= LIMITE_S


def test_llm1_lenta_reduz_o_timeout_da_llm2_pelo_prazo_compartilhado(pedido, monkeypatch):
    relogio = Relogio()
    llm1 = ClienteLento(relogio, gasto=70.0, erro=APITimeoutError())  # passou do próprio timeout (cliente mal comportado)
    llm2 = ClienteLentoOpenAI(relogio, gasto=20.0, saida=_saida())
    instalar(monkeypatch, llm1=llm1, llm2=llm2)
    r = orchestrator.analisar(pedido, relogio=relogio)
    assert llm2.chamadas[0]["timeout"] == pytest.approx(20.0)  # 100 - 10 de reserva - 70 já gastos
    assert r.motor == "llm2" and relogio.agora <= LIMITE_S


def test_sem_prazo_para_a_llm2_ela_nem_e_chamada_e_a_cadeia_segue(pedido, monkeypatch):
    relogio = Relogio()
    llm1 = ClienteLento(relogio, gasto=90.0, erro=APITimeoutError())
    llm2 = ClienteLentoOpenAI(relogio, gasto=35.0, saida=_saida())
    instalar(monkeypatch, llm1=llm1, llm2=llm2)
    r = orchestrator.analisar(pedido, relogio=relogio)
    assert llm2.chamadas == []
    assert [(t.motor, t.erro) for t in r.tentativas] == [("llm1", "timeout"), ("llm2", "timeout"), ("local", None)]
    assert relogio.agora == 90.0 and relogio.agora <= LIMITE_S


def test_o_teste_de_prazo_nao_dorme_de_verdade(pedido, monkeypatch):
    import time

    def proibido(_):
        raise AssertionError("sleep real em teste")

    monkeypatch.setattr(time, "sleep", proibido)
    relogio = Relogio()
    instalar(monkeypatch, llm1=ClienteLento(relogio, 55.0, erro=APITimeoutError()), llm2=ClienteLentoOpenAI(relogio, 35.0, erro=APITimeoutError()))
    orchestrator.analisar(pedido, relogio=relogio)
