/* Moldura das telas de acesso (Figma 01 e 02): painel da marca à esquerda e formulário à direita.
   Abaixo de 1.024 px o painel some e o formulário centraliza, com o logo em cima. */

import type { ReactNode } from "react";
import { Logo } from "../../components/ui/base";

/** Foto do painel de marca: trocar pelo asset do Figma ("image 3"). Sem foto, usa a cor sólida da marca. */
const FOTO_LOGIN: string | null = null;

export function LayoutAcesso({ titulo, texto, children }: { titulo: string; texto: string; children: ReactNode }) {
  const fundo = FOTO_LOGIN
    ? { background: `linear-gradient(rgba(0,34,51,.8), rgba(0,34,51,.8)), url(${FOTO_LOGIN}) center / cover` }
    : undefined;
  return (
    <div className="flex min-h-screen bg-branco">
      <aside className="flex w-[41.7%] flex-none items-center bg-ink px-[72px] py-12 text-branco ate-1024:hidden" style={fundo}>
        <div className="max-w-[440px]">
          <Logo claro />
          <p className="mt-[22px] mb-0 text-[36px] leading-[1.15] font-semibold tracking-[-0.02em]">{titulo}</p>
          <p className="mt-4 mb-0 text-[15px] leading-[1.55] text-marca-texto">{texto}</p>
        </div>
      </aside>
      <main className="flex flex-1 items-center justify-center px-4 py-12">
        <div className="w-full max-w-[380px]">
          <div className="mb-7 hidden ate-1024:block">
            <Logo />
          </div>
          {children}
        </div>
      </main>
    </div>
  );
}
