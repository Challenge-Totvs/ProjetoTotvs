import { useEffect, type RefObject } from "react";

/** Fecha um menu flutuante ao clicar fora dele ou apertar Esc. */
export function useFecharFora(aberto: boolean, fechar: () => void, ref: RefObject<HTMLElement | null>) {
  useEffect(() => {
    if (!aberto) return undefined;
    const fora = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) fechar();
    };
    const esc = (e: KeyboardEvent) => {
      if (e.key === "Escape") fechar();
    };
    document.addEventListener("mousedown", fora);
    document.addEventListener("keydown", esc);
    return () => {
      document.removeEventListener("mousedown", fora);
      document.removeEventListener("keydown", esc);
    };
  }, [aberto, fechar, ref]);
}
