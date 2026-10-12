"""Dados SINTÉTICOS para os testes do P8 (nada vem do corpus da TOTVS)."""
import csv
import random
from pathlib import Path

FRASES_RISCO = [
    "O suporte demora demais para responder os chamados.",
    "O preço ficou muito caro para o que a gente usa.",
    "Estamos avaliando cancelar o contrato no fim do ano.",
    "Tivemos erro na apuração do SPED de novo.",
]
FRASES_OPORTUNIDADE = [
    "Vamos abrir uma nova filial no mês que vem.",
    "Queremos contratar um módulo adicional de business intelligence.",
    "Gostaria de saber o valor de mais licenças.",
]
FRASES_INTERESSE = [
    "Isso ajuda bastante, gostei muito da demonstração.",
    "Achei interessante, pode enviar os detalhes da proposta.",
]
FRASES_NEUTRAS = [
    "Bom dia, tudo bem com vocês hoje?",
    "Vou compartilhar a tela para mostrar o relatório.",
    "Anotei os pontos e mando o resumo por e-mail.",
    "Os números do mês fecharam sem diferença.",
    "Consigo marcar a próxima conversa na terça.",
]


def transcricao(rng: random.Random, turnos: int = 8) -> str:
    linhas = []
    for i in range(turnos):
        banco = rng.choice([FRASES_NEUTRAS, FRASES_NEUTRAS, FRASES_RISCO, FRASES_OPORTUNIDADE, FRASES_INTERESSE])
        linhas.append(f"[LOCUTOR {rng.choice([3, 7, 12])}]: {rng.choice(banco)}")
    return "\n".join(linhas)


def corpus(reunioes: int = 30, semente: int = 1) -> list[dict]:
    rng = random.Random(semente)
    return [{"reuniao": f"R{i:03d}", "CODT": f"C{i // 3:03d}", "transcricao": transcricao(rng)} for i in range(reunioes)]


def gravar(caminho: Path, linhas: list[dict]) -> Path:
    with open(caminho, "w", encoding="utf-8", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=list(linhas[0]))
        escritor.writeheader()
        escritor.writerows(linhas)
    return caminho
