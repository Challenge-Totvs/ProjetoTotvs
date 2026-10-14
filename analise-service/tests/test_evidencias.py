"""POST /evidencias (busca no histórico do cliente, TF-IDF, sem API). Frases sintéticas; nenhuma chamada de rede."""
import json
import logging
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas import RespostaEvidencias

CONTRATO = Path(__file__).resolve().parents[2] / "docs" / "contrato"
SUPORTE = "O suporte demora demais para responder, abrimos três chamados e ninguém retornou."
PRECO = "O preço ficou muito caro para o que a gente usa."
FILIAL = "Vamos abrir uma nova filial no mês que vem."


@pytest.fixture
def cliente():
    return TestClient(app)


def _json(nome):
    return json.loads((CONTRATO / nome).read_text(encoding="utf-8"))


def _post(cliente, **corpo):
    return cliente.post("/evidencias", json=corpo)


def test_trecho_com_palavras_da_consulta_volta_primeiro(cliente):
    r = _post(cliente, consulta="demora do suporte",
              trechos=[{"id": "1:1", "texto": PRECO}, {"id": "1:2", "texto": SUPORTE}, {"id": "2:1", "texto": FILIAL}])
    assert r.status_code == 200
    corpo = r.json()
    assert [e["id"] for e in corpo["evidencias"]] == ["1:2"] and corpo["evidencias"][0]["score"] > 0
    assert corpo["versaoContrato"] == "v3"


def test_sem_limiar_volta_tudo_que_tem_palavra_em_comum_em_ordem(cliente):
    r = _post(cliente, consulta="suporte chamados",
              trechos=[{"id": "fraco", "texto": "Os chamados do faturamento estão abertos."},
                       {"id": "forte", "texto": SUPORTE}, {"id": "nada", "texto": FILIAL}])
    ids = [e["id"] for e in r.json()["evidencias"]]
    scores = [e["score"] for e in r.json()["evidencias"]]
    assert ids == ["forte", "fraco"] and scores == sorted(scores, reverse=True) and all(s > 0 for s in scores)


def test_topk_limita_e_o_padrao_e_10(cliente):
    trechos = [{"id": f"t{i}", "texto": f"{SUPORTE} Variação {i}."} for i in range(15)]
    assert len(_post(cliente, consulta="suporte", trechos=trechos, topK=2).json()["evidencias"]) == 2
    assert len(_post(cliente, consulta="suporte", trechos=trechos).json()["evidencias"]) == 10


def test_sem_trechos_lista_vazia(cliente):
    r = _post(cliente, consulta="suporte")
    assert r.status_code == 200 and r.json() == {"evidencias": [], "versaoContrato": "v3"}


def test_consulta_sem_vocabulario_util_lista_vazia(cliente):
    r = _post(cliente, consulta="de que o a", trechos=[{"id": "a", "texto": "o de que"}])
    assert r.status_code == 200 and r.json()["evidencias"] == []


@pytest.mark.parametrize("consulta", ["", "   "])
def test_consulta_vazia_422(cliente, consulta):
    r = _post(cliente, consulta=consulta, trechos=[{"id": "a", "texto": SUPORTE}])
    assert r.status_code == 422
    assert r.json()["codigo"] == "pedido_invalido" and r.json()["detalhes"] == [{"campo": "consulta", "problema": "vazio"}]


def test_consulta_ausente_422(cliente):
    r = cliente.post("/evidencias", json={"trechos": []})
    assert r.status_code == 422 and r.json()["detalhes"] == [{"campo": "consulta", "problema": "ausente"}]


def test_limite_de_tamanho_da_consulta(cliente):
    assert _post(cliente, consulta="suporte " * 70).status_code == 422  # 560 caracteres
    assert _post(cliente, consulta="x" * 500).status_code == 200


def test_limite_de_500_trechos(cliente):
    trechos = [{"id": f"t{i}", "texto": f"Trecho sintético número {i} sobre o suporte."} for i in range(501)]
    assert _post(cliente, consulta="suporte", trechos=trechos).status_code == 422
    assert _post(cliente, consulta="suporte", trechos=trechos[:500]).status_code == 200


def test_limite_de_tamanho_do_texto_do_trecho(cliente):
    assert _post(cliente, consulta="suporte", trechos=[{"id": "a", "texto": "suporte " * 251}]).status_code == 422  # 2008
    assert _post(cliente, consulta="suporte", trechos=[{"id": "a", "texto": "x" * 2000}]).status_code == 200


@pytest.mark.parametrize("extra", [{"topK": 0}, {"topK": 51}])
def test_topk_fora_dos_limites_422(cliente, extra):
    assert _post(cliente, consulta="suporte", **extra).status_code == 422


def test_trecho_sem_id_ou_texto_422(cliente):
    assert _post(cliente, consulta="suporte", trechos=[{"texto": PRECO}]).status_code == 422
    assert _post(cliente, consulta="suporte", trechos=[{"id": "a", "texto": ""}]).status_code == 422


def test_422_nao_devolve_texto_do_pedido(cliente):
    r = _post(cliente, consulta="suporte", trechos=[{"id": "a", "texto": PRECO}], topK=99)
    assert r.status_code == 422 and "suporte" not in r.text and "caro" not in r.text


def test_resposta_bate_com_a_fixture(cliente):
    r = cliente.post("/evidencias", json=_json("pedido-evidencias.json"))
    assert r.status_code == 200
    assert r.json() == _json("resposta-evidencias.json")
    RespostaEvidencias.model_validate(_json("resposta-evidencias.json"))


def test_sem_estado_entre_pedidos(cliente):
    pedido = {"consulta": "suporte", "trechos": [{"id": "a", "texto": SUPORTE}]}
    primeiro = cliente.post("/evidencias", json=pedido).json()
    _post(cliente, consulta="preço", trechos=[{"id": "b", "texto": PRECO}, {"id": "c", "texto": FILIAL}])
    assert cliente.post("/evidencias", json=pedido).json() == primeiro


def test_log_so_tem_tamanhos(cliente, caplog):
    with caplog.at_level(logging.INFO):
        _post(cliente, consulta="suporte", trechos=[{"id": "a", "texto": PRECO}])
    assert "evidencias:" in caplog.text and "suporte" not in caplog.text.lower() and "caro" not in caplog.text


def test_nenhuma_chamada_de_rede(cliente, monkeypatch):
    import socket

    def proibido(*a, **k):
        raise AssertionError("rede")

    monkeypatch.setattr(socket, "create_connection", proibido)
    assert _post(cliente, consulta="suporte", trechos=[{"id": "a", "texto": SUPORTE}]).status_code == 200
