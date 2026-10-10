/* Primitivos visuais da interface, portados da demo para Tailwind. */

import type { ReactNode } from "react";
import { AlertCircle, AlertTriangle, CheckCircle2, Circle, Info, Loader2, Lock, type LucideIcon } from "lucide-react";
import { cx, iniciais } from "../../lib/formato";
import { btn, card, contagem as classeContagem } from "./classes";

/* ---------- Tecla ---------- */

/** Tecla de atalho. `claro` é a versão usada dentro do botão primário (fundo escuro). */
export function Kbd({ children, claro }: { children: ReactNode; claro?: boolean }) {
  return (
    <kbd
      className={cx(
        "inline-block min-w-4 rounded border border-b-2 px-1 text-center font-sans text-[11px] leading-4 font-medium",
        claro ? "border-white/25 bg-white/12 text-branco" : "border-linha-forte bg-branco text-ardosia",
      )}
    >
      {children}
    </kbd>
  );
}

/* ---------- Logo ---------- */

/** Logo provisório (o definitivo está com outro integrante do grupo). */
export function Logo({ claro, tamanho = 20 }: { claro?: boolean; tamanho?: number }) {
  return (
    <div className="flex items-center gap-2.5">
      <span aria-hidden="true" className="flex-none rounded-[3px] bg-sinal" style={{ width: tamanho / 2, height: tamanho / 2 }} />
      <span className={cx("font-semibold tracking-[-0.01em]", claro ? "text-branco" : "text-ink")} style={{ fontSize: tamanho }}>
        InsightCall
      </span>
    </div>
  );
}

/* ---------- Aviso ---------- */

type Tom = "erro" | "info" | "atencao" | "ok" | "neutro";

const TONS: Record<Tom, { classe: string; Icone: LucideIcon }> = {
  erro: { classe: "bg-critico-fundo text-critico border-critico-borda", Icone: AlertCircle },
  info: { classe: "bg-sinal-fundo text-sinal-texto border-sinal-borda", Icone: Info },
  atencao: { classe: "bg-atencao-fundo text-atencao border-atencao-borda", Icone: AlertTriangle },
  ok: { classe: "bg-resolvido-fundo text-resolvido border-resolvido-borda", Icone: CheckCircle2 },
  neutro: { classe: "bg-nevoa text-ardosia border-linha", Icone: Info },
};

/** Caixa de aviso colorida, com ação opcional à direita. */
export function Aviso({ tom = "info", children, acao }: { tom?: Tom; children: ReactNode; acao?: ReactNode }) {
  const s = TONS[tom];
  return (
    <div
      role={tom === "erro" ? "alert" : "status"}
      className={cx("flex flex-wrap items-center gap-2 rounded-lg border px-3 py-2.5 text-[13px] leading-[1.45]", s.classe)}
    >
      <span className="flex min-w-0 flex-[1_1_260px] items-start gap-2">
        <s.Icone size={16} className="mt-px flex-none" aria-hidden="true" />
        <span className="min-w-0 flex-1">{children}</span>
      </span>
      {acao}
    </div>
  );
}

/* ---------- Avatar ---------- */

export function Avatar({ nome, tamanho = 28, tom = "neutro" }: { nome: string; tamanho?: number; tom?: "neutro" | "sinal" }) {
  return (
    <span
      aria-hidden="true"
      className={cx(
        "inline-flex flex-none items-center justify-center rounded-full border border-linha font-semibold",
        tom === "sinal" ? "bg-sinal-fundo text-sinal-texto" : "bg-nevoa text-ardosia",
      )}
      style={{ width: tamanho, height: tamanho, fontSize: Math.round(tamanho * 0.4) }}
    >
      {iniciais(nome)}
    </span>
  );
}

/* ---------- Etiqueta ---------- */

/**
 * Etiqueta pequena. As cores vêm como classes do Tailwind:
 * cor = "bg-... text-... border-..." (padrão: névoa, ardósia, linha).
 */
export function Etiqueta({
  children,
  cor = "bg-nevoa text-ardosia border-linha",
  tracejada,
  title,
  icone: Icone,
}: {
  children: ReactNode;
  cor?: string;
  tracejada?: boolean;
  title?: string;
  icone?: LucideIcon;
}) {
  return (
    <span
      title={title}
      className={cx(
        "inline-flex items-center gap-1 rounded border px-[7px] text-[11.5px] leading-[18px] font-medium whitespace-nowrap",
        tracejada ? "border-dashed" : "border-solid",
        cor,
      )}
    >
      {Icone && <Icone size={12} aria-hidden="true" className="flex-none" />}
      {children}
    </span>
  );
}

/* ---------- Seção (cartão com título) ---------- */

export function Secao({
  titulo,
  contagem,
  acao,
  children,
  sub,
  id,
  semPadding,
}: {
  titulo?: ReactNode;
  contagem?: number | null;
  acao?: ReactNode;
  children?: ReactNode;
  sub?: ReactNode;
  id?: string;
  semPadding?: boolean;
}) {
  return (
    <section className={card} aria-labelledby={id ? `${id}-t` : undefined}>
      {(titulo || acao) && (
        <header className="flex items-center gap-2.5 border-b border-linha px-4 py-3">
          <div className="min-w-0 flex-1">
            <h2 id={id ? `${id}-t` : undefined} className="m-0 flex items-center gap-2 text-[13.5px] font-semibold text-ink">
              {titulo}
              {contagem != null && <span className={classeContagem}>{contagem}</span>}
            </h2>
            {sub && <p className="mt-0.5 mb-0 text-xs text-ardosia">{sub}</p>}
          </div>
          {acao}
        </header>
      )}
      <div className={semPadding ? undefined : "px-4 py-3"}>{children}</div>
    </section>
  );
}

/* ---------- Número ---------- */

export function Numero({
  rotulo,
  valor,
  tom,
  sub,
  titulo,
}: {
  rotulo: ReactNode;
  valor: ReactNode;
  tom?: "critico" | "atencao" | "ok";
  sub?: ReactNode;
  titulo?: string;
}) {
  const cor = tom === "critico" ? "text-critico" : tom === "atencao" ? "text-atencao" : tom === "ok" ? "text-resolvido" : "text-ink";
  return (
    <div className="min-w-0 rounded-[10px] border border-linha bg-branco px-3 py-2.5" title={titulo}>
      <div className="text-xs text-ardosia">{rotulo}</div>
      <div className={cx("mt-0.5 text-[22px] leading-[1.2] font-semibold tabular-nums", cor)}>{valor}</div>
      {sub && <div className="mt-0.5 text-xs leading-[1.35] text-faint">{sub}</div>}
    </div>
  );
}

/* ---------- Estado vazio ---------- */

export function Vazio({ titulo, texto, acao, icone: Icone = Circle }: { titulo: ReactNode; texto?: ReactNode; acao?: ReactNode; icone?: LucideIcon }) {
  return (
    <div className="px-3 py-[22px] text-center text-ardosia">
      <Icone size={18} aria-hidden="true" className="inline align-baseline text-faint" />
      <div className="mt-1.5 text-[13.5px] font-medium text-ink">{titulo}</div>
      {texto && <div className="mt-1 text-[12.5px] leading-[1.45]">{texto}</div>}
      {acao && <div className="mt-2.5">{acao}</div>}
    </div>
  );
}

/* ---------- Controle segmentado ---------- */

export function Segmentado<T extends string>({
  rotulo,
  opcoes,
  valor,
  onChange,
}: {
  rotulo: string;
  opcoes: [T, string, number?][];
  valor: T;
  onChange: (v: T) => void;
}) {
  return (
    <div role="radiogroup" aria-label={rotulo} className="inline-flex flex-wrap gap-0.5 rounded-lg bg-hover p-0.5">
      {opcoes.map(([k, l, n]) => (
        <button
          key={k}
          type="button"
          role="radio"
          aria-checked={valor === k}
          onClick={() => onChange(k)}
          className="inline-flex h-7 items-center gap-1.5 rounded-md px-2.5 text-[12.5px] whitespace-nowrap text-ardosia aria-checked:bg-branco aria-checked:font-medium aria-checked:text-ink aria-checked:shadow-[0_1px_2px_rgba(0,34,51,.12)]"
        >
          {l}
          {n != null && <span className="text-[11px] text-faint tabular-nums">{n}</span>}
        </button>
      ))}
    </div>
  );
}

/* ---------- Cabeçalho da página ---------- */

export function CabecalhoPagina({ titulo, texto, acoes, antes }: { titulo: ReactNode; texto?: ReactNode; acoes?: ReactNode; antes?: ReactNode }) {
  return (
    <div className="mb-[18px] flex flex-wrap items-end gap-3">
      <div className="min-w-[220px] flex-1">
        {antes}
        <h1 className="m-0 text-[21px] font-semibold tracking-[-0.01em] text-ink">{titulo}</h1>
        {texto && <p className="mt-[5px] mb-0 text-[13.5px] leading-[1.45] text-ardosia">{texto}</p>}
      </div>
      {acoes && <div className="flex flex-wrap items-center gap-2">{acoes}</div>}
    </div>
  );
}

/** "Só leitura. As ações são de {nome}." */
export function AvisoLeitura({ nome }: { nome?: string }) {
  return (
    <div className="mb-4">
      <Aviso tom="neutro">
        <span className="inline-flex items-center gap-1.5">
          <Lock size={13} aria-hidden="true" />
          Só leitura. {nome ? `As ações são de ${nome}.` : "As ações nos temas são do vendedor."}
        </span>
      </Aviso>
    </div>
  );
}

/* ---------- Carregamento e erro ---------- */

/** Espera enquanto os dados da tela chegam do backend. */
export function Carregando({ texto = "Carregando…" }: { texto?: string }) {
  return (
    <div className="flex items-center justify-center gap-2 py-16 text-[13px] text-ardosia" role="status">
      <Loader2 size={16} className="animate-giro" aria-hidden="true" />
      {texto}
    </div>
  );
}

/** Falha ao carregar a tela, com "Tentar de novo". */
export function ErroCarregar({ mensagem, onTentar }: { mensagem: string; onTentar: () => void }) {
  return (
    <div className="mx-auto max-w-[560px] py-10">
      <Aviso
        tom="erro"
        acao={
          <button type="button" className={btn({ sm: true })} onClick={onTentar}>
            Tentar de novo
          </button>
        }
      >
        {mensagem}
      </Aviso>
    </div>
  );
}
