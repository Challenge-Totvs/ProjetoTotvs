import { http } from "./http";
import type { Id, Inicio, InicioSemanal } from "../types/api";

/**
 * GET /api/inicio — o Início do vendedor logado, tudo pronto.
 * janelaDias: quando informado, muda só esta visualização (não a janela configurada do time).
 */
export async function buscarInicio(janelaDias?: number): Promise<Inicio> {
  const { data } = await http.get<Inicio>("/api/inicio", { params: janelaDias ? { janelaDias } : undefined });
  return data;
}

/** GET /api/vendedores/{id}/inicio — a visão de um vendedor, para o gestor (só leitura). */
export async function buscarInicioDoVendedor(vendedorId: Id): Promise<Inicio> {
  const { data } = await http.get<Inicio>(`/api/vendedores/${vendedorId}/inicio`);
  return data;
}

/** GET /api/inicio/semanal — série semanal (realizadas, analisadas e engajamento médio) do vendedor logado. */
export async function buscarInicioSemanal(janelaDias?: number): Promise<InicioSemanal> {
  const { data } = await http.get<InicioSemanal>("/api/inicio/semanal", { params: janelaDias ? { janelaDias } : undefined });
  return data;
}
