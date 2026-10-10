/* Regras das facetas da lista de clientes do gestor (sem componentes, para o recarregamento rápido do Vite). */

import type { ClienteResumo, Indicadores } from "../../types/api";

/** Os quatro grupos de facetas. */
export type GrupoFaceta = "tipo" | "situacao" | "vendedor" | "segmento";

/** Valores marcados em cada grupo (vazio = grupo sem filtro). */
export type Facetas = Record<GrupoFaceta, string[]>;

export const FACETAS_VAZIAS: Facetas = { tipo: [], situacao: [], vendedor: [], segmento: [] };

/** Facetas de situação: chave, rótulo e o teste feito nos indicadores do cliente. */
export const FACETAS_SITUACAO: [string, string, (ind: Indicadores) => boolean][] = [
  ["risco_sem_retorno", "Com risco sem retorno", (ind) => ind.riscosSemRetorno > 0],
  ["oport_perdida", "Com oportunidade perdida", (ind) => ind.oportPerdidas > 0],
  ["recorrente", "Com tema recorrente", (ind) => ind.recorrentes > 0],
  ["sem_atencao", "Sem pontos de atenção", (ind) => !ind.riscosSemRetorno && !ind.oportPerdidas && !ind.oportSemRetorno],
];

/** O cliente passa no grupo com estes valores marcados? (basta passar em um deles) */
export function passaFaceta(c: ClienteResumo, grupo: GrupoFaceta, valores: string[]): boolean {
  if (grupo === "tipo") return valores.includes(c.tipo || "sem");
  if (grupo === "situacao") return valores.some((v) => FACETAS_SITUACAO.find((f) => f[0] === v)?.[2](c.indicadores));
  if (grupo === "vendedor") return valores.includes(String(c.vendedor.id));
  return valores.includes(c.segmento);
}

/** Um grupo da coluna: chave, título e as opções [valor, rótulo]. */
export type GrupoOpcoes = [GrupoFaceta, string, [string, string][]];
