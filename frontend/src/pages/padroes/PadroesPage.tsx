/* Padrões (gestor): o mesmo tema visto entre todos os clientes do time.
   A agregação vem pronta do backend; a tela filtra, lista e mostra o padrão
   selecionado (parâmetro :chave da URL) no painel lateral. */

import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { listarClientes } from "../../api/clientes";
import { listarPadroesAgregados } from "../../api/gestor";
import { InspetorPadrao } from "../../components/padroes/InspetorPadrao";
import { CabecalhoPagina, Carregando, ErroCarregar, Segmentado, Vazio } from "../../components/ui/base";
import { barraFerramentas, card, comPainel, conteudo, direita, tabela, td, th, tr } from "../../components/ui/classes";
import { Glifo } from "../../components/ui/glifos";
import { MiniHistograma } from "../../components/ui/graficos";
import { BotaoPainel, PainelLateral } from "../../components/ui/Sobrepostos";
import { useApp, useAtalhos, useTrilha } from "../../context/AppContext";
import { useApi } from "../../hooks/useApi";
import type { ClienteResumo, PadraoAgregado } from "../../types/api";
import { cx, pct, plural } from "../../lib/formato";
import { rotas } from "../../lib/rotas";

type FiltroCliente = "todos" | "ativo" | "prospect" | "sem";
type FiltroTipo = "todos" | "risco" | "oportunidade";

/** Célula numérica alinhada à direita. */
const tdNum = cx(td, direita, "tabular-nums");

/** Quantos clientes do time são do tipo ("sem" = sem tipo definido). */
const contarTipo = (clientes: ClienteResumo[], t: FiltroCliente) => clientes.filter((c) => (t === "sem" ? !c.tipo : c.tipo === t)).length;

export default function PadroesPage() {
  const app = useApp();
  const navigate = useNavigate();
  const { chave } = useParams();
  const [tipoCliente, setTipoCliente] = useState<FiltroCliente>("todos");
  const [tipo, setTipo] = useState<FiltroTipo>("todos");
  useTrilha([{ l: "Padrões" }]);

  // Padrões do recorte. Com filtro, busca também a lista sem filtro só para a contagem do rodapé.
  const padroes = useApi(async () => {
    const semFiltro = tipoCliente === "todos" && tipo === "todos";
    const [lista, todos] = await Promise.all([
      listarPadroesAgregados(tipoCliente, tipo),
      semFiltro ? Promise.resolve(null) : listarPadroesAgregados(),
    ]);
    return { lista, totalPadroes: (todos ?? lista).length };
  }, [tipoCliente, tipo, app.versao]);

  // Clientes do time, para as contagens do filtro de tipo de cliente.
  const clientes = useApi(listarClientes, [app.versao]);

  // Abrir a tela já com um padrão na URL (ou trocar de padrão) abre o painel.
  useEffect(() => {
    if (chave) app.setPainelAberto(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [chave]);

  const grupos: PadraoAgregado[] = padroes.dados?.lista ?? [];
  // O padrão selecionado só vale se estiver no recorte atual.
  const sel = grupos.find((g) => g.padrao === chave) || null;
  const idx = sel ? grupos.indexOf(sel) : -1;
  // Com o painel aberto, a tabela perde as colunas de taxa.
  const compacto = app.painelAberto && !!sel;

  /** Seleciona o padrão (troca a URL) e abre o painel. `trocar` não cria entrada no histórico. */
  const selecionar = (p: string, trocar = false) => {
    navigate(rotas.padrao(p), { replace: trocar });
    app.setPainelAberto(true);
  };

  useAtalhos(
    {
      j: () => grupos[idx + 1] && selecionar(grupos[idx + 1].padrao, true),
      k: () => idx > 0 && selecionar(grupos[idx - 1].padrao, true),
    },
    [
      [["J", "K"], "mover"],
      [["]"], "painel"],
    ],
  );

  // Primeira carga: espera ou erro. Recargas (troca de filtro, ações) mantêm a tela.
  if (padroes.carregando && !padroes.dados) return <Carregando />;
  if (!padroes.dados) return <ErroCarregar mensagem={padroes.erro || "Não foi possível carregar os padrões."} onTentar={() => void padroes.recarregar()} />;

  const listaClientes = clientes.dados ?? [];
  const n = (t: FiltroCliente) => (clientes.dados ? contarTipo(listaClientes, t) : undefined);

  return (
    <>
      <CabecalhoPagina
        titulo="Padrões"
        texto={`O mesmo tema visto entre todos os clientes do time. Ordenado pelos que mais ficam sem retorno, viram oportunidade perdida ou se repetem, na janela de ${app.janelaDias} dias.`}
        acoes={<BotaoPainel aberto={app.painelAberto} onClick={() => app.setPainelAberto(!app.painelAberto)} />}
      />
      <div className={comPainel}>
        <div className={conteudo}>
          {/* Filtros: tipo de cliente e riscos/oportunidades (cada troca busca de novo no backend) */}
          <div className={barraFerramentas}>
            <Segmentado<FiltroCliente>
              rotulo="Tipo de cliente"
              valor={tipoCliente}
              onChange={setTipoCliente}
              opcoes={[
                ["todos", "Todos os clientes"],
                ["ativo", "Ativos", n("ativo")],
                ["prospect", "Prospects", n("prospect")],
                ["sem", "Sem tipo", n("sem")],
              ]}
            />
            <Segmentado<FiltroTipo>
              rotulo="Riscos ou oportunidades"
              valor={tipo}
              onChange={setTipo}
              opcoes={[
                ["todos", "Todos"],
                ["risco", "Riscos"],
                ["oportunidade", "Oportunidades"],
              ]}
            />
          </div>

          {/* Tabela de padrões: clique seleciona e abre o painel */}
          <div className={cx(card, "overflow-x-auto")}>
            <table className={tabela}>
              <thead>
                <tr>
                  <th className={th}>Padrão</th>
                  <th className={cx(th, direita)}>Clientes</th>
                  <th className={cx(th, direita)}>Sem retorno</th>
                  <th className={cx(th, direita)}>Perdidas</th>
                  <th className={cx(th, direita)}>Recorrentes</th>
                  {!compacto && <th className={cx(th, direita)}>Tratados na conversa</th>}
                  {!compacto && <th className={cx(th, direita)}>Não procede</th>}
                  <th className={th}>Onde na conversa</th>
                </tr>
              </thead>
              <tbody>
                {grupos.map((g) => (
                  <tr key={g.padrao} className={tr} aria-selected={sel?.padrao === g.padrao} onClick={() => selecionar(g.padrao)}>
                    <td className={td}>
                      <span className="inline-flex items-center gap-2">
                        <Glifo tipo={g.tipo} tamanho={12} />
                        <span className="font-medium whitespace-nowrap text-ink">{g.nome}</span>
                      </span>
                    </td>
                    <td className={tdNum}>{g.clientes}</td>
                    {/* Sem retorno: vermelho no risco, âmbar na oportunidade */}
                    <td className={cx(tdNum, g.semRetorno ? (g.tipo === "risco" ? "font-semibold text-critico" : "font-semibold text-atencao") : "text-faint")}>{g.semRetorno}</td>
                    {/* Perdidas só fazem sentido para oportunidade; risco sem perdidas mostra "—" */}
                    <td className={cx(tdNum, g.perdidas ? "font-semibold text-atencao" : "text-faint")}>{g.tipo === "oportunidade" || g.perdidas ? g.perdidas : "—"}</td>
                    <td className={cx(tdNum, g.recorrentes ? "text-ink" : "text-faint")}>{g.recorrentes}</td>
                    {!compacto && <td className={tdNum}>{g.taxaConversa == null ? "—" : pct(g.taxaConversa)}</td>}
                    {!compacto && <td className={cx(tdNum, g.naoProcede ? "text-ink" : "text-faint")}>{g.naoProcede ? pct(g.taxaNaoProcede) : "0%"}</td>}
                    {/* Barras com raio de 2px como na demo (o MiniHistograma da base usa rounded-sm = 4px) */}
                    <td className={td}>
                      <MiniHistograma terco={g.terco} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {!grupos.length && <Vazio titulo="Nenhum padrão neste recorte" />}
          </div>

          {/* Rodapé: quantos padrões da lista fechada aparecem no time (sem filtro) */}
          <p className="mx-0.5 mt-2.5 mb-0 text-xs leading-[1.5] text-faint">
            {plural(padroes.dados.totalPadroes, "padrão", "padrões")} da lista fechada aparecem nos temas do time. A lista é normalizada pelo backend, e a LLM escolhe
            dela; padrão livre fragmentaria esta tela em centenas de grupos de um item.
          </p>
        </div>

        {/* Painel lateral com o padrão selecionado */}
        {app.painelAberto && sel && (
          <PainelLateral titulo="Padrão" onFechar={() => app.setPainelAberto(false)}>
            <InspetorPadrao g={sel} />
          </PainelLateral>
        )}
      </div>
    </>
  );
}
