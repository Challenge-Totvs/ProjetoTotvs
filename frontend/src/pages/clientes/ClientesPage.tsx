/* Lista de clientes: busca os clientes do usuário e mostra a tela do perfil. */

import { listarClientes } from "../../api/clientes";
import { ClientesVendedor } from "../../components/clientes/ClientesVendedor";
import { Carregando, ErroCarregar } from "../../components/ui/base";
import { useApp, useTrilha } from "../../context/AppContext";
import { useApi } from "../../hooks/useApi";

export default function ClientesPage() {
  const app = useApp();
  // Recarrega a lista depois de cada ação (app.versao muda).
  const { dados, erro, carregando, recarregar } = useApi(listarClientes, [app.versao]);
  useTrilha([{ l: "Clientes" }]);

  // Primeira carga: espera ou erro. Recargas mantêm a tela como está.
  if (carregando && !dados) return <Carregando />;
  if (!dados) return <ErroCarregar mensagem={erro || "Não foi possível carregar os clientes."} onTentar={() => void recarregar()} />;

  if (app.gestor) {
    // Etapa 2: tela do gestor com facetas e agrupamento
    return <ClientesVendedor clientes={dados} />;
  }
  return <ClientesVendedor clientes={dados} />;
}
