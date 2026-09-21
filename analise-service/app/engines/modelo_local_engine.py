import joblib
from pathlib import Path
import re
from app.schemas import AnaliseResponse, ItemAnalise, SentimentoGeral, MotorUtilizado


_pipeline = joblib.load(Path(__file__).parent.parent / "modelos" / "classificador_risco.joblib")

def _dividir_em_trechos(conteudo: str) -> list[str]:
    partes = re.split(r'(?=\[\d{2}:\d{2}\])', conteudo)
    return [p.strip() for p in partes if p.strip()]

def analisar(conteudo: str) -> AnaliseResponse:
    trechos = _dividir_em_trechos(conteudo)

    if not trechos:
        raise ValueError("Nenhum trecho reconhecido na transcrição")

    probabilidades = _pipeline.predict_proba(trechos)[:, 1]

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


    

    
