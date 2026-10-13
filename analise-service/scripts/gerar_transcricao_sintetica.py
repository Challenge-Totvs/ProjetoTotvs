"""Gera uma transcrição SINTÉTICA no formato do pedido v3, com tamanho configurável e temas plantados.

    cd analise-service
    python scripts/gerar_transcricao_sintetica.py                          # ~72 mil caracteres (P90)
    python scripts/gerar_transcricao_sintetica.py --caracteres 30000 --saida /tmp/t.json
    python scripts/gerar_transcricao_sintetica.py --padroes renovacao,preco_objecao

Para medir o pior caso de tempo das LLMs reais (`scripts/smoke_llm.py --entrada <arquivo>`). 72.000 caracteres
(~21 mil tokens) é o P90 de tamanho da amostra. O fundo é feito de frases NEUTRAS (nenhuma casa com as expressões do
`regras_engine`); os temas plantados são frases-modelo de alguns dos 14 padrões, espalhadas do início ao fim (o último
fica perto de 90% da reunião, para ver se a LLM acha temas tardios), mais duas frases de interesse. Tudo é inventado
aqui com semente fixa; nada vem do corpus da TOTVS. Imprime só contagens e os NÚMEROS dos turnos plantados.
Cabeçalho do pedido (`dataReuniao`, `padroes`) copiado de `docs/contrato/pedido-v3.json`.
"""
import argparse
import json
import random
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PEDIDO_BASE = RAIZ.parent / "docs" / "contrato" / "pedido-v3.json"
SAIDA_PADRAO = RAIZ / "tests" / "fixtures" / "transcricao-sintetica-p90.json"
CARACTERES_P90 = 72_000

_MODULOS = ["financeiro", "estoque", "faturamento", "folha", "compras", "contábil", "relatórios", "agenda"]
_AREAS = ["a diretoria", "o financeiro", "o time comercial", "a operação", "o atendimento"]
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

# Uma frase-modelo por padrão (as 14 casam com a expressão do próprio padrão em `regras_engine`).
PLANTADOS: dict[str, str] = {
    "suporte_insatisfacao": "O suporte demora demais para responder, já abrimos três chamados no {m} e ninguém retornou até agora.",
    "preco_objecao": "Sinceramente, o preço ficou muito caro para o que a gente usa no dia a dia.",
    "prazo_implantacao": "O prazo de implantação do {m} atrasou duas vezes e {a} está perdendo a paciência com o cronograma.",
    "concorrente_citado": "Recebemos uma proposta de um concorrente com condições melhores para o mesmo escopo.",
    "cancelamento_citado": "Estamos avaliando cancelar o contrato se o problema do {m} não for resolvido {t}.",
    "adocao_resistencia": "O pessoal resiste a usar o {m}, muita gente voltou para a planilha.",
    "fiscal_problema": "Tivemos erro na apuração do SPED e o fiscal não fecha desde a última atualização.",
    "orcamento_restrito": "O orçamento deste ano está apertado, não tem verba para nada novo antes do segundo semestre.",
    "expansao_unidade": "Vamos abrir uma nova filial no mês que vem e gostaria de levar o mesmo sistema para lá.",
    "modulo_adicional": "Queremos contratar um módulo adicional de business intelligence para {a}.",
    "integracao": "Precisamos integrar o sistema com a plataforma de comércio eletrônico, tem como fazer isso {t}?",
    "renovacao": "O contrato vence em dezembro e a gente quer conversar sobre a renovação com condições melhores.",
    "upgrade_licencas": "Gostaria de saber o valor de mais licenças, vamos ter mais usuários no próximo trimestre.",
    "treinamento": "Precisamos de um treinamento para a equipe nova, de preferência {t}.",
}
PADROES_PADRAO = (
    "suporte_insatisfacao", "preco_objecao", "cancelamento_citado", "integracao", "renovacao", "treinamento",
)
_INTERESSE = [
    "Isso ajuda bastante, gostei muito dessa abordagem para o {m}.",
    "Achei interessante a proposta, pode enviar os detalhes para eu levar para {a}.",
]


def _frase(rng: random.Random, modelo: str) -> str:
    return modelo.format(m=rng.choice(_MODULOS), a=rng.choice(_AREAS), t=rng.choice(_MEIOS))


def _turno_neutro(rng: random.Random) -> str:
    return " ".join(_frase(rng, rng.choice(_NEUTRAS)) for _ in range(rng.randint(1, 3)))


def _posicoes(total_turnos: int, quantidade: int) -> list[int]:
    """Índices espalhados de ~10% a ~90% da reunião, sem repetir."""
    if quantidade == 1:
        return [total_turnos // 2]
    inicio, fim = total_turnos * 0.1, total_turnos * 0.9
    passo = (fim - inicio) / (quantidade - 1)
    return sorted({min(total_turnos - 1, round(inicio + i * passo)) for i in range(quantidade)})


def gerar(caracteres: int = CARACTERES_P90, semente: int = 42, padroes: tuple[str, ...] = PADROES_PADRAO) -> dict:
    """Pedido v3 com pelo menos `caracteres` de texto. Devolve o pedido; os plantados ficam em `plantados()`."""
    desconhecidos = [p for p in padroes if p not in PLANTADOS]
    if desconhecidos:
        raise ValueError(f"padrão sem frase plantada: {desconhecidos}")
    base = json.loads(PEDIDO_BASE.read_text(encoding="utf-8"))
    rng = random.Random(semente)
    textos, total = [], 0
    while total < caracteres:
        textos.append(_turno_neutro(rng))
        total += len(textos[-1])

    plantas = [("tema", p) for p in padroes] + [("interesse", i) for i in range(len(_INTERESSE))]
    rng.shuffle(plantas)
    for indice, (tipo, chave) in zip(_posicoes(len(textos), len(plantas)), plantas):
        modelo = PLANTADOS[chave] if tipo == "tema" else _INTERESSE[chave]
        textos[indice] = _frase(rng, modelo)  # troca o turno inteiro: o tamanho não estoura
    while sum(len(t) for t in textos) < caracteres:  # a troca pode encurtar a reunião: completa com neutros
        textos.append(_turno_neutro(rng))

    turnos = [{"n": i + 1, "locutor": 1 + i % 2, "texto": texto} for i, texto in enumerate(textos)]
    return {"turnos": turnos, "dataReuniao": base["dataReuniao"], "padroes": base["padroes"], "contraexemplos": []}


def plantados(pedido: dict, padroes: tuple[str, ...] = PADROES_PADRAO) -> dict[str, int]:
    """Número do turno de cada padrão plantado (para conferir o que a LLM achou). Usa as expressões do regras_engine."""
    sys.path.insert(0, str(RAIZ))
    from app.engines.regras_engine import EXPRESSOES, dobrar

    achados: dict[str, int] = {}
    for turno in pedido["turnos"]:
        dobrado = dobrar(turno["texto"])
        for padrao in padroes:
            if padrao not in achados and EXPRESSOES[padrao].search(dobrado):
                achados[padrao] = turno["n"]
    return achados


def main(argv: list[str]) -> int:
    analisador = argparse.ArgumentParser(description="Gera uma transcrição sintética (pedido v3) para medir tempo.")
    analisador.add_argument("--caracteres", type=int, default=CARACTERES_P90,
                            help=f"tamanho mínimo da transcrição (padrão {CARACTERES_P90}, o P90 do corpus)")
    analisador.add_argument("--semente", type=int, default=42)
    analisador.add_argument("--padroes", default=",".join(PADROES_PADRAO),
                            help="padrões plantados, separados por vírgula (padrão: seis, de risco e oportunidade)")
    analisador.add_argument("--saida", type=Path, default=SAIDA_PADRAO,
                            help="arquivo JSON de saída (padrão: tests/fixtures/transcricao-sintetica-p90.json)")
    args = analisador.parse_args(argv)
    padroes = tuple(p.strip() for p in args.padroes.split(",") if p.strip())
    dados = gerar(args.caracteres, args.semente, padroes)
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    args.saida.write_text(json.dumps(dados, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    total = sum(len(t["texto"]) for t in dados["turnos"])
    print(json.dumps({"saida": args.saida.name, "turnos": len(dados["turnos"]), "caracteres": total,
                      "tokens_estimados": round(total / 3.4), "plantados": plantados(dados, padroes)},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
