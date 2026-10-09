/* Etapas da tela de andamento da análise (mesmos rótulos da demo). */

import type { Motor } from "../../types/api";

export type EstadoEtapa = "pendente" | "rodando" | "ok" | "falhou";

/** Uma linha da lista de andamento. `falha` aparece embaixo quando a etapa falha. */
export interface Etapa {
  id: string;
  rotulo: string;
  estado: EstadoEtapa;
  falha?: string;
}

/** Rótulo da etapa de cada motor da cadeia (mesmos textos da demo). */
export const ROTULO_MOTOR: Record<Motor, string> = {
  llm1: "Analisando com a LLM principal",
  llm2: "Analisando com a LLM secundária",
  local: "Analisando com o modelo local (contingência)",
  regras: "Analisando com as regras",
};

/** Mensagem embaixo da etapa quando o motor não respondeu. */
export const FALHA_MOTOR: Record<Motor, string> = {
  llm1: "Sem resposta da LLM principal. Seguindo para a próxima.",
  llm2: "Sem resposta da LLM secundária. Seguindo para o modelo local.",
  local: "Sem resposta do modelo local. Seguindo para as regras.",
  regras: "As regras não conseguiram analisar o texto.",
};

/** Etapas no começo do envio: tudo pendente; a LLM principal é a que roda durante a espera. */
export function etapasIniciais(): Etapa[] {
  return [
    { id: "pseudo", rotulo: "Pseudonimizando nomes de pessoas, empresas e lugares", estado: "pendente" },
    { id: "llm1", rotulo: ROTULO_MOTOR.llm1, estado: "pendente" },
    { id: "verif", rotulo: "Conferindo cada citação no texto original", estado: "pendente" },
    { id: "temas", rotulo: "Atualizando os temas do cliente", estado: "pendente" },
  ];
}
