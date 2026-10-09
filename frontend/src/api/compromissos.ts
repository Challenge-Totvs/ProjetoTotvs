import { http } from "./http";
import type { Compromisso, Id } from "../types/api";

/** PATCH /api/compromissos/{id} — marca ou desmarca como cumprido. */
export async function marcarCompromisso(id: Id, cumprido: boolean): Promise<Compromisso> {
  const { data } = await http.patch<Compromisso>(`/api/compromissos/${id}`, { cumprido });
  return data;
}
