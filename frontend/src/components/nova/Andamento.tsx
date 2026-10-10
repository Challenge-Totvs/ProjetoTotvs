/* Tela de andamento da análise (Nova transcrição): cronômetro e etapas. */

import { AlertTriangle, CheckCircle2, Circle, Loader2 } from "lucide-react";
import { CabecalhoPagina, Secao } from "../ui/base";
import { btn } from "../ui/classes";
import { pad } from "../../lib/datas";
import { cx } from "../../lib/formato";
import type { EstadoEtapa, Etapa } from "./etapas";

/** Ícone de cada estado da etapa. */
function IconeEtapa({ estado }: { estado: EstadoEtapa }) {
  if (estado === "rodando") return <Loader2 size={15} className="animate-giro text-sinal-texto" aria-label="em andamento" />;
  if (estado === "ok") return <CheckCircle2 size={15} className="text-resolvido" aria-label="concluída" />;
  if (estado === "falhou") return <AlertTriangle size={15} className="text-atencao" aria-label="falhou" />;
  return <Circle size={15} className="text-linha-forte" aria-label="pendente" />;
}

export function Andamento({ etapas, segundos, onCancelar }: { etapas: Etapa[]; segundos: number; onCancelar: () => void }) {
  return (
    <>
      <CabecalhoPagina
        titulo="Analisando a transcrição"
        texto="A análise roda em segundo plano. Você pode sair desta tela; o aviso chega quando terminar."
      />
      <Secao
        id="proc"
        titulo="Andamento"
        acao={
          // Cronômetro mm:ss desde o envio.
          <span className="text-[13px] text-ardosia tabular-nums">
            {pad(Math.floor(segundos / 60))}:{pad(segundos % 60)}
          </span>
        }
      >
        <ol className="m-0 grid list-none gap-2.5 p-0" aria-live="polite">
          {etapas.map((et) => (
            <li key={et.id} className={cx("flex items-start gap-2.5 text-[13.5px]", et.estado === "pendente" ? "text-faint" : "text-ink")}>
              <span className="flex w-[18px] justify-center pt-px">
                <IconeEtapa estado={et.estado} />
              </span>
              <span>
                {et.rotulo}
                {et.estado === "falhou" && et.falha && <span className="mt-0.5 block text-[12.5px] text-atencao">{et.falha}</span>}
              </span>
            </li>
          ))}
        </ol>
        <div className="mt-4">
          <button type="button" className={btn()} onClick={onCancelar}>
            Cancelar análise
          </button>
        </div>
      </Secao>
    </>
  );
}
