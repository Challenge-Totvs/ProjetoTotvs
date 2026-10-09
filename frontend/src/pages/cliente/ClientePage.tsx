/* Página do cliente (/clientes/:id?tema=): números, mapa de temas, reuniões,
   compromissos e o painel do tema selecionado, com os atalhos J/K/Enter/V/T/N/A. */

import { useState } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import { History, Upload, Users } from "lucide-react";
import { buscarCliente } from "../../api/clientes";
import { infoErro } from "../../api/http";
import { InspetorTema } from "../../components/cliente/InspetorTema";
import { MapaTemas } from "../../components/cliente/MapaTemas";
import { ItemCompromisso } from "../../components/tema/Itens";
import { AvisoLeitura, CabecalhoPagina, Carregando, ErroCarregar, Etiqueta, Numero, Secao, Vazio } from "../../components/ui/base";
import { COR } from "../../components/ui/cores";
import { btn, comPainel, conteudo, direita, linkForte, numeros, tabela, td, th, tr } from "../../components/ui/classes";
import { ChipMotor, ChipTipoCliente, GlifosTema, LegendaGlifos } from "../../components/ui/glifos";
import { BotaoPainel, PainelLateral } from "../../components/ui/Sobrepostos";
import { useApp, useAtalhos, useTrilha } from "../../context/AppContext";
import { useApi } from "../../hooks/useApi";
import { fmtDiaSemana, fmtHora, hoje, paraData, relativo } from "../../lib/datas";
import { ultimaCitacao } from "../../lib/dominio";
import { cx, plural } from "../../lib/formato";
import { rotas } from "../../lib/rotas";
import type { ClienteDetalhe, Id } from "../../types/api";

/** Marca usada quando a API responde 404 (cliente não existe ou não é do escopo). */
const NAO_ENCONTRADO = "nao_encontrado" as const;

export default function ClientePage() {
  const { id } = useParams();
  // A chave reinicia o estado da página (seleção, histórico) ao trocar de cliente.
  return <PaginaCliente key={id} id={Number(id)} />;
}

function PaginaCliente({ id }: { id: Id }) {
  const app = useApp();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const temaParam = params.get("tema") ? Number(params.get("tema")) : null;

  // Busca a página inteira do cliente; 404 vira "Cliente não encontrado".
  const { dados, erro, carregando, recarregar } = useApi<ClienteDetalhe | typeof NAO_ENCONTRADO>(
    () =>
      Number.isFinite(id)
        ? buscarCliente(id).catch((e: unknown) => {
            if (infoErro(e).status === 404) return NAO_ENCONTRADO;
            throw e;
          })
        : Promise.resolve(NAO_ENCONTRADO),
    [id, app.versao],
  );
  const cliente = dados && dados !== NAO_ENCONTRADO ? dados : null;

  const [mostrarHistorico, setMostrarHistorico] = useState(false);
  const [selLocal, setSelLocal] = useState<Id | null>(temaParam);
  const [contextoAberto, setContextoAberto] = useState<string | null>(null);

  // Tema vindo da URL (?tema=): quando muda, seleciona o tema (ajuste de estado durante a renderização,
  // como a documentação do React recomenda, em vez de um useEffect).
  const [temaDaUrl, setTemaDaUrl] = useState<Id | null>(temaParam);
  if (temaParam !== temaDaUrl) {
    setTemaDaUrl(temaParam);
    if (temaParam) {
      setSelLocal(temaParam);
      setContextoAberto(null);
    }
  }
  // Se o tema da URL está fora de pauta, abre o histórico. Roda uma vez por tema, não a cada recarga.
  const [historicoAplicado, setHistoricoAplicado] = useState<Id | null>(null);
  if (temaParam && cliente && historicoAplicado !== temaParam) {
    setHistoricoAplicado(temaParam);
    const t = cliente.temas.find((x) => x.id === temaParam);
    if (t && !t.emPauta) setMostrarHistorico(true);
  }

  const todos = cliente ? cliente.temas : [];
  const emPauta = todos.filter((t) => t.emPauta);
  const historico = todos.filter((t) => !t.emPauta);
  const visiveis = mostrarHistorico ? [...emPauta, ...historico] : emPauta;
  const sel = visiveis.find((t) => t.id === selLocal) || visiveis[0] || null;
  const idx = sel ? visiveis.indexOf(sel) : -1;
  // Só o vendedor dono do cliente age nos temas.
  const podeAgir = !!cliente && !app.gestor && cliente.vendedor.id === app.usuario.id;
  const reunioes = cliente ? cliente.reunioes : [];
  const analisadas = reunioes.filter((r) => r.status === "analisada");

  const selecionar = (temaId: Id) => {
    setSelLocal(temaId);
    setContextoAberto(null);
    if (!app.painelAberto) app.setPainelAberto(true);
  };

  useTrilha([{ l: "Clientes", para: rotas.clientes }, { l: cliente ? cliente.nome : "Cliente" }]);

  useAtalhos(
    {
      j: () => {
        const prox = visiveis[idx + 1];
        if (prox) selecionar(prox.id);
      },
      k: () => {
        if (idx > 0) selecionar(visiveis[idx - 1].id);
      },
      Enter: () => {
        const u = sel && ultimaCitacao(sel);
        if (u) navigate(rotas.reuniao(u.reuniaoId, u.turno));
      },
      // V abre (ou fecha) o contexto da citação mais recente do tema selecionado.
      v: () => {
        const u = sel && ultimaCitacao(sel);
        if (!u) return;
        if (!app.painelAberto) app.setPainelAberto(true);
        const chave = `${u.reuniaoId}-${u.turno}`;
        setContextoAberto((c) => (c === chave ? null : chave));
      },
      ...(podeAgir && sel && !sel.naoProcede
        ? {
            t: () => {
              if (!sel.registroFora) app.abrirModal("fora", sel);
            },
            n: () => app.abrirModal("naoProcede", sel),
            a: () => app.abrirModal("avisar", sel),
          }
        : {}),
    },
    [
      [["J", "K"], "tema"],
      [["Enter"], "abrir reunião"],
      [["V"], "ver no contexto"],
      ...(podeAgir
        ? ([
            [["T"], "tratei fora"],
            [["N"], "não procede"],
            [["A"], "avisar gestor"],
          ] as [string[], string][])
        : []),
      [["]"], "painel"],
    ],
  );

  if (carregando && !dados) return <Carregando />;
  if (erro && !dados) return <ErroCarregar mensagem={erro} onTentar={() => void recarregar()} />;
  if (!cliente)
    return (
      <Vazio
        titulo="Cliente não encontrado"
        acao={
          <button type="button" className={btn()} onClick={() => navigate(rotas.clientes)}>
            Voltar para Clientes
          </button>
        }
      />
    );

  const ind = cliente.indicadores;
  const ultima = cliente.ultimaReuniao;
  const proxima = cliente.proximaReuniao;
  // Compromissos pelo prazo; sem prazo conta como hoje (igual à demo).
  const prazo = (p: string | null) => (p ? paraData(p) : hoje()).getTime();
  const compromissos = [...cliente.compromissos].sort((a, b) => prazo(a.prazo) - prazo(b.prazo));
  const tratados = ind.tratadosConversa + ind.tratadosFora;

  return (
    <>
      <CabecalhoPagina
        antes={
          <div className="mb-2 flex flex-wrap gap-1.5">
            <ChipTipoCliente tipo={cliente.tipo} />
            <Etiqueta>{cliente.segmento}</Etiqueta>
            {app.gestor && <Etiqueta icone={Users}>{cliente.vendedor.nome}</Etiqueta>}
          </div>
        }
        titulo={cliente.nome}
        texto={`${cliente.contatos.map((c) => `${c.nome} (${c.cargo})`).join(" · ")}${ultima ? ` · última reunião ${relativo(paraData(ultima.dataHora))}` : ""}${
          proxima ? ` · próxima ${fmtDiaSemana(paraData(proxima.dataHora))}, ${fmtHora(paraData(proxima.dataHora))}` : ""
        }`}
        acoes={
          <>
            {podeAgir && (
              <button type="button" className={btn()} onClick={() => navigate(rotas.nova({ clienteId: cliente.id }))}>
                <Upload size={15} aria-hidden="true" />
                Nova transcrição
              </button>
            )}
            <BotaoPainel aberto={app.painelAberto} onClick={() => app.setPainelAberto(!app.painelAberto)} />
          </>
        }
      />
      {app.gestor && <AvisoLeitura nome={cliente.vendedor.nome} />}

      <div className={comPainel}>
        <div className={cx(conteudo, "grid gap-4")}>
          {/* Os quatro números do cliente */}
          <div className={numeros(4)}>
            <Numero rotulo="Temas em pauta" valor={ind.emPauta} sub={`${ind.foraDePauta} fora de pauta${ind.naoProcede ? ` · ${ind.naoProcede} não procede` : ""}`} />
            <Numero
              rotulo="Riscos sem retorno"
              valor={ind.riscosSemRetorno}
              tom={ind.riscosSemRetorno ? "critico" : undefined}
              sub={ind.riscosRecorrentes ? plural(ind.riscosRecorrentes, "recorrente", "recorrentes") : "nenhum recorrente"}
            />
            <Numero
              rotulo="Oportunidades perdidas"
              valor={ind.oportPerdidas}
              tom={ind.oportPerdidas ? "atencao" : undefined}
              sub={`${ind.oportSemRetorno} sem retorno na janela`}
            />
            <Numero
              rotulo="Tratados"
              valor={tratados}
              tom={tratados ? "ok" : undefined}
              sub={`${ind.tratadosConversa} na conversa · ${ind.tratadosFora} fora da reunião`}
            />
          </div>

          {/* Mapa de temas, com o histórico (fora de pauta e não procede) sob demanda */}
          <Secao
            id="mapa"
            titulo="Mapa de temas"
            sub={`Cada coluna é uma reunião. A situação vem das conversas e da janela de ${app.janelaDias} dias.`}
            acao={
              historico.length > 0 && (
                <button type="button" className={btn({ sm: true })} onClick={() => setMostrarHistorico((v) => !v)} aria-pressed={mostrarHistorico}>
                  <History size={14} aria-hidden="true" />
                  {mostrarHistorico ? "Ocultar histórico" : `Histórico (${historico.length})`}
                </button>
              )
            }
          >
            {visiveis.length ? (
              <MapaTemas
                clienteNome={cliente.nome}
                temas={visiveis}
                reunioes={analisadas}
                selId={sel ? sel.id : null}
                onSelecionar={selecionar}
                maxColunas={app.painelAberto ? 4 : 6}
              />
            ) : (
              <Vazio
                titulo="Nenhum tema em pauta"
                texto={historico.length ? "Há temas no histórico: fora de pauta ou marcados como não procede." : "Os temas aparecem depois da primeira análise."}
              />
            )}
            <div className="mt-3">
              <LegendaGlifos compacta />
            </div>
          </Secao>

          {/* Reuniões, da mais recente para a mais antiga */}
          <Secao id="reunioes" titulo="Reuniões" contagem={reunioes.length} semPadding>
            <div className="overflow-x-auto">
              <table className={tabela}>
                <thead>
                  <tr>
                    <th className={th}>Data</th>
                    <th className={th}>Reunião</th>
                    <th className={th}>Contato</th>
                    <th className={th}>Análise</th>
                    <th className={cx(th, direita)}>Engajamento</th>
                    <th className={th}>Temas citados</th>
                  </tr>
                </thead>
                <tbody>
                  {[...reunioes].reverse().map((r) => {
                    const analisada = r.status === "analisada";
                    const data = paraData(r.dataHora);
                    // Temas citados nesta reunião, a partir das citações de cada tema.
                    const temasR = todos.filter((t) => t.citacoes.some((c) => c.reuniaoId === r.id));
                    return (
                      <tr key={r.id} className={cx(tr, !analisada && "cursor-default!")} onClick={() => analisada && navigate(rotas.reuniao(r.id))}>
                        <td className={cx(td, "whitespace-nowrap tabular-nums")}>
                          {fmtDiaSemana(data)}, {fmtHora(data)}
                        </td>
                        <td className={td}>
                          {analisada ? (
                            <button
                              type="button"
                              className={linkForte}
                              onClick={(e) => {
                                e.stopPropagation();
                                navigate(rotas.reuniao(r.id));
                              }}
                            >
                              {r.titulo}
                            </button>
                          ) : (
                            r.titulo
                          )}
                        </td>
                        <td className={cx(td, "text-[12.5px]")}>{r.contato}</td>
                        <td className={td}>
                          {analisada && r.motor && <ChipMotor motor={r.motor} />}
                          {r.status === "agendada" &&
                            (r.confirmada ? (
                              <Etiqueta cor={COR.resolvido}>Agendada · confirmada</Etiqueta>
                            ) : (
                              <Etiqueta cor={COR.atencaoBranco}>Agendada · a confirmar</Etiqueta>
                            ))}
                          {r.status === "aguardando" &&
                            (podeAgir ? (
                              <button
                                type="button"
                                className={btn({ sm: true })}
                                onClick={(e) => {
                                  e.stopPropagation();
                                  navigate(rotas.nova({ clienteId: cliente.id, reuniaoId: r.id }));
                                }}
                              >
                                <Upload size={13} aria-hidden="true" />
                                Enviar transcrição
                              </button>
                            ) : (
                              <Etiqueta cor={COR.atencaoBranco}>Aguardando transcrição</Etiqueta>
                            ))}
                        </td>
                        <td className={cx(td, direita, "tabular-nums")}>{analisada && r.score != null ? r.score : "—"}</td>
                        <td className={td}>
                          <span className="inline-flex items-center gap-1.5">
                            {temasR.slice(0, 6).map((t) => {
                              const c = t.citacoes.find((x) => x.reuniaoId === r.id);
                              return <GlifosTema key={t.id} tipos={t.tipos} tratado={c ? c.tratado : null} tamanho={11} />;
                            })}
                            {!temasR.length && <span className="text-xs text-faint">—</span>}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </Secao>

          {/* Compromissos ditos pelo vendedor nas reuniões deste cliente */}
          {compromissos.length > 0 && (
            <Secao id="comp-cliente" titulo="Compromissos com este cliente" contagem={compromissos.filter((c) => c.estado !== "cumprido").length} semPadding>
              <ul className="m-0 list-none p-0">
                {compromissos.map((cp) => (
                  <ItemCompromisso key={cp.id} cp={cp} somenteLeitura={!podeAgir} mostrarCliente={false} />
                ))}
              </ul>
            </Secao>
          )}
        </div>

        {/* Painel lateral com o tema selecionado */}
        {app.painelAberto && sel && (
          <PainelLateral titulo="Tema" onFechar={() => app.setPainelAberto(false)}>
            <InspetorTema tema={sel} podeAgir={podeAgir} contextoAberto={contextoAberto} setContextoAberto={setContextoAberto} />
          </PainelLateral>
        )}
      </div>
    </>
  );
}
