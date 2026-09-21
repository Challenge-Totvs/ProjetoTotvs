import joblib
from pathlib import Path
import re
from app.schemas import AnaliseResponse, ItemAnalise, SentimentoGeral, MotorUtilizado


_pipeline = joblib.load(Path(__file__).parent.parent / "modelos" / "classificador_risco.joblib")

transcricao_b = """[00:03] Consultor: Bom dia, João. Como está o uso do sistema?
[00:12] Cliente: Bom dia. Olha, sendo bem sincero, não estamos satisfeitos.
[00:20] Cliente: O suporte demora demais pra responder, já abrimos 3 chamados esse mês.
[00:35] Consultor: Sinto muito por isso, vou verificar com a equipe.
[00:45] Cliente: E o preço da renovação subiu bastante, não faz sentido pagar mais por um serviço pior.
[01:10] Cliente: Estamos avaliando seriamente cancelar e migrar pra outro fornecedor.
[01:30] Consultor: Entendo a frustração. Posso trazer uma proposta de desconto?
[01:40] Cliente: Pode trazer, mas não estou muito otimista, viu.
[02:00] Cliente: A equipe já está desmotivada de usar essa ferramenta.
"""

transcricao_c = """[00:05] Consultor: Bom dia, Patrícia! Como foi o teste do módulo?
[00:14] Cliente: Foi ótimo! A equipe adorou, ficou muito mais rápido que o processo antigo.
[00:30] Cliente: Já quero fechar o contrato o quanto antes, faz total sentido pra gente.
[00:50] Cliente: O preço está dentro do que esperávamos, sem problema nenhum.
[01:05] Consultor: Que ótimo ouvir isso! Posso já preparar a proposta final?
[01:15] Cliente: Pode sim, quanto antes melhor. Estamos animados com a parceria.
"""

def _dividir_em_trechos(conteudo: str) -> list[str]:
    partes = re.split(r'(?=\[\d{2}:\d{2}\])', conteudo)
    return [p.strip() for p in partes if p.strip()]

def analisar(conteudo: str) -> AnaliseResponse:
    trechos = _dividir_em_trechos(conteudo)

    if not trechos:
        raise ValueError("Nenhum trecho reconhecido na transcrição")

    probabilidades = _pipeline.predict_proba(trechos)[:, 1]

    for nome, texto in [("B", transcricao_b), ("C", transcricao_c)]:
        print(f"\n=== Transcrição {nome} ===")
        trechos = _dividir_em_trechos(texto)    
        probs = _pipeline.predict_proba(trechos)[:, 1]
        for trecho, prob in zip(trechos, probs):
            print(f"{prob:.3f} | {trecho}")

    pontos_desinteresse = []
    for trecho, prob in zip(trechos, probabilidades):
        if prob >= 0.6:
            pontos_desinteresse.append(ItemAnalise(descricao=trecho, trecho=trecho))

    proporcao_risco = len(pontos_desinteresse) / len(trechos)
    score = round((1 - proporcao_risco) * 100)

    if score >= 70:
        sentimento = SentimentoGeral.POSITIVO
    elif score >= 45:
        sentimento = SentimentoGeral.NEUTRO
    else:
        sentimento = SentimentoGeral.NEGATIVO

    return AnaliseResponse(
        pontosInteresse=[],
        pontosDesinteresse=pontos_desinteresse,
        oportunidadesVenda=[],
        scoreEngajamento=score,
        sentimentoGeral=sentimento,
        recomendacaoProximosPassos=None,
        motorUtilizado=MotorUtilizado.MODELO_LOCAL
    )

resultado = analisar(transcricao_c)
print(resultado)

    

    
