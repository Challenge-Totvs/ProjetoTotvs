/* Dois gráficos da série semanal do Início: barras (realizadas/analisadas) e linha (engajamento médio).
   Cada um tem um eixo só (nunca dois eixos y na mesma área) — por isso são dois gráficos, não um combinado. */

import { useState } from "react";
import type { PontoSemanal } from "../../types/api";
import { paraData, fmtData } from "../../lib/datas";
import { cx } from "../../lib/formato";

const ALTURA = 160;
const MARGEM = { topo: 10, baixo: 22, esq: 6, dir: 6 };

/** Caminho de uma barra com o topo arredondado e a base encostada na linha de base. */
function barraPath(x: number, yTopo: number, largura: number, altura: number, raio = 4): string {
  if (altura <= 0) return "";
  const r = Math.min(raio, largura / 2, altura);
  const base = yTopo + altura;
  return `M${x},${base} L${x},${yTopo + r} Q${x},${yTopo} ${x + r},${yTopo} L${x + largura - r},${yTopo} Q${x + largura},${yTopo} ${x + largura},${yTopo + r} L${x + largura},${base} Z`;
}

function rotuloSemana(iso: string): string {
  return fmtData(paraData(iso));
}

/** Caixa flutuante com o detalhe do ponto sob o cursor, posicionada perto da marca. */
function Dica({ x, y, titulo, linhas }: { x: number; y: number; titulo: string; linhas: { texto: string; cor?: string }[] }) {
  return (
    <div
      className="pointer-events-none absolute z-10 min-w-[120px] -translate-x-1/2 rounded-md border border-linha bg-branco px-2.5 py-1.5 text-[11.5px] leading-[1.4] text-ink shadow-[0_2px_8px_rgba(0,34,51,.12)]"
      style={{ left: x, top: y, transform: "translate(-50%, -100%)" }}
    >
      <div className="font-semibold">{titulo}</div>
      {linhas.map((l, i) => (
        <div key={i} className={cx("flex items-center gap-1.5", l.cor)}>
          {l.texto}
        </div>
      ))}
    </div>
  );
}

/** Barras agrupadas: reuniões realizadas x analisadas, por semana. */
export function GraficoReunioesSemanais({ semanas }: { semanas: PontoSemanal[] }) {
  const [sobre, setSobre] = useState<number | null>(null);
  const largura = 560;
  const areaL = largura - MARGEM.esq - MARGEM.dir;
  const areaA = ALTURA - MARGEM.topo - MARGEM.baixo;
  const maxValor = Math.max(1, ...semanas.map((s) => s.realizadas));
  const escalaY = (v: number) => areaA - (v / maxValor) * areaA;

  const grupoL = areaL / Math.max(1, semanas.length);
  const barraL = Math.min(18, grupoL / 2 - 3);

  return (
    <div className="relative">
      <svg viewBox={`0 0 ${largura} ${ALTURA}`} className="w-full" role="img" aria-label="Reuniões realizadas e analisadas por semana">
        <g transform={`translate(${MARGEM.esq},${MARGEM.topo})`}>
          {[0, 0.5, 1].map((f) => (
            <line key={f} x1={0} x2={areaL} y1={areaA * f} y2={areaA * f} stroke="var(--color-linha)" strokeWidth={1} />
          ))}
          {semanas.map((s, i) => {
            const cx0 = i * grupoL + grupoL / 2;
            const hR = areaA - escalaY(s.realizadas);
            const hA = areaA - escalaY(s.analisadas);
            return (
              <g
                key={s.inicioSemana}
                onMouseEnter={() => setSobre(i)}
                onMouseLeave={() => setSobre((v) => (v === i ? null : v))}
              >
                <rect x={cx0 - grupoL / 2} y={0} width={grupoL} height={areaA} fill="transparent" />
                <path d={barraPath(cx0 - barraL - 1, escalaY(s.realizadas), barraL, hR)} fill="var(--color-ardosia)" />
                <path d={barraPath(cx0 + 1, escalaY(s.analisadas), barraL, hA)} fill="var(--color-sinal-texto)" />
                <text x={cx0} y={areaA + 15} textAnchor="middle" fontSize={10.5} fill="var(--color-faint)">
                  {rotuloSemana(s.inicioSemana)}
                </text>
              </g>
            );
          })}
        </g>
      </svg>
      {sobre != null && (
        <Dica
          x={MARGEM.esq + sobre * grupoL + grupoL / 2}
          y={MARGEM.topo + escalaY(Math.max(semanas[sobre].realizadas, semanas[sobre].analisadas)) - 6}
          titulo={`Semana de ${rotuloSemana(semanas[sobre].inicioSemana)}`}
          linhas={[
            { texto: `● Realizadas: ${semanas[sobre].realizadas}`, cor: "text-ardosia" },
            { texto: `● Analisadas: ${semanas[sobre].analisadas}`, cor: "text-sinal-texto" },
          ]}
        />
      )}
      <div className="mt-1.5 flex items-center gap-3.5 text-[11.5px] text-ardosia">
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-2 w-2 rounded-[2px]" style={{ background: "var(--color-ardosia)" }} aria-hidden="true" />
          Realizadas
        </span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-2 w-2 rounded-[2px]" style={{ background: "var(--color-sinal-texto)" }} aria-hidden="true" />
          Analisadas
        </span>
      </div>
    </div>
  );
}

/** Linha: engajamento médio (score 0–100) das reuniões analisadas, por semana. Semanas sem score ficam com um vão na linha. */
export function GraficoEngajamentoSemanal({ semanas }: { semanas: PontoSemanal[] }) {
  const [sobre, setSobre] = useState<number | null>(null);
  const largura = 560;
  const areaL = largura - MARGEM.esq - MARGEM.dir;
  const areaA = ALTURA - MARGEM.topo - MARGEM.baixo;
  const passo = areaL / Math.max(1, semanas.length - 1 || 1);
  const escalaY = (v: number) => areaA - (v / 100) * areaA;
  const x = (i: number) => (semanas.length > 1 ? i * passo : areaL / 2);

  // Segmentos contínuos: quebra o traço onde não há score ainda.
  const segmentos: { pontos: [number, number][] }[] = [];
  let atual: [number, number][] = [];
  semanas.forEach((s, i) => {
    if (s.engajamentoMedio == null) {
      if (atual.length) segmentos.push({ pontos: atual });
      atual = [];
      return;
    }
    atual.push([x(i), escalaY(s.engajamentoMedio)]);
  });
  if (atual.length) segmentos.push({ pontos: atual });

  return (
    <div className="relative">
      <svg viewBox={`0 0 ${largura} ${ALTURA}`} className="w-full" role="img" aria-label="Engajamento médio por semana">
        <g transform={`translate(${MARGEM.esq},${MARGEM.topo})`}>
          {[0, 50, 100].map((v) => (
            <g key={v}>
              <line x1={0} x2={areaL} y1={escalaY(v)} y2={escalaY(v)} stroke="var(--color-linha)" strokeWidth={1} />
              <text x={-2} y={escalaY(v) + 3} textAnchor="end" fontSize={10} fill="var(--color-faint)">
                {v}
              </text>
            </g>
          ))}
          {segmentos.map((seg, si) => (
            <polyline
              key={si}
              points={seg.pontos.map(([px, py]) => `${px},${py}`).join(" ")}
              fill="none"
              stroke="var(--color-resolvido)"
              strokeWidth={2}
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          ))}
          {semanas.map((s, i) =>
            s.engajamentoMedio == null ? null : (
              <circle
                key={s.inicioSemana}
                cx={x(i)}
                cy={escalaY(s.engajamentoMedio)}
                r={sobre === i ? 4.5 : 3}
                fill="var(--color-resolvido)"
                onMouseEnter={() => setSobre(i)}
                onMouseLeave={() => setSobre((v) => (v === i ? null : v))}
                style={{ cursor: "pointer" }}
              />
            ),
          )}
          {semanas.map((s, i) => (
            <text key={s.inicioSemana} x={x(i)} y={areaA + 15} textAnchor="middle" fontSize={10.5} fill="var(--color-faint)">
              {rotuloSemana(s.inicioSemana)}
            </text>
          ))}
        </g>
      </svg>
      {sobre != null && semanas[sobre].engajamentoMedio != null && (
        <Dica
          x={MARGEM.esq + x(sobre)}
          y={MARGEM.topo + escalaY(semanas[sobre].engajamentoMedio as number) - 10}
          titulo={`Semana de ${rotuloSemana(semanas[sobre].inicioSemana)}`}
          linhas={[{ texto: `Engajamento médio: ${Math.round(semanas[sobre].engajamentoMedio as number)}`, cor: "text-resolvido" }]}
        />
      )}
    </div>
  );
}
