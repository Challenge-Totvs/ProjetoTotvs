/* Coluna da direita da reunião: engajamento (score) e métricas da conversa. */

import type { Analise, MetricasConversa } from "../../types/api";
import { plural } from "../../lib/formato";
import { Secao } from "../ui/base";
import { BarraFala } from "../ui/graficos";
import { btn, rotuloMetrica } from "../ui/classes";

const linhaMetrica = "flex items-center justify-between gap-2.5";
const valorMetrica = "text-[13.5px] text-ink tabular-nums";

/** Score de engajamento de 0 a 100, com a barra e de onde ele vem. */
export function SecaoEngajamento({ analise, riscos, oportunidades }: { analise: Analise; riscos: number; oportunidades: number }) {
  const score = analise.score ?? 0;
  return (
    <Secao id="score" titulo="Engajamento">
      <div className="flex items-baseline gap-1.5">
        <span className="text-[32px] font-semibold text-ink tabular-nums">{analise.score}</span>
        <span className="text-[13px] text-ardosia">de 100</span>
      </div>
      <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-hover">
        <span className="block h-full bg-ink" style={{ width: `${score}%` }} />
      </div>
      <p className="mt-2 mb-0 text-[12.5px] leading-[1.5] text-ardosia">
        Baseado em {plural(analise.interesse.length, "sinal de interesse", "sinais de interesse")}, {plural(riscos, "risco", "riscos")} e{" "}
        {plural(oportunidades, "oportunidade", "oportunidades")}.{analise.sentimento && ` Sentimento geral ${analise.sentimento}, estimativa da LLM.`}
      </p>
    </Secao>
  );
}

/** Métricas por volume de fala. Os botões "Ir ao turno" só aparecem com a transcrição. */
export function SecaoMetricas({ mt, onIrAoTurno }: { mt: MetricasConversa; onIrAoTurno?: (n: number) => void }) {
  // Sem papéis inferidos, mostra a fatia de cada locutor: "L1 58% · L2 28% · L3 15%".
  const porLocutor = Object.entries(mt.porLocutor)
    .map(([l, w]) => `L${l} ${Math.round((w / mt.total) * 100)}%`)
    .join(" · ");
  const mm = mt.maiorMonologo;
  const mc = mt.maiorFalaCliente;
  return (
    <Secao id="metricas" titulo="Métricas da conversa" sub="Por volume de fala, em palavras: a transcrição não tem horário">
      <div className="grid gap-3.5">
        <div>
          <div className={rotuloMetrica}>Fala por papel</div>
          {mt.papeisInferidos ? (
            <BarraFala vendedor={mt.falaVendedor} />
          ) : (
            <span className="text-[12.5px] text-faint">O motor não inferiu os papéis. Por locutor: {porLocutor}</span>
          )}
        </div>
        <div className={linhaMetrica}>
          <div>
            <div className={rotuloMetrica}>Maior monólogo</div>
            <div className={valorMetrica}>
              {mm.palavras} palavras · {mm.papel ? mm.papel : `locutor ${mm.locutor}`} · turno {mm.turno}
            </div>
          </div>
          {onIrAoTurno && (
            <button type="button" className={btn({ sm: true })} onClick={() => onIrAoTurno(mm.turno)}>
              Ir ao turno
            </button>
          )}
        </div>
        {mc && (
          <div className={linhaMetrica}>
            <div>
              <div className={rotuloMetrica}>Maior fala do cliente</div>
              <div className={valorMetrica}>
                {mc.palavras} palavras · turno {mc.turno}
              </div>
            </div>
            {onIrAoTurno && (
              <button type="button" className={btn({ sm: true })} onClick={() => onIrAoTurno(mc.turno)}>
                Ir ao turno
              </button>
            )}
          </div>
        )}
        <div className={linhaMetrica}>
          <div>
            <div className={rotuloMetrica}>Trocas de locutor por minuto</div>
            <div className={valorMetrica}>{mt.trocasPorMin == null ? "Sem a duração da reunião" : mt.trocasPorMin.toFixed(1).replace(".", ",")}</div>
          </div>
        </div>
        {mt.perguntas && (
          <div className={linhaMetrica}>
            <div>
              <div className={rotuloMetrica}>Perguntas, estimativa</div>
              <div className={valorMetrica}>
                vendedor {mt.perguntas.vendedor} · cliente {mt.perguntas.cliente}
              </div>
            </div>
          </div>
        )}
      </div>
    </Secao>
  );
}
