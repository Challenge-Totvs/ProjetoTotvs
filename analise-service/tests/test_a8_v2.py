"""A8 v2: cinco expressões exigem contexto de demanda/objeto; o interesse perde as palavras-muleta.

Frases SINTÉTICAS. Casam sobre o texto dobrado (sem acento, minúsculas), como no motor.
"""
import pytest

from app.engines import regras_engine
from app.schemas import PedidoAnalise

DEVE_CASAR = {
    "integracao": [
        "Precisamos integrar o sistema com a loja virtual.",
        "Tem como conectar com o nosso ERP antigo?",
        "A integração com o banco é uma necessidade de vocês.",
    ],
    "modulo_adicional": [
        "Queremos contratar um módulo de BI.",
        "Gostaríamos de saber do módulo adicional de telemedicina.",
        "Temos interesse no business intelligence.",
    ],
    "treinamento": [
        "Precisamos de um treinamento para a equipe.",
        "Podemos agendar um workshop na semana que vem?",
        "Queremos um treinamento adicional para o financeiro.",
    ],
    "concorrente_citado": [
        "Estamos comparando com um concorrente.",
        "Recebemos uma proposta da Omie.",
        "Outro fornecedor ofereceu desconto.",
    ],
    "cancelamento_citado": [
        "Estamos avaliando cancelar o contrato.",
        "A assinatura talvez seja rescindida em dezembro.",
        "Não vamos renovar no fim do ano.",
    ],
}

NAO_DEVE_CASAR = {
    "integracao": [
        "A integração roda no servidor desde ontem.",
        "A API devolve os dados em JSON.",
    ],
    "modulo_adicional": [
        "O módulo financeiro roda no servidor.",
        "O módulo de estoque abre pela tela inicial.",
    ],
    "treinamento": [
        "O treinamento de ontem foi no auditório.",
        "Tivemos treinamento na terça.",
    ],
    "concorrente_citado": [
        "Vamos usar outro sistema de ponto na filial.",
        "Falamos com outra empresa de limpeza.",
    ],
    "cancelamento_citado": [
        "Vou cancelar a reunião de amanhã.",
        "Preciso cancelar o almoço de sexta.",
    ],
}


def _casa(padrao: str, frase: str) -> bool:
    return bool(regras_engine.EXPRESSOES[padrao].search(regras_engine.dobrar(frase)))


@pytest.mark.parametrize("padrao, frase", [(p, f) for p, fs in DEVE_CASAR.items() for f in fs])
def test_intencao_explicita_casa(padrao, frase):
    assert _casa(padrao, frase), frase


@pytest.mark.parametrize("padrao, frase", [(p, f) for p, fs in NAO_DEVE_CASAR.items() for f in fs])
def test_mencao_generica_nao_casa(padrao, frase):
    assert not _casa(padrao, frase), frase


@pytest.mark.parametrize("frase", ["Isso ajuda bastante.", "Gostei da proposta.", "Queremos avançar.", "Pode enviar a proposta."])
def test_interesse_casa_expressoes_de_intencao(frase):
    assert regras_engine.EXPRESSAO_INTERESSE.search(regras_engine.dobrar(frase)), frase


@pytest.mark.parametrize("frase", ["Ótimo.", "Perfeito.", "Combinado.", "Fechado.", "Ótimo, perfeito, combinado, fechado."])
def test_interesse_ignora_muletas(frase):
    assert not regras_engine.EXPRESSAO_INTERESSE.search(regras_engine.dobrar(frase)), frase


def test_muleta_nao_gera_interesse_no_motor():
    pedido = PedidoAnalise.model_validate({"turnos": [
        {"n": 1, "locutor": 1, "texto": "Bom dia, tudo bem?"},
        {"n": 2, "locutor": 2, "texto": "Combinado, então fechado."},
    ]})
    assert regras_engine.analisar(pedido)["interesse"] == []
