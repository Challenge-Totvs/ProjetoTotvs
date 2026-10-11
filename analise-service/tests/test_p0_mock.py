import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app

RAIZ_SERVICO = Path(__file__).resolve().parent.parent
CONTRATO = RAIZ_SERVICO.parent / "docs" / "contrato"


def _fixture(nome: str) -> dict:
    return json.loads((CONTRATO / nome).read_text(encoding="utf-8"))


@pytest.fixture
def cliente():
    return TestClient(app)


# --- config ---

def test_config_padrao_e_real(monkeypatch):
    from app import config
    monkeypatch.delenv("PIPELINE_VERSAO", raising=False)
    config.obter_config.cache_clear()
    assert config.obter_config().pipeline_versao == "real"
    config.obter_config.cache_clear()


def test_config_valor_invalido_da_erro_claro(monkeypatch):
    from app import config
    monkeypatch.setenv("PIPELINE_VERSAO", "teste")
    config.obter_config.cache_clear()
    with pytest.raises(ValueError, match="PIPELINE_VERSAO"):
        config.obter_config()
    config.obter_config.cache_clear()


# --- AC1: pedido v3 ---

@pytest.mark.parametrize("nome", ["pedido-v3.json", "pedido-v3-extras.json"])
def test_ac1_aceita_pedidos_v3(cliente, pipeline_versao, nome):
    pipeline_versao("mock")
    resposta = cliente.post("/analisar", json=_fixture(nome))
    assert resposta.status_code == 200


@pytest.mark.parametrize(
    "corpo",
    [
        {"dataReuniao": "2026-10-07", "padroes": []},
        {"turnos": []},
        {"conteudo": "[LOCUTOR 1] Bom dia.", "formatoOrigem": "TXT"},
    ],
    ids=["sem_turnos", "turnos_vazio", "formato_v1"],
)
def test_ac1_recusa_pedido_invalido_com_422_estruturado(cliente, pipeline_versao, corpo):
    pipeline_versao("mock")
    resposta = cliente.post("/analisar", json=corpo)
    assert resposta.status_code == 422
    corpo_erro = resposta.json()
    assert corpo_erro["codigo"] == "pedido_invalido"
    assert isinstance(corpo_erro["mensagem"], str) and corpo_erro["mensagem"]
    assert any(d["campo"] == "turnos" for d in corpo_erro["detalhes"])


def test_422_nao_ecoa_texto_da_transcricao(cliente, pipeline_versao):
    pipeline_versao("mock")
    corpo = {"turnos": [{"n": 1, "locutor": 1, "texto": ""}, {"n": 2, "locutor": "x", "texto": "segredo do cliente"}]}
    resposta = cliente.post("/analisar", json=corpo)
    assert resposta.status_code == 422
    assert "segredo do cliente" not in resposta.text


# --- AC8: flag mock ---

def test_ac8_mock_devolve_fixture_e_header(cliente, pipeline_versao):
    pipeline_versao("mock")
    resposta = cliente.post("/analisar", json=_fixture("pedido-v3.json"))
    assert resposta.status_code == 200
    assert resposta.headers["X-Insightcall-Pipeline"] == "mock"
    assert resposta.json() == _fixture("resposta-v3-llm.json")


def test_mock_sem_fixture_da_erro_explicito(monkeypatch, tmp_path):
    from app import mock
    monkeypatch.setattr(mock, "CAMINHO_RESPOSTA_MOCK", tmp_path / "nao-existe.json")
    mock.carregar_resposta_mock.cache_clear()
    with pytest.raises(FileNotFoundError, match="nao-existe.json"):
        mock.carregar_resposta_mock()
    mock.carregar_resposta_mock.cache_clear()


def test_real_ainda_nao_migrado_responde_503_estruturado(cliente, pipeline_versao):
    pipeline_versao("real")
    resposta = cliente.post("/analisar", json=_fixture("pedido-v3.json"))
    assert resposta.status_code == 503
    assert resposta.headers["X-Insightcall-Pipeline"] == "real"
    assert resposta.json()["codigo"] == "analise_indisponivel"


# --- AC7: sobe sem .joblib e sem chaves; /health ---

def test_ac7_app_importa_sem_chaves_e_sem_carregar_joblib():
    env = {k: v for k, v in os.environ.items() if not k.startswith("LLM_")}
    env.pop("PIPELINE_VERSAO", None)
    codigo = (
        "import sys, app.main; "
        "assert 'app.engines.modelo_local_engine' not in sys.modules; "
        "assert 'joblib' not in sys.modules"
    )
    resultado = subprocess.run(
        [sys.executable, "-c", codigo], cwd=RAIZ_SERVICO, env=env, capture_output=True, text=True, timeout=60
    )
    assert resultado.returncode == 0, resultado.stderr


@pytest.mark.parametrize("versao", ["real", "mock"])
def test_ac7_health_no_formato_do_contrato(cliente, pipeline_versao, versao):
    pipeline_versao(versao)
    resposta = cliente.get("/health")
    assert resposta.status_code == 200
    esperado = _fixture("health.json") | {"pipelineVersao": versao}
    assert resposta.json() == esperado
