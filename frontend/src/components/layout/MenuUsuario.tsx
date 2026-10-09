/* Menu do usuário no topo: nome, e-mail, perfil, time e Sair. */

import { useCallback, useRef, useState } from "react";
import { LogOut } from "lucide-react";
import { useApp } from "../../context/AppContext";
import { useFecharFora } from "../../hooks/useFecharFora";
import { Avatar, Etiqueta } from "../ui/base";
import { COR } from "../ui/cores";

export const classeFlutuante =
  "absolute top-[42px] right-0 z-30 max-w-[calc(100vw-24px)] overflow-hidden rounded-[10px] border border-linha bg-branco shadow-[0_12px_32px_rgba(0,34,51,.16)]";

export function MenuUsuario({ onSair }: { onSair: () => void }) {
  const { usuario } = useApp();
  const [aberto, setAberto] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const fechar = useCallback(() => setAberto(false), []);
  useFecharFora(aberto, fechar, ref);
  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => setAberto((a) => !a)}
        aria-expanded={aberto}
        aria-label={`Menu de ${usuario.nome}`}
        className="flex h-[34px] items-center gap-2.5 rounded-lg pr-1 pl-2.5 hover:bg-hover"
      >
        <span className="text-[13px] text-ink max-[900px]:hidden">{usuario.nome}</span>
        <Avatar nome={usuario.nome} tamanho={30} tom="sinal" />
      </button>
      {aberto && (
        <div role="menu" className={classeFlutuante} style={{ width: 260 }}>
          <div className="border-b border-linha px-3.5 py-3">
            <div className="text-[13px] font-semibold text-ink">{usuario.nome}</div>
            <div className="mt-0.5 text-xs text-ardosia">{usuario.email}</div>
            <div className="mt-2 flex gap-1.5">
              <Etiqueta cor={COR.sinal}>{usuario.perfil === "gestor" ? "Gestor" : "Vendedor"}</Etiqueta>
              <Etiqueta>Time {usuario.time}</Etiqueta>
            </div>
          </div>
          <button type="button" role="menuitem" onClick={onSair} className="flex w-full items-center gap-2 px-3.5 py-2.5 text-[13px] text-ink hover:bg-hover">
            <LogOut size={15} aria-hidden="true" />
            Sair
          </button>
        </div>
      )}
    </div>
  );
}
