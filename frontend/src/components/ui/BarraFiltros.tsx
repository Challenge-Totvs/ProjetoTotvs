/* Barra de busca com filtros embutidos: campo de texto + chips removíveis por valor marcado +
   botão "Filtro" que abre um pop-up de dois níveis (escolher o campo, depois o(s) valor(es)),
   como na demo. Substitui a antiga coluna fixa de facetas (sidebar de caixas de marcar) e os
   filtros de um só valor por vez, para o mesmo padrão em qualquer tela com lista filtrável. */

import { useEffect, useRef, useState } from "react";
import { ChevronLeft, ListFilter, X } from "lucide-react";
import { cx } from "../../lib/formato";
import { barraFerramentas, btn, link } from "./classes";

/** Um grupo de filtro: chave, título e as opções [valor, rótulo]. Mesmo formato de `GrupoOpcoes`. */
export type GrupoFiltro<G extends string = string> = [G, string, [string, string][]];

export function BarraFiltros<G extends string>({
  campoBusca,
  grupos,
  marcadas,
  onAlternar,
  contar,
  onLimpar,
  extra,
}: {
  /** O próprio campo de busca (label com ícone e input), já pronto — cada tela mantém seu placeholder e aria-label. */
  campoBusca: React.ReactNode;
  grupos: GrupoFiltro<G>[];
  marcadas: Record<G, string[]>;
  onAlternar: (grupo: G, valor: string) => void;
  /** Quantos itens ficariam com este valor marcado (considerando os outros filtros e a busca). Opcional. */
  contar?: (grupo: G, valor: string) => number;
  /** Só aparece o "Limpar filtros" quando há busca ou algum valor marcado. */
  onLimpar: (() => void) | null;
  /** Controles à direita da barra que não são filtro (ex.: ordenar, agrupar por, contagem). */
  extra?: React.ReactNode;
}) {
  const [aberto, setAberto] = useState(false);
  const [campoAberto, setCampoAberto] = useState<G | null>(null);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!aberto) return;
    const fora = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setAberto(false);
        setCampoAberto(null);
      }
    };
    const esc = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setAberto(false);
        setCampoAberto(null);
      }
    };
    document.addEventListener("mousedown", fora);
    document.addEventListener("keydown", esc);
    return () => {
      document.removeEventListener("mousedown", fora);
      document.removeEventListener("keydown", esc);
    };
  }, [aberto]);

  // Um chip por valor marcado, em qualquer grupo.
  const chips: { grupo: G; valor: string; rotulo: string }[] = [];
  for (const [chave, titulo, opcoes] of grupos) {
    for (const v of marcadas[chave] || []) {
      chips.push({ grupo: chave, valor: v, rotulo: `${titulo}: ${opcoes.find(([val]) => val === v)?.[1] ?? v}` });
    }
  }

  const grupoAberto = campoAberto != null ? grupos.find(([chave]) => chave === campoAberto) : null;

  return (
    <div className={barraFerramentas}>
      {campoBusca}

      {chips.map((c) => (
        <button
          key={`${c.grupo}:${c.valor}`}
          type="button"
          className="inline-flex items-center gap-1 rounded-full border border-sinal-texto bg-sinal-fundo px-2.5 py-1 text-[12px] text-sinal-texto hover:bg-branco"
          onClick={() => onAlternar(c.grupo, c.valor)}
          title="Remover este filtro"
        >
          {c.rotulo}
          <X size={11} aria-hidden="true" />
        </button>
      ))}

      <div className="relative" ref={ref}>
        <button
          type="button"
          className={btn({ sm: true })}
          onClick={() => {
            setAberto((a) => !a);
            setCampoAberto(null);
          }}
          aria-expanded={aberto}
          aria-haspopup="true"
        >
          <ListFilter size={13} aria-hidden="true" />
          Filtro
        </button>
        {aberto && (
          <div
            role="menu"
            className="absolute top-[calc(100%+6px)] left-0 z-20 w-[240px] rounded-lg border border-linha bg-branco p-1.5 shadow-[0_8px_24px_rgba(0,34,51,.18)]"
          >
            {!grupoAberto ? (
              grupos.map(([chave, titulo]) => (
                <button
                  key={chave}
                  type="button"
                  className="flex w-full items-center justify-between rounded-md px-2 py-1.5 text-left text-[13px] text-ink hover:bg-nevoa"
                  onClick={() => setCampoAberto(chave)}
                >
                  {titulo}
                  {!!marcadas[chave]?.length && <span className="text-xs text-ardosia tabular-nums">{marcadas[chave].length}</span>}
                </button>
              ))
            ) : (
              <>
                <button
                  type="button"
                  className="mb-1 flex w-full items-center gap-1 rounded-md px-2 py-1 text-left text-[12px] font-semibold text-ardosia hover:bg-nevoa"
                  onClick={() => setCampoAberto(null)}
                >
                  <ChevronLeft size={13} aria-hidden="true" />
                  {grupoAberto[1]}
                </button>
                <div className="max-h-[260px] overflow-y-auto">
                  {grupoAberto[2].map(([v, l]) => {
                    const ativo = !!marcadas[grupoAberto[0]]?.includes(v);
                    const n = contar?.(grupoAberto[0], v);
                    return (
                      <label
                        key={v}
                        className={cx(
                          "flex w-full cursor-pointer items-center gap-2 rounded-md px-2 py-1.5 text-left text-[13px] text-ink hover:bg-nevoa",
                          !n && !ativo && "opacity-50",
                        )}
                      >
                        <input type="checkbox" className="accent-sinal-texto" checked={ativo} onChange={() => onAlternar(grupoAberto[0], v)} />
                        <span className="min-w-0 flex-1 truncate">{l}</span>
                        {n != null && <span className="text-xs text-faint tabular-nums">{n}</span>}
                      </label>
                    );
                  })}
                </div>
              </>
            )}
          </div>
        )}
      </div>

      {onLimpar && (
        <button type="button" className={cx(link, "text-[12.5px]")} onClick={onLimpar}>
          Limpar filtros
        </button>
      )}

      {extra}
    </div>
  );
}
