/* Seção "Transcrição": os turnos da reunião, no texto original ou como a LLM recebeu. */

import { FileText } from "lucide-react";
import type { TemaNaReuniao, TurnoTranscricao } from "../../types/api";
import { rotuloPapel } from "../../lib/dominio";
import { cx } from "../../lib/formato";
import { Aviso, Carregando, ErroCarregar, Secao, Segmentado, Vazio } from "../ui/base";
import { GlifosTema } from "../ui/glifos";

export type VisaoTranscricao = "original" | "llm";

export function SecaoTranscricao({
  temTranscricao,
  totalTurnos,
  turnos,
  textosLlm,
  carregando,
  erro,
  onTentar,
  visao,
  onVisao,
  temas,
  destaque,
}: {
  temTranscricao: boolean;
  /** Número de turnos da reunião, usado no subtítulo enquanto o texto carrega. */
  totalTurnos: number | null;
  /** Turnos no texto original (nulo enquanto carrega). */
  turnos: TurnoTranscricao[] | null;
  /** Texto de cada turno como a LLM recebeu (já pseudonimizado pelo backend). */
  textosLlm: Map<number, string> | null;
  carregando: boolean;
  erro: string | null;
  onTentar: () => void;
  visao: VisaoTranscricao;
  onVisao: (v: VisaoTranscricao) => void;
  /** Temas desta reunião, para marcar os turnos citados. */
  temas: TemaNaReuniao[];
  destaque: number | null;
}) {
  // Temas citados em cada turno: o turno ganha fundo e os chips dos temas.
  const citadosNoTurno = new Map<number, TemaNaReuniao[]>();
  for (const x of temas) citadosNoTurno.set(x.citacao.turno, [...(citadosNoTurno.get(x.citacao.turno) ?? []), x]);

  // Na versão da LLM, troca o texto do turno; enquanto não chega, mostra o original.
  const textoTurno = (t: TurnoTranscricao) => (visao === "llm" && textosLlm ? (textosLlm.get(t.n) ?? t.texto) : t.texto);

  let conteudo;
  if (!temTranscricao) {
    conteudo = (
      <Vazio icone={FileText} titulo="Sem a transcrição completa" texto="Os trechos citados aparecem nos temas, com os turnos vizinhos quando existem." />
    );
  } else if (!turnos) {
    conteudo = carregando || !erro ? <Carregando /> : <ErroCarregar mensagem={erro} onTentar={onTentar} />;
  } else {
    conteudo = (
      <>
        {visao === "llm" && (
          <div className="px-4 pt-3">
            <Aviso tom="info">
              Antes de qualquer chamada a LLM externa, nomes de pessoas, empresas e lugares viram pseudônimos estáveis e tipados. O texto original fica
              só no InsightCall.
            </Aviso>
          </div>
        )}
        <ol className="m-0 max-h-[520px] list-none overflow-y-auto py-1.5">
          {turnos.map((t) => {
            const cit = citadosNoTurno.get(t.n);
            return (
              <li
                key={t.n}
                id={`turno-${t.n}`}
                className={cx(
                  "flex gap-3 border-l-[3px] px-4 py-2",
                  destaque === t.n ? "border-sinal-texto bg-sinal-fundo" : cit ? "border-transparent bg-citado" : "border-transparent",
                )}
              >
                <span className="w-7 flex-none pt-0.5 text-right text-[11.5px] text-faint tabular-nums">{t.n}</span>
                <span className="min-w-0 flex-1">
                  <span className="flex flex-wrap items-center gap-2">
                    <span className="text-[11.5px] font-semibold text-ardosia">{rotuloPapel(t.locutor, t.papel)}</span>
                    {cit?.map((x) => (
                      <span key={x.tema.id} className="inline-flex items-center gap-1 text-[11.5px] text-ink">
                        <GlifosTema tipos={x.tema.tipos} tratado={x.citacao.tratado} tamanho={10} />
                        {x.tema.titulo}
                      </span>
                    ))}
                  </span>
                  <span className="mt-0.5 block text-[13.5px] leading-[1.55] text-ink">{textoTurno(t)}</span>
                </span>
              </li>
            );
          })}
        </ol>
      </>
    );
  }

  return (
    <Secao
      id="transcricao"
      titulo="Transcrição"
      sub={
        temTranscricao
          ? `${turnos?.length ?? totalTurnos ?? 0} turnos no formato do dataset, [LOCUTOR n]`
          : "Transcrição completa indisponível para esta reunião"
      }
      acao={
        temTranscricao && (
          <Segmentado
            rotulo="Versão da transcrição"
            valor={visao}
            onChange={onVisao}
            opcoes={[
              ["original", "Texto original"],
              ["llm", "Como a LLM recebeu"],
            ]}
          />
        )
      }
      semPadding
    >
      {conteudo}
    </Secao>
  );
}
