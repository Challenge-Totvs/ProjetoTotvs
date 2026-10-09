/* Início do vendedor (e a mesma tela, só leitura, na visão do gestor).
   Recebe tudo pronto do backend (GET /api/inicio) e só exibe. */

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { AlertTriangle, Building2, CheckCircle2, CornerDownRight, Plus, Repeat, Upload, type LucideIcon } from "lucide-react";
import type { Inicio, Tema, TipoMudanca } from "../../types/api";
import { useAtalhos } from "../../context/AppContext";
import { paraData, relativo } from "../../lib/datas";
import { ROTULO_MUDANCA, ultimaCitacao } from "../../lib/dominio";
import { cx, pct, plural } from "../../lib/formato";
import { rotas } from "../../lib/rotas";
import { Aviso, AvisoLeitura, CabecalhoPagina, Numero, Secao, Vazio } from "../ui/base";
import { btn, grid2, grid3, item, itemSub, itemTitulo, link, lista as classeLista, numeros } from "../ui/classes";
import { Glifo, GlifosTema } from "../ui/glifos";
import { ItemCompromisso, ItemReuniaoAgenda, ItemTema } from "../tema/Itens";

/** Ícone de cada tipo de mudança. Os tipos sem ícone mostram os glifos do tema. */
const ICONE_MUDANCA: Partial<Record<TipoMudanca, LucideIcon>> = {
  tratado: CheckCircle2,
  tratado_fora: CornerDownRight,
  virou_perdida: AlertTriangle,
  voltou_sem_resposta: Repeat,
  de_novo_sem_resposta: Repeat,
  voltou: Repeat,
};

/** Quantas mudanças aparecem antes do "Ver todas as N". */
const MUDANCAS_VISIVEIS = 6;

export function PainelInicio({ inicio, somenteLeitura, nomeVendedor }: { inicio: Inicio; somenteLeitura?: boolean; nomeVendedor?: string }) {
  const navigate = useNavigate();
  const W = inicio.janelaDias;
  // Na visão do gestor, sem nome informado, usa o nome que veio do backend.
  const nome = nomeVendedor ?? (somenteLeitura ? inicio.vendedor.nome : undefined);
  const primeiro = nome ? nome.split(" ")[0] : null;

  const { riscos, oportunidades, mudancas, compromissos, agenda, pendentes } = inicio;
  const m = inicio.desempenho;

  // Subtítulo das oportunidades: quantas já viraram perdidas e quantas ainda estão na janela.
  const perdidas = oportunidades.filter((t) => t.situacao === "oportunidade_perdida").length;
  const dentroDaJanela = oportunidades.filter((t) => t.situacao === "sem_retorno").length;

  const [verTodasMudancas, setVerTodasMudancas] = useState(false);

  // Lista única para J/K: primeiro a coluna de riscos, depois a de oportunidades.
  // Um tema pode estar nas duas colunas (risco e oportunidade), por isso guarda a coluna.
  const lista = [...riscos.map((t) => ({ t, col: "r" })), ...oportunidades.map((t) => ({ t, col: "o" }))];
  const [sel, setSel] = useState(0);
  const abrir = (t: Tema) => navigate(rotas.cliente(t.clienteId, t.id));

  useAtalhos(
    {
      j: () => setSel((s) => Math.min(lista.length - 1, s + 1)),
      k: () => setSel((s) => Math.max(0, s - 1)),
      Enter: () => {
        if (lista[sel]) abrir(lista[sel].t);
      },
    },
    lista.length
      ? [
          [["J", "K"], "mover"],
          [["Enter"], "abrir o tema"],
        ]
      : [],
  );
  const atual = lista[sel] ?? null;
  const selecionado = (t: Tema, col: string) => atual != null && atual.t.id === t.id && atual.col === col;

  return (
    <>
      <CabecalhoPagina
        titulo={somenteLeitura ? `Visão de ${nome}` : "Início"}
        texto={`${
          somenteLeitura
            ? `O que pede atenção nos ${inicio.clientes} clientes de ${primeiro}`
            : `O que pede sua atenção hoje, nos seus ${inicio.clientes} clientes`
        }. Janela de acompanhamento: ${W} dias.`}
        acoes={
          !somenteLeitura && (
            <button type="button" className={btn({ primario: true })} onClick={() => navigate(rotas.nova())}>
              <Plus size={15} aria-hidden="true" />
              Nova transcrição
            </button>
          )
        }
      />

      {somenteLeitura && <AvisoLeitura nome={nome} />}

      {/* Reuniões que já aconteceram e ainda esperam a transcrição. */}
      {!somenteLeitura && pendentes.length > 0 && (
        <div className="mb-4">
          <Aviso
            tom="info"
            acao={
              <button
                type="button"
                className={btn({ sm: true })}
                onClick={() => navigate(rotas.nova({ clienteId: pendentes[0].clienteId, reuniaoId: pendentes[0].reuniaoId }))}
              >
                <Upload size={14} aria-hidden="true" />
                Enviar transcrição
              </button>
            }
          >
            {pendentes.length === 1
              ? `A reunião de ${relativo(paraData(pendentes[0].dataHora))} com ${pendentes[0].clienteNome} ainda não tem transcrição.`
              : `${pendentes.length} reuniões realizadas ainda não têm transcrição.`}
          </Aviso>
        </div>
      )}

      {/* Sem clientes: só o convite para a primeira transcrição. */}
      {!inicio.clientes && (
        <Secao>
          <Vazio
            icone={Building2}
            titulo={somenteLeitura ? `${primeiro} ainda não tem clientes` : "Você ainda não tem clientes"}
            texto={
              somenteLeitura
                ? "Os clientes aparecem quando a primeira transcrição é enviada."
                : "Envie a primeira transcrição e cadastre o cliente no caminho. Os temas aparecem assim que a análise termina."
            }
            acao={
              !somenteLeitura && (
                <button type="button" className={btn({ primario: true })} onClick={() => navigate(rotas.nova())}>
                  Nova transcrição
                </button>
              )
            }
          />
        </Secao>
      )}

      {inicio.clientes > 0 && (
        <div className="grid gap-4">
          {/* Riscos e oportunidades, lado a lado. */}
          <div className={grid2}>
            <Secao
              id="ini-riscos"
              titulo={
                <>
                  <Glifo tipo="risco" tamanho={12} />
                  Riscos sem retorno
                </>
              }
              contagem={riscos.length}
              sub="Na última reunião em que apareceram, ficaram sem resposta"
              semPadding
            >
              {riscos.length ? (
                <div className={classeLista}>
                  {riscos.map((t) => (
                    <ItemTema key={t.id} tema={t} mostrarCliente selecionado={selecionado(t, "r")} onClick={() => abrir(t)} />
                  ))}
                </div>
              ) : (
                <Vazio icone={CheckCircle2} titulo="Nenhum risco sem retorno" texto="Todos os riscos citados foram respondidos na conversa ou tratados fora dela." />
              )}
            </Secao>
            <Secao
              id="ini-oport"
              titulo={
                <>
                  <Glifo tipo="oportunidade" tamanho={12} />
                  Oportunidades sem tratamento
                </>
              }
              contagem={oportunidades.length}
              sub={`${plural(perdidas, "perdida", "perdidas")} e ${dentroDaJanela} ainda dentro da janela`}
              semPadding
            >
              {oportunidades.length ? (
                <div className={classeLista}>
                  {oportunidades.map((t) => (
                    <ItemTema key={t.id} tema={t} mostrarCliente selecionado={selecionado(t, "o")} onClick={() => abrir(t)} mostrarSituacao />
                  ))}
                </div>
              ) : (
                <Vazio icone={CheckCircle2} titulo="Nenhuma oportunidade sem tratamento" texto="As oportunidades citadas foram tratadas na conversa ou fora dela." />
              )}
            </Secao>
          </div>

          {/* Mudanças, compromissos e agenda. */}
          <div className={grid3}>
            <Secao id="ini-mudancas" titulo="Mudou desde a última reunião" sub="Últimos 14 dias" semPadding>
              {mudancas.length ? (
                <ul className={cx(classeLista, "m-0 list-none p-0")}>
                  {(verTodasMudancas ? mudancas : mudancas.slice(0, MUDANCAS_VISIVEIS)).map((ev) => {
                    const Icone = ICONE_MUDANCA[ev.tipo];
                    // Cor do ícone: perdida em atenção, tratados em verde, o resto em ardósia.
                    const cor = ev.tipo === "virou_perdida" ? "text-atencao" : ev.tipo.startsWith("trat") ? "text-resolvido" : "text-ardosia";
                    return (
                      <li key={ev.id}>
                        <button type="button" className={item} onClick={() => abrir(ev.tema)}>
                          <span className={cx("pt-0.5", cor)}>
                            {Icone ? (
                              <Icone size={14} aria-hidden="true" />
                            ) : (
                              <GlifosTema tipos={ev.tema.tipos} tratado={ultimaCitacao(ev.tema)?.tratado ?? null} />
                            )}
                          </span>
                          <span className="min-w-0 flex-1">
                            <span className="block text-xs leading-[1.4] font-medium text-ink">{ROTULO_MUDANCA[ev.tipo]}</span>
                            <span className={cx(itemTitulo, "font-normal!")}>{ev.tema.titulo}</span>
                            <span className={itemSub}>
                              {ev.tema.clienteNome} · {relativo(paraData(ev.data))}
                            </span>
                          </span>
                        </button>
                      </li>
                    );
                  })}
                </ul>
              ) : (
                <Vazio titulo="Nada mudou nos últimos 14 dias" />
              )}
              {mudancas.length > MUDANCAS_VISIVEIS && (
                <div className="border-t border-linha px-4 py-2">
                  <button type="button" className={cx(link, "text-[12.5px]")} onClick={() => setVerTodasMudancas((v) => !v)}>
                    {verTodasMudancas ? "Mostrar menos" : `Ver todas as ${mudancas.length}`}
                  </button>
                </div>
              )}
            </Secao>
            <Secao
              id="ini-comp"
              titulo="Compromissos"
              contagem={compromissos.filter((c) => c.estado !== "cumprido").length}
              sub="Promessas do vendedor, lidas das reuniões"
              semPadding
            >
              {compromissos.length ? (
                <ul className="m-0 list-none p-0">
                  {compromissos.map((cp) => (
                    <ItemCompromisso key={cp.id} cp={cp} somenteLeitura={somenteLeitura} />
                  ))}
                </ul>
              ) : (
                <Vazio titulo="Nenhum compromisso em aberto" />
              )}
            </Secao>
            <Secao id="ini-agenda" titulo="Próximas reuniões" contagem={agenda.length} sub="Próximos 14 dias" semPadding>
              {agenda.length ? (
                <ul className="m-0 list-none p-0">
                  {agenda.map((r) => (
                    <ItemReuniaoAgenda key={r.reuniaoId} r={r} somenteLeitura={somenteLeitura} />
                  ))}
                </ul>
              ) : (
                <Vazio titulo="Nenhuma reunião marcada" />
              )}
            </Secao>
          </div>

          {/* Números das reuniões na janela (nunca de vendas). */}
          <Secao
            id="ini-desempenho"
            titulo={somenteLeitura ? `Reuniões de ${primeiro} nos últimos ${W} dias` : `Suas reuniões nos últimos ${W} dias`}
            sub="Medidas das reuniões, não de vendas: valor vendido e taxa de fechamento dependem do CRM."
          >
            <div className={numeros()}>
              <Numero rotulo="Reuniões realizadas" valor={m.realizadas} sub={`${m.analisadas} analisadas`} />
              {somenteLeitura && (
                <Numero
                  rotulo="Temas tratados na própria conversa"
                  valor={m.taxaConversa == null ? "—" : pct(m.taxaConversa)}
                  sub={`${m.tratadosConversa} de ${m.comLeitura} temas citados · papel do locutor inferido`}
                  tom={m.taxaConversa != null && m.taxaConversa < 0.5 ? "atencao" : undefined}
                />
              )}
              <Numero rotulo="Tratados fora da reunião" valor={m.tratadosFora} sub={somenteLeitura ? `registrados por ${primeiro}` : "registrados por você"} />
              <Numero rotulo="Oportunidades tratadas" valor={`${m.oportTratadas} de ${m.oportIdentificadas}`} sub="das citadas na janela" />
              <Numero
                rotulo={somenteLeitura ? "Fala do vendedor" : "Sua fala nas reuniões"}
                valor={m.falaVendedor == null ? "—" : pct(m.falaVendedor)}
                sub="média, por palavras"
              />
            </div>
          </Secao>
        </div>
      )}
    </>
  );
}
