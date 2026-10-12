"""LLM_PRINCIPAL_WORKSPACE_ID opcional: presente => cabeçalho anthropic-workspace-id; ausente => nada muda."""
import pytest

from app import config
from app.engines import llm_engine


@pytest.fixture
def criados(monkeypatch):
    import anthropic
    import openai

    registro = {}

    class AnthropicFalso:
        def __init__(self, **kw):
            registro["anthropic"] = kw

    class OpenAIFalso:
        def __init__(self, **kw):
            registro["openai"] = kw

    monkeypatch.setattr(anthropic, "Anthropic", AnthropicFalso)
    monkeypatch.setattr(openai, "OpenAI", OpenAIFalso)
    monkeypatch.setattr(llm_engine, "_CLIENTES", {})
    monkeypatch.setenv("LLM_PRINCIPAL_API_KEY", "chave-ficticia-1")
    monkeypatch.setenv("LLM_SECUNDARIA_API_KEY", "chave-ficticia-2")
    return registro


def test_workspace_presente_envia_cabecalho(criados, monkeypatch):
    monkeypatch.setenv("LLM_PRINCIPAL_WORKSPACE_ID", "wrkspc_ficticio")
    llm_engine._criar_cliente("llm1")
    assert criados["anthropic"]["default_headers"] == {"anthropic-workspace-id": "wrkspc_ficticio"}
    assert criados["anthropic"]["max_retries"] == 0 and criados["anthropic"]["timeout"] == 55.0


def test_workspace_ausente_nao_muda_nada(criados):
    assert config.workspace_llm1() is None
    llm_engine._criar_cliente("llm1")
    assert set(criados["anthropic"]) == {"api_key", "timeout", "max_retries"}


def test_workspace_vazio_conta_como_ausente(criados, monkeypatch):
    monkeypatch.setenv("LLM_PRINCIPAL_WORKSPACE_ID", "   ")
    llm_engine._criar_cliente("llm1")
    assert "default_headers" not in criados["anthropic"]


def test_workspace_nao_afeta_a_openai(criados, monkeypatch):
    monkeypatch.setenv("LLM_PRINCIPAL_WORKSPACE_ID", "wrkspc_ficticio")
    llm_engine._criar_cliente("llm2")
    assert set(criados["openai"]) == {"api_key", "timeout", "max_retries"}


def test_trocar_workspace_cria_outro_cliente(criados, monkeypatch):
    primeiro = llm_engine.obter_cliente("llm1")
    monkeypatch.setenv("LLM_PRINCIPAL_WORKSPACE_ID", "wrkspc_ficticio")
    segundo = llm_engine.obter_cliente("llm1")
    assert primeiro is not segundo and criados["anthropic"]["default_headers"]["anthropic-workspace-id"] == "wrkspc_ficticio"


def test_smoke_mostra_so_se_o_workspace_esta_definido(monkeypatch, capsys):
    import importlib.util
    from pathlib import Path

    raiz = Path(__file__).resolve().parent.parent
    spec = importlib.util.spec_from_file_location("smoke_llm", raiz / "scripts" / "smoke_llm.py")
    smoke = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(smoke)
    monkeypatch.setattr(smoke, "rodar", lambda motor, pedido: {"motor": motor, "ok": True})
    monkeypatch.setenv("LLM_PRINCIPAL_WORKSPACE_ID", "wrkspc_ficticio")
    assert smoke.main(["llm1"]) == 0
    saida = capsys.readouterr().out
    assert "workspace=definido" in saida and "wrkspc_ficticio" not in saida
