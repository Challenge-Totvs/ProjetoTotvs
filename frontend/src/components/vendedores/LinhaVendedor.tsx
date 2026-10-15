/* Uma linha da tabela de Vendedores: avatar, nome e e-mail, os números da janela,
   "Relatório (.docx)" individual e "Ver visão". */

import { useState, type MouseEvent } from "react";
import { ChevronRight, FileDown, Loader2 } from "lucide-react";
import { Avatar } from "../ui/base";
import { btnIcone, direita, num, td, tr } from "../ui/classes";
import { cx, pct } from "../../lib/formato";
import { relatorioDesempenhoVendedor } from "../../lib/relatorioDocx";
import type { VendedorResumo } from "../../types/api";

/** Célula numérica alinhada à direita, com algarismos de mesma largura. */
const celNum = cx(td, direita, num);

export function LinhaVendedor({ v, janelaDias, selecionada, onAbrir }: { v: VendedorResumo; janelaDias: number; selecionada: boolean; onAbrir: () => void }) {
  const m = v.metricas;
  const [gerando, setGerando] = useState(false);

  async function baixarRelatorio(e: MouseEvent) {
    e.stopPropagation();
    setGerando(true);
    try {
      await relatorioDesempenhoVendedor(v.nome, janelaDias, m);
    } finally {
      setGerando(false);
    }
  }
  return (
    <tr className={tr} aria-selected={selecionada} onClick={onAbrir}>
      <td className={td}>
        <span className="flex items-center gap-2.5">
          <Avatar nome={v.nome} tamanho={28} />
          <span>
            <span className="block font-medium text-ink">{v.nome}</span>
            <span className="block text-xs text-ardosia">{v.email}</span>
          </span>
        </span>
      </td>
      <td className={celNum}>{m.clientes}</td>
      <td className={celNum}>{m.realizadas}</td>
      {/* Riscos e perdidas: coloridos e em negrito quando há algum; cinza quando zero. */}
      <td className={cx(celNum, m.riscosSemRetorno ? "font-semibold text-critico" : "text-faint")}>{m.riscosSemRetorno}</td>
      <td className={cx(celNum, m.oportPerdidas ? "font-semibold text-atencao" : "text-faint")}>{m.oportPerdidas}</td>
      {/* Sem tema citado na janela não há taxa: mostra um travessão. */}
      <td className={celNum}>{m.taxaConversa == null ? "—" : pct(m.taxaConversa)}</td>
      <td className={celNum}>{m.tratadosFora}</td>
      <td className={cx(celNum, m.compromissosVencidos ? "text-critico" : "text-faint")}>{m.compromissosVencidos}</td>
      <td className={cx(td, direita)}>
        <span className="inline-flex items-center gap-1.5 whitespace-nowrap">
          <button type="button" className={btnIcone} title={`Relatório de ${v.nome} (.docx)`} disabled={gerando} onClick={(e) => void baixarRelatorio(e)}>
            {gerando ? <Loader2 size={14} className="animate-giro" aria-hidden="true" /> : <FileDown size={14} aria-hidden="true" />}
          </button>
          <span className="inline-flex items-center gap-1 text-[12.5px] text-sinal-texto">
            Ver visão
            <ChevronRight size={14} aria-hidden="true" />
          </span>
        </span>
      </td>
    </tr>
  );
}
