export interface ItemAnalise {
    descricao: string
    trecho: string
}

export type SentimentoGeral = 'POSITIVO' | 'NEUTRO' | 'NEGATIVO'
export type MotorUtilizado = 'LLM_PRIMARIA' | 'LLM_SECUNDARIA' | 'MODELO_LOCAL' | 'REGEX_FALLBACK'

export interface ResultadoAnalise {
    pontosInteresse: ItemAnalise[]
    pontosDesinteresse: ItemAnalise[]
    oportunidadesVenda: ItemAnalise[]
    scoreEngajamento: number
    sentimentoGeral: SentimentoGeral
    recomendacaoProximosPassos: string | null
    motorUtilizado: MotorUtilizado
}