/* Marcas da régua da conversa de uma reunião: um glifo por tipo de cada tema
   citado (no estado da citação) e um círculo por ponto de interesse. */

import type { MarcaRegua, ReuniaoDetalhe } from "../../types/api";

/** Texto curto do estado da citação, usado no título da marca. */
function rotuloResposta(tratado: boolean | null): string {
  if (tratado === true) return "respondido";
  if (tratado === false) return "sem resposta";
  return "sem leitura";
}

export function marcasDaReuniao(reuniao: ReuniaoDetalhe): MarcaRegua[] {
  const marcas: MarcaRegua[] = [];
  // Temas: um tema que é risco e oportunidade ganha duas marcas no mesmo turno.
  for (const { tema, citacao } of reuniao.temas) {
    for (const tipo of tema.tipos) {
      marcas.push({
        turno: citacao.turno,
        tipo,
        tratado: citacao.tratado,
        titulo: `${tema.titulo}, ${rotuloResposta(citacao.tratado)}`,
        temaId: tema.id,
      });
    }
  }
  // Pontos de interesse: sempre círculo vazado, sem tema ligado.
  for (const x of reuniao.analise?.interesse ?? []) {
    marcas.push({ turno: x.turno, tipo: "interesse", tratado: false, titulo: `Interesse: ${x.texto}`, temaId: null });
  }
  return marcas;
}
