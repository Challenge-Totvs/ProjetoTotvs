/* Datas e textos de formatação, iguais aos da demo.
   Toda contagem de dias é entre datas civis (sem horas), no fuso do navegador. */

import type { DataISO } from "../types/api";

const DIA_MS = 86400000;
export const SEMANA = ["dom", "seg", "ter", "qua", "qui", "sex", "sáb"];

const pad = (n: number) => String(n).padStart(2, "0");
export { pad };

/** Converte o texto ISO do backend em Date. "2026-10-06" vira o dia local, sem deslocar pelo fuso. */
export function paraData(iso: DataISO): Date {
  const soDia = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso);
  if (soDia) return new Date(Number(soDia[1]), Number(soDia[2]) - 1, Number(soDia[3]));
  return new Date(iso);
}

export function inicioDia(d: Date): Date {
  const x = new Date(d);
  x.setHours(0, 0, 0, 0);
  return x;
}

export function hoje(): Date {
  return inicioDia(new Date());
}

/** Dias entre duas datas civis (b - a). */
export function diasEntre(a: Date, b: Date): number {
  return Math.round((inicioDia(b).getTime() - inicioDia(a).getTime()) / DIA_MS);
}

export const fmtData = (d: Date) => `${pad(d.getDate())}/${pad(d.getMonth() + 1)}`;
export const fmtDataAno = (d: Date) => `${fmtData(d)}/${d.getFullYear()}`;
export const fmtHora = (d: Date) => `${pad(d.getHours())}:${pad(d.getMinutes())}`;
export const fmtDiaSemana = (d: Date) => `${SEMANA[d.getDay()]}, ${fmtData(d)}`;

/** "hoje", "ontem", "amanhã", "há N dias" ou "em N dias". */
export function relativo(d: Date): string {
  const n = diasEntre(d, hoje());
  if (n === 0) return "hoje";
  if (n === 1) return "ontem";
  if (n === -1) return "amanhã";
  if (n > 1) return `há ${n} dias`;
  return `em ${-n} dias`;
}

/** Data de hoje no formato do <input type="date">. */
export function hojeISO(): string {
  const h = hoje();
  return `${h.getFullYear()}-${pad(h.getMonth() + 1)}-${pad(h.getDate())}`;
}

/** Tempo de um aviso ao gestor: "agora", "há 5 min", "há 2 h" ou "ontem, 17:40". */
export function quandoAviso(d: Date): string {
  const min = Math.round((Date.now() - d.getTime()) / 60000);
  if (min < 1) return "agora";
  if (min < 60) return `há ${min} min`;
  if (min < 24 * 60 && diasEntre(d, hoje()) === 0) return `há ${Math.round(min / 60)} h`;
  return `${relativo(d)}, ${fmtHora(d)}`;
}
