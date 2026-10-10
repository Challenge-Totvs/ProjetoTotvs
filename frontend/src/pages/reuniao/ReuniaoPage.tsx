/* Página da reunião: régua da conversa, análise, métricas e transcrição.
   Rota /reunioes/:id, com ?turno= para rolar até um turno e destacá-lo. */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import { AlertCircle, ArrowLeft, Calendar, ShieldCheck, Sparkles, Upload } from "lucide-react";
import type { ReuniaoDetalhe } from "../../types/api";
import { buscarReuniao, buscarTranscricao } from "../../api/reunioes";
import { useApp, useAtalhos, useTrilha, type ItemTrilha } from "../../context/AppContext";
import { useApi } from "../../hooks/useApi";
import { fmtData, fmtDiaSemana, fmtHora, paraData, relativo } from "../../lib/datas";
import { temOport, temRisco } from "../../lib/dominio";
import { plural } from "../../lib/formato";
import { rotas } from "../../lib/rotas";
import { Aviso, CabecalhoPagina, Carregando, ErroCarregar, Etiqueta, Secao, Vazio } from "../../components/ui/base";
import { COR } from "../../components/ui/cores";
import { btn, gridReuniao, lista } from "../../components/ui/classes";
import { ChipMotor, Glifo, LegendaGlifos } from "../../components/ui/glifos";
import { Regua } from "../../components/ui/graficos";
import { ItemCompromisso, ItemTema } from "../../components/tema/Itens";
import { ItemAnalise, ItemInteresse, listaAnalise } from "../../components/reuniao/ItensAnalise";
import { marcasDaReuniao } from "../../components/reuniao/marcas";
import { SecaoEngajamento, SecaoMetricas } from "../../components/reuniao/Metricas";
import { SecaoTranscricao, type VisaoTranscricao } from "../../components/reuniao/Transcricao";

export default function ReuniaoPage() {
  const app = useApp();
  const id = Number(useParams().id);
  const [params] = useSearchParams();
  const turnoParam = Number(params.get("turno")) || null;

  // Recarrega quando muda a reunião ou depois de uma ação (ex.: marcar compromisso).
  const { dados: r, erro, carregando, recarregar } = useApi(() => buscarReuniao(id), [id, app.versao]);

  // Trilha do topo: Clientes › cliente › "título, data". Enquanto carrega, só "Reunião".
  const trilha: ItemTrilha[] =
    r && r.id === id
      ? [
          { l: "Clientes", para: rotas.clientes },
          { l: r.cliente.nome, para: rotas.cliente(r.cliente.id) },
          { l: `${r.titulo}, ${fmtData(paraData(r.dataHora))}` },
        ]
      : [{ l: "Clientes", para: rotas.clientes }, { l: "Reunião" }];
  useTrilha(trilha);
  // A página não tem atalhos próprios (mesmo que a demo).
  useAtalhos({}, []);

  if (carregando && !r) return <Carregando />;
  if (!r) return <ErroCarregar mensagem={erro ?? "Não foi possível carregar a reunião."} onTentar={() => void recarregar()} />;
  if (r.status !== "analisada" || !r.analise) return <ReuniaoPendente r={r} />;
  // key: trocar de reunião zera a versão da transcrição e o turno destacado.
  return <PaginaAnalisada key={r.id} r={r} turno={turnoParam} />;
}

/* ---------- Reunião agendada ou aguardando transcrição ---------- */

function ReuniaoPendente({ r }: { r: ReuniaoDetalhe }) {
  const app = useApp();
  const navigate = useNavigate();
  const data = paraData(r.dataHora);
  // Só o vendedor dono do cliente envia a transcrição.
  const podeAgir = !app.gestor && r.cliente.vendedor.id === app.usuario.id;
  return (
    <>
      <CabecalhoPagina titulo={r.titulo} texto={`${r.cliente.nome} · ${r.contato} · ${fmtDiaSemana(data)}, ${fmtHora(data)}`} />
      <Secao>
        {r.status === "agendada" ? (
          <Vazio
            icone={Calendar}
            titulo={`Reunião agendada para ${relativo(data)}`}
            texto={r.confirmada ? "Confirmada pelo cliente." : "Ainda a confirmar com o cliente."}
            acao={
              <button type="button" className={btn()} onClick={() => navigate(rotas.cliente(r.cliente.id))}>
                Preparar pelo cliente
              </button>
            }
          />
        ) : (
          <Vazio
            icone={Upload}
            titulo="Esta reunião ainda não tem transcrição"
            texto="Assim que a transcrição for enviada, a análise roda e os temas do cliente são atualizados."
            acao={
              podeAgir && (
                <button type="button" className={btn({ primario: true })} onClick={() => navigate(rotas.nova({ clienteId: r.cliente.id, reuniaoId: r.id }))}>
                  Enviar transcrição
                </button>
              )
            }
          />
        )}
      </Secao>
    </>
  );
}

/* ---------- Reunião analisada ---------- */

function PaginaAnalisada({ r, turno }: { r: ReuniaoDetalhe; turno: number | null }) {
  const app = useApp();
  const navigate = useNavigate();
  // A página só chega aqui com análise; o "as" evita checar de novo em cada uso.
  const analise = r.analise as NonNullable<ReuniaoDetalhe["analise"]>;
  const cliente = r.cliente;
  const data = paraData(r.dataHora);
  const podeAgir = !app.gestor && cliente.vendedor.id === app.usuario.id;

  /* Transcrição: o texto original vem logo; a versão da LLM só quando pedida. */
  const [visao, setVisao] = useState<VisaoTranscricao>("original");
  const [pediuLlm, setPediuLlm] = useState(false);
  const original = useApi(() => (r.temTranscricao ? buscarTranscricao(r.id, "original") : Promise.resolve(null)), [r.id, r.temTranscricao]);
  const llm = useApi(() => (pediuLlm && r.temTranscricao ? buscarTranscricao(r.id, "llm") : Promise.resolve(null)), [r.id, r.temTranscricao, pediuLlm]);
  const textosLlm = useMemo(() => (llm.dados ? new Map(llm.dados.map((t) => [t.n, t.texto])) : null), [llm.dados]);
  const turnos = original.dados;

  /* Turno destacado e rolagem até ele. Se a transcrição ainda não chegou,
     o turno fica guardado em `alvo` e a rolagem acontece quando ela aparecer. */
  const [destaque, setDestaque] = useState<number | null>(turno);
  const alvo = useRef<number | null>(turno);
  const rolarAoAlvo = useCallback(() => {
    window.setTimeout(() => {
      const n = alvo.current;
      if (n == null) return;
      const el = document.getElementById(`turno-${n}`);
      if (!el) return;
      alvo.current = null;
      el.scrollIntoView({ block: "center", behavior: "smooth" });
    }, 30);
  }, []);
  const irAoTurno = useCallback(
    (n: number) => {
      setDestaque(n);
      alvo.current = n;
      rolarAoAlvo();
    },
    [rolarAoAlvo],
  );
  // ?turno= mudou (ex.: clique num compromisso desta mesma reunião): destaca já
  // no render e rola no efeito abaixo.
  const [turnoVisto, setTurnoVisto] = useState(turno);
  if (turno !== turnoVisto) {
    setTurnoVisto(turno);
    if (turno != null) setDestaque(turno);
  }
  useEffect(() => {
    if (turno == null) return;
    alvo.current = turno;
    rolarAoAlvo();
  }, [turno, rolarAoAlvo]);
  // A transcrição chegou: rola até o turno pedido, se houver.
  useEffect(() => {
    if (turnos) rolarAoAlvo();
  }, [turnos, rolarAoAlvo]);

  /* Listas da análise (os temas já vêm por turno e sem os "não procede"). */
  const riscos = r.temas.filter((x) => temRisco(x.tema));
  const oportunidades = r.temas.filter((x) => temOport(x.tema));
  const interesse = analise.interesse;
  const marcas = marcasDaReuniao(r);
  const conferidas = r.temas.length + interesse.length;
  const descartados = analise.descartados;
  const contingencia = analise.motor === "local" || analise.motor === "regras";

  return (
    <>
      <CabecalhoPagina
        antes={
          <div className="mb-2 flex flex-wrap items-center gap-1.5">
            <ChipMotor motor={analise.motor} />
            <Etiqueta cor={COR.resolvido} icone={ShieldCheck}>{`${conferidas} de ${conferidas} citações conferidas`}</Etiqueta>
            {descartados.length > 0 && (
              <Etiqueta cor={COR.criticoBranco} icone={AlertCircle}>
                {plural(descartados.length, "sinal descartado", "sinais descartados")}
              </Etiqueta>
            )}
          </div>
        }
        titulo={r.titulo}
        texto={`${cliente.nome} · ${r.contato} · ${fmtDiaSemana(data)}, ${fmtHora(data)}${r.duracaoMin ? ` · ${r.duracaoMin} min` : ""} · ${r.turnos} turnos · vendedor ${cliente.vendedor.nome}`}
        acoes={
          <button type="button" className={btn()} onClick={() => navigate(rotas.cliente(cliente.id))}>
            <ArrowLeft size={15} aria-hidden="true" />
            Ver o cliente
          </button>
        }
      />
      {contingencia && (
        <div className="mb-4">
          <Aviso tom="atencao">
            {analise.motor === "local"
              ? "Análise em contingência pelo modelo local: sem resumo, sem compromissos e sem leitura de quem falou. A reunião é reprocessada quando uma LLM voltar."
              : "Análise em contingência pelas regras: sem resumo, sem compromissos e sem leitura de quem falou. A reunião é reprocessada quando uma LLM voltar."}
          </Aviso>
        </div>
      )}
      <div className="grid gap-4">
        <Secao
          id="regua"
          titulo="Régua da conversa"
          sub="Posição de cada tema ao longo da reunião, por turno. A transcrição não tem horário, então a régua não mostra minutos."
        >
          {/* Clique na marca: vai ao turno na transcrição; sem transcrição, abre o tema no cliente. */}
          <Regua
            turnos={r.turnos}
            marcas={marcas}
            serie={analise.sentimentoSerie}
            destaque={destaque}
            onMarca={(m) => {
              if (r.temTranscricao) irAoTurno(m.turno);
              else if (m.temaId) navigate(rotas.cliente(cliente.id, m.temaId));
            }}
          />
          <div className="mt-2.5">
            <LegendaGlifos />
          </div>
        </Secao>

        <div className={gridReuniao}>
          {/* Coluna da esquerda: o que a análise encontrou */}
          <div className="grid content-start gap-4">
            {analise.resumo && (
              <Secao id="resumo" titulo="Resumo" acao={<Etiqueta icone={Sparkles}>Gerado por IA</Etiqueta>}>
                <p className="m-0 text-[13.5px] leading-[1.6] text-ink">{analise.resumo}</p>
              </Secao>
            )}
            <Secao
              id="riscos-r"
              titulo={
                <>
                  <Glifo tipo="risco" tamanho={12} />
                  Riscos e objeções
                </>
              }
              contagem={riscos.length}
              semPadding
            >
              {riscos.length ? (
                <ul className={listaAnalise}>
                  {riscos.map((x) => (
                    <ItemAnalise key={x.tema.id} item={x} turnos={turnos} />
                  ))}
                </ul>
              ) : (
                <Vazio titulo="Nenhum risco nesta reunião" />
              )}
            </Secao>
            <Secao
              id="oport-r"
              titulo={
                <>
                  <Glifo tipo="oportunidade" tamanho={12} />
                  Oportunidades
                </>
              }
              contagem={oportunidades.length}
              semPadding
            >
              {oportunidades.length ? (
                <ul className={listaAnalise}>
                  {oportunidades.map((x) => (
                    <ItemAnalise key={x.tema.id} item={x} turnos={turnos} />
                  ))}
                </ul>
              ) : (
                <Vazio titulo="Nenhuma oportunidade nesta reunião" />
              )}
            </Secao>
            <Secao
              id="interesse-r"
              titulo={
                <>
                  <Glifo tipo="interesse" tamanho={12} />
                  Pontos de interesse
                </>
              }
              contagem={interesse.length}
              semPadding
            >
              {interesse.length ? (
                <ul className={listaAnalise}>
                  {interesse.map((x) => (
                    <ItemInteresse key={x.turno} x={x} turnos={turnos} />
                  ))}
                </ul>
              ) : (
                <Vazio titulo="Nenhum ponto de interesse registrado" />
              )}
            </Secao>
            {analise.proximosPassos.length > 0 && (
              <Secao id="passos" titulo="Próximos passos sugeridos" acao={<Etiqueta icone={Sparkles}>Gerado por IA</Etiqueta>}>
                <ol className="m-0 grid list-decimal gap-1.5 pl-[18px] text-[13.5px] leading-[1.5]">
                  {analise.proximosPassos.map((p) => (
                    <li key={p}>{p}</li>
                  ))}
                </ol>
              </Secao>
            )}
            {r.compromissos.length > 0 && (
              <Secao id="comp-r" titulo="Compromissos do vendedor nesta reunião" semPadding>
                <ul className="m-0 list-none p-0">
                  {r.compromissos.map((cp) => (
                    <ItemCompromisso key={cp.id} cp={cp} somenteLeitura={!podeAgir} mostrarCliente={false} />
                  ))}
                </ul>
              </Secao>
            )}
            {descartados.length > 0 && (
              <Secao id="descartes" titulo="Sinais descartados" sub="A citação devolvida não existe no texto original, então o sinal não aparece na análise">
                {descartados.map((d) => (
                  <div key={d.texto} className="text-[13px] leading-[1.5]">
                    <div className="text-ink line-through decoration-critico">{d.texto}</div>
                    <div className="mt-0.5 text-xs text-critico">Evidência não localizada. {d.motivo}</div>
                  </div>
                ))}
              </Secao>
            )}
          </div>

          {/* Coluna da direita: engajamento, métricas e a situação atual dos temas */}
          <div className="grid content-start gap-4">
            <SecaoEngajamento analise={analise} riscos={riscos.length} oportunidades={oportunidades.length} />
            {r.metricas && <SecaoMetricas mt={r.metricas} onIrAoTurno={r.temTranscricao ? irAoTurno : undefined} />}
            <Secao id="temas-r" titulo="Temas desta reunião, hoje" sub="Situação atual de cada tema no cliente" semPadding>
              {r.temas.length ? (
                <div className={lista}>
                  {r.temas.map((x) => (
                    <ItemTema
                      key={x.tema.id}
                      tema={x.tema}
                      onClick={() => navigate(rotas.cliente(cliente.id, x.tema.id))}
                      mostrarSituacao
                      etiquetasAbaixo
                      detalhe={`turno ${x.citacao.turno} nesta reunião`}
                    />
                  ))}
                </div>
              ) : (
                <Vazio titulo="Nenhum tema" />
              )}
            </Secao>
          </div>
        </div>

        <SecaoTranscricao
          temTranscricao={r.temTranscricao}
          totalTurnos={r.turnos}
          turnos={turnos}
          textosLlm={textosLlm}
          carregando={original.carregando}
          erro={original.erro}
          onTentar={() => void original.recarregar()}
          visao={visao}
          onVisao={(v) => {
            setVisao(v);
            if (v === "llm") setPediuLlm(true);
          }}
          temas={r.temas}
          destaque={destaque}
        />
      </div>
    </>
  );
}
