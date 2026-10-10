/* Mapa de temas do cliente: uma linha por tema, uma coluna por reunião analisada.
   Em cada reunião, o glifo da citação (ou um traço quando o tema não foi citado). */

import { useNavigate } from "react-router-dom";
import type { Citacao, Id, ReuniaoItem, Tema } from "../../types/api";
import { fmtData, fmtDataAno, paraData } from "../../lib/datas";
import { rotas } from "../../lib/rotas";
import { linkNeutro } from "../ui/classes";
import { ChipRecorrente, GlifosTema, TagSituacao } from "../ui/glifos";
import { cx } from "../../lib/formato";

/** Linha do mapa (cabeçalho ou tema). As colunas vêm do style, porque dependem do número de reuniões. */
const linha = "grid items-center gap-1.5 border-t border-linha px-2.5 py-[9px]";

export function MapaTemas({
  clienteNome,
  temas,
  reunioes,
  selId,
  onSelecionar,
  maxColunas = 6,
}: {
  clienteNome: string;
  temas: Tema[];
  /** Reuniões analisadas do cliente, da mais antiga para a mais recente. */
  reunioes: ReuniaoItem[];
  selId: Id | null;
  onSelecionar: (id: Id) => void;
  maxColunas?: number;
}) {
  const navigate = useNavigate();
  // Só as últimas reuniões cabem; as anteriores ficam ocultas (e contadas no cabeçalho).
  const colunas = reunioes.slice(-maxColunas);
  const ocultas = reunioes.length - colunas.length;
  const grade = `minmax(170px, 1.5fr) repeat(${colunas.length}, 52px) minmax(150px, 1fr)`;
  if (!temas.length) return null;

  return (
    <div className="overflow-x-auto">
      <div className="grid" role="grid" aria-label={`Mapa de temas de ${clienteNome}`} style={{ minWidth: 350 + colunas.length * 58 }}>
        {/* Cabeçalho: "Tema", as datas das reuniões e "Situação" */}
        <div className={cx(linha, "border-t-0 pt-0 text-[11.5px] font-semibold text-ardosia")} role="row" style={{ gridTemplateColumns: grade }}>
          <span role="columnheader">Tema{ocultas > 0 ? ` · ${ocultas} reuniões anteriores ocultas` : ""}</span>
          {colunas.map((r) => {
            const data = paraData(r.dataHora);
            return (
              <span role="columnheader" key={r.id} className="text-center">
                <button
                  type="button"
                  className={cx(linkNeutro, "text-[11.5px] text-ardosia tabular-nums")}
                  onClick={() => navigate(rotas.reuniao(r.id))}
                  title={`${r.titulo} · ${fmtDataAno(data)}`}
                >
                  {fmtData(data)}
                </button>
              </span>
            );
          })}
          <span role="columnheader">Situação</span>
        </div>

        {/* Uma linha por tema */}
        {temas.map((t) => {
          const sel = t.id === selId;
          // Citação do tema em cada reunião, para achar rápido por coluna.
          const porReuniao: Record<Id, Citacao> = {};
          for (const c of t.citacoes) porReuniao[c.reuniaoId] = c;
          return (
            <div
              key={t.id}
              role="row"
              aria-selected={sel}
              className={cx(
                linha,
                "cursor-pointer rounded-md aria-selected:bg-sinal-fundo aria-selected:shadow-[inset_3px_0_0_var(--color-sinal-texto)] [&:not([aria-selected=true])]:hover:bg-nevoa",
              )}
              style={{ gridTemplateColumns: grade }}
              onClick={() => onSelecionar(t.id)}
              tabIndex={-1}
            >
              <span role="gridcell" className="min-w-0">
                <button
                  type="button"
                  className="text-left text-[13.5px] leading-[1.35] font-medium text-ink"
                  onClick={(e) => {
                    e.stopPropagation();
                    onSelecionar(t.id);
                  }}
                  aria-pressed={sel}
                >
                  {t.titulo}
                </button>
                <span className="mt-0.5 block text-[11.5px] text-ardosia">
                  {t.tipos.map((x) => (x === "risco" ? "Risco" : "Oportunidade")).join(" e ")}
                  {t.semelhanteNaoProcede && !t.naoProcede ? " · parecido com não procede" : ""}
                </span>
              </span>
              {colunas.map((r) => {
                const c = porReuniao[r.id];
                return (
                  <span role="gridcell" key={r.id} className="flex justify-center">
                    {c ? (
                      <GlifosTema tipos={t.tipos} tratado={c.tratado} tamanho={13} />
                    ) : (
                      <span className="block h-px w-2.5 bg-linha-forte" aria-label="Não citado" role="img" />
                    )}
                  </span>
                );
              })}
              <span role="gridcell" className="flex flex-wrap items-center gap-1">
                <TagSituacao tema={t} compacta />
                {t.recorrente && <ChipRecorrente n={t.reunioesNaJanela} />}
                {t.venceEm != null && (
                  <span className="text-[11.5px] whitespace-nowrap text-atencao">{t.venceEm === 1 ? "perde amanhã" : `perde em ${t.venceEm} d`}</span>
                )}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
