import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import config, orchestrator, saude
from app.cadeia import executar_cadeia
from app.engines import llm_engine
from app.erros import ErroMotor
from app.main import app
from app.schemas import PedidoAnalise, SaidaLLM
from test_p2_llm import ClienteAnthropicFalso, ClienteOpenAIFalso, RateLimitError, instalar, resposta_anthropic, saida_valida

CONTRATO = Path(__file__).resolve().parents[2] / "docs" / "contrato"


@pytest.fixture
def pedido():
    return PedidoAnalise.model_validate(json.loads((CONTRATO / "pedido-v3.json").read_text(encoding="utf-8")))


@pytest.fixture
def relogio(monkeypatch):
    agora = [1000.0]
    monkeypatch.setattr(saude, "relogio", lambda: agora[0])
    return agora


@pytest.fixture
def cliente():
    return TestClient(app)


def _ok(cliente):
    return {m["motor"]: m["ok"] for m in cliente.get("/health").json()["motores"]}


@pytest.fixture
def chaves(monkeypatch):
    for v in ("LLM_PRINCIPAL_API_KEY", "LLM_SECUNDARIA_API_KEY"):
        monkeypatch.setenv(v, "chave-ficticia")
    for v in ("LLM_PRINCIPAL_MODEL", "LLM_SECUNDARIA_MODEL"):
        monkeypatch.setenv(v, "modelo-ficticio")


# --- última tentativa real, janela de 5 minutos ---

def test_falha_recente_derruba_o_ok_por_cinco_minutos(cliente, chaves, relogio):
    assert _ok(cliente)["llm1"] is True
    saude.registrar_tentativa("llm1", ok=False)
    assert _ok(cliente)["llm1"] is False
    relogio[0] += 299
    assert _ok(cliente)["llm1"] is False
    relogio[0] += 2  # 301 s depois
    assert _ok(cliente)["llm1"] is True


def test_tentativa_bem_sucedida_depois_da_falha_recupera_na_hora(cliente, chaves, relogio):
    saude.registrar_tentativa("llm1", ok=False)
    relogio[0] += 10
    saude.registrar_tentativa("llm1", ok=True)
    assert _ok(cliente)["llm1"] is True


def test_falha_de_um_motor_nao_afeta_os_outros(cliente, chaves, relogio):
    saude.registrar_tentativa("llm1", ok=False)
    estado = _ok(cliente)
    assert estado == {"llm1": False, "llm2": True, "local": True, "regras": True}
    assert cliente.get("/health").json()["status"] == "ok"  # llm2 ainda está ok


def test_sem_configuracao_o_ok_continua_falso_mesmo_sem_falha(cliente, relogio):
    assert _ok(cliente)["llm1"] is False


def test_com_as_duas_llms_caidas_o_status_e_degradado(cliente, chaves, relogio):
    saude.registrar_tentativa("llm1", ok=False)
    saude.registrar_tentativa("llm2", ok=False)
    assert cliente.get("/health").json()["status"] == "degradado"


def test_cadeia_registra_o_resultado_de_cada_tentativa(pedido, cliente, chaves, relogio):
    def falha(_):
        raise ErroMotor("timeout")

    executar_cadeia(pedido, [("llm1", falha), ("llm2", lambda p: {"score": 50, "sentimento": "neutro"})])
    assert _ok(cliente)["llm1"] is False and _ok(cliente)["llm2"] is True


def test_nao_configurado_e_sem_prazo_nao_contam_como_tentativa_real(pedido, cliente, chaves, relogio):
    def sem_chamar(_):
        raise ErroMotor("timeout", real=False)

    executar_cadeia(pedido, [("llm1", sem_chamar), ("regras", lambda p: {"score": 50, "sentimento": "neutro"})])
    assert _ok(cliente)["llm1"] is True


def test_erro_real_da_llm_derruba_o_health_pelo_fluxo_completo(pedido, cliente, chaves, relogio, monkeypatch):
    instalar(monkeypatch, llm1=ClienteAnthropicFalso(erro=RateLimitError()),
             llm2=ClienteOpenAIFalso(saida=SaidaLLM.model_validate(saida_valida())))
    r = orchestrator.analisar(pedido)
    assert r.motor == "llm2"
    assert _ok(cliente) == {"llm1": False, "llm2": True, "local": True, "regras": True}


# --- FORCAR_FALHA ---

def test_forcar_falha_e_vazia_por_padrao():
    assert config.motores_forcados() == frozenset()


def test_forcar_falha_aceita_lista_e_ignora_nomes_invalidos(monkeypatch):
    monkeypatch.setenv("FORCAR_FALHA", " llm1, LLM2 ,inventado,, ")
    assert config.motores_forcados() == frozenset({"llm1", "llm2"})


def test_forcar_falha_derruba_a_llm_principal_sem_chamar_a_api(pedido, cliente, chaves, relogio, monkeypatch):
    llm1 = ClienteAnthropicFalso(resposta_anthropic(saida_valida()))
    llm2 = ClienteOpenAIFalso(saida=SaidaLLM.model_validate(saida_valida()))
    instalar(monkeypatch, llm1=llm1, llm2=llm2)
    monkeypatch.setenv("FORCAR_FALHA", "llm1")
    assert _ok(cliente)["llm1"] is False  # a demo vê a LLM principal fora do ar já no /health
    r = orchestrator.analisar(pedido)
    assert r.motor == "llm2" and llm1.chamadas == []
    assert [(t.motor, t.ok) for t in r.tentativas] == [("llm1", False), ("llm2", True)]
    assert r.tentativas[0].erro == "erro_provedor"
    assert _ok(cliente) == {"llm1": False, "llm2": True, "local": True, "regras": True}


def test_sem_forcar_falha_a_llm_principal_responde(pedido, chaves, monkeypatch):
    llm1 = ClienteAnthropicFalso(resposta_anthropic(saida_valida()))
    instalar(monkeypatch, llm1=llm1)
    assert orchestrator.analisar(pedido).motor == "llm1" and len(llm1.chamadas) == 1


def test_forcar_falha_vale_para_local_e_regras(pedido, monkeypatch):
    monkeypatch.setenv("FORCAR_FALHA", "local,regras")
    from app.erros import AnaliseIndisponivel

    with pytest.raises(AnaliseIndisponivel) as e:
        orchestrator.analisar(pedido, llms=())
    assert [(t.motor, t.erro) for t in e.value.tentativas] == [("local", "erro_provedor"), ("regras", "erro_provedor")]
