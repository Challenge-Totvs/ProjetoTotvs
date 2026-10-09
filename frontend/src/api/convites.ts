import { http } from "./http";
import type { Convite } from "../types/api";

/** GET /api/convites — convites pendentes do time (gestor). */
export async function listarConvites(): Promise<Convite[]> {
  const { data } = await http.get<Convite[]>("/api/convites");
  return data;
}

/** POST /api/convites — convida como vendedor (gestor). */
export async function convidar(email: string): Promise<Convite> {
  const { data } = await http.post<Convite>("/api/convites", { email, perfil: "vendedor" });
  return data;
}
