import json
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.erros import AnaliseIndisponivel, registrar_handlers
from app.main import app
from app.schemas import Tentativa

CONTRATO = Path(__file__).resolve().parents[2] / "docs" / "contrato"


def _fixture(nome):
    return json.loads((CONTRATO / nome).read_text(encoding="utf-8"))


def _app_de_teste():
    teste = FastAPI()
    registrar_handlers(teste)

    @teste.get("/indisponivel")
    def indisponivel():
        raise AnaliseIndisponivel([
            Tentativa(motor="llm1", ok=False, erro="timeout", duracaoMs=55000),
            Tentativa(motor="llm2", ok=False, erro="autenticacao", duracaoMs=420),
            Tentativa(motor="local", ok=False, erro="modelo_indisponivel", duracaoMs=3),
            Tentativa(motor="regras", ok=False, erro="erro_interno", duracaoMs=2),
        ])

    @teste.get("/defeito")
    def defeito():
        raise RuntimeError("trecho secreto da transcricao do cliente")

    return TestClient(teste, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def pipeline(pipeline_versao):
    pipeline_versao("real")


def test_422_igual_a_fixture():
    fixture = _fixture("erro-422.json")
    r = TestClient(app).post("/analisar", json={"turnos": []})
    assert r.status_code == 422
    corpo = r.json()
    assert set(corpo) == set(fixture)
    assert corpo["codigo"] == fixture["codigo"] and corpo["detalhes"] == fixture["detalhes"]


def test_503_igual_a_fixture():
    fixture = _fixture("erro-503.json")
    r = _app_de_teste().get("/indisponivel")
    assert r.status_code == 503
    corpo = r.json()
    assert corpo == fixture
    assert r.headers["X-Insightcall-Pipeline"] == "real"
    for t in corpo["tentativas"]:
        Tentativa.model_validate(t)


def test_500_sem_stack_e_sem_texto_da_transcricao():
    r = _app_de_teste().get("/defeito")
    assert r.status_code == 500
    assert r.json()["codigo"] == "erro_interno"
    assert set(r.json()) == {"codigo", "mensagem"}
    assert "secreto" not in r.text and "Traceback" not in r.text and "RuntimeError" not in r.text
    assert r.headers["X-Insightcall-Pipeline"] == "real"


def test_500_nao_loga_texto_da_transcricao(caplog):
    with caplog.at_level("DEBUG"):
        _app_de_teste().get("/defeito")
    assert "secreto" not in caplog.text
