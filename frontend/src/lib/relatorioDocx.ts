/* Geração de relatórios .docx, 100% no navegador (sem endpoint novo no backend).
   Usa os mesmos dados já carregados nas telas (ClienteDetalhe, VendedorResumo[], Inicio),
   então não há consulta extra nem risco de regressão no backend.

   Quatro relatórios, pedidos como "feats que faltam" da demo:
   - relatorioRelacionamentoCliente: visão geral do cliente (indicadores, temas em pauta, compromissos)
   - relatorioReunioesCliente: lista de reuniões do cliente
   - relatorioDesempenhoTime: números do time + tabela por vendedor (visão do gestor)
   - relatorioDesempenhoVendedor: números de um vendedor (própria visão ou a do gestor sobre ele) */

import { Document, HeadingLevel, Packer, Paragraph, Table, TableCell, TableRow, TextRun, WidthType } from "docx";
import { saveAs } from "file-saver";
import { fmtDataAno, fmtHora, paraData } from "./datas";
import { fmtNum, pct } from "./formato";
import type { ClienteDetalhe, MetricasVendedor, ReuniaoItem, VendedorResumo } from "../types/api";

const TITULO_COR = "0B2540";

function titulo(texto: string) {
  return new Paragraph({ heading: HeadingLevel.HEADING_1, spacing: { after: 160 }, children: [new TextRun({ text: texto, color: TITULO_COR })] });
}

function subtitulo(texto: string) {
  return new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 240, after: 120 }, children: [new TextRun(texto)] });
}

function paragrafo(texto: string, opts: { itálico?: boolean; cor?: string } = {}) {
  return new Paragraph({
    spacing: { after: 100 },
    children: [new TextRun({ text: texto, italics: opts.itálico, color: opts.cor })],
  });
}

function rodape(gerado = new Date()) {
  return new Paragraph({
    spacing: { before: 360 },
    children: [new TextRun({ text: `Gerado pelo InsightCall em ${fmtDataAno(gerado)} às ${fmtHora(gerado)}.`, italics: true, size: 18, color: "6B7A8D" })],
  });
}

function celula(texto: string, opts: { cabecalho?: boolean } = {}) {
  return new TableCell({
    width: { size: 0, type: WidthType.AUTO },
    children: [new Paragraph({ children: [new TextRun({ text: texto, bold: opts.cabecalho })] })],
  });
}

function tabela(cabecalhos: string[], linhas: string[][]) {
  return new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    rows: [new TableRow({ children: cabecalhos.map((c) => celula(c, { cabecalho: true })) }), ...linhas.map((l) => new TableRow({ children: l.map((c) => celula(c)) }))],
  });
}

async function baixar(doc: Document, nomeArquivo: string) {
  const blob = await Packer.toBlob(doc);
  saveAs(blob, nomeArquivo);
}

/* ---------- Relacionamento com o cliente ---------- */

export async function relatorioRelacionamentoCliente(cliente: ClienteDetalhe) {
  const i = cliente.indicadores;
  const doc = new Document({
    sections: [
      {
        children: [
          titulo(`Relacionamento com ${cliente.nome}`),
          paragrafo(`${cliente.segmento} · ${cliente.tipo ?? "sem tipo"} · vendedor ${cliente.vendedor.nome}`, { itálico: true, cor: "6B7A8D" }),

          subtitulo("Indicadores"),
          tabela(
            ["Indicador", "Valor"],
            [
              ["Temas em pauta", fmtNum(i.emPauta)],
              ["Riscos sem retorno", fmtNum(i.riscosSemRetorno)],
              ["Riscos recorrentes", fmtNum(i.riscosRecorrentes)],
              ["Oportunidades perdidas", fmtNum(i.oportPerdidas)],
              ["Oportunidades sem retorno", fmtNum(i.oportSemRetorno)],
              ["Tratados na conversa", fmtNum(i.tratadosConversa)],
              ["Tratados fora da reunião", fmtNum(i.tratadosFora)],
              ["Fora de pauta", fmtNum(i.foraDePauta)],
              ["Não procede", fmtNum(i.naoProcede)],
              ["Recorrentes", fmtNum(i.recorrentes)],
            ],
          ),

          subtitulo("Temas em pauta"),
          ...(cliente.temas.length === 0
            ? [paragrafo("Nenhum tema em pauta no momento.", { itálico: true })]
            : [
                tabela(
                  ["Tema", "Tipo", "Situação", "Última atividade"],
                  cliente.temas.map((t) => [t.titulo, t.tipos.join(", "), t.situacao.replace(/_/g, " "), fmtDataAno(paraData(t.ultimaAtividade))]),
                ),
              ]),

          subtitulo("Compromissos"),
          ...(cliente.compromissos.length === 0
            ? [paragrafo("Nenhum compromisso registrado.", { itálico: true })]
            : [
                tabela(
                  ["Compromisso", "Prazo", "Estado"],
                  cliente.compromissos.map((c) => [c.texto, c.prazo ? fmtDataAno(paraData(c.prazo)) : "sem prazo", c.estado.replace(/_/g, " ")]),
                ),
              ]),

          rodape(),
        ],
      },
    ],
  });
  await baixar(doc, `relacionamento-${slug(cliente.nome)}.docx`);
}

/* ---------- Reuniões do cliente ---------- */

export async function relatorioReunioesCliente(cliente: { nome: string }, reunioes: ReuniaoItem[]) {
  const doc = new Document({
    sections: [
      {
        children: [
          titulo(`Reuniões — ${cliente.nome}`),
          paragrafo(`${reunioes.length} reunião(ões) registrada(s).`, { itálico: true, cor: "6B7A8D" }),
          tabela(
            ["Data", "Título", "Status", "Contato", "Motor", "Score"],
            reunioes.map((r) => [
              `${fmtDataAno(paraData(r.dataHora))} ${fmtHora(paraData(r.dataHora))}`,
              r.titulo,
              r.status,
              r.contato ?? "—",
              r.motor ?? "—",
              r.score == null ? "—" : String(r.score),
            ]),
          ),
          rodape(),
        ],
      },
    ],
  });
  await baixar(doc, `reunioes-${slug(cliente.nome)}.docx`);
}

/* ---------- Desempenho do time (gestor) ---------- */

function linhaMetricas(m: MetricasVendedor): string[] {
  return [
    fmtNum(m.realizadas),
    fmtNum(m.clientes),
    m.taxaConversa == null ? "—" : pct(m.taxaConversa),
    fmtNum(m.oportTratadas),
    fmtNum(m.riscosSemRetorno),
    fmtNum(m.oportPerdidas),
    fmtNum(m.compromissosVencidos),
  ];
}

export async function relatorioDesempenhoTime(nomeTime: string, janelaDias: number, time: MetricasVendedor, vendedores: VendedorResumo[]) {
  const doc = new Document({
    sections: [
      {
        children: [
          titulo(`Desempenho do time ${nomeTime}`),
          paragrafo(`Últimos ${janelaDias} dias. Medidas das reuniões, não de vendas: valor vendido e fechamento dependem do CRM.`, {
            itálico: true,
            cor: "6B7A8D",
          }),

          subtitulo("Resumo do time"),
          tabela(
            ["Métrica", "Valor"],
            [
              ["Reuniões realizadas", fmtNum(time.realizadas)],
              ["Reuniões analisadas", fmtNum(time.analisadas)],
              ["Temas tratados na própria conversa", time.taxaConversa == null ? "—" : pct(time.taxaConversa)],
              ["Tratados fora da reunião", fmtNum(time.tratadosFora)],
              ["Oportunidades tratadas", `${fmtNum(time.oportTratadas)} de ${fmtNum(time.oportIdentificadas)}`],
              ["Fala do vendedor (média)", time.falaVendedor == null ? "—" : pct(time.falaVendedor)],
              ["Riscos sem retorno", fmtNum(time.riscosSemRetorno)],
              ["Oportunidades perdidas", fmtNum(time.oportPerdidas)],
              ["Compromissos vencidos", fmtNum(time.compromissosVencidos)],
              ["Clientes ativos", fmtNum(time.clientes)],
            ],
          ),

          subtitulo("Por vendedor"),
          tabela(
            ["Vendedor", "Reuniões", "Clientes", "Tratados na conversa", "Oport. tratadas", "Riscos sem retorno", "Oport. perdidas", "Compromissos vencidos"],
            vendedores.map((v) => [v.nome, ...linhaMetricas(v.metricas)]),
          ),

          rodape(),
        ],
      },
    ],
  });
  await baixar(doc, `desempenho-time-${slug(nomeTime)}.docx`);
}

/* ---------- Desempenho de um vendedor ---------- */

export async function relatorioDesempenhoVendedor(nomeVendedor: string, janelaDias: number, m: MetricasVendedor) {
  const doc = new Document({
    sections: [
      {
        children: [
          titulo(`Desempenho — ${nomeVendedor}`),
          paragrafo(`Últimos ${janelaDias} dias. Medidas das reuniões, não de vendas.`, { itálico: true, cor: "6B7A8D" }),
          tabela(
            ["Métrica", "Valor"],
            [
              ["Reuniões realizadas", fmtNum(m.realizadas)],
              ["Reuniões analisadas", fmtNum(m.analisadas)],
              ["Temas tratados na própria conversa", m.taxaConversa == null ? "—" : pct(m.taxaConversa)],
              ["Tratados fora da reunião", fmtNum(m.tratadosFora)],
              ["Oportunidades tratadas", `${fmtNum(m.oportTratadas)} de ${fmtNum(m.oportIdentificadas)}`],
              ["Fala do vendedor (média)", m.falaVendedor == null ? "—" : pct(m.falaVendedor)],
              ["Riscos sem retorno", fmtNum(m.riscosSemRetorno)],
              ["Oportunidades perdidas", fmtNum(m.oportPerdidas)],
              ["Compromissos vencidos", fmtNum(m.compromissosVencidos)],
              ["Clientes", fmtNum(m.clientes)],
            ],
          ),
          rodape(),
        ],
      },
    ],
  });
  await baixar(doc, `desempenho-${slug(nomeVendedor)}.docx`);
}

function slug(texto: string): string {
  return texto
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "");
}
