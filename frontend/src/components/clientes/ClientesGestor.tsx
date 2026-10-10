/* Clientes do time (gestor): facetas, busca, agrupamento, tabela e prévia no painel lateral. */

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ChevronDown, Search } from "lucide-react";
import type { ClienteResumo } from "../../types/api";
import { useApp, useAtalhos } from "../../context/AppContext";
import { rotuloTipoCliente } from "../../lib/dominio";
import { cx, normalizar, plural } from "../../lib/formato";
import { rotas } from "../../lib/rotas";
import { CabecalhoPagina, Vazio } from "../ui/base";
import { barraFerramentas, btn, busca as classeBusca, card, comPainel, conteudo, select, tabela, td, th, tr } from "../ui/classes";
import { ChipsTemas, ChipTipoCliente } from "../ui/glifos";
import { BotaoPainel, PainelLateral } from "../ui/Sobrepostos";
import { CelulaCliente, CelulaUltimaReuniao, TdIndicadores, ThIndicadores } from "./Celulas";
import { FACETAS_SITUACAO, FACETAS_VAZIAS, passaFaceta, type Facetas, type GrupoFaceta, type GrupoOpcoes } from "./facetas";
import { FacetasClientes } from "./FacetasClientes";
import { PreviaCliente } from "./PreviaCliente";

type Agrupar = "nenhum" | "vendedor" | "segmento" | "tipo";

/** Um bloco da tabela: o nome do grupo ("" sem agrupamento) e os clientes dele. */
interface Bloco {
  chave: string;
  itens: ClienteResumo[];
}

export function ClientesGestor({ clientes: todos }: { clientes: ClienteResumo[] }) {
  const app = useApp();
  const navigate = useNavigate();
  const [busca, setBusca] = useState("");
  const [facetas, setFacetas] = useState<Facetas>(FACETAS_VAZIAS);
  const [agrupar, setAgrupar] = useState<Agrupar>("nenhum");
  // Grupos recolhidos (pelo nome do grupo).
  const [fechados, setFechados] = useState<Record<string, boolean>>({});
  const [selId, setSelId] = useState<number | null>(null);

  // Busca sem acento em nome, contatos, segmento e vendedor.
  const termo = normalizar(busca.trim());
  const passaBusca = (c: ClienteResumo) =>
    !termo || normalizar(`${c.nome} ${c.contatos.map((x) => x.nome).join(" ")} ${c.segmento} ${c.vendedor.nome}`).includes(termo);
  // Passa na busca e em todos os grupos marcados (`exceto` ignora um grupo, para contar as opções dele).
  const passa = (c: ClienteResumo, exceto?: GrupoFaceta) =>
    passaBusca(c) && (Object.entries(facetas) as [GrupoFaceta, string[]][]).every(([g, vs]) => g === exceto || !vs.length || passaFaceta(c, g, vs));

  // Clientes filtrados, os que pedem mais atenção primeiro.
  const filtrados = todos
    .filter((c) => passa(c))
    .sort((a, b) => b.indicadores.atencao - a.indicadores.atencao || a.nome.localeCompare(b.nome));
  const contar = (grupo: GrupoFaceta, valor: string) => todos.filter((c) => passa(c, grupo) && passaFaceta(c, grupo, [valor])).length;
  const alternar = (grupo: GrupoFaceta, valor: string) =>
    setFacetas((f) => ({ ...f, [grupo]: f[grupo].includes(valor) ? f[grupo].filter((v) => v !== valor) : [...f[grupo], valor] }));
  const limpar = () => {
    setFacetas(FACETAS_VAZIAS);
    setBusca("");
  };
  const algumFiltro = !!busca.trim() || Object.values(facetas).some((v) => v.length);

  // Opções das facetas: vendedores na ordem em que aparecem, segmentos em ordem alfabética.
  const vendedores = new Map<string, string>();
  for (const c of todos) if (!vendedores.has(String(c.vendedor.id))) vendedores.set(String(c.vendedor.id), c.vendedor.nome);
  const segmentos = Array.from(new Set(todos.map((c) => c.segmento))).sort();
  const grupos: GrupoOpcoes[] = [
    ["tipo", "Tipo", [["ativo", "Ativo"], ["prospect", "Prospect"], ["sem", "Sem tipo"]]],
    ["situacao", "Situação", FACETAS_SITUACAO.map(([k, l]): [string, string] => [k, l])],
    ["vendedor", "Vendedor", Array.from(vendedores)],
    ["segmento", "Segmento", segmentos.map((s): [string, string] => [s, s])],
  ];

  // Monta os blocos da tabela: um só sem agrupamento, ou um por grupo em ordem alfabética.
  const chaveGrupo = (c: ClienteResumo) =>
    agrupar === "vendedor" ? c.vendedor.nome : agrupar === "segmento" ? c.segmento : agrupar === "tipo" ? rotuloTipoCliente(c.tipo) : "";
  const blocos: Bloco[] = [];
  if (agrupar === "nenhum") blocos.push({ chave: "", itens: filtrados });
  else {
    const mapa: Record<string, ClienteResumo[]> = {};
    for (const c of filtrados) (mapa[chaveGrupo(c)] ||= []).push(c);
    Object.keys(mapa)
      .sort()
      .forEach((k) => blocos.push({ chave: k, itens: mapa[k] }));
  }

  // Só as linhas visíveis (fora dos grupos recolhidos) entram na seleção e no J/K.
  const visiveis = blocos.flatMap((b) => (fechados[b.chave] ? [] : b.itens));
  const selecionado = visiveis.find((c) => c.id === selId) || null;
  const idx = selecionado ? visiveis.indexOf(selecionado) : -1;
  // Com o painel aberto, a tabela fica só com Cliente, Padrões e os dois números.
  const compacto = app.painelAberto && !!selecionado;
  const nColunas = compacto ? 4 : 7;

  const abrir = (c: ClienteResumo) => navigate(rotas.cliente(c.id));
  // Selecionar uma linha já abre o painel com a prévia.
  const selecionar = (id: number) => {
    setSelId(id);
    app.setPainelAberto(true);
  };

  useAtalhos(
    {
      j: () => visiveis[idx + 1] && selecionar(visiveis[idx + 1].id),
      k: () => idx > 0 && selecionar(visiveis[idx - 1].id),
      Enter: () => selecionado && abrir(selecionado),
    },
    [
      [["J", "K"], "mover"],
      [["Enter"], "abrir cliente"],
      [["]"], "painel"],
    ],
  );

  return (
    <>
      <CabecalhoPagina
        titulo="Clientes"
        texto="Os clientes do time e os padrões que se repetem no contexto de cada um. Reuniões soltas não aparecem aqui: do cliente se chega à reunião e à citação."
        acoes={
          <>
            <label className="inline-flex items-center gap-1.5 text-[12.5px] text-ardosia">
              Agrupar por
              <select className={select()} value={agrupar} onChange={(e) => setAgrupar(e.target.value as Agrupar)}>
                <option value="nenhum">Nenhum</option>
                <option value="vendedor">Vendedor</option>
                <option value="segmento">Segmento</option>
                <option value="tipo">Tipo</option>
              </select>
            </label>
            <BotaoPainel aberto={app.painelAberto} onClick={() => app.setPainelAberto(!app.painelAberto)} />
          </>
        }
      />
      <div className={comPainel}>
        {/* Coluna de facetas à esquerda */}
        <FacetasClientes grupos={grupos} marcadas={facetas} contar={contar} onAlternar={alternar} onLimpar={algumFiltro ? limpar : null} />

        <div className={conteudo}>
          {/* Busca e quantos clientes ficaram */}
          <div className={barraFerramentas}>
            <label className={classeBusca}>
              <Search size={14} aria-hidden="true" className="text-faint" />
              <input
                value={busca}
                onChange={(e) => setBusca(e.target.value)}
                placeholder="Buscar cliente, contato ou vendedor"
                aria-label="Buscar cliente, contato ou vendedor"
              />
            </label>
            <span className="text-[12.5px] text-ardosia tabular-nums">{plural(filtrados.length, "cliente", "clientes")}</span>
          </div>

          {/* Tabela: um tbody por grupo; clique seleciona, duplo clique abre o cliente */}
          <div className={cx(card, "overflow-x-auto")}>
            <table className={tabela}>
              <thead>
                <tr>
                  <th className={th}>Cliente</th>
                  {!compacto && <th className={th}>Tipo</th>}
                  {!compacto && <th className={th}>Vendedor</th>}
                  {!compacto && <th className={th}>Última reunião</th>}
                  <th className={th}>Padrões no contexto do cliente</th>
                  <ThIndicadores compacto={compacto} />
                </tr>
              </thead>
              {blocos.map((b) => {
                const fechado = !!fechados[b.chave];
                // Soma dos dois indicadores no grupo, para a linha do cabeçalho do grupo.
                const somaR = b.itens.reduce((s, c) => s + c.indicadores.riscosSemRetorno, 0);
                const somaO = b.itens.reduce((s, c) => s + c.indicadores.oportPerdidas, 0);
                return (
                  <tbody key={b.chave || "todos"}>
                    {b.chave && (
                      // Cabeçalho do grupo: clica para recolher ou abrir
                      <tr className="cursor-pointer">
                        <td colSpan={nColunas} className="cursor-default border-b border-linha bg-nevoa px-4 py-[7px] align-middle [tr:last-child>&]:border-b-0">
                          <button
                            type="button"
                            className="inline-flex items-center gap-1.5 text-[12.5px] font-semibold text-ink"
                            onClick={() => setFechados((f) => ({ ...f, [b.chave]: !fechado }))}
                            aria-expanded={!fechado}
                          >
                            <ChevronDown size={14} aria-hidden="true" className={fechado ? "-rotate-90" : undefined} />
                            {b.chave}
                            <span className="font-normal text-ardosia">
                              {"· "}
                              {plural(b.itens.length, "cliente", "clientes")}
                              {" · "}
                              <span className={somaR ? "text-critico" : "text-ardosia"}>{plural(somaR, "risco sem retorno", "riscos sem retorno")}</span>
                              {" · "}
                              <span className={somaO ? "text-atencao" : "text-ardosia"}>{plural(somaO, "oportunidade perdida", "oportunidades perdidas")}</span>
                            </span>
                          </button>
                        </td>
                      </tr>
                    )}
                    {!fechado &&
                      b.itens.map((c) => (
                        <tr key={c.id} className={tr} aria-selected={selecionado?.id === c.id} onClick={() => selecionar(c.id)} onDoubleClick={() => abrir(c)}>
                          <td className={td}>
                            <CelulaCliente c={c} sub={compacto ? c.vendedor.nome : c.segmento} mostrarTipo={compacto} />
                          </td>
                          {!compacto && (
                            <td className={td}>
                              <ChipTipoCliente tipo={c.tipo} />
                            </td>
                          )}
                          {!compacto && <td className={cx(td, "text-[12.5px] whitespace-nowrap")}>{c.vendedor.nome}</td>}
                          {!compacto && (
                            <td className={td}>
                              <CelulaUltimaReuniao cliente={c} />
                            </td>
                          )}
                          <td className={cx(td, compacto ? "max-w-[240px]" : "max-w-[340px]")}>
                            <ChipsTemas temas={c.temasEmPauta} porPadrao max={compacto ? 2 : 3} />
                          </td>
                          <TdIndicadores ind={c.indicadores} />
                        </tr>
                      ))}
                  </tbody>
                );
              })}
            </table>
            {!filtrados.length && (
              <Vazio
                titulo="Nenhum cliente com esses filtros"
                acao={
                  <button type="button" className={btn({ sm: true })} onClick={limpar}>
                    Limpar filtros
                  </button>
                }
              />
            )}
          </div>
          <p className="mx-0.5 mt-2.5 mb-0 text-xs leading-[1.5] text-faint">
            Tipo vem da classificação lead ou customer do cadastro. No corpus do Challenge só 1 em cada 5 reuniões tem essa informação, por isso “Sem tipo” fica visível.
          </p>
        </div>

        {/* Painel lateral com a prévia do cliente selecionado */}
        {app.painelAberto && selecionado && (
          <PainelLateral titulo="Cliente" onFechar={() => app.setPainelAberto(false)}>
            <PreviaCliente cliente={selecionado} />
          </PainelLateral>
        )}
      </div>
    </>
  );
}
