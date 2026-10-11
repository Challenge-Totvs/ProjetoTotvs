from pydantic import BaseModel, Field
from enum import Enum


# --- Pedido v3 (contrato v3 §3). Campos desconhecidos são ignorados. Limites finos e enums: P1. ---

class Turno(BaseModel):
    n: int = Field(ge=1)
    locutor: int
    texto: str = Field(min_length=1)

class Contraexemplo(BaseModel):
    padrao: str
    texto: str
    motivo: str

class ItemContextoCliente(BaseModel):
    tipo: str
    texto: str
    origem: str
    data: str

class ItemGlossario(BaseModel):
    termo: str
    significa: str
    escopo: str

class CorrecaoAnterior(BaseModel):
    padrao: str
    textoOriginal: str
    correcao: str
    motivo: str

class PedidoAnalise(BaseModel):
    turnos: list[Turno] = Field(min_length=1)
    dataReuniao: str | None = None
    padroes: list[str] = []
    contraexemplos: list[Contraexemplo] = []
    contextoCliente: list[ItemContextoCliente] = []
    glossarioTime: list[ItemGlossario] = []
    correcoesAnteriores: list[CorrecaoAnterior] = []


# --- Contrato v1 (retirado). Ainda usado pelo orchestrator até P1/P2. ---

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