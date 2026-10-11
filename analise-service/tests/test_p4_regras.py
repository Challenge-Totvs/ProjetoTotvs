import json
from pathlib import Path

import pytest

from app.engines import regras_engine
from app.schemas import AnaliseResponse, PedidoAnalise

FIXTURES = Path(__file__).resolve().parent / "fixtures"
CONTRATO = Path(__file__).resolve().parents[2] / "docs" / "contrato"
CASOS = json.loads((FIXTURES / "regras_por_padrao.json").read_text(encoding="utf-8"))
PADROES = [p for p in CASOS if not p.startswith("_") and p != "neutra"]


def _pedido(textos, **extra):
    turnos = [{"n": i, "locutor": 1 + i % 2, "texto": t} for i, t in enumerate(textos, start=1)]
    return PedidoAnalise.model_validate({"turnos": turnos, **extra})


def test_ha_uma_expressao_para_cada_um_dos_14_padroes():
    assert len(PADROES) == 14
    assert set(regras_engine.EXPRESSOES) == set(PADROES)


@pytest.mark.parametrize("padrao", PADROES)
def test_cada_padrao_e_encontrado_no_turno_certo(padrao):
    caso = CASOS[padrao]
    saida = regras_engine.analisar(_pedido(caso["turnos"]))
    por_padrao = {t["padrao"]: t for t in saida["temas"]}
    assert padrao in por_padrao, f"{padrao} não encontrado em {caso['turnos'][caso['turno'] - 1]!r}"
    tema = por_padrao[padrao]
    assert tema["turno"] == caso["turno"] and tema["turnoFim"] == caso["turno"]
    assert tema["texto"] == caso["turnos"][caso["turno"] - 1]
    assert tema["tratado"] is None and "confianca" not in tema
    assert tema["tipos"] == [regras_engine.TIPO_DO_PADRAO[padrao]]
    assert saida["descartados"] == []


def test_transcricao_neutra_nao_gera_tema():
    saida = regras_engine.analisar(_pedido(CASOS["neutra"]["turnos"]))
    assert saida["temas"] == []


def test_so_os_padroes_do_pedido_sao_procurados():
    caso = CASOS["suporte_insatisfacao"]
    saida = regras_engine.analisar(_pedido(caso["turnos"], padroes=["renovacao"]))
    assert saida["temas"] == []


def test_um_tema_por_padrao_com_a_primeira_ocorrencia():
    pedido = _pedido([
        "Bom dia, vamos começar.",
        "O orçamento deste ano está bem apertado e sem folga.",
        "Pois é, o orçamento continua apertado para o segundo semestre.",
    ])
    temas = [t for t in regras_engine.analisar(pedido)["temas"] if t["padrao"] == "orcamento_restrito"]
    assert len(temas) == 1 and temas[0]["turno"] == 2


def test_contraexemplo_suprime_o_turno():
    textos = ["Bom dia, tudo bem?", "Vamos cancelar a reserva do salão de eventos.", "Estamos avaliando cancelar o contrato."]
    contra = [{"padrao": "cancelamento_citado", "texto": "Vamos cancelar a reserva do salão de eventos.", "motivo": "fora_contexto"}]
    sem = [t for t in regras_engine.analisar(_pedido(textos))["temas"] if t["padrao"] == "cancelamento_citado"]
    com = [t for t in regras_engine.analisar(_pedido(textos, contraexemplos=contra))["temas"]
           if t["padrao"] == "cancelamento_citado"]
    assert sem[0]["turno"] == 2 and com[0]["turno"] == 3


def test_acento_e_maiusculas_nao_atrapalham():
    pedido = _pedido(["Bom dia.", "O ORCAMENTO deste ano ESTA bem APERTADO."])
    assert {t["padrao"] for t in regras_engine.analisar(pedido)["temas"]} == {"orcamento_restrito"}


def test_texto_longo_e_recortado_em_ate_600_caracteres():
    longo = "x " * 400 + "o orçamento está apertado " + "y " * 400
    saida = regras_engine.analisar(_pedido(["Bom dia, vamos começar.", longo]))
    tema = saida["temas"][0]
    assert tema["padrao"] == "orcamento_restrito" and len(tema["texto"]) <= 600 and "apertado" in tema["texto"]


def test_trecho_curto_vai_para_descartados():
    saida = regras_engine.analisar(_pedido(["Bom dia.", "Cancelar!"]))
    assert saida["temas"] == []
    assert saida["descartados"][0]["motivo"] == "trecho_curto" and saida["descartados"][0]["padrao"] == "cancelamento_citado"


def test_sem_trechos_analisaveis_levanta_erro_explicito():
    from app.erros import ErroMotor

    with pytest.raises(ErroMotor) as e:
        regras_engine.analisar(_pedido(["   ", "\n"]))
    assert e.value.codigo == "entrada_sem_trechos"


# --- score, sentimento, interesse ---

def test_score_50_sem_sinais():
    saida = regras_engine.analisar(_pedido(CASOS["neutra"]["turnos"]))
    assert saida["score"] == 50 and saida["sentimento"] == "neutro"


def test_score_e_proporcao_de_sinais_positivos():
    # 1 interesse + 0 oportunidade contra 2 riscos = 1/3
    pedido = _pedido([
        "Bom dia, tudo bem?",
        "O orçamento está apertado.",
        "Abrimos um chamado no suporte e ninguém retornou.",
        "Isso ajuda bastante, gostei da ideia.",
    ])
    saida = regras_engine.analisar(pedido)
    assert saida["score"] == 33 and saida["sentimento"] == "negativo"


@pytest.mark.parametrize(
    "score, esperado",
    [(100, "positivo"), (70, "positivo"), (69, "neutro"), (45, "neutro"), (44, "negativo"), (0, "negativo")],
)
def test_sentimento_pelos_limiares(score, esperado):
    assert regras_engine.sentimento_do_score(score) == esperado
    assert regras_engine.LIMIAR_POSITIVO == 70 and regras_engine.LIMIAR_NEUTRO == 45


def test_interesse_por_palavra_chave_com_citacao_literal():
    saida = regras_engine.analisar(_pedido(["Bom dia, tudo bem?", "Isso ajuda bastante, gostei muito."]))
    assert saida["interesse"][0]["turno"] == 2
    assert saida["interesse"][0]["citacao"] == "Isso ajuda bastante, gostei muito."


# --- contrato: a saída vira AnaliseResponse e tem o formato da fixture de regras ---

def test_saida_valida_em_analise_response_com_a_fixture_do_contrato():
    pedido = PedidoAnalise.model_validate(json.loads((CONTRATO / "pedido-v3.json").read_text(encoding="utf-8")))
    saida = regras_engine.analisar(pedido)
    r = AnaliseResponse(**saida, motor="regras", tentativas=[{"motor": "regras", "ok": True}])
    padroes = {t.padrao for t in r.temas}
    assert {"suporte_insatisfacao", "orcamento_restrito"} <= padroes
    fixture = json.loads((CONTRATO / "resposta-v3-regras.json").read_text(encoding="utf-8"))
    campos_fixture = set(fixture) - {"motor", "tentativas", "versaoContrato", "avisos"}
    assert set(saida) == campos_fixture
