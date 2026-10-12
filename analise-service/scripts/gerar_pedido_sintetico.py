"""Gera um pedido SINTÉTICO de tamanho arbitrário (para medir tempo das LLMs reais com uma reunião longa).

    cd analise-service
    python scripts/gerar_pedido_sintetico.py --caracteres 72000 --saida dados_locais/pedido-p90.json

72.000 caracteres (~21 mil tokens) é o P90 de tamanho da amostra. O texto é inventado aqui (frases-modelo combinadas
por uma semente fixa); nada vem do corpus da TOTVS. Mantenha a saída em `dados_locais/` (ignorada pelo git). Imprime só
contagens. Cabeçalho do pedido (`dataReuniao`, `padroes`) copiado de `docs/contrato/pedido-v3.json`.
"""
import argparse
import json
import random
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PEDIDO_BASE = RAIZ.parent / "docs" / "contrato" / "pedido-v3.json"

_MODULOS = ["financeiro", "estoque", "faturamento", "folha", "compras", "contábil", "relatórios", "agenda", "caixa"]
_AREAS = ["a diretoria", "o financeiro", "o time comercial", "a operação", "o pessoal da loja", "o atendimento"]
_MEIOS = ["na terça", "no fim do mês", "na semana que vem", "depois do fechamento", "antes da virada do trimestre"]

_NEUTRAS = [
    "Bom dia, tudo bem? Obrigado por reservar esse horário para a gente conversar.",
    "Deixa eu compartilhar a tela para mostrar como ficou o módulo {m} depois da última atualização.",
    "A gente rodou o processo de {m} ontem e os números fecharam sem diferença no fim do dia.",
    "Anotei aqui os pontos que combinamos na reunião passada e vou repassar um por um.",
    "{a} usa o sistema todos os dias e, no geral, o uso está estável desde o mês passado.",
    "Pode ser, eu vejo isso com o time e retorno {t}. Me lembra se eu esquecer.",
    "Entendi o ponto. Vou registrar e já deixo o responsável avisado para acompanhar.",
    "O volume de lançamentos no {m} cresceu bastante, mas ainda está dentro do esperado para essa época.",
    "Sobre a agenda, consigo marcar a próxima conversa {t}, no mesmo horário de hoje.",
    "Vou mandar um resumo por e-mail com o que conversamos e os próximos passos de cada lado.",
    "Pelo que vi no painel, a maior parte das rotinas de {m} está rodando sem intervenção manual.",
    "Nada de novo por aqui, o time seguiu o plano e {a} só pediu um ajuste pequeno de layout.",
]

_RISCO = [
    "O suporte demora demais para responder, já abrimos três chamados no {m} e ninguém retornou até agora.",
    "Sinceramente, o preço ficou muito caro para o que a gente usa, o valor está bem acima do nosso orçamento.",
    "Estamos avaliando cancelar o contrato se o problema do {m} não for resolvido {t}.",
    "Recebemos uma proposta de um concorrente com condições melhores para o mesmo módulo de {m}.",
    "O prazo de implantação do {m} atrasou duas vezes e {a} está perdendo a paciência com o cronograma.",
    "Tivemos erro na apuração do SPED e o fiscal não fecha desde a última atualização.",
    "O orçamento deste ano está apertado, não tem verba para nada novo antes do segundo semestre.",
    "O pessoal resiste a usar o {m}, a equipe não se adaptou e muita gente voltou para a planilha.",
]

_OPORTUNIDADE = [
    "Queremos contratar um módulo adicional de business intelligence para {a}.",
    "Precisamos integrar o sistema com a plataforma de comércio eletrônico, tem como fazer isso {t}?",
    "Vamos abrir uma nova filial no mês que vem e gostaria de levar o mesmo sistema para lá.",
    "Precisamos de um treinamento para a equipe nova, de preferência {t}.",
    "O contrato vence em dezembro e a gente quer conversar sobre a renovação com condições melhores.",
    "Gostaria de saber o valor de mais licenças, vamos ter mais usuários a partir do próximo trimestre.",
]

_INTERESSE = [
    "Isso ajuda bastante, gostei muito dessa abordagem para o {m}.",
    "Achei interessante a proposta, pode enviar os detalhes para eu levar para {a}.",
    "Excelente, queremos avançar com isso ainda este mês.",
]


def _frase(rng: random.Random, banco: list[str]) -> str:
    return rng.choice(banco).format(m=rng.choice(_MODULOS), a=rng.choice(_AREAS), t=rng.choice(_MEIOS))


def _turno(rng: random.Random) -> str:
    """1 a 3 frases; cerca de 70% neutras, 14% risco, 11% oportunidade, 5% interesse."""
    partes = []
    for _ in range(rng.randint(1, 3)):
        sorteio = rng.random()
        banco = _NEUTRAS if sorteio < 0.70 else _RISCO if sorteio < 0.84 else _OPORTUNIDADE if sorteio < 0.95 else _INTERESSE
        partes.append(_frase(rng, banco))
    return " ".join(partes)


def gerar(caracteres: int, semente: int = 42) -> dict:
    base = json.loads(PEDIDO_BASE.read_text(encoding="utf-8"))
    rng = random.Random(semente)
    turnos, total = [], 0
    while total < caracteres:
        texto = _turno(rng)
        turnos.append({"n": len(turnos) + 1, "locutor": 1 + len(turnos) % 2, "texto": texto})
        total += len(texto)
    return {"turnos": turnos, "dataReuniao": base["dataReuniao"], "padroes": base["padroes"], "contraexemplos": []}


def main(argv: list[str]) -> int:
    analisador = argparse.ArgumentParser(description="Gera um pedido sintético de tamanho P90 para medir tempo.")
    analisador.add_argument("--caracteres", type=int, default=72_000, help="tamanho mínimo da transcrição (padrão 72000)")
    analisador.add_argument("--semente", type=int, default=42)
    analisador.add_argument("--saida", type=Path, default=RAIZ / "dados_locais" / "pedido-p90.json")
    args = analisador.parse_args(argv)
    dados = gerar(args.caracteres, args.semente)
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    args.saida.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
    total = sum(len(t["texto"]) for t in dados["turnos"])
    print(json.dumps({"saida": args.saida.name, "turnos": len(dados["turnos"]), "caracteres": total,
                      "tokens_estimados": round(total / 3.4)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
