/* Pequenos formatadores de texto e número, iguais aos da demo. */

export function plural(n: number, um: string, varios: string): string {
  return `${n} ${n === 1 ? um : varios}`;
}

export const pct = (x: number) => `${Math.round(x * 100)}%`;

export const fmtNum = (n: number) => Number(n).toLocaleString("pt-BR");

/** Remove acentos e passa para minúsculas, para buscas. */
export const normalizar = (t: string | null | undefined) =>
  String(t || "")
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase();

/** Até duas iniciais do nome, para o avatar. */
export const iniciais = (nome: string | null | undefined) =>
  String(nome || "?")
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0].toUpperCase())
    .join("");

/** Junta classes do Tailwind ignorando valores vazios. */
export function cx(...classes: (string | false | null | undefined)[]): string {
  return classes.filter(Boolean).join(" ");
}
