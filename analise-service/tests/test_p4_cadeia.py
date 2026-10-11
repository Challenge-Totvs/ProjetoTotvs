import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import config, orchestrator
from app.engines import modelo_local_engine, regras_engine
from app.erros import AnaliseIndisponivel, ErroMotor
from app.main import app
from app.schemas import AnaliseResponse, PedidoAnalise

CONTRATO = Path(__file__).resolve().parents[2] / "docs" / "contrato"


def _json(nome):
    return json.loads((CONTRATO / nome).read_text(encoding="utf-8"))


@pytest.fixture
def pedido():
    return PedidoAnalise.model_validate(_json("pedido-v3.json"))


def _falha(codigo):
    def motor(_pedido):
        raise ErroMotor(codigo)
    return motor


LLMS_FORA = [("llm1", _falha("timeout")), ("llm2", _falha("autenticacao"))]


def test_llms_fora_responde_o_local_com_temas_e_aviso(pedido):
    r = orchestrator.analisar(pedido, LLMS_FORA)
    assert r.motor == "local" and r.avisos == ["contingencia_modelo_local"]
    assert [(t.motor, t.ok, t.erro) for t in r.tentativas] == [
        ("llm1", False, "timeout"), ("llm2", False, "autenticacao"), ("local", True, None)]
    assert {"suporte_insatisfacao", "orcamento_restrito"} <= {t.padrao for t in r.temas}
    assert r.versaoContrato == "v3"


def test_sem_joblib_cai_para_regras(pedido, monkeypatch, tmp_path):
    monkeypatch.setattr(config, "CAMINHO_MODELO_LOCAL", tmp_path / "nao-existe.joblib")
    r = orchestrator.analisar(pedido, LLMS_FORA)
    assert r.motor == "regras" and r.avisos == ["contingencia_regras"]
    assert [(t.motor, t.erro) for t in r.tentativas] == [
        ("llm1", "timeout"), ("llm2", "autenticacao"), ("local", "modelo_indisponivel"), ("regras", None)]
    assert r.temas


def test_sem_llms_a_cadeia_comeca_no_local(pedido):
    r = orchestrator.analisar(pedido, llms=())
    assert r.motor == "local" and [t.motor for t in r.tentativas] == ["local"]


def test_tudo_fora_levanta_analise_indisponivel(pedido, monkeypatch):
    monkeypatch.setattr(modelo_local_engine, "analisar", _falha("modelo_indisponivel"))
    monkeypatch.setattr(regras_engine, "analisar", _falha("entrada_sem_trechos"))
    with pytest.raises(AnaliseIndisponivel) as e:
        orchestrator.analisar(pedido, LLMS_FORA)
    assert [(t.motor, t.erro) for t in e.value.tentativas] == [
        ("llm1", "timeout"), ("llm2", "autenticacao"), ("local", "modelo_indisponivel"), ("regras", "entrada_sem_trechos")]


# --- pelo router, pipeline real ---

@pytest.fixture
def cliente_real(pipeline_versao):
    pipeline_versao("real")
    return TestClient(app)


def test_router_real_devolve_200_no_formato_das_fixtures_de_contingencia(cliente_real):
    r = cliente_real.post("/analisar", json=_json("pedido-v3.json"))
    assert r.status_code == 200 and r.headers["X-Insightcall-Pipeline"] == "real"
    corpo = r.json()
    AnaliseResponse.model_validate(corpo)
    assert corpo["motor"] == "local"
    fixture = _json("resposta-v3-local.json")
    assert set(corpo) == set(fixture)
    assert all(t["tratado"] is None and "confianca" not in t for t in corpo["temas"])
    assert [(t["motor"], t["ok"], t.get("erro")) for t in corpo["tentativas"]] == [
        ("llm1", False, "nao_configurado"), ("llm2", False, "nao_configurado"), ("local", True, None)]


def test_router_real_sem_joblib_responde_regras(cliente_real, monkeypatch, tmp_path):
    monkeypatch.setattr(config, "CAMINHO_MODELO_LOCAL", tmp_path / "nao-existe.joblib")
    corpo = cliente_real.post("/analisar", json=_json("pedido-v3.json")).json()
    assert corpo["motor"] == "regras" and corpo["avisos"] == ["contingencia_regras"]
    assert set(corpo) == set(_json("resposta-v3-regras.json"))


def test_router_real_tudo_fora_e_503_estruturado(cliente_real, monkeypatch):
    monkeypatch.setattr(modelo_local_engine, "analisar", _falha("modelo_indisponivel"))
    monkeypatch.setattr(regras_engine, "analisar", _falha("erro_interno"))
    r = cliente_real.post("/analisar", json=_json("pedido-v3.json"))
    assert r.status_code == 503
    corpo = r.json()
    assert corpo["codigo"] == "analise_indisponivel"
    assert [(t["motor"], t["erro"]) for t in corpo["tentativas"]] == [
        ("llm1", "nao_configurado"), ("llm2", "nao_configurado"),
        ("local", "modelo_indisponivel"), ("regras", "erro_interno")]
