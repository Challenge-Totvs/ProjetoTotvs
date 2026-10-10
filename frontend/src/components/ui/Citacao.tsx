/* Citação conferida, com "Ver no contexto" (os turnos vizinhos). */

import { useState } from "react";
import { ShieldCheck } from "lucide-react";
import type { Papel, TurnoContexto, TurnoTranscricao } from "../../types/api";
import { rotuloPapel } from "../../lib/dominio";
import { cx } from "../../lib/formato";
import { link } from "./classes";

export interface CitacaoExibida {
  turno: number;
  texto: string;
  conferida?: boolean;
  locutor?: number | null;
  papel?: Papel | null;
  contexto?: TurnoContexto[] | null;
}

export function Citacao({
  cit,
  turnos,
  onAbrirReuniao,
  compacta,
  contextoAberto,
  onAlternarContexto,
}: {
  cit: CitacaoExibida;
  /** Transcrição já carregada na tela (página da reunião). Sem ela, usa o contexto que veio na citação. */
  turnos?: TurnoTranscricao[] | null;
  onAbrirReuniao?: () => void;
  compacta?: boolean;
  /** Controle externo do contexto (painel do tema abre um por vez). */
  contextoAberto?: boolean;
  onAlternarContexto?: () => void;
}) {
  const [aberto, setAberto] = useState(false);
  const mostrar = contextoAberto != null ? contextoAberto : aberto;
  const alternar = onAlternarContexto || (() => setAberto((a) => !a));

  const turnoTexto = turnos ? turnos.find((t) => t.n === cit.turno) : null;
  const conferida = turnoTexto ? turnoTexto.texto.includes(cit.texto) : cit.conferida !== false;
  const loc = turnoTexto ? turnoTexto.locutor : (cit.locutor ?? null);
  const papel = turnoTexto ? turnoTexto.papel : (cit.papel ?? null);

  let contexto: TurnoContexto[] | null = null;
  if (turnos && turnos.length) {
    const ini = Math.max(1, cit.turno - 2);
    const fim = Math.min(turnos.length, cit.turno + 2);
    contexto = turnos.filter((t) => t.n >= ini && t.n <= fim).map((t) => ({ turno: t.n, locutor: t.locutor, papel: t.papel, texto: t.texto }));
  } else if (cit.contexto && cit.contexto.length) {
    contexto = [...cit.contexto].sort((a, b) => a.turno - b.turno);
  }

  return (
    <figure className="m-0">
      <blockquote className="m-0 border-l-2 border-linha-forte py-1.5 pl-3 text-[13.5px] leading-normal text-ink">“{cit.texto}”</blockquote>
      <figcaption className="mt-1.5 flex flex-wrap items-center gap-x-2.5 gap-y-1 text-[11.5px] text-ardosia">
        <span className="tabular-nums">Turno {cit.turno}</span>
        {!compacta && <span>{rotuloPapel(loc, papel)}</span>}
        {conferida ? (
          <span className="inline-flex items-center gap-1 text-resolvido">
            <ShieldCheck size={12} aria-hidden="true" />
            Conferida no texto original
          </span>
        ) : (
          <span className="text-critico">Evidência não localizada</span>
        )}
        {contexto && (
          <button type="button" className={cx(link, "text-[11.5px]")} onClick={alternar} aria-expanded={mostrar}>
            {mostrar ? "Fechar contexto" : "Ver no contexto"}
          </button>
        )}
        {onAbrirReuniao && (
          <button type="button" className={cx(link, "text-[11.5px]")} onClick={onAbrirReuniao}>
            Abrir reunião
          </button>
        )}
      </figcaption>
      {mostrar && contexto && (
        <ol className="mt-2 mb-0 grid list-none gap-0.5 rounded-lg bg-nevoa p-1.5" aria-label="Turnos vizinhos da citação">
          {contexto.map((t) => {
            const citado = t.turno === cit.turno;
            return (
              <li
                key={t.turno}
                className={cx("rounded border-l-2 px-2 py-1.5", citado ? "border-sinal-texto bg-sinal-fundo" : "border-transparent bg-transparent")}
              >
                <span className="text-[11px] text-faint tabular-nums">
                  Turno {t.turno} · {rotuloPapel(t.locutor, t.papel)}
                </span>
                <span className="block text-[12.5px] leading-[1.45] text-ink">{t.texto}</span>
              </li>
            );
          })}
        </ol>
      )}
    </figure>
  );
}
