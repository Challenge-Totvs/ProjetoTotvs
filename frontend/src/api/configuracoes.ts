import { http } from "./http";
import type { Configuracoes, StatusMotor } from "../types/api";

/** GET /api/configuracoes — janela de acompanhamento atual e as permitidas. */
export async function buscarConfiguracoes(): Promise<Configuracoes> {
  const { data } = await http.get<Configuracoes>("/api/configuracoes");
  return data;
}

/** PUT /api/configuracoes/janela — só gestor. */
export async function definirJanela(dias: number): Promise<Configuracoes> {
  const { data } = await http.put<Configuracoes>("/api/configuracoes/janela", { dias });
  return data;
}

/** GET /api/configuracoes/janela/previa?dias= — quantos temas mudam com outra janela. */
export async function previaJanela(dias: number): Promise<{ temasQueMudam: number }> {
  const { data } = await http.get<{ temasQueMudam: number }>("/api/configuracoes/janela/previa", { params: { dias } });
  return data;
}

/** GET /api/motores/status — estado de cada motor, para o banner e Configurações. */
export async function buscarStatusMotores(): Promise<StatusMotor[]> {
  const { data } = await http.get<StatusMotor[]>("/api/motores/status");
  return data;
}
