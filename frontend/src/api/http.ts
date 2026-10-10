import axios, { AxiosError } from "axios";
import type { ErroApi } from "../types/api";

/** Chave do token no localStorage. */
export const TOKEN_KEY = "insightcall_token";
/** Marca deixada quando a sessão expira, para o login mostrar o aviso. */
export const SESSAO_EXPIRADA_KEY = "insightcall_sessao_expirada";

/** Cliente HTTP do backend Java. A URL vem de VITE_API_URL (padrão: localhost:8080). */
export const http = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "http://localhost:8080",
});

// Antes de cada requisição: coloca o token no cabeçalho Authorization.
http.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY);
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Depois de cada resposta: 401 com token salvo significa sessão vencida.
http.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    const url = error.config?.url ?? "";
    const ehLogin = url.includes("/api/auth/");
    if (error.response?.status === 401 && !ehLogin && localStorage.getItem(TOKEN_KEY)) {
      localStorage.removeItem(TOKEN_KEY);
      sessionStorage.setItem(SESSAO_EXPIRADA_KEY, "1");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  },
);

/** Extrai a mensagem de erro do backend ({ codigo, mensagem }) ou devolve um texto padrão. */
export function mensagemDeErro(erro: unknown, padrao = "Não foi possível concluir. Tente de novo."): string {
  const e = erro as AxiosError<Partial<ErroApi> | string>;
  const corpo = e?.response?.data;
  if (typeof corpo === "string" && corpo.trim()) return corpo;
  if (corpo && typeof corpo === "object" && corpo.mensagem) return corpo.mensagem;
  if (e?.code === "ERR_NETWORK") return "Sem conexão com o servidor. Confira se o backend está no ar.";
  return padrao;
}

/** Código do erro do backend (ex.: "email_em_uso") e o status HTTP. */
export function infoErro(erro: unknown): { status: number | null; codigo: string | null } {
  const e = erro as AxiosError<Partial<ErroApi>>;
  const corpo = e?.response?.data;
  return {
    status: e?.response?.status ?? null,
    codigo: corpo && typeof corpo === "object" && corpo.codigo ? corpo.codigo : null,
  };
}
