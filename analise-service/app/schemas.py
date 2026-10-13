from enum import Enum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

# --- Listas fechadas (contrato v3 §6). Valor fora da lista derruba a análise no Java. ---

Padrao = Literal[
    "suporte_insatisfacao", "preco_objecao", "prazo_implantacao", "concorrente_citado",
    "cancelamento_citado", "adocao_resistencia", "fiscal_problema", "orcamento_restrito",
    "expansao_unidade", "modulo_adicional", "integracao", "renovacao", "upgrade_licencas", "treinamento",
]
Motor = Literal["llm1", "llm2", "local", "regras"]
Sentimento = Literal["positivo", "neutro", "negativo"]
Papel = Literal["vendedor", "cliente"]
TipoTema = Literal["risco", "oportunidade"]
RegraPrazo = Literal["sexta", "segunda", "sexta_semana_que_vem", "mesmo_dia", "mais2"]
TipoEventoConduta = Literal[
    "pagamento_confirmado_antes_de_dados", "desconto_fora_da_politica", "prazo_prometido_sem_confirmar_capacidade",
]
ErroTentativa = Literal[
    "nao_configurado", "timeout", "limite_requisicoes", "autenticacao", "truncado", "sem_resposta_estruturada",
    "schema_invalido", "recusa", "erro_provedor", "modelo_indisponivel", "entrada_sem_trechos", "erro_interno",
]
Aviso = Literal["contingencia_modelo_local", "contingencia_regras", "saida_parcial"]
MotivoDescarte = Literal[
    "evidencia_nao_localizada", "padrao_fora_da_lista", "evento_fora_da_lista", "trecho_curto", "trecho_longo",
]
OrigemDescarte = Literal["tema", "interesse", "compromisso", "eventoConduta"]
MotivoContraexemplo = Literal["nao_cliente", "fora_contexto", "tema_errado", "outro"]


# --- Pedido v3 (contrato v3 §3, limites §3.2). Campos desconhecidos são ignorados. ---

Texto500 = Field(max_length=500)


class Turno(BaseModel):
    n: int = Field(ge=1)
    locutor: int
    texto: str = Field(min_length=1, max_length=5000)

class Contraexemplo(BaseModel):
    padrao: str = Texto500
    texto: str = Texto500
    motivo: MotivoContraexemplo

class ItemContextoCliente(BaseModel):
    tipo: Literal["ajuste_manual"]
    texto: str = Texto500
    origem: Literal["vendedor", "gestor"]
    data: str = Texto500

class ItemGlossario(BaseModel):
    termo: str = Texto500
    significa: str = Texto500
    escopo: Literal["time"]

class CorrecaoAnterior(BaseModel):
    padrao: str = Texto500
    textoOriginal: str = Texto500
    correcao: Literal["nao_procede"]
    motivo: str = Texto500

class PedidoAnalise(BaseModel):
    turnos: list[Turno] = Field(min_length=1, max_length=3000)
    dataReuniao: str | None = None
    padroes: list[Padrao] = []
    contraexemplos: list[Contraexemplo] = Field(default=[], max_length=50)
    contextoCliente: list[ItemContextoCliente] = Field(default=[], max_length=50)
    glossarioTime: list[ItemGlossario] = Field(default=[], max_length=50)
    correcoesAnteriores: list[CorrecaoAnterior] = Field(default=[], max_length=50)

    @field_validator("turnos")
    @classmethod
    def _n_consecutivo(cls, turnos: list[Turno]) -> list[Turno]:
        if [t.n for t in turnos] != list(range(1, len(turnos) + 1)):
            raise ValueError("n deve ser consecutivo de 1 a N")
        return turnos


# --- Resposta v3 (contrato v3 §4): o que a API devolve ao Java ---

class Tentativa(BaseModel):
    motor: Motor
    ok: bool
    erro: ErroTentativa | None = None
    duracaoMs: int | None = None

class Interesse(BaseModel):
    texto: str
    turno: int = Field(ge=1)
    citacao: str

class Tema(BaseModel):
    padrao: Padrao
    titulo: str = Field(max_length=120)
    tipos: list[TipoTema] = Field(min_length=1, max_length=2)
    turno: int = Field(ge=1)
    turnoFim: int = Field(ge=1)
    tratado: bool | None
    texto: str = Field(min_length=10, max_length=600)
    confianca: float | None = Field(default=None, ge=0, le=1)

    @field_validator("tipos")
    @classmethod
    def _sem_repeticao(cls, tipos: list[str]) -> list[str]:
        if len(set(tipos)) != len(tipos):
            raise ValueError("tipos sem repetição")
        return tipos

class Compromisso(BaseModel):
    turno: int = Field(ge=1)
    texto: str
    regra: RegraPrazo | None

class EventoConduta(BaseModel):
    tipo: TipoEventoConduta
    turno: int = Field(ge=1)
    texto: str
    confianca: float = Field(ge=0, le=1)

class Descartado(BaseModel):
    texto: str
    motivo: MotivoDescarte
    origem: OrigemDescarte | None = None
    padrao: str | None = None

class AnaliseResponse(BaseModel):
    motor: Motor
    tentativas: list[Tentativa]
    score: int = Field(ge=0, le=100)
    sentimento: Sentimento
    papeis: dict[str, Papel] = {}
    resumo: str | None = Field(default=None, max_length=1500)
    interesse: list[Interesse] = []
    proximosPassos: list[str] = Field(default=[], max_length=5)
    temas: list[Tema] = []
    compromissos: list[Compromisso] = []
    sentimentoSerie: list[tuple[int, float]] = Field(default=[], max_length=60)
    descartados: list[Descartado] = []
    eventosConduta: list[EventoConduta] | None = None
    versaoContrato: Literal["v3"] | None = None
    avisos: list[Aviso] | None = None


# --- SaidaLLM: só o que a LLM preenche. Saída estruturada estrita: todos os campos
# obrigatórios, sem dict livre nem tupla. `padrao` e `tipo` são str para o código descartar
# (padrao_fora_da_lista / evento_fora_da_lista) em vez de a LLM falhar o schema. ---

class _Estrito(BaseModel):
    model_config = ConfigDict(extra="forbid")

class PapelLocutor(_Estrito):
    locutor: int
    papel: Papel

class InteresseLLM(_Estrito):
    texto: str
    turno: int
    citacao: str

class TemaLLM(_Estrito):
    padrao: str
    titulo: str
    tipos: list[TipoTema]
    turno: int
    tratado: bool | None
    texto: str
    confianca: float

class CompromissoLLM(_Estrito):
    turno: int
    texto: str
    regra: RegraPrazo | None

class PontoSentimento(_Estrito):
    turno: int
    valor: float

class EventoCondutaLLM(_Estrito):
    tipo: str
    turno: int
    texto: str
    confianca: float

class SaidaLLM(_Estrito):
    score: int
    sentimento: Sentimento
    papeis: list[PapelLocutor]
    resumo: str
    interesse: list[InteresseLLM]
    proximosPassos: list[str]
    temas: list[TemaLLM]
    compromissos: list[CompromissoLLM]
    sentimentoSerie: list[PontoSentimento]
    eventosConduta: list[EventoCondutaLLM]


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

class AnaliseResponseV1(BaseModel):
    pontosInteresse : list[ItemAnalise]
    pontosDesinteresse : list[ItemAnalise]
    oportunidadesVenda : list[ItemAnalise]
    scoreEngajamento : int
    sentimentoGeral : SentimentoGeral
    recomendacaoProximosPassos : str | None
    motorUtilizado : MotorUtilizado

# --- /similares (PROPOSTA, docs/contrato/similares.md): RAG-lite, sem API ---

TextoSimilares = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]


class ReferenciaSimilar(BaseModel):
    id: str = Field(min_length=1, max_length=100)
    texto: TextoSimilares


class PedidoSimilares(BaseModel):
    texto: TextoSimilares
    referencias: list[ReferenciaSimilar] = Field(default=[], max_length=200)
    topK: int = Field(default=3, ge=1, le=50)
    limiar: float | None = Field(default=None, ge=0, le=1)


class ItemSimilar(BaseModel):
    id: str
    score: float = Field(ge=0, le=1)


class RespostaSimilares(BaseModel):
    similares: list[ItemSimilar]
    versaoContrato: Literal["v3"] = "v3"
