/* Modal, painel lateral recolhível, botão do painel e grupo de opções. */

import { useEffect, useRef, type ReactNode } from "react";
import { PanelRightClose, PanelRightOpen, X, type LucideIcon } from "lucide-react";
import { cx } from "../../lib/formato";
import { Kbd } from "./base";
import { btn, btnIcone } from "./classes";

/** Janela de diálogo. Fecha com Esc ou clicando fora. */
export function Modal({
  titulo,
  descricao,
  onFechar,
  children,
  largura = 520,
}: {
  titulo: string;
  descricao?: ReactNode;
  onFechar: () => void;
  children: ReactNode;
  largura?: number;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const fechar = useRef(onFechar);
  useEffect(() => {
    fechar.current = onFechar;
  }, [onFechar]);

  useEffect(() => {
    // Foco inicial: o elemento marcado com data-autofoco, ou o primeiro campo.
    const el = ref.current;
    if (el) {
      const foco = el.querySelector<HTMLElement>("[data-autofoco]") || el.querySelector<HTMLElement>("input, textarea, select, button[role='radio']");
      if (foco) foco.focus();
    }
    const esc = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.stopPropagation();
        fechar.current();
      }
    };
    document.addEventListener("keydown", esc, true);
    return () => document.removeEventListener("keydown", esc, true);
  }, []);

  return (
    <div
      className="fixed inset-0 z-60 flex items-center justify-center bg-[rgba(0,34,51,.32)] p-4"
      onMouseDown={(e) => e.target === e.currentTarget && onFechar()}
    >
      <div
        ref={ref}
        role="dialog"
        aria-modal="true"
        aria-label={titulo}
        className="max-w-full overflow-hidden rounded-xl border border-linha bg-branco shadow-[0_16px_40px_rgba(0,34,51,.22)]"
        style={{ width: largura }}
      >
        <header className="flex items-start gap-3 px-[18px] pt-4 pb-3">
          <div className="min-w-0 flex-1">
            <h2 className="m-0 text-base font-semibold text-ink">{titulo}</h2>
            {descricao && <p className="mt-1 mb-0 text-[13px] leading-[1.45] text-ardosia">{descricao}</p>}
          </div>
          <button type="button" className={btnIcone} onClick={onFechar} aria-label="Fechar">
            <X size={16} />
          </button>
        </header>
        <div className="max-h-[62vh] overflow-y-auto px-[18px] pt-1 pb-4">{children}</div>
      </div>
    </div>
  );
}

/** Painel à direita do conteúdo. Abaixo de 1.100 px vira gaveta sobre a tela. */
export function PainelLateral({ titulo, onFechar, children, rotulo }: { titulo: string; onFechar: () => void; children: ReactNode; rotulo?: string }) {
  return (
    <>
      <div
        className="hidden ate-1100:fixed ate-1100:inset-[56px_0_0_0] ate-1100:z-45 ate-1100:block ate-1100:bg-[rgba(0,34,51,.18)]"
        onClick={onFechar}
        aria-hidden="true"
      />
      <aside
        aria-label={rotulo || titulo}
        className="sticky top-0 max-h-[calc(100vh-56px-32px-48px)] w-[360px] flex-none overflow-y-auto rounded-xl border border-linha bg-branco ate-1100:fixed ate-1100:top-14 ate-1100:right-0 ate-1100:bottom-0 ate-1100:z-50 ate-1100:max-h-none ate-1100:w-[min(420px,100vw)] ate-1100:rounded-none ate-1100:border-0 ate-1100:border-l ate-1100:shadow-[-12px_0_32px_rgba(0,34,51,.18)]"
      >
        <header className="sticky top-0 z-1 flex items-center gap-2 border-b border-linha bg-branco py-2.5 pr-3 pl-4">
          <span className="min-w-0 flex-1 text-xs font-semibold tracking-[0.04em] text-ardosia uppercase">{titulo}</span>
          <button type="button" className={btnIcone} onClick={onFechar} aria-label="Recolher painel" title="Recolher painel (])">
            <PanelRightClose size={16} />
          </button>
        </header>
        <div className="p-4">{children}</div>
      </aside>
    </>
  );
}

/** Botão "Painel ]" do cabeçalho das telas com painel. */
export function BotaoPainel({ aberto, onClick }: { aberto: boolean; onClick: () => void }) {
  return (
    <button type="button" className={btn()} onClick={onClick} aria-pressed={aberto} title="Painel lateral (])">
      {aberto ? <PanelRightClose size={15} aria-hidden="true" /> : <PanelRightOpen size={15} aria-hidden="true" />}
      <span className="ate-640:hidden">Painel</span>
      <Kbd>]</Kbd>
    </button>
  );
}

/** Grupo de opções em cartões (formulários dos modais). */
export function GrupoRadio({
  nome,
  rotulo,
  opcoes,
  valor,
  onChange,
  colunas = 1,
}: {
  nome: string;
  rotulo: string;
  opcoes: [string, string, LucideIcon?][];
  valor: string | null;
  onChange: (v: string) => void;
  colunas?: number;
}) {
  return (
    <fieldset className="m-0 border-0 p-0">
      <legend className="mb-1.5 p-0 text-[13px] font-medium text-ink">{rotulo}</legend>
      <div className="grid gap-1.5" style={{ gridTemplateColumns: `repeat(${colunas}, minmax(0,1fr))` }}>
        {opcoes.map(([k, l, Icone]) => (
          <label
            key={k}
            className={cx(
              "flex cursor-pointer items-center gap-2 rounded-lg border px-2.5 py-2 text-[13px] [&_input]:m-0 [&_input]:accent-sinal-texto",
              valor === k ? "border-sinal-texto bg-sinal-fundo" : "border-linha bg-branco hover:border-linha-forte",
            )}
          >
            <input type="radio" name={nome} value={k} checked={valor === k} onChange={() => onChange(k)} />
            {Icone && <Icone size={14} aria-hidden="true" />}
            <span>{l}</span>
          </label>
        ))}
      </div>
    </fieldset>
  );
}
