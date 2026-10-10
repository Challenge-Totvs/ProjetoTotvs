import { Loader2 } from "lucide-react";
import { btnCta } from "../../components/ui/classes";

/** Botão grande de envio das telas de acesso, com o estado de carregamento. */
export function BotaoEnviar({ carregando, rotulo, rotuloCarregando }: { carregando: boolean; rotulo: string; rotuloCarregando: string }) {
  return (
    <button type="submit" className={btnCta} aria-busy={carregando}>
      {carregando ? (
        <>
          <Loader2 size={16} className="animate-giro" aria-hidden="true" />
          {rotuloCarregando}
        </>
      ) : (
        rotulo
      )}
    </button>
  );
}
