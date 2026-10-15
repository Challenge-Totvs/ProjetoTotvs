/* Botão "Relatório (.docx)" — gera o arquivo no navegador (lib/relatorioDocx) e baixa.
   Reaproveitado nas telas de Cliente, Desempenho e Vendedores. */

import { useState } from "react";
import { FileDown, Loader2 } from "lucide-react";
import { btn } from "./classes";
import { cx } from "../../lib/formato";

export function BotaoRelatorio({ rotulo = "Relatório (.docx)", gerar, sm }: { rotulo?: string; gerar: () => Promise<void>; sm?: boolean }) {
  const [gerando, setGerando] = useState(false);
  const [erro, setErro] = useState(false);

  async function aoClicar() {
    setGerando(true);
    setErro(false);
    try {
      await gerar();
    } catch {
      setErro(true);
    } finally {
      setGerando(false);
    }
  }

  return (
    <button type="button" className={cx(btn({ sm }), "disabled:cursor-progress disabled:opacity-70")} disabled={gerando} onClick={() => void aoClicar()} title={erro ? "Não foi possível gerar o relatório. Tente de novo." : undefined}>
      {gerando ? <Loader2 size={14} className="animate-giro" aria-hidden="true" /> : <FileDown size={14} aria-hidden="true" />}
      {erro ? "Tentar de novo" : rotulo}
    </button>
  );
}
