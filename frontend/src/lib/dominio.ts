/* Listas fechadas e textos de exibição, iguais aos da demo e do handoff (apêndice A). */

import { CornerDownRight, Mail, MessageCircle, Phone, Users, type LucideIcon } from "lucide-react";
import type { Compromisso, Situacao, Tema, TipoMudanca, TipoTema } from "../types/api";
import { diasEntre, fmtData, fmtDiaSemana, hoje, paraData, relativo } from "./datas";

export const LIMITE_CARACTERES = 200000;
export const JANELAS = [14, 21, 30, 45, 60, 90];
export const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export const DOMINIOS_PESSOAIS = [
  "gmail.com",
  "hotmail.com",
  "outlook.com",
  "live.com",
  "yahoo.com",
  "yahoo.com.br",
  "icloud.com",
  "bol.com.br",
  "uol.com.br",
];

/** Lista fechada de padrões (a LLM escolhe desta lista). */
export const PADROES: Record<string, { nome: string; tipo: TipoTema }> = {
  suporte_insatisfacao: { nome: "Insatisfação com o suporte", tipo: "risco" },
  preco_objecao: { nome: "Objeção de preço", tipo: "risco" },
  prazo_implantacao: { nome: "Prazo de implantação", tipo: "risco" },
  concorrente_citado: { nome: "Concorrente citado", tipo: "risco" },
  cancelamento_citado: { nome: "Cancelamento citado", tipo: "risco" },
  adocao_resistencia: { nome: "Resistência da equipe", tipo: "risco" },
  fiscal_problema: { nome: "Problema no fechamento fiscal", tipo: "risco" },
  orcamento_restrito: { nome: "Orçamento restrito", tipo: "risco" },
  expansao_unidade: { nome: "Expansão para nova unidade", tipo: "oportunidade" },
  modulo_adicional: { nome: "Módulo adicional", tipo: "oportunidade" },
  integracao: { nome: "Integração com outro sistema", tipo: "oportunidade" },
  renovacao: { nome: "Renovação do contrato", tipo: "oportunidade" },
  upgrade_licencas: { nome: "Ampliação de licenças", tipo: "oportunidade" },
  treinamento: { nome: "Treinamento da equipe", tipo: "oportunidade" },
};

export const SEGMENTOS = [
  "Agronegócio",
  "Construção Civil",
  "Educação",
  "Hotelaria",
  "Indústria",
  "Logística",
  "Saúde",
  "Tecnologia",
  "Varejo",
];

export function rotuloTipoCliente(tipo: string | null): string {
  if (tipo === "ativo") return "Ativo";
  if (tipo === "prospect") return "Prospect";
  return "Sem tipo";
}

/** "Tratei fora da reunião": o que foi feito, por tipo do tema. */
export const ACOES_FORA: Record<TipoTema, [string, string][]> = {
  oportunidade: [
    ["proposta", "Proposta enviada"],
    ["demonstracao", "Demonstração agendada"],
    ["material", "Material técnico enviado"],
    ["telefone", "Retorno por telefone"],
    ["outra_area", "Encaminhada a outra área"],
    ["outro_o", "Outro"],
  ],
  risco: [
    ["suporte", "Encaminhado ao suporte"],
    ["retorno", "Retorno dado ao cliente"],
    ["condicao", "Condição comercial oferecida"],
    ["alinhamento", "Reunião de alinhamento marcada"],
    ["outro_r", "Outro"],
  ],
};

export const CANAIS: [string, string, LucideIcon][] = [
  ["email", "E-mail", Mail],
  ["telefone", "Telefone", Phone],
  ["whatsapp", "WhatsApp", MessageCircle],
  ["presencial", "Presencial", Users],
  ["outro", "Outro", CornerDownRight],
];

export const MOTIVOS_NAO_PROCEDE: [string, string][] = [
  ["nao_cliente", "Não era o cliente falando"],
  ["fora_contexto", "Fora de contexto"],
  ["tema_errado", "Tema errado"],
  ["outro", "Outro"],
];

export const MOTORES: Record<string, { nome: string; curto: string }> = {
  llm1: { nome: "LLM principal", curto: "LLM principal" },
  llm2: { nome: "LLM secundária", curto: "LLM secundária" },
  local: { nome: "Modelo local (contingência)", curto: "Modelo local" },
  regras: { nome: "Regras", curto: "Regras" },
};

export const ROTULO_SITUACAO: Record<Situacao, string> = {
  sem_retorno: "Sem retorno",
  oportunidade_perdida: "Oportunidade perdida",
  tratado_conversa: "Tratado na conversa",
  tratado_fora: "Tratado fora da reunião",
  fora_de_pauta: "Fora de pauta",
  sem_leitura: "Sem leitura de resposta",
  nao_procede: "Não procede",
};

export const ROTULO_MUDANCA: Record<TipoMudanca, string> = {
  novo_risco: "Novo risco",
  nova_oportunidade: "Nova oportunidade",
  novo_tema: "Novo tema, risco e oportunidade",
  tratado: "Tratado na conversa",
  voltou_sem_resposta: "Voltou e ficou sem resposta",
  de_novo_sem_resposta: "Citado de novo, ainda sem resposta",
  voltou: "Voltou a aparecer",
  virou_perdida: "Virou oportunidade perdida",
  tratado_fora: "Tratado fora da reunião",
  sem_leitura: "Citado, sem leitura de resposta",
};

export function nomeAcaoFora(acao: string): string {
  const a = [...ACOES_FORA.oportunidade, ...ACOES_FORA.risco].find(([k]) => k === acao);
  return a ? a[1] : "Ação registrada";
}

export function nomeCanal(canal: string): string {
  const c = CANAIS.find(([k]) => k === canal);
  return c ? c[1] : canal;
}

export function nomeMotivo(motivo: string | null): string {
  const m = MOTIVOS_NAO_PROCEDE.find(([k]) => k === motivo);
  return m ? m[1] : "Sem motivo informado";
}

/* ---------- Tema ---------- */

export const temRisco = (t: Tema) => t.tipos.includes("risco");
export const temOport = (t: Tema) => t.tipos.includes("oportunidade");
export const ultimaCitacao = (t: Tema) => t.citacoes[t.citacoes.length - 1];

export type EstadoGlifo = "aberto" | "tratado" | "indefinido";

export function estadoCitacao(tratado: boolean | null): EstadoGlifo {
  if (tratado === true) return "tratado";
  if (tratado === false) return "aberto";
  return "indefinido";
}

export function descreverCitacao(tipos: TipoTema[], tratado: boolean | null): string {
  const tipo =
    tipos.includes("risco") && tipos.includes("oportunidade")
      ? "Risco e oportunidade"
      : tipos.includes("risco")
        ? "Risco"
        : "Oportunidade";
  const est = tratado === true ? "respondido na reunião" : tratado === false ? "sem resposta" : "sem leitura de resposta";
  return `${tipo}, ${est}`;
}

/** Texto curto ao lado do tema nas listas: "sem resposta há 9 dias", "perde em 22 dias" etc. */
export function detalheAtencao(t: Tema): string {
  if (t.situacao === "oportunidade_perdida" && t.perdidaEm) return `perdida ${relativo(paraData(t.perdidaEm))}`;
  if (t.situacao === "sem_retorno" && temOport(t) && !temRisco(t))
    return t.venceEm === 1 ? "perde amanhã" : `perde em ${t.venceEm} dias`;
  if (t.situacao === "sem_retorno") {
    const d = t.diasUltimaCitacao;
    return `sem resposta ${d === 0 ? "desde hoje" : d === 1 ? "desde ontem" : `há ${d} dias`}`;
  }
  if (t.situacao === "sem_leitura") return "sem leitura de resposta";
  return relativo(paraData(t.ultimaAtividade));
}

/* ---------- Compromisso ---------- */

export function rotuloPrazo(cp: Compromisso): string {
  if (cp.estado === "cumprido") return cp.cumpridoEm ? `cumprido em ${fmtData(paraData(cp.cumpridoEm))}` : "cumprido";
  if (cp.estado === "sem_prazo" || !cp.prazo) return "sem prazo dito na reunião";
  const atraso = cp.atraso ?? diasEntre(paraData(cp.prazo), hoje());
  if (cp.estado === "vencido") return `venceu ${atraso === 1 ? "ontem" : `há ${atraso} dias`} (${fmtDiaSemana(paraData(cp.prazo))})`;
  if (cp.estado === "hoje") return "vence hoje";
  return `vence ${-atraso === 1 ? "amanhã" : `em ${-atraso} dias`} (${fmtDiaSemana(paraData(cp.prazo))})`;
}

/* ---------- Transcrição ---------- */

export interface TurnoLido {
  n: number;
  loc: number;
  texto: string;
}

/** Regra única de turnos (SDD 5.2). Aqui só alimenta os contadores ao vivo do formulário. */
export function lerTurnos(texto: string): TurnoLido[] {
  const linhas = String(texto || "").replace(/\r\n?/g, "\n").split("\n");
  const turnos: { loc: number; texto: string }[] = [];
  for (const l of linhas) {
    const m = l.match(/^\s*\[LOCUTOR\s*(\d+)\]\s*:?\s*(.*)$/i);
    if (m) turnos.push({ loc: Number(m[1]), texto: m[2].trim() });
    else if (l.trim() && turnos.length) turnos[turnos.length - 1].texto = `${turnos[turnos.length - 1].texto} ${l.trim()}`.trim();
  }
  return turnos.filter((t) => t.texto).map((t, i) => ({ ...t, n: i + 1 }));
}

/** "Locutor 2 · cliente, inferido" ou só "Locutor 2" sem papel. */
export function rotuloPapel(loc: number | null, papel: string | null | undefined): string {
  if (loc == null) return "Locutor";
  if (!papel) return `Locutor ${loc}`;
  return `Locutor ${loc} · ${papel}, inferido`;
}

/** Exemplo de pseudonimização mostrado em Configurações. */
export function pseudonimizar(texto: string, entidades: [string, string][]): string {
  const contagem: Record<string, number> = {};
  const mapa: Record<string, string> = {};
  for (const [termo, tipo] of entidades) {
    if (!mapa[termo]) {
      contagem[tipo] = (contagem[tipo] || 0) + 1;
      mapa[termo] = `[${tipo}_${contagem[tipo]}]`;
    }
  }
  let saida = texto;
  const ordenadas = [...entidades].sort((a, b) => b[0].length - a[0].length);
  for (const [termo] of ordenadas) {
    const re = new RegExp(`(?<![\\p{L}])${termo.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}(?![\\p{L}])`, "gu");
    saida = saida.replace(re, mapa[termo]);
  }
  return saida;
}
