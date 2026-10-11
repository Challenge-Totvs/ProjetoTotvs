import json
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import config, saude
from app.main import app

RAIZ_SERVICO = Path(__file__).resolve().parent.parent
CONTRATO = RAIZ_SERVICO.parent / "docs" / "contrato"
CHAVES = ("LLM_PRINCIPAL_API_KEY", "LLM_PRINCIPAL_MODEL", "LLM_SECUNDARIA_API_KEY", "LLM_SECUNDARIA_MODEL")


@pytest.fixture(autouse=True)
def ambiente_limpo(monkeypatch):
    for chave in CHAVES:
        monkeypatch.delenv(chave, raising=False)
    saude.modelo_local_carrega.cache_clear()
    yield
    saude.modelo_local_carrega.cache_clear()


@pytest.fixture
def cliente():
    return TestClient(app)


def _motores(resposta):
    return {m["motor"]: m["ok"] for m in resposta.json()["motores"]}


def test_sem_chaves_e_sem_joblib_responde_200_degradado(cliente, monkeypatch, tmp_path):
    monkeypatch.setattr(config, "CAMINHO_MODELO_LOCAL", tmp_path / "nao-existe.joblib")
    r = cliente.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "degradado"
    assert _motores(r) == {"llm1": False, "llm2": False, "local": False, "regras": True}


def test_formato_igual_ao_da_fixture(cliente):
    fixture = json.loads((CONTRATO / "health.json").read_text(encoding="utf-8"))
    corpo = cliente.get("/health").json()
    assert set(corpo) == set(fixture)
    assert [m["motor"] for m in corpo["motores"]] == [m["motor"] for m in fixture["motores"]]
    assert all(set(m) == {"motor", "ok"} and isinstance(m["ok"], bool) for m in corpo["motores"])


def test_llm_ok_exige_chave_e_modelo(cliente, monkeypatch):
    monkeypatch.setenv("LLM_PRINCIPAL_API_KEY", "chave-ficticia")
    assert _motores(cliente.get("/health"))["llm1"] is False
    monkeypatch.setenv("LLM_PRINCIPAL_MODEL", "modelo-ficticio")
    r = cliente.get("/health")
    assert _motores(r)["llm1"] is True and _motores(r)["llm2"] is False
    assert r.json()["status"] == "ok"


def test_health_nao_devolve_a_chave(cliente, monkeypatch):
    monkeypatch.setenv("LLM_PRINCIPAL_API_KEY", "sk-segredo-123")
    monkeypatch.setenv("LLM_PRINCIPAL_MODEL", "modelo-ficticio")
    assert "sk-segredo-123" not in cliente.get("/health").text


def test_local_ok_com_o_artefato_do_repo(cliente):
    assert _motores(cliente.get("/health"))["local"] is True


def test_local_fora_se_o_artefato_nao_carrega(cliente, monkeypatch, tmp_path):
    corrompido = tmp_path / "corrompido.joblib"
    corrompido.write_text("isto nao e um modelo", encoding="utf-8")
    monkeypatch.setattr(config, "CAMINHO_MODELO_LOCAL", corrompido)
    r = cliente.get("/health")
    assert r.status_code == 200 and _motores(r)["local"] is False


@pytest.mark.parametrize(
    "ok, esperado",
    [
        ({"llm1": True, "llm2": False, "local": False, "regras": True}, "ok"),
        ({"llm1": False, "llm2": True, "local": False, "regras": True}, "ok"),
        ({"llm1": False, "llm2": False, "local": True, "regras": True}, "degradado"),
        ({"llm1": False, "llm2": False, "local": False, "regras": True}, "degradado"),
        ({"llm1": False, "llm2": False, "local": False, "regras": False}, "indisponivel"),
    ],
)
def test_calculo_do_status(ok, esperado):
    assert saude.calcular_status(ok) == esperado


def test_health_nao_importa_clients_de_llm():
    codigo = (
        "import sys; from fastapi.testclient import TestClient; from app.main import app; "
        "r = TestClient(app).get('/health'); assert r.status_code == 200; "
        "assert 'anthropic' not in sys.modules and 'openai' not in sys.modules"
    )
    r = subprocess.run([sys.executable, "-c", codigo], cwd=RAIZ_SERVICO, capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr
