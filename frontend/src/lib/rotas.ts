/* Endereços das telas, num lugar só (SDD 9.3). */

import type { Id } from "../types/api";

export const rotas = {
  login: "/login",
  cadastro: "/cadastro",
  inicio: "/inicio",
  clientes: "/clientes",
  configuracoes: "/configuracoes",
  padroes: "/padroes",
  vendedores: "/vendedores",

  /** Página do cliente; com `temaId`, abre já com o tema selecionado. */
  cliente: (id: Id, temaId?: Id | null) => (temaId ? `/clientes/${id}?tema=${temaId}` : `/clientes/${id}`),

  /** Página da reunião; com `turno`, rola até o turno e o destaca. */
  reuniao: (id: Id, turno?: number | null) => (turno ? `/reunioes/${id}?turno=${turno}` : `/reunioes/${id}`),

  /** Nova transcrição, opcionalmente com cliente e reunião já escolhidos. */
  nova: (p: { clienteId?: Id | null; reuniaoId?: Id | null } = {}) => {
    const q = new URLSearchParams();
    if (p.clienteId) q.set("cliente", String(p.clienteId));
    if (p.reuniaoId) q.set("reuniao", String(p.reuniaoId));
    const s = q.toString();
    return s ? `/transcricoes/nova?${s}` : "/transcricoes/nova";
  },

  padrao: (chave: string) => `/padroes/${chave}`,
  vendedor: (id: Id) => `/vendedores/${id}`,
};

/** Tela inicial de cada perfil. */
export const inicialDoPerfil = (perfil: "vendedor" | "gestor") => (perfil === "gestor" ? rotas.clientes : rotas.inicio);
