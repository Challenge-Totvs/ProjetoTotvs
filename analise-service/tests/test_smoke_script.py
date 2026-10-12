import importlib.util
import json
from pathlib import Path

import pytest

from app.engines import llm_engine
from app.schemas import PedidoAnalise
from test_p2_llm import ClienteAnthropicFalso, RateLimitError, instalar, resposta_anthropic, saida_valida

RAIZ = Path(__file__).resolve().parent.parent
PEDIDO = RAIZ.parent / "docs" / "contrato" / "pedido-v3.json"


@pytest.fixture
def smoke():
    spec = importlib.util.spec_from_file_location("smoke_llm", RAIZ / "scripts" / "smoke_llm.py")
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


@pytest.fixture
def pedido():
    return PedidoAnalise.model_validate(json.loads(PEDIDO.read_text(encoding="utf-8")))


def test_smoke_imprime_so_contagens(smoke, pedido, monkeypatch):
    inventado = saida_valida()["temas"][0] | {"texto": "Frase inventada que nao existe na reuniao.", "padrao": "renovacao"}
    entrada = saida_valida(temas=saida_valida()["temas"] + [inventado])
    instalar(monkeypatch, llm1=ClienteAnthropicFalso(resposta_anthropic(entrada)))
    resultado = smoke.rodar("llm1", pedido)
    assert resultado["ok"] is True and resultado["valida_em_AnaliseResponse"] is True
    assert resultado["devolvido_pela_llm"]["temas"] == 4 and resultado["confirmado_pela_conferencia"]["temas"] == 3
    assert resultado["descartados_por_motivo"] == {"evidencia_nao_localizada": 1}
    assert resultado["avisos"] == ["saida_parcial"]
    texto = json.dumps(resultado, ensure_ascii=False)
    assert "inventada" not in texto and all(t.texto not in texto for t in pedido.turnos)
    assert llm_engine.processar_saida.__module__ == "app.engines.llm_engine"  # o espião foi desfeito


def test_smoke_erro_mostra_so_o_codigo(smoke, pedido, monkeypatch):
    instalar(monkeypatch, llm1=ClienteAnthropicFalso(erro=RateLimitError("Abrimos um chamado secreto")))
    resultado = smoke.rodar("llm1", pedido)
    assert resultado == {"motor": "llm1", "ok": False, "erro": "limite_requisicoes", "tempo_s": resultado["tempo_s"]}


def test_prompt_validado_com_llm_real():
    # Smoke das duas LLMs registrado em docs/evidencias/smoke-12-10.md.
    assert llm_engine.PROMPT_VALIDADO_COM_LLM_REAL is True


def test_aviso_de_prompt_nao_validado_so_aparece_com_a_constante_falsa(smoke, monkeypatch, capsys):
    monkeypatch.setattr(smoke, "rodar", lambda motor, pedido: {"motor": motor, "ok": True})
    monkeypatch.setattr(llm_engine, "PROMPT_VALIDADO_COM_LLM_REAL", True)
    assert smoke.main(["llm2"]) == 0
    assert "NÃO validado" not in capsys.readouterr().out
    monkeypatch.setattr(llm_engine, "PROMPT_VALIDADO_COM_LLM_REAL", False)
    assert smoke.main(["llm2"]) == 0
    assert smoke.AVISO_PROMPT_NAO_VALIDADO in capsys.readouterr().out
