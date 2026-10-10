/* Início do vendedor: busca os dados prontos e entrega ao PainelInicio. */

import { buscarInicio } from "../../api/inicio";
import { PainelInicio } from "../../components/inicio/PainelInicio";
import { Carregando, ErroCarregar } from "../../components/ui/base";
import { useApp, useTrilha } from "../../context/AppContext";
import { useApi } from "../../hooks/useApi";

export default function InicioPage() {
  const app = useApp();
  useTrilha([{ l: "Início" }]);
  // app.versao muda depois de cada ação (ex.: marcar compromisso) e a tela recarrega.
  const { dados, erro, carregando, recarregar } = useApi(buscarInicio, [app.versao]);

  if (carregando && !dados) return <Carregando />;
  if (!dados) return <ErroCarregar mensagem={erro ?? "Não foi possível carregar o Início."} onTentar={() => void recarregar()} />;
  return <PainelInicio inicio={dados} />;
}
