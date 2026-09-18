from pydantic import BaseModel
from enum import Enum

class AnaliseRequest(BaseModel):
    conteudo: str
    formatoOrigem: str

class ItemAnalise(BaseModel):
    descricao: str
    trecho: str

class SentimentoGeral(str, Enum):
    POSITIVO = "POSITIVO"
    NEUTRO = "NEUTRO"
    NEGATIVO = "NEGATIVO"

class MotorUtilizado(str, Enum):
    LLM_PRIMARIA = "LLM_PRIMARIA"
    LLM_SECUNDARIA = "LLM_SECUNDARIA"
    MODELO_LOCAL = "MODELO_LOCAL"
    REGEX_FALLBACK = "REGEX_FALLBACK"

class AnaliseResponse(BaseModel):
    pontosInteresse : list[ItemAnalise]
    pontosDesinteresse : list[ItemAnalise]
    oportunidadesVenda : list[ItemAnalise]
    scoreEngajamento : int
    sentimentoGeral : SentimentoGeral
    recomendacaoProximosPassos : str | None
    motorUtilizado : MotorUtilizado