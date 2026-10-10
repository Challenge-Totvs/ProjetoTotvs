import { http } from "./http";
import type { ClienteDetalhe, ClienteResumo, Id, NovoClienteRequest } from "../types/api";

/** GET /api/clientes — vendedor: os próprios; gestor: os do escopo. */
export async function listarClientes(): Promise<ClienteResumo[]> {
  const { data } = await http.get<ClienteResumo[]>("/api/clientes");
  return data;
}

/** GET /api/clientes/{id} — página do cliente inteira. */
export async function buscarCliente(id: Id): Promise<ClienteDetalhe> {
  const { data } = await http.get<ClienteDetalhe>(`/api/clientes/${id}`);
  return data;
}

/** POST /api/clientes — cria o cliente com o primeiro contato. */
export async function criarCliente(dados: NovoClienteRequest): Promise<ClienteDetalhe> {
  const { data } = await http.post<ClienteDetalhe>("/api/clientes", dados);
  return data;
}
