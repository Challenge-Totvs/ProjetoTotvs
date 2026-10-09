/* Receitas de classes do Tailwind reaproveitadas em várias telas.
   Cada função monta a lista completa de classes de uma variante, sem duas
   classes disputando a mesma propriedade (por exemplo, bg-branco e bg-ink). */

import { cx } from "../../lib/formato";

/* ---------- Botões ---------- */

export function btn(opcoes: { primario?: boolean; sm?: boolean; className?: string } = {}): string {
  const { primario, sm, className } = opcoes;
  return cx(
    "inline-flex items-center gap-[7px] whitespace-nowrap rounded-lg border",
    sm ? "h-7 px-2.5 text-[12.5px]" : "h-[34px] px-3 text-[13px]",
    primario
      ? "border-ink bg-ink text-branco enabled:hover:border-primario-hover enabled:hover:bg-primario-hover"
      : "border-linha bg-branco text-ink enabled:hover:border-linha-forte enabled:hover:bg-nevoa aria-pressed:border-linha-forte aria-pressed:bg-hover",
    className,
  );
}

/** Botão grande das telas de acesso (Entrar, Criar conta). */
export const btnCta =
  "inline-flex h-[46px] w-full items-center justify-center gap-2 rounded-lg bg-sinal text-sm font-semibold text-ink hover:bg-sinal-hover aria-busy:cursor-progress";

/** Botão só com ícone (fechar, recolher). */
export const btnIcone =
  "inline-flex h-[30px] w-[30px] flex-none items-center justify-center rounded-md text-ardosia hover:bg-hover hover:text-ink";

/* ---------- Links ---------- */

export const link = "font-medium text-sinal-texto hover:underline";
export const linkNeutro = "hover:underline";
export const linkForte = "text-left font-semibold text-ink hover:underline";

/* ---------- Campos ---------- */

const campoBase =
  "w-full rounded-lg border border-linha bg-branco outline-none placeholder:text-faint hover:border-linha-forte focus:border-sinal-texto focus:shadow-[0_0_0_3px_var(--color-sinal-fundo)] aria-[invalid=true]:border-critico";

export const input = cx(campoBase, "h-11 px-3.5 text-sm");
export const textarea = cx(campoBase, "resize-y px-3 py-2.5 text-[13.5px] leading-normal");

export function select(largo = false): string {
  return cx(
    "seta-select rounded-lg border border-linha bg-branco pr-7 pl-2.5 outline-none hover:border-linha-forte focus:border-sinal-texto focus:shadow-[0_0_0_3px_var(--color-sinal-fundo)] aria-[invalid=true]:border-critico",
    largo ? "h-10 w-full text-sm" : "h-8 text-[13px]",
  );
}

/** Rótulo com o campo dentro (formulários de Nova transcrição). */
export const campo = "grid content-start gap-1.5 text-[13px] font-medium text-ink";
export const erroCampo = "text-xs leading-[1.4] font-normal text-critico";
export const opcional = "text-xs font-normal text-faint";

/* ---------- Blocos ---------- */

export const card = "min-w-0 rounded-xl border border-linha bg-branco";
export const contagem = "rounded-full bg-hover px-[7px] text-[11.5px] leading-[18px] font-semibold text-ardosia";
export const bloco = "rounded-[10px] border border-linha bg-nevoa p-3";
export const rotuloBloco = "mb-2 text-[11px] font-semibold tracking-[0.04em] text-faint uppercase";
export const rotuloMetrica = "mb-1 text-xs text-ardosia";
export const num = "tabular-nums";

/** Grade de números: ajusta sozinha, 2 colunas ou 4 colunas. */
export function numeros(colunas?: 2 | 4): string {
  if (colunas === 2) return "grid grid-cols-2 gap-2.5 max-[640px]:grid-cols-1";
  if (colunas === 4) return "grid grid-cols-4 gap-2.5 max-[1100px]:grid-cols-2 max-[640px]:grid-cols-1";
  return "grid grid-cols-[repeat(auto-fit,minmax(160px,1fr))] gap-2.5";
}

/* ---------- Grades de página ---------- */

export const grid2 = "grid grid-cols-2 items-start gap-4 max-[900px]:grid-cols-1";
export const grid3 = "grid grid-cols-3 items-start gap-4 max-[1200px]:grid-cols-2 max-[900px]:grid-cols-1";
export const gridReuniao = "grid grid-cols-[minmax(0,1.6fr)_minmax(0,1fr)] items-start gap-4 max-[1100px]:grid-cols-1";
export const gridForm = "grid grid-cols-2 gap-3.5 max-[900px]:grid-cols-1";

/** Conteúdo com o painel lateral ao lado. */
export const comPainel = "flex items-start gap-4 max-[1024px]:flex-wrap";
export const conteudo = "min-w-0 flex-1";

/* ---------- Listas ---------- */

/** Lista com uma linha entre os itens. */
export const lista = "grid divide-y divide-linha";
export const listaBorda = "overflow-hidden rounded-[10px] border border-linha";
export const itemTitulo = "block text-[13.5px] leading-[1.4] font-medium text-ink";
export const itemSub = "mt-0.5 block text-xs leading-[1.4] text-ardosia";

/** Item clicável de lista (tema, mudança). */
export const item =
  "flex w-full items-start gap-2.5 bg-branco px-4 py-2.5 text-left hover:bg-nevoa aria-[current=true]:bg-sinal-fundo aria-[current=true]:shadow-[inset_3px_0_0_var(--color-sinal-texto)]";

/* ---------- Barra de ferramentas e busca ---------- */

export const barraFerramentas = "mb-3 flex flex-wrap items-center gap-2.5";
export const busca =
  "inline-flex h-[34px] max-w-[360px] min-w-60 flex-1 items-center gap-2 rounded-lg border border-linha bg-branco px-2.5 focus-within:border-sinal-texto focus-within:shadow-[0_0_0_3px_var(--color-sinal-fundo)] max-[640px]:w-full max-[640px]:max-w-none max-[640px]:min-w-0 [&_input]:w-full [&_input]:border-0 [&_input]:bg-transparent [&_input]:px-0.5 [&_input]:py-px [&_input]:text-[13px] [&_input]:outline-none [&_input]:placeholder:text-[#757575]";

/* ---------- Tabelas ---------- */

export const tabela = "w-full border-collapse text-[13px]";
export const th = "border-b border-linha bg-branco px-3 py-[9px] text-left text-[11.5px] font-semibold whitespace-nowrap text-ardosia first:pl-4";
export const td = "border-b border-linha px-3 py-2.5 align-middle first:pl-4 [tr:last-child>&]:border-b-0";
export const direita = "text-right!";

/** Linha de tabela clicável, com destaque quando selecionada. */
export const tr =
  "cursor-pointer [&:not([aria-selected=true]):hover>td]:bg-nevoa aria-selected:[&>td]:bg-sinal-fundo aria-selected:[&>td:first-child]:shadow-[inset_3px_0_0_var(--color-sinal-texto)]";
