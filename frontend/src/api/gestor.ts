import { http } from "./http";
import type { Id, Notificacoes, PadraoAgregado, VendedorResumo } from "../types/api";

/** GET /api/notificacoes — pedidos de apoio do gestor (o sino). */
export async function listarNotificacoes(): Promise<Notificacoes> {
  const { data } = await http.get<Notificacoes>("/api/notificacoes");
  return data;
}

/** PATCH /api/notificacoes/{id} — marca o pedido como lido. */
export async function marcarNotificacaoLida(id: Id): Promise<void> {
  await http.patch(`/api/notificacoes/${id}`, { lida: true });
}

/**
 * GET /api/padroes/agregado — os padrões vistos entre os clientes do escopo.
 * tipoCliente: "todos" | "ativo" | "prospect" | "sem"; tipo: "todos" | "risco" | "oportunidade".
 */
export async function listarPadroesAgregados(tipoCliente = "todos", tipo = "todos"): Promise<PadraoAgregado[]> {
  const { data } = await http.get<PadraoAgregado[]>("/api/padroes/agregado", { params: { tipoCliente, tipo } });
  return data;
}

/** GET /api/vendedores — uma linha por vendedor do escopo, com os números da janela. */
export async function listarVendedores(): Promise<VendedorResumo[]> {
  const { data } = await http.get<VendedorResumo[]>("/api/vendedores");
  return data;
}
