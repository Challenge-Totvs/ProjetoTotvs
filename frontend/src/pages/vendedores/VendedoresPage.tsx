/* Vendedores (gestor): uma linha por vendedor do time, com os números da janela.
   Clicar na linha (ou Enter) abre a visão pessoal do vendedor, só para leitura. */

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { listarVendedores } from "../../api/gestor";
import { CabecalhoPagina, Carregando, ErroCarregar } from "../../components/ui/base";
import { card, direita, num, td, tabela, th } from "../../components/ui/classes";
import { LinhaVendedor } from "../../components/vendedores/LinhaVendedor";
import { useApp, useAtalhos, useTrilha } from "../../context/AppContext";
import { useApi } from "../../hooks/useApi";
import { cx, pct } from "../../lib/formato";
import { rotas } from "../../lib/rotas";
import type { VendedorResumo } from "../../types/api";

/** Mediana simples (lista pequena, poucos vendedores por time). */
function mediana(valores: number[]): number {
  if (valores.length === 0) return 0;
  const ord = [...valores].sort((a, b) => a - b);
  const meio = Math.floor(ord.length / 2);
  return ord.length % 2 ? ord[meio] : (ord[meio - 1] + ord[meio]) / 2;
}

/** Linha de referência "Mediana do time": metade do time fica de cada lado, por definição — não é meta. */
function LinhaMediana({ vendedores }: { vendedores: VendedorResumo[] }) {
  const col = (f: (v: VendedorResumo) => number) => mediana(vendedores.map(f));
  const taxas = vendedores.map((v) => v.metricas.taxaConversa).filter((t): t is number => t != null);
  const celNum = cx(td, direita, num, "text-ardosia");
  return (
    <tr className="border-b border-linha-forte bg-nevoa">
      <td className={cx(td, "font-medium text-ardosia")}>Mediana do time</td>
      <td className={celNum}>{col((v) => v.metricas.clientes)}</td>
      <td className={celNum}>{col((v) => v.metricas.realizadas)}</td>
      <td className={celNum}>{col((v) => v.metricas.riscosSemRetorno)}</td>
      <td className={celNum}>{col((v) => v.metricas.oportPerdidas)}</td>
      <td className={celNum}>{taxas.length ? pct(mediana(taxas)) : "—"}</td>
      <td className={celNum}>{col((v) => v.metricas.tratadosFora)}</td>
      <td className={celNum}>{col((v) => v.metricas.compromissosVencidos)}</td>
      <td className={td} />
    </tr>
  );
}

export default function VendedoresPage() {
  const app = useApp();
  const navigate = useNavigate();
  useTrilha([{ l: "Vendedores" }]);
  // O backend já devolve as métricas prontas; a janela muda o cálculo, então entra nas deps.
  const { dados, erro, carregando, recarregar } = useApi(listarVendedores, [app.versao, app.janelaDias]);
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
        texto={`Time ${app.usuario.time}. Abra a visão pessoal de cada vendedor, como ele vê, só para leitura. Números dos últimos ${app.janelaDias} dias.`}
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
            {linhas.length > 1 && <LinhaMediana vendedores={linhas} />}
            {linhas.map((v, i) => (
              <LinhaVendedor key={v.id} v={v} janelaDias={app.janelaDias} selecionada={i === sel} onAbrir={() => navigate(rotas.vendedor(v.id))} />
            ))}
          </tbody>
        </table>
      </div>
      <p className="mx-0.5 mt-2.5 mb-0 text-xs leading-normal text-faint">
        A mediana do time é uma referência, não uma meta: por definição, metade do time fica de cada lado dela. “Tratados na conversa” é a parcela dos temas
        citados na janela que foram respondidos na própria reunião. Depende do papel do locutor, que a LLM infere: é uma estimativa e não ordena nada.
      </p>
    </>
  );
}
