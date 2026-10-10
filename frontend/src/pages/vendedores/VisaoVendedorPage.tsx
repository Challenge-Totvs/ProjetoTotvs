/* Visão do vendedor (gestor): o mesmo Início que o vendedor vê, só para leitura. */

import { useParams } from "react-router-dom";
import { buscarInicioDoVendedor } from "../../api/inicio";
import { PainelInicio } from "../../components/inicio/PainelInicio";
import { Carregando, ErroCarregar } from "../../components/ui/base";
import { useApp, useTrilha } from "../../context/AppContext";
import { useApi } from "../../hooks/useApi";
import { rotas } from "../../lib/rotas";

export default function VisaoVendedorPage() {
  const app = useApp();
  const { id: idUrl } = useParams();
  const id = Number(idUrl);
  // Busca o Início desse vendedor; troca de vendedor (id) ou ação (versao) busca de novo.
  const { dados, erro, carregando, recarregar } = useApi(() => buscarInicioDoVendedor(id), [id, app.versao]);
  // Ao trocar de vendedor, ignora os dados do anterior até os novos chegarem.
  const inicio = dados && dados.vendedor.id === id ? dados : null;
  useTrilha([{ l: "Vendedores", para: rotas.vendedores }, { l: inicio?.vendedor.nome ?? "" }]);

  if (carregando && !inicio) return <Carregando />;
  if (!inicio) return <ErroCarregar mensagem={erro ?? "Não foi possível carregar a visão do vendedor."} onTentar={() => void recarregar()} />;
  return <PainelInicio inicio={inicio} somenteLeitura nomeVendedor={inicio.vendedor.nome} />;
}
