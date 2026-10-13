"""P7 — POST /similares (RAG-lite, TF-IDF, sem API). Frases sintéticas; nenhuma chamada de rede."""
import json
import logging
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import similares
from app.main import app
from app.schemas import RespostaSimilares

CONTRATO = Path(__file__).resolve().parents[2] / "docs" / "contrato"
SUPORTE = "O suporte demora demais para responder, abrimos três chamados e ninguém retornou."
PRECO = "O preço ficou muito caro para o que a gente usa."
FILIAL = "Vamos abrir uma nova filial no mês que vem."
SPED = "A apuração do SPED deu erro de novo no fechamento."


@pytest.fixture
def cliente():
    return TestClient(app)


def _json(nome):
    return json.loads((CONTRATO / nome).read_text(encoding="utf-8"))


def _post(cliente, **corpo):
    return cliente.post("/similares", json=corpo)


def test_frase_quase_igual_casa(cliente):
    r = _post(cliente, texto="O suporte demora demais para responder, abrimos 3 chamados e ninguém retornou!",
              referencias=[{"id": "a", "texto": SUPORTE}, {"id": "b", "texto": PRECO}])
    assert r.status_code == 200
    corpo = r.json()
    assert [s["id"] for s in corpo["similares"]] == ["a"] and corpo["similares"][0]["score"] > 0.8
    assert corpo["versaoContrato"] == "v3"


def test_acento_e_maiusculas_nao_importam():
    pares = similares.buscar_similares("PRECO FICOU MUITO CARO", [("x", PRECO)])
    assert pares and pares[0][0] == "x"


def test_assuntos_diferentes_nao_casam(cliente):
    r = _post(cliente, texto=SPED, referencias=[{"id": "a", "texto": SUPORTE}, {"id": "b", "texto": PRECO},
                                                {"id": "c", "texto": FILIAL}])
    assert r.json()["similares"] == []


def test_ordem_por_score_decrescente(cliente):
    r = _post(cliente, texto="O suporte demora demais para responder os chamados.", limiar=0.01,
              referencias=[{"id": "fraco", "texto": "Os chamados do faturamento estão abertos."},
                           {"id": "forte", "texto": SUPORTE},
                           {"id": "nada", "texto": FILIAL}])
    ids = [s["id"] for s in r.json()["similares"]]
    scores = [s["score"] for s in r.json()["similares"]]
    assert ids == ["forte", "fraco"] and scores == sorted(scores, reverse=True)


def test_topk_limita_a_quantidade(cliente):
    refs = [{"id": f"r{i}", "texto": f"{SUPORTE} Variação {i}."} for i in range(6)]
    assert len(_post(cliente, texto=SUPORTE, referencias=refs, topK=2).json()["similares"]) == 2
    assert len(_post(cliente, texto=SUPORTE, referencias=refs).json()["similares"]) == 3  # padrão 3


def test_limiar_do_pedido_substitui_o_padrao(cliente):
    refs = [{"id": "a", "texto": SUPORTE}]
    texto = "Ninguém do suporte retornou."
    assert _post(cliente, texto=texto, referencias=refs, limiar=0.99).json()["similares"] == []
    assert _post(cliente, texto=texto, referencias=refs, limiar=0.01).json()["similares"][0]["id"] == "a"


def test_limiar_e_constante_nomeada():
    assert 0 < similares.LIMIAR_SIMILARIDADE < 1


def test_limiar_padrao_e_025_e_a_parafrase_distante_so_volta_com_limiar_explicito(cliente):
    # Decisão de 12/10 (0,2 -> 0,25): a np-104 da fixture (score 0,2301) deixou de casar com o padrão.
    assert similares.LIMIAR_SIMILARIDADE == 0.25
    pedido = _json("pedido-similares.json")
    assert [s["id"] for s in cliente.post("/similares", json=pedido).json()["similares"]] == ["np-101"]
    com_limiar_antigo = cliente.post("/similares", json={**pedido, "limiar": 0.2}).json()["similares"]
    assert com_limiar_antigo == [{"id": "np-101", "score": 0.259}, {"id": "np-104", "score": 0.2301}]


def test_sem_referencias_lista_vazia(cliente):
    r = _post(cliente, texto=SUPORTE)
    assert r.status_code == 200 and r.json() == {"similares": [], "versaoContrato": "v3"}


def test_texto_sem_vocabulario_util_lista_vazia(cliente):
    r = _post(cliente, texto="de que o a", referencias=[{"id": "a", "texto": "o de que"}])
    assert r.status_code == 200 and r.json()["similares"] == []


def test_score_zero_nunca_volta():
    assert similares.buscar_similares(SPED, [("a", FILIAL)], limiar=0.0) == []


@pytest.mark.parametrize("texto", ["", "   "])
def test_texto_vazio_422(cliente, texto):
    r = _post(cliente, texto=texto, referencias=[{"id": "a", "texto": SUPORTE}])
    assert r.status_code == 422
    corpo = r.json()
    assert corpo["codigo"] == "pedido_invalido" and corpo["detalhes"] == [{"campo": "texto", "problema": "vazio"}]


def test_texto_ausente_422(cliente):
    r = cliente.post("/similares", json={"referencias": []})
    assert r.status_code == 422 and r.json()["detalhes"] == [{"campo": "texto", "problema": "ausente"}]


def test_limite_de_200_referencias(cliente):
    refs = [{"id": f"r{i}", "texto": f"Referência sintética número {i} sobre o suporte."} for i in range(201)]
    assert _post(cliente, texto=SUPORTE, referencias=refs).status_code == 422
    assert _post(cliente, texto=SUPORTE, referencias=refs[:200]).status_code == 200


@pytest.mark.parametrize("extra", [{"topK": 0}, {"topK": 51}, {"limiar": -0.1}, {"limiar": 1.5}])
def test_topk_e_limiar_fora_dos_limites_422(cliente, extra):
    assert _post(cliente, texto=SUPORTE, **extra).status_code == 422


def test_referencia_sem_id_ou_texto_422(cliente):
    assert _post(cliente, texto=SUPORTE, referencias=[{"texto": PRECO}]).status_code == 422
    assert _post(cliente, texto=SUPORTE, referencias=[{"id": "a", "texto": ""}]).status_code == 422


def test_422_nao_devolve_texto_do_pedido(cliente):
    r = _post(cliente, texto=SUPORTE, referencias=[{"id": "a", "texto": PRECO}], topK=99)
    assert r.status_code == 422 and "suporte" not in r.text and "caro" not in r.text


def test_resposta_bate_com_a_fixture(cliente):
    r = cliente.post("/similares", json=_json("pedido-similares.json"))
    assert r.status_code == 200
    assert r.json() == _json("resposta-similares.json")
    RespostaSimilares.model_validate(_json("resposta-similares.json"))


def test_campos_desconhecidos_sao_ignorados(cliente):
    r = _post(cliente, texto=SUPORTE, referencias=[{"id": "a", "texto": SUPORTE, "cliente": "x"}], extra=1)
    assert r.status_code == 200 and r.json()["similares"][0]["id"] == "a"


def test_sem_estado_entre_pedidos(cliente):
    primeiro = _post(cliente, texto=SUPORTE, referencias=[{"id": "a", "texto": SUPORTE}]).json()
    _post(cliente, texto=PRECO, referencias=[{"id": "b", "texto": PRECO}, {"id": "c", "texto": FILIAL}])
    assert _post(cliente, texto=SUPORTE, referencias=[{"id": "a", "texto": SUPORTE}]).json() == primeiro


def test_log_so_tem_tamanhos(cliente, caplog):
    with caplog.at_level(logging.INFO):
        _post(cliente, texto=SUPORTE, referencias=[{"id": "a", "texto": PRECO}])
    assert "similares:" in caplog.text and "suporte" not in caplog.text.lower() and "caro" not in caplog.text


def test_mock_tambem_responde(cliente, pipeline_versao):
    pipeline_versao("mock")
    assert _post(cliente, texto=SUPORTE, referencias=[{"id": "a", "texto": SUPORTE}]).status_code == 200


def test_nenhuma_chamada_de_rede(cliente, monkeypatch):
    import socket

    def proibido(*a, **k):
        raise AssertionError("rede")

    monkeypatch.setattr(socket, "create_connection", proibido)
    assert _post(cliente, texto=SUPORTE, referencias=[{"id": "a", "texto": SUPORTE}]).status_code == 200


def test_importar_o_app_nao_carrega_sklearn():
    codigo = "import app.main, app.similares, sys; assert 'sklearn' not in sys.modules"
    raiz = Path(__file__).resolve().parent.parent
    r = subprocess.run([sys.executable, "-c", codigo], cwd=raiz, capture_output=True,
                       env={"INSIGHTCALL_IGNORAR_DOTENV": "1", "SYSTEMROOT": __import__("os").environ.get("SYSTEMROOT", "")})
    assert r.returncode == 0, r.stderr.decode(errors="replace")[-500:]
