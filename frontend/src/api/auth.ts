import { http } from "./http";
import type { AvaliacaoDominio, LoginResponse, RegisterRequest, Usuario } from "../types/api";

/** POST /api/auth/login */
export async function login(email: string, senha: string): Promise<LoginResponse> {
  const { data } = await http.post<LoginResponse>("/api/auth/login", { email, senha });
  return data;
}

/** POST /api/auth/register */
export async function registrar(dados: RegisterRequest): Promise<LoginResponse> {
  const { data } = await http.post<LoginResponse>("/api/auth/register", dados);
  return data;
}

/** GET /api/auth/dominio?email= — dica ao vivo do domínio no cadastro. */
export async function avaliarDominio(email: string): Promise<AvaliacaoDominio> {
  const { data } = await http.get<AvaliacaoDominio>("/api/auth/dominio", { params: { email } });
  return data;
}

/** GET /api/me — quem está logado. */
export async function buscarMe(): Promise<Usuario> {
  const { data } = await http.get<Usuario>("/api/me");
  return data;
}
