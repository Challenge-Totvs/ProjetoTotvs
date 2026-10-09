/* Sessão: guarda o token e o usuário logado (GET /api/me). */

import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import * as authApi from "../api/auth";
import { SESSAO_EXPIRADA_KEY, TOKEN_KEY } from "../api/http";
import type { RegisterRequest, Usuario } from "../types/api";

interface AuthContextData {
  usuario: Usuario | null;
  /** true enquanto confere o token salvo, na abertura da aplicação. */
  carregando: boolean;
  entrar: (email: string, senha: string) => Promise<Usuario>;
  cadastrar: (dados: RegisterRequest) => Promise<Usuario>;
  sair: () => void;
}

const AuthContext = createContext<AuthContextData | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [usuario, setUsuario] = useState<Usuario | null>(null);
  const [carregando, setCarregando] = useState(() => !!localStorage.getItem(TOKEN_KEY));

  // Ao abrir a aplicação com um token salvo, busca quem é o usuário.
  useEffect(() => {
    if (!localStorage.getItem(TOKEN_KEY)) return;
    authApi
      .buscarMe()
      .then(setUsuario)
      .catch(() => localStorage.removeItem(TOKEN_KEY))
      .finally(() => setCarregando(false));
  }, []);

  /** Grava o token e carrega o usuário (usa o que veio no login, se veio). */
  const iniciarSessao = useCallback(async (token: string, veio?: Usuario) => {
    localStorage.setItem(TOKEN_KEY, token);
    sessionStorage.removeItem(SESSAO_EXPIRADA_KEY);
    const u = veio ?? (await authApi.buscarMe());
    setUsuario(u);
    return u;
  }, []);

  const entrar = useCallback(
    async (email: string, senha: string) => {
      const resp = await authApi.login(email, senha);
      return iniciarSessao(resp.token, resp.usuario);
    },
    [iniciarSessao],
  );

  const cadastrar = useCallback(
    async (dados: RegisterRequest) => {
      const resp = await authApi.registrar(dados);
      if (resp?.token) return iniciarSessao(resp.token, resp.usuario);
      // Backend que ainda não devolve token no cadastro: entra com login logo em seguida.
      return entrar(dados.email, dados.senha);
    },
    [iniciarSessao, entrar],
  );

  const sair = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    setUsuario(null);
  }, []);

  return <AuthContext.Provider value={{ usuario, carregando, entrar, cadastrar, sair }}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth deve ser usado dentro de AuthProvider");
  return ctx;
}
