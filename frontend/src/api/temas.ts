import { http } from "./http";
import type { Id, Tema, TratadoForaRequest } from "../types/api";

/** POST /api/temas/{id}/tratado-fora — registra "Tratei fora da reunião". */
export async function registrarFora(temaId: Id, dados: TratadoForaRequest): Promise<Tema> {
  const { data } = await http.post<Tema>(`/api/temas/${temaId}/tratado-fora`, dados);
  return data;
}

/** DELETE /api/temas/{id}/tratado-fora — remove o registro vigente. */
export async function removerFora(temaId: Id): Promise<Tema> {
  const { data } = await http.delete<Tema>(`/api/temas/${temaId}/tratado-fora`);
  return data;
}

/** POST /api/temas/{id}/nao-procede — marca como não procede, com motivo opcional. */
export async function marcarNaoProcede(temaId: Id, motivo: string | null): Promise<Tema> {
  const { data } = await http.post<Tema>(`/api/temas/${temaId}/nao-procede`, { motivo });
  return data;
}

/** DELETE /api/temas/{id}/nao-procede — desfaz o "não procede". */
export async function desfazerNaoProcede(temaId: Id): Promise<Tema> {
  const { data } = await http.delete<Tema>(`/api/temas/${temaId}/nao-procede`);
  return data;
}

/** POST /api/temas/{id}/avisos — "Avisar gestor". */
export async function avisarGestor(temaId: Id, mensagem: string): Promise<{ id: Id }> {
  const { data } = await http.post<{ id: Id }>(`/api/temas/${temaId}/avisos`, { mensagem });
  return data;
}

/** DELETE /api/avisos/{id} — desfaz o aviso enquanto não foi lido. */
export async function desfazerAviso(avisoId: Id): Promise<void> {
  await http.delete(`/api/avisos/${avisoId}`);
}
