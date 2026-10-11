import { readFileSync, writeFileSync } from "node:fs";

const [entrada, saida] = process.argv.slice(2);
const linhas = readFileSync(entrada, "utf8").split("\n");

function bloco(nome) {
  const ini = linhas.findIndex((l) => l.startsWith(`const ${nome} =`));
  if (ini < 0) throw new Error(`Não achei ${nome} no arquivo`);
  if (/;\s*$/.test(linhas[ini]) && !/=\s*[\[{]\s*$/.test(linhas[ini])) return linhas[ini]; // const de uma linha só
  let fim = ini;
  while (!/^[\]}];?\s*$/.test(linhas[fim])) fim++;
  return linhas.slice(ini, fim + 1).join("\n");
}


const prelude = `const dia = (d, h = "10:00") => ({ d, h });\n`;
const nomes = ["USUARIOS_SEED", "CLIENTES_SEED", "TRANSCRICOES", "R", "REUNIOES_SEED", "C", "TEMAS_SEED", "COMPROMISSOS_SEED"];
const d = new Function(
  prelude + nomes.map(bloco).join("\n") +
    "\nreturn { USUARIOS_SEED, CLIENTES_SEED, TRANSCRICOES, REUNIOES_SEED, TEMAS_SEED, COMPROMISSOS_SEED };",
)();

const FILLER = "(trecho fora do recorte da demonstração)";


const conflitos = [];
function transcricaoDe(r) {
  if (d.TRANSCRICOES[r.id]) return d.TRANSCRICOES[r.id].map(([loc, texto]) => ({ loc, texto }));
  if (!r.turnos) return null;
  const turnos = Array.from({ length: r.turnos }, (_, i) => ({ loc: i % 2 === 0 ? 1 : 2, texto: FILLER, conhecido: false }));
  const poe = (n, loc, texto, origem) => {
    if (n < 1 || n > r.turnos) { conflitos.push(`${r.id}: turno ${n} fora de 1..${r.turnos} (${origem})`); return; }
    const t = turnos[n - 1];
    if (t.conhecido && t.texto !== texto) { conflitos.push(`${r.id}: turno ${n} com dois textos (${origem})`); return; }
    t.loc = loc; t.texto = texto; t.conhecido = true;
  };
  for (const tema of d.TEMAS_SEED)
    for (const c of tema.citacoes.filter((x) => x.reuniao === r.id)) {
      poe(c.turno, 2, c.texto, `tema ${tema.id}`);                                  
      for (const [n, loc, texto] of c.contexto ?? []) poe(n, loc, texto, `contexto de ${tema.id}`);
    }
  for (const i of r.interesse) poe(i.turno, 2, i.citacao, "interesse");
  return turnos.map(({ loc, texto }) => ({ loc, texto }));
}

const seed = {
  usuarios: d.USUARIOS_SEED.map(({ email, senha, nome, perfil, vendedorId }) => ({ email, senha, nome, perfil, vendedorId: vendedorId ?? null })),
  clientes: d.CLIENTES_SEED,
  reunioes: d.REUNIOES_SEED.map((r) => ({
    id: r.id, cliente: r.cliente, d: r.data.d, h: r.data.h, titulo: r.titulo, contato: r.contato,
    status: r.status, confirmada: !!r.confirmada, duracaoMin: r.duracaoMin ?? null, score: r.score ?? null,
    sentimento: r.sentimento, resumo: r.resumo, papeis: r.papeis, interesse: r.interesse,
    proximosPassos: r.proximosPassos, descartados: r.descartados, sentimentoSerie: r.sentimentoSerie ?? [],
    transcricao: r.status === "analisada" || r.status === "aguardando" ? transcricaoDe(r) : null,
  })),
  temas: d.TEMAS_SEED.map((t) => ({
    id: t.id, cliente: t.cliente, padrao: t.padrao, titulo: t.titulo, tipos: t.tipos,
    citacoes: t.citacoes.map(({ reuniao, turno, tratado, texto }) => ({ reuniao, turno, tratado, texto })),
    naoProcede: t.naoProcede ? { motivo: t.naoProcede.motivo, por: t.naoProcede.por, d: t.naoProcede.em.d, h: t.naoProcede.em.h } : null,
  })),
  compromissos: d.COMPROMISSOS_SEED,   
};

writeFileSync(saida, JSON.stringify(seed, null, 1));
const q = (f) => seed.reunioes.filter(f).length;
console.log({
  usuarios: seed.usuarios.length, clientes: seed.clientes.length, reunioes: seed.reunioes.length,
  analisadas: q((r) => r.status === "analisada"), agendadas: q((r) => r.status === "agendada"), aguardando: q((r) => r.status === "aguardando"),
  comTranscricao: q((r) => r.transcricao), temas: seed.temas.length, compromissos: seed.compromissos.length,
  conflitos: conflitos.length,
});
conflitos.forEach((c) => console.log("CONFLITO", c));