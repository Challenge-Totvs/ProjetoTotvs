/* Pequenos gráficos: fala por papel, histograma em terços, distribuição e a régua da conversa. */

import type { MarcaRegua } from "../../types/api";
import { estadoCitacao } from "../../lib/dominio";
import { Glifo } from "./glifos";

/* ---------- Fala por papel ---------- */

export function BarraFala({ vendedor, rotulos = ["Vendedor", "Cliente"] }: { vendedor: number | null; rotulos?: [string, string] }) {
  if (vendedor == null) return <span className="text-xs text-faint">Sem papéis inferidos</span>;
  const v = Math.round(vendedor * 100);
  return (
    <div>
      <div
        className="flex h-2 overflow-hidden rounded-full bg-hover"
        role="img"
        aria-label={`${rotulos[0]} ${v}% das palavras, ${rotulos[1]} ${100 - v}%`}
      >
        <span className="bg-ink" style={{ width: `${v}%` }} />
        <span className="bg-fala-cliente" style={{ width: `${100 - v}%` }} />
      </div>
      <div className="mt-1 flex justify-between text-xs text-ardosia tabular-nums">
        <span>
          {rotulos[0]} {v}%
        </span>
        <span>
          {rotulos[1]} {100 - v}%
        </span>
      </div>
    </div>
  );
}

/* ---------- Onde na conversa (início, meio e fim) ---------- */

export function MiniHistograma({ terco }: { terco: [number, number, number] }) {
  const max = Math.max(1, ...terco);
  const nomes = ["início", "meio", "fim"];
  return (
    <span
      role="img"
      aria-label={`Onde na conversa: ${terco.map((n, i) => `${n} no ${nomes[i]}`).join(", ")}`}
      className="inline-flex h-5 items-end gap-[3px]"
    >
      {terco.map((n, i) => (
        <span
          key={i}
          title={`${n} no ${nomes[i]}`}
          className={n ? "w-2.5 rounded-xs bg-ardosia" : "w-2.5 rounded-xs bg-linha"}
          style={{ height: Math.max(2, Math.round((n / max) * 20)) }}
        />
      ))}
    </span>
  );
}

/* ---------- Distribuição (barras horizontais) ---------- */

export function Distribuicao({ itens, total }: { itens: [string, number][]; total?: number }) {
  const max = Math.max(1, ...itens.map((x) => x[1]));
  return (
    <ul className="m-0 grid list-none gap-1.5 p-0">
      {itens.map(([rotulo, n]) => (
        <li key={rotulo} className="grid grid-cols-[minmax(0,1fr)_90px_28px] items-center gap-2 text-[12.5px]">
          <span className="truncate text-ink">{rotulo}</span>
          <span className="h-1.5 overflow-hidden rounded-full bg-hover">
            <span className="block h-full bg-ardosia" style={{ width: `${(n / max) * 100}%` }} />
          </span>
          <span className="text-right text-ardosia tabular-nums">{n}</span>
        </li>
      ))}
      {!itens.length && <li className="text-[12.5px] text-faint">Sem dados {total === 0 ? "neste recorte" : ""}</li>}
    </ul>
  );
}

/* ---------- Régua da conversa: posição do turno, nunca minuto ---------- */

interface MarcaPosicionada extends MarcaRegua {
  chave: string;
  pos: number;
  linha: number;
}

/** Empilha marcas muito próximas em até três linhas, para não se sobreporem. */
function posicionar(marcas: MarcaRegua[], N: number): MarcaPosicionada[] {
  const ordenadas = marcas
    .map((m, i) => ({ ...m, chave: `${m.temaId ?? "int"}-${m.turno}-${m.tipo}-${i}`, pos: Math.min(1, Math.max(0, (m.turno - 0.5) / N)), linha: 0 }))
    .sort((a, b) => a.pos - b.pos);
  const ultimaPorLinha: (number | undefined)[] = [];
  return ordenadas.map((m) => {
    let linha = 0;
    while (linha < 3 && ultimaPorLinha[linha] != null && m.pos - (ultimaPorLinha[linha] as number) < 0.022) linha += 1;
    if (linha > 2) linha = 2;
    ultimaPorLinha[linha] = m.pos;
    return { ...m, linha };
  });
}

const estadoMarca = (m: MarcaRegua) => (m.tipo === "interesse" ? "aberto" : estadoCitacao(m.tratado));

export function Regua({
  turnos,
  marcas,
  serie,
  destaque,
  onMarca,
  mini,
  rotulo,
}: {
  turnos: number | null;
  marcas: MarcaRegua[];
  serie?: [number, number][] | null;
  destaque?: number | null;
  onMarca?: (m: MarcaRegua) => void;
  mini?: boolean;
  rotulo?: string;
}) {
  const N = Math.max(1, turnos || 1);
  const ms = posicionar(marcas, N);

  if (mini) {
    return (
      <div className="relative mt-[5px] h-3 w-[120px]" role="img" aria-label={rotulo || `Régua da conversa com ${marcas.length} marcas`}>
        <span className="absolute top-1.5 right-0 left-0 h-px rounded-sm bg-linha" />
        {ms.map((m) => (
          <span key={m.chave} className="absolute -translate-x-1/2" style={{ left: `${m.pos * 100}%`, top: 3 - m.linha * 3 }}>
            <Glifo tipo={m.tipo} estado={estadoMarca(m)} tamanho={8} />
          </span>
        ))}
      </div>
    );
  }

  const pontos =
    serie && serie.length > 1 ? serie.map(([t, v]) => `${(((t - 0.5) / N) * 100).toFixed(2)},${(20 - v * 16).toFixed(2)}`).join(" ") : null;

  return (
    <div>
      {pontos && (
        <div className="mb-0.5">
          <div className="flex justify-between text-[11px] text-faint">
            <span>Sentimento do cliente, estimativa da LLM</span>
            <span>linha tracejada: neutro</span>
          </div>
          <svg
            width="100%"
            height="36"
            viewBox="0 0 100 40"
            preserveAspectRatio="none"
            role="img"
            aria-label="Curva do sentimento do cliente ao longo da reunião"
            className="mt-0.5 block"
          >
            <line x1="0" x2="100" y1="20" y2="20" stroke="#e1e7eb" strokeDasharray="2 2" vectorEffect="non-scaling-stroke" />
            <polyline points={pontos} fill="none" stroke="#007399" strokeWidth="1.5" vectorEffect="non-scaling-stroke" strokeLinejoin="round" />
          </svg>
        </div>
      )}
      <div className="relative" style={{ height: 40 + 8 * Math.max(0, ...ms.map((m) => m.linha)) }}>
        <span className="absolute top-5 right-0 left-0 h-0.5 rounded-sm bg-linha" />
        {destaque != null && (
          <span
            aria-hidden="true"
            className="absolute top-1 bottom-1 w-0.5 -translate-x-px rounded-sm bg-sinal-texto"
            style={{ left: `${((destaque - 0.5) / N) * 100}%` }}
          />
        )}
        {ms.map((m) => (
          <button
            key={m.chave}
            type="button"
            className="absolute flex h-[18px] w-[18px] -translate-x-1/2 items-center justify-center rounded hover:bg-hover"
            onClick={() => onMarca && onMarca(m)}
            aria-label={`Turno ${m.turno}: ${m.titulo}`}
            title={`Turno ${m.turno} · ${m.titulo}`}
            style={{ left: `${m.pos * 100}%`, top: 13 + m.linha * 9 }}
          >
            <Glifo tipo={m.tipo} estado={estadoMarca(m)} tamanho={13} />
          </button>
        ))}
      </div>
      <div className="mt-1 flex justify-between text-[11px] text-faint tabular-nums">
        <span>Turno 1 · início</span>
        <span>meio</span>
        <span>fim · turno {N}</span>
      </div>
    </div>
  );
}
