import { http } from "./http";
import type { Convite, ConviteDetalhe, LoginResponse } from "../types/api";

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

/** GET /api/convites/{token} — público: dados do convite. */
export async function buscarConvite(token: string): Promise<ConviteDetalhe> {
  const { data } = await http.get<ConviteDetalhe>(`/api/convites/${token}`);
  return data;
}

/**
 * POST /api/convites/{token}/aceitar — público: cria o acesso e já entra.
 * Erros esperados: 404 (convite não existe), 409 `convite_aceito` (já usado), 410 `convite_expirado`.
 */
export async function aceitarConvite(token: string, nome: string, senha: string): Promise<LoginResponse> {
  const { data } = await http.post<LoginResponse>(`/api/convites/${token}/aceitar`, { nome, senha });
  return data;
}
