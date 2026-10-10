/* Facetas da lista de clientes do gestor: grupos de caixas de marcar (Tipo, Situação, Vendedor, Segmento). */

import { Check } from "lucide-react";
import type { Facetas, GrupoFaceta, GrupoOpcoes } from "./facetas";
import { link } from "../ui/classes";

export function FacetasClientes({
  grupos,
  marcadas,
  contar,
  onAlternar,
  onLimpar,
}: {
  grupos: GrupoOpcoes[];
  marcadas: Facetas;
  /** Quantos clientes ficariam com este valor marcado (considerando os outros grupos e a busca). */
  contar: (grupo: GrupoFaceta, valor: string) => number;
  onAlternar: (grupo: GrupoFaceta, valor: string) => void;
  /** Só aparece o "Limpar filtros" quando há busca ou faceta marcada. */
  onLimpar: (() => void) | null;
}) {
  return (
    // Coluna fixa de 200px; em telas estreitas vira uma grade em cima da tabela.
    <aside
      aria-label="Facetas"
      className="sticky top-0 w-[200px] flex-none ate-1024:static ate-1024:grid ate-1024:w-full ate-1024:grid-cols-[repeat(auto-fit,minmax(180px,1fr))] ate-1024:gap-x-4 ate-1024:gap-y-0"
    >
      {grupos.map(([g, titulo, valores]) => (
        <div key={g} className="mb-3.5">
          <div className="mt-0 mr-0 mb-1 ml-1.5 text-[11px] font-semibold tracking-[0.04em] text-faint uppercase">{titulo}</div>
          {valores.map(([v, l]) => {
            const n = contar(g, v);
            const ativo = marcadas[g].includes(v);
            return (
              // Valor sem nenhum cliente fica desabilitado (a não ser que já esteja marcado).
              <button
                key={v}
                type="button"
                className="group flex w-full items-center gap-2 rounded-md px-1.5 py-[5px] text-left text-[12.5px] text-ink enabled:hover:bg-hover"
                aria-pressed={ativo}
                onClick={() => onAlternar(g, v)}
                disabled={!n && !ativo}
              >
                {/* Caixinha: branca, ou azul com o check quando marcada */}
                <span
                  className="inline-flex h-3.5 w-3.5 flex-none items-center justify-center rounded-[3px] border border-linha-forte bg-branco group-aria-pressed:border-sinal-texto group-aria-pressed:bg-sinal-texto group-aria-pressed:text-branco"
                  aria-hidden="true"
                >
                  {ativo && <Check size={11} />}
                </span>
                <span className="min-w-0 flex-1 truncate">{l}</span>
                <span className="text-faint tabular-nums">{n}</span>
              </button>
            );
          })}
        </div>
      ))}
      {onLimpar && (
        <button type="button" className={`${link} text-[12.5px]`} onClick={onLimpar}>
          Limpar filtros
        </button>
      )}
    </aside>
  );
}
