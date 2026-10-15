/* Vendedores (gestor): uma linha por vendedor do time, com os números da janela.
   Clicar na linha (ou Enter) abre a visão pessoal do vendedor, só para leitura. */

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { listarVendedores } from "../../api/gestor";
import { CabecalhoPagina, Carregando, ErroCarregar, Segmentado } from "../../components/ui/base";
import { card, direita, tabela, th } from "../../components/ui/classes";
import { LinhaVendedor } from "../../components/vendedores/LinhaVendedor";
import { useApp, useAtalhos, useTrilha } from "../../context/AppContext";
import { useApi } from "../../hooks/useApi";
import { useJanelaVisao } from "../../hooks/useJanelaVisao";
import { cx } from "../../lib/formato";
import { rotas } from "../../lib/rotas";

/** Visões de 30/60/90 dias: muda só o que a tela mostra, não a janela configurada do time. */
type JanelaVisao = "30" | "60" | "90";
const OPCOES_JANELA: [JanelaVisao, string][] = [
  ["30", "30 dias"],
  ["60", "60 dias"],
  ["90", "90 dias"],
];

export default function VendedoresPage() {
  const app = useApp();
  const navigate = useNavigate();
  useTrilha([{ l: "Vendedores" }]);
  const [janela, setJanela] = useJanelaVisao(app.janelaDias);
  // O backend já devolve as métricas prontas; a janela muda o cálculo, então entra nas deps.
  const { dados, erro, carregando, recarregar } = useApi(() => listarVendedores(janela), [app.versao, janela]);
  const linhas = dados ?? [];
  // Linha selecionada pelo teclado (J/K), destacada na tabela.
  const [sel, setSel] = useState(0);

  useAtalhos(
    {
      j: () => setSel((s) => Math.min(linhas.length - 1, s + 1)),
      k: () => setSel((s) => Math.max(0, s - 1)),
      Enter: () => linhas[sel] && navigate(rotas.vendedor(linhas[sel].id)),
    },
    [
      [["J", "K"], "mover"],
      [["Enter"], "abrir visão"],
    ],
  );

  if (carregando && !dados) return <Carregando />;
  if (!dados) return <ErroCarregar mensagem={erro ?? "Não foi possível carregar os vendedores."} onTentar={() => void recarregar()} />;

  return (
    <>
      <CabecalhoPagina
        titulo="Vendedores"
        texto={`Time ${app.usuario.time}. Abra a visão pessoal de cada vendedor, como ele vê, só para leitura. Números dos últimos ${janela} dias.`}
        acoes={<Segmentado rotulo="Janela" opcoes={OPCOES_JANELA} valor={String(janela) as JanelaVisao} onChange={(v) => setJanela(Number(v))} />}
      />
      <div className={cx(card, "overflow-x-auto")}>
        <table className={tabela}>
          <thead>
            <tr>
              <th className={th}>Vendedor</th>
              <th className={cx(th, direita)}>Clientes</th>
              <th className={cx(th, direita)}>Reuniões</th>
              <th className={cx(th, direita)}>Riscos sem retorno</th>
              <th className={cx(th, direita)}>Oport. perdidas</th>
              <th className={cx(th, direita)}>Tratados na conversa</th>
              <th className={cx(th, direita)}>Tratados fora</th>
              <th className={cx(th, direita)}>Compromissos vencidos</th>
              <th className={th} />
            </tr>
          </thead>
          <tbody>
            {linhas.map((v, i) => (
              <LinhaVendedor key={v.id} v={v} selecionada={i === sel} onAbrir={() => navigate(rotas.vendedor(v.id))} />
            ))}
          </tbody>
        </table>
      </div>
      <p className="mx-0.5 mt-2.5 mb-0 text-xs leading-normal text-faint">
        “Tratados na conversa” é a parcela dos temas citados na janela que foram respondidos na própria reunião. Depende do papel do locutor, que a LLM
        infere: é uma estimativa e não ordena nada.
      </p>
    </>
  );
}
