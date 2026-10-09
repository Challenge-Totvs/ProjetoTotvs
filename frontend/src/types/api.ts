/* =====================================================================
   Contrato entre o frontend e o backend Java (SDD v3.0, seção 7).

   Regras gerais
   - Datas chegam como texto ISO 8601: "2026-10-06" para dia e
     "2026-10-06T10:00:00-03:00" para data e hora. Use paraData() de
     lib/datas.ts para converter (ela trata o dia sem fuso como dia local).
   - Os valores derivados (situação do tema, recorrência, indicadores,
     números do Início) vêm prontos do backend. A interface só exibe.
   - Os valores de enum são os mesmos da demo (minúsculos, com "_").
   ===================================================================== */

export type Id = number;
export type DataISO = string;

export type Perfil = "vendedor" | "gestor";
export type TipoTema = "risco" | "oportunidade";
export type TipoCliente = "ativo" | "prospect" | null;
export type Papel = "vendedor" | "cliente";
export type Motor = "llm1" | "llm2" | "local" | "regras";
export type Sentimento = "positivo" | "neutro" | "negativo";
export type StatusReuniao = "agendada" | "aguardando" | "analisada";

export type Situacao =
  | "sem_retorno"
  | "oportunidade_perdida"
  | "sem_leitura"
  | "tratado_conversa"
  | "tratado_fora"
  | "fora_de_pauta"
  | "nao_procede";

export type EstadoCompromisso = "cumprido" | "sem_prazo" | "vencido" | "hoje" | "no_prazo";

export type TipoMudanca =
  | "novo_risco"
  | "nova_oportunidade"
  | "novo_tema"
  | "tratado"
  | "voltou_sem_resposta"
  | "de_novo_sem_resposta"
  | "voltou"
  | "virou_perdida"
  | "tratado_fora"
  | "sem_leitura";

/* ---------- Erros ---------- */

/** Corpo de erro padrão do backend: { codigo, mensagem }. */
export interface ErroApi {
  codigo: string;
  mensagem: string;
}

/* ---------- Acesso ---------- */

export interface Usuario {
  id: Id;
  nome: string;
  email: string;
  perfil: Perfil;
  /** Nome do time, ex.: "Comercial". */
  time: string;
  /** Gestor do time, para o "Avisar gestor". Nulo se o time não tiver gestor. */
  gestor: { id: Id; nome: string } | null;
}

export interface LoginRequest {
  email: string;
  senha: string;
}

export interface LoginResponse {
  token: string;
  expiraEm?: DataISO;
  usuario?: Usuario;
}

export interface RegisterRequest {
  nome: string;
  email: string;
  senha: string;
}

/** GET /api/auth/dominio?email= — dica ao vivo do cadastro. */
export type AvaliacaoDominio =
  | { situacao: "ok"; organizacao: string; time: string }
  | { situacao: "pessoal" }
  | { situacao: "sem_organizacao" };

/* ---------- Clientes e contatos ---------- */

export interface Contato {
  id: Id;
  nome: string;
  cargo: string;
}

export interface VendedorRef {
  id: Id;
  nome: string;
}

/** Indicadores de um cliente (handoff, seção 8.11). */
export interface Indicadores {
  emPauta: number;
  riscosSemRetorno: number;
  riscosRecorrentes: number;
  oportPerdidas: number;
  oportSemRetorno: number;
  tratadosConversa: number;
  tratadosFora: number;
  foraDePauta: number;
  naoProcede: number;
  recorrentes: number;
  /** Peso de ordenação "Mais atenção". Nunca aparece na tela. */
  atencao: number;
}

/** Marca da régua da conversa: posição de um tema ou interesse num turno. */
export interface MarcaRegua {
  turno: number;
  tipo: TipoTema | "interesse";
  /** true respondido, false sem resposta, null sem leitura. Interesse usa false. */
  tratado: boolean | null;
  titulo: string;
  temaId: Id | null;
}

export interface ReuniaoResumo {
  id: Id;
  titulo: string;
  dataHora: DataISO;
  status: StatusReuniao;
}

/** Linha da lista de clientes (GET /api/clientes). */
export interface ClienteResumo {
  id: Id;
  nome: string;
  tipo: TipoCliente;
  segmento: string;
  vendedor: VendedorRef;
  contatos: Contato[];
  indicadores: Indicadores;
  /** Reunião mais recente que já aconteceu (não agendada). */
  ultimaReuniao: ReuniaoResumo | null;
  /** Reunião analisada mais recente, com as marcas da régua em miniatura. */
  ultimaAnalisada: (ReuniaoResumo & { turnos: number; marcas: MarcaRegua[] }) | null;
  /** Agendada mais próxima a partir de hoje. */
  proximaReuniao: ReuniaoResumo | null;
  /** Temas em pauta, já na ordem do mapa (handoff 8.11). */
  temasEmPauta: Tema[];
}

export interface NovoClienteRequest {
  nome: string;
  tipo: TipoCliente;
  segmento: string;
  contato: { nome: string; cargo: string };
}

/* ---------- Temas ---------- */

export interface TurnoContexto {
  turno: number;
  locutor: number;
  papel: Papel | null;
  texto: string;
}

export interface Citacao {
  reuniaoId: Id;
  reuniaoTitulo: string;
  reuniaoData: DataISO;
  turno: number;
  tratado: boolean | null;
  texto: string;
  /** A citação foi localizada no texto original. */
  conferida: boolean;
  locutor: number | null;
  papel: Papel | null;
  /** Turnos vizinhos (dois antes e dois depois), incluindo o citado. */
  contexto: TurnoContexto[] | null;
}

export interface RegistroFora {
  acao: string;
  canal: string;
  data: DataISO;
  observacao: string | null;
  por: VendedorRef;
}

export interface MarcacaoNaoProcede {
  motivo: string | null;
  por: VendedorRef;
  em: DataISO;
}

export interface AvisoGestor {
  id: Id;
  de: VendedorRef;
  mensagem: string | null;
  criadoEm: DataISO;
}

/** Tema acompanhado, com tudo o que a interface precisa já calculado. */
export interface Tema {
  id: Id;
  clienteId: Id;
  clienteNome: string;
  padrao: string;
  padraoNome: string;
  titulo: string;
  tipos: TipoTema[];
  situacao: Situacao;
  emPauta: boolean;
  atencao: boolean;
  recorrente: boolean;
  reunioesNaJanela: number;
  /** A última citação tem leitura de resposta (tratado diferente de nulo). */
  leitura: boolean;
  /** Dias desde a última citação. */
  diasUltimaCitacao: number;
  /** Data da última atividade (última citação ou registro fora). */
  ultimaAtividade: DataISO;
  /** Dias para virar oportunidade perdida (só "sem_retorno" com oportunidade). */
  venceEm: number | null;
  /** Data em que virou oportunidade perdida. */
  perdidaEm: DataISO | null;
  /** Frase do painel do tema (handoff 8.3). */
  explicacao: string;
  /** Citações em ordem cronológica (a última é a mais recente). */
  citacoes: Citacao[];
  registroFora: RegistroFora | null;
  naoProcede: MarcacaoNaoProcede | null;
  semelhanteNaoProcede: { texto: string; clienteNome: string } | null;
  anterior: { id: Id; titulo: string } | null;
  avisos: AvisoGestor[];
}

export interface TratadoForaRequest {
  acao: string;
  canal: string;
  data: DataISO;
  observacao: string;
}

/* ---------- Página do cliente ---------- */

export interface ReuniaoItem {
  id: Id;
  titulo: string;
  dataHora: DataISO;
  status: StatusReuniao;
  confirmada: boolean;
  contato: string;
  motor: Motor | null;
  score: number | null;
  turnos: number | null;
}

export interface ClienteDetalhe extends ClienteResumo {
  /** Todos os temas (em pauta e histórico), na ordem do mapa. */
  temas: Tema[];
  /** Reuniões do cliente, da mais antiga para a mais recente. */
  reunioes: ReuniaoItem[];
  compromissos: Compromisso[];
}

/* ---------- Compromissos ---------- */

export interface Compromisso {
  id: Id;
  clienteId: Id;
  clienteNome: string;
  reuniaoId: Id;
  turno: number;
  texto: string;
  prazo: DataISO | null;
  estado: EstadoCompromisso;
  /** Dias de atraso (positivo vencido, zero hoje, negativo no prazo). */
  atraso: number | null;
  cumprido: boolean;
  cumpridoEm: DataISO | null;
}

/* ---------- Início ---------- */

export interface Mudanca {
  id: string;
  tipo: TipoMudanca;
  data: DataISO;
  tema: Tema;
}

export interface AgendaItem {
  reuniaoId: Id;
  clienteId: Id;
  clienteNome: string;
  titulo: string;
  contato: string;
  dataHora: DataISO;
  confirmada: boolean;
}

export interface PendenteTranscricao {
  reuniaoId: Id;
  clienteId: Id;
  clienteNome: string;
  dataHora: DataISO;
}

/** Números do vendedor na janela (handoff 8.14). */
export interface MetricasVendedor {
  realizadas: number;
  analisadas: number;
  taxaConversa: number | null;
  tratadosConversa: number;
  comLeitura: number;
  tratadosFora: number;
  oportIdentificadas: number;
  oportTratadas: number;
  falaVendedor: number | null;
  riscosSemRetorno: number;
  oportPerdidas: number;
  compromissosVencidos: number;
  clientes: number;
}

/** GET /api/inicio e GET /api/vendedores/{id}/inicio. */
export interface Inicio {
  janelaDias: number;
  vendedor: VendedorRef;
  clientes: number;
  pendentes: PendenteTranscricao[];
  /** Riscos sem retorno, já ordenados. */
  riscos: Tema[];
  /** Oportunidades perdidas e depois as sem retorno, já ordenadas. */
  oportunidades: Tema[];
  /** Últimos 14 dias, mais recente primeiro. */
  mudancas: Mudanca[];
  compromissos: Compromisso[];
  /** Agendadas nos próximos 14 dias. */
  agenda: AgendaItem[];
  desempenho: MetricasVendedor;
}

/* ---------- Reunião ---------- */

export interface InteresseItem {
  texto: string;
  turno: number;
  citacao: string;
  conferida: boolean;
  /** Quem falou no turno da citação (pode faltar quando o motor não sabe). */
  locutor?: number | null;
  papel?: Papel | null;
}

export interface Descartado {
  texto: string;
  motivo: string;
}

export interface Analise {
  motor: Motor;
  score: number | null;
  sentimento: Sentimento | null;
  resumo: string | null;
  /** Locutor -> papel inferido. Nulo quando o motor não sabe quem falou. */
  papeis: Record<string, Papel> | null;
  interesse: InteresseItem[];
  proximosPassos: string[];
  /** Pares [turno, valor de -1 a 1]. */
  sentimentoSerie: [number, number][] | null;
  descartados: Descartado[];
}

export interface BlocoFala {
  palavras: number;
  papel: Papel | null;
  locutor: number;
  turno: number;
}

/** Métricas da conversa por volume de fala (handoff 8.13). */
export interface MetricasConversa {
  papeisInferidos: boolean;
  total: number;
  porLocutor: Record<string, number>;
  falaVendedor: number | null;
  maiorMonologo: BlocoFala;
  maiorFalaCliente: BlocoFala | null;
  trocasPorMin: number | null;
  perguntas: { vendedor: number; cliente: number } | null;
}

export interface TemaNaReuniao {
  tema: Tema;
  /** A citação deste tema nesta reunião. */
  citacao: Citacao;
}

export interface ReuniaoDetalhe {
  id: Id;
  titulo: string;
  dataHora: DataISO;
  duracaoMin: number | null;
  status: StatusReuniao;
  confirmada: boolean;
  contato: string;
  turnos: number | null;
  cliente: { id: Id; nome: string; vendedor: VendedorRef };
  analise: Analise | null;
  /** Temas citados nesta reunião (sem os marcados como não procede), por turno. */
  temas: TemaNaReuniao[];
  compromissos: Compromisso[];
  metricas: MetricasConversa | null;
  /** Há transcrição gravada para esta reunião. */
  temTranscricao: boolean;
}

export interface TurnoTranscricao {
  n: number;
  locutor: number;
  papel: Papel | null;
  texto: string;
}

/* ---------- Nova transcrição ---------- */

export interface NovaReuniaoRequest {
  clienteId: Id;
  titulo: string;
  dataHora: DataISO;
  duracaoMin: number | null;
  contatoId: Id | null;
  status: "aguardando" | "agendada";
}

export interface EnviarTranscricaoRequest {
  conteudo: string;
  formatoOrigem: "COLADO" | "ARQUIVO";
  nomeArquivo: string | null;
}

export interface EnviarTranscricaoResponse {
  transcricaoId: Id;
  caracteres: number;
  turnos: number;
  locutores: number;
}

export interface TentativaMotor {
  motor: Motor;
  ok: boolean;
}

export interface ResultadoAnalisarResponse {
  reuniaoId: Id;
  motor: Motor;
  tentativas: TentativaMotor[];
  novos: number;
  atualizados: number;
  compromissos: number;
}

/* ---------- Configurações e motores ---------- */

export interface StatusMotor {
  motor: Motor;
  ok: boolean;
}

export interface Configuracoes {
  janelaDias: number;
  janelasPermitidas: number[];
}

export interface Convite {
  email: string;
  perfil: Perfil;
  criadoEm: DataISO;
}
