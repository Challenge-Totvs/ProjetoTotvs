import { http } from "./http";
import type { Id, Inicio } from "../types/api";

/** GET /api/inicio — o Início do vendedor logado, tudo pronto. */
export async function buscarInicio(): Promise<Inicio> {
  const { data } = await http.get<Inicio>("/api/inicio");
  return data;
}

/** GET /api/vendedores/{id}/inicio — a visão de um vendedor, para o gestor (só leitura). */
export async function buscarInicioDoVendedor(vendedorId: Id): Promise<Inicio> {
  const { data } = await http.get<Inicio>(`/api/vendedores/${vendedorId}/inicio`);
  return data;
}
