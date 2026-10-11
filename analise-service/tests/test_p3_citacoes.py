import copy
import json
from pathlib import Path

import pytest

from app.citacoes import conferir_citacoes
from app.schemas import Descartado

CONTRATO = Path(__file__).resolve().parents[2] / "docs" / "contrato"


def _json(nome):
    return json.loads((CONTRATO / nome).read_text(encoding="utf-8"))


def _turnos(*textos):
    return [{"n": i, "locutor": 1, "texto": t} for i, t in enumerate(textos, start=1)]


def _conferir(turnos, texto, turno, origem="tema", **extra):
    ok, descartados = conferir_citacoes(turnos, [{"texto": texto, "turno": turno, **extra}], origem=origem)
    return ok, descartados


T = _turnos(
    "Bom dia, tudo bem?",
    "Abrimos um chamado sobre o faturamento há três semanas.",
    "Posso fechar o reajuste",
    "fixo por dois anos, tudo bem?",
    "Combinado entre nós.",
    "Fechado então.",
)


def test_acerto_exato():
    ok, desc = _conferir(T, "Abrimos um chamado sobre o faturamento há três semanas.", 2)
    assert desc == []
    assert ok[0]["turno"] == 2 and ok[0]["turnoFim"] == 2
    assert ok[0]["texto"] == "Abrimos um chamado sobre o faturamento há três semanas."


def test_recorte_dentro_do_turno_grava_o_trecho_recebido():
    ok, _ = _conferir(T, "chamado sobre o faturamento", 2)
    assert ok[0]["texto"] == "chamado sobre o faturamento"


def test_diferenca_de_espacos_e_aspas_grava_texto_recebido():
    turnos = _turnos('Ele disse “vamos cancelar” e  saiu —  rápido…  depois voltou.')
    ok, desc = _conferir(turnos, 'disse "vamos cancelar" e saiu - rápido... depois', 1)
    assert desc == []
    assert ok[0]["texto"] == 'disse “vamos cancelar” e  saiu —  rápido…  depois'


def test_ignora_maiusculas_mas_nao_acentos():
    ok, desc = _conferir(T, "ABRIMOS UM CHAMADO SOBRE O FATURAMENTO", 2)
    assert desc == [] and ok[0]["texto"] == "Abrimos um chamado sobre o faturamento"
    ok, desc = _conferir(T, "Abrimos um chamado sobre o faturamento ha tres semanas", 2)
    assert ok == [] and desc[0]["motivo"] == "evidencia_nao_localizada"


@pytest.mark.parametrize("indicado", [1, 3, 4])
def test_turno_errado_mas_vizinho_e_corrigido(indicado):
    ok, desc = _conferir(T, "Abrimos um chamado sobre o faturamento há três semanas.", indicado)
    assert desc == [] and ok[0]["turno"] == 2 and ok[0]["turnoFim"] == 2


def test_turno_alem_de_dois_vizinhos_nao_e_buscado():
    ok, desc = _conferir(T, "Abrimos um chamado sobre o faturamento há três semanas.", 6)
    assert ok == [] and desc[0]["motivo"] == "evidencia_nao_localizada"


def test_trecho_entre_dois_turnos():
    ok, desc = _conferir(T, "fechar o reajuste fixo por dois anos", 3)
    assert desc == []
    assert (ok[0]["turno"], ok[0]["turnoFim"]) == (3, 4)
    assert ok[0]["texto"] == "fechar o reajuste fixo por dois anos"


def test_trecho_entre_tres_turnos():
    turnos = _turnos("Vou enviar", "a proposta", "até segunda, combinado")
    ok, desc = _conferir(turnos, "enviar a proposta até segunda", 1)
    assert desc == [] and (ok[0]["turno"], ok[0]["turnoFim"]) == (1, 3)


def test_trecho_entre_turnos_com_turno_indicado_errado():
    ok, _ = _conferir(T, "fechar o reajuste fixo por dois anos", 5)
    assert (ok[0]["turno"], ok[0]["turnoFim"]) == (3, 4)


def test_trecho_inexistente_e_descartado_com_origem_e_padrao():
    ok, desc = _conferir(T, "O cliente pediu cancelamento imediato do contrato.", 2, padrao="cancelamento_citado")
    assert ok == []
    assert desc == [{
        "texto": "O cliente pediu cancelamento imediato do contrato.",
        "motivo": "evidencia_nao_localizada", "origem": "tema", "padrao": "cancelamento_citado",
    }]
    Descartado.model_validate(desc[0])


def test_alucinacao_parecida_uma_palavra_trocada_e_descartada():
    ok, desc = _conferir(T, "Abrimos um chamado sobre o faturamento há quatro semanas.", 2)
    assert ok == [] and desc[0]["motivo"] == "evidencia_nao_localizada"


def test_trecho_curto():
    ok, desc = _conferir(T, "Fechado.", 6)
    assert ok == [] and desc[0]["motivo"] == "trecho_curto"


def test_trecho_longo():
    longo = "palavra " * 100
    ok, desc = _conferir(_turnos(longo), longo, 1)
    assert ok == [] and desc[0]["motivo"] == "trecho_longo"


def test_tamanho_considera_o_texto_normalizado():
    turnos = _turnos("a" * 600 + " fim")
    ok, desc = _conferir(turnos, "a" * 600, 1)
    assert desc == [] and len(ok) == 1
    ok, desc = _conferir(turnos, "a" * 601, 1)
    assert desc[0]["motivo"] == "trecho_longo"


def test_turno_inexistente_e_descartado():
    ok, desc = _conferir(T, "Abrimos um chamado sobre o faturamento há três semanas.", 99)
    assert ok == [] and desc[0]["motivo"] == "evidencia_nao_localizada"


def test_campo_de_texto_configuravel_e_itens_nao_sao_alterados():
    itens = [{"citacao": "chamado sobre o faturamento", "turno": 3, "texto": "descricao"}]
    antes = copy.deepcopy(itens)
    ok, desc = conferir_citacoes(T, itens, origem="interesse", campo_texto="citacao")
    assert itens == antes
    assert ok[0]["turno"] == 2 and ok[0]["citacao"] == "chamado sobre o faturamento" and ok[0]["texto"] == "descricao"


def test_mistura_de_acertos_e_descartes_preserva_ordem():
    itens = [
        {"texto": "Combinado entre nós.", "turno": 5},
        {"texto": "frase que nao existe na reuniao", "turno": 1},
        {"texto": "Bom dia, tudo bem?", "turno": 1},
    ]
    ok, desc = conferir_citacoes(T, itens, origem="compromisso")
    assert [i["turno"] for i in ok] == [5, 1] and len(desc) == 1 and desc[0]["origem"] == "compromisso"


# --- AC4 com as fixtures: toda citação de resposta-v3-llm.json existe no pedido-v3.json ---

def test_ac4_fixture_llm_confirma_contra_pedido():
    turnos = _json("pedido-v3.json")["turnos"]
    r = _json("resposta-v3-llm.json")
    grupos = [
        ("tema", r["temas"], "texto"),
        ("interesse", r["interesse"], "citacao"),
        ("compromisso", r["compromissos"], "texto"),
        ("eventoConduta", r["eventosConduta"], "texto"),
    ]
    for origem, itens, campo in grupos:
        ok, desc = conferir_citacoes(turnos, itens, origem=origem, campo_texto=campo)
        assert desc == [], origem
        assert len(ok) == len(itens)
        for antes, depois in zip(itens, ok):
            assert depois["turno"] == antes["turno"], origem
            assert depois["turnoFim"] == antes.get("turnoFim", antes["turno"]), origem
            assert depois[campo] == antes[campo], origem


def test_ac4_fixture_descartado_e_realmente_inexistente():
    turnos = _json("pedido-v3.json")["turnos"]
    d = _json("resposta-v3-llm.json")["descartados"][0]
    ok, desc = conferir_citacoes(turnos, [{"texto": d["texto"], "turno": 3, "padrao": d["padrao"]}], origem="tema")
    assert ok == [] and desc[0]["motivo"] == d["motivo"]


@pytest.mark.parametrize("nome", ["resposta-v3-local.json", "resposta-v3-regras.json"])
def test_local_e_regras_apenas_confirmam(nome):
    turnos = _json("pedido-v3.json")["turnos"]
    temas = _json(nome)["temas"]
    ok, desc = conferir_citacoes(turnos, temas, origem="tema")
    assert desc == [] and [t["texto"] for t in ok] == [t["texto"] for t in temas]
