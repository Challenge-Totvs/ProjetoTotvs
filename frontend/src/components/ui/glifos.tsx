/* Glifos (triângulo = risco, losango = oportunidade, círculo = interesse) e etiquetas de tema.
   Forma e cor andam juntas: a cor nunca carrega o significado sozinha. */

import { CornerDownRight, Cpu, Repeat } from "lucide-react";
import type { Motor, Tema, TipoCliente, TipoTema } from "../../types/api";
import { descreverCitacao, estadoCitacao, MOTORES, ROTULO_SITUACAO, temRisco, type EstadoGlifo } from "../../lib/dominio";
import { Etiqueta } from "./base";
import { COR } from "./cores";

const BRANCO = "#ffffff";
const CORES = {
  riscoAberto: "#c8322b",
  riscoTratado: "#78909c",
  oportAberta: "#c27c0e",
  oportTratada: "#0d8c73",
  interesse: "#5a6b75",
};

function corGlifo(tipo: TipoTema | "interesse", estado: EstadoGlifo): string {
  if (tipo === "risco") return estado === "aberto" ? CORES.riscoAberto : CORES.riscoTratado;
  if (tipo === "oportunidade") return estado === "aberto" ? CORES.oportAberta : CORES.oportTratada;
  return CORES.interesse;
}

export function Glifo({
  tipo,
  estado = "aberto",
  tamanho = 12,
  titulo,
}: {
  tipo: TipoTema | "interesse";
  estado?: EstadoGlifo;
  tamanho?: number;
  titulo?: string;
}) {
  const cor = corGlifo(tipo, estado);
  const vazado = estado === "indefinido" || tipo === "interesse";
  const props = vazado ? { fill: BRANCO, stroke: cor, strokeWidth: 1.6 } : { fill: cor };
  const s = tamanho;
  let forma;
  if (tipo === "risco") forma = <path d={`M${s / 2} 1.2 L${s - 0.8} ${s - 1.2} H0.8 Z`} {...props} />;
  else if (tipo === "oportunidade") forma = <path d={`M${s / 2} 0.8 L${s - 0.8} ${s / 2} L${s / 2} ${s - 0.8} L0.8 ${s / 2} Z`} {...props} />;
  else forma = <circle cx={s / 2} cy={s / 2} r={s / 2 - 1.4} {...props} />;
  return (
    <svg
      width={s}
      height={s}
      viewBox={`0 0 ${s} ${s}`}
      role={titulo ? "img" : undefined}
      aria-label={titulo}
      aria-hidden={titulo ? undefined : "true"}
      className="block flex-none"
    >
      {forma}
    </svg>
  );
}

/** Os glifos dos tipos do tema, no estado da citação. */
export function GlifosTema({ tipos, tratado, tamanho = 12 }: { tipos: TipoTema[]; tratado: boolean | null; tamanho?: number }) {
  const est = estadoCitacao(tratado);
  return (
    <span className="inline-flex items-center gap-0.5" role="img" aria-label={descreverCitacao(tipos, tratado)}>
      {tipos.includes("risco") && <Glifo tipo="risco" estado={est} tamanho={tamanho} />}
      {tipos.includes("oportunidade") && <Glifo tipo="oportunidade" estado={est} tamanho={tamanho} />}
    </span>
  );
}

export function LegendaGlifos({ compacta }: { compacta?: boolean }) {
  const itens: [TipoTema | "interesse", EstadoGlifo, string][] = [
    ["risco", "aberto", "Risco sem resposta"],
    ["risco", "tratado", "Risco respondido"],
    ["oportunidade", "aberto", "Oportunidade sem tratamento"],
    ["oportunidade", "tratado", "Oportunidade tratada"],
  ];
  if (!compacta) itens.push(["interesse", "aberto", "Interesse"]);
  return (
    <div className="flex flex-wrap gap-x-3.5 gap-y-1.5 text-[11.5px] text-ardosia">
      {itens.map(([t, e, l]) => (
        <span key={l} className="inline-flex items-center gap-[5px]">
          <Glifo tipo={t} estado={e} tamanho={11} />
          {l}
        </span>
      ))}
      <span className="inline-flex items-center gap-[5px]">
        <Glifo tipo="risco" estado="indefinido" tamanho={11} />
        Sem leitura de resposta
      </span>
    </div>
  );
}

/** Etiqueta da situação do tema. `compacta` tira o "perde em N d". */
export function TagSituacao({ tema, compacta }: { tema: Tema; compacta?: boolean }) {
  const s = tema.situacao;
  if (s === "sem_retorno") {
    if (temRisco(tema)) return <Etiqueta cor={COR.critico}>Sem retorno</Etiqueta>;
    return (
      <Etiqueta cor={COR.atencaoBranco} title="Oportunidade citada e ainda sem tratamento, dentro da janela">
        {compacta ? "Sem retorno" : `Sem retorno · ${tema.venceEm === 1 ? "perde amanhã" : `perde em ${tema.venceEm} d`}`}
      </Etiqueta>
    );
  }
  if (s === "oportunidade_perdida") return <Etiqueta cor={COR.atencao}>Oportunidade perdida</Etiqueta>;
  if (s === "tratado_conversa") return <Etiqueta cor={COR.resolvido}>Tratado na conversa</Etiqueta>;
  if (s === "tratado_fora")
    return (
      <Etiqueta cor={COR.resolvido} icone={CornerDownRight}>
        Tratado fora da reunião
      </Etiqueta>
    );
  if (s === "sem_leitura")
    return (
      <Etiqueta cor={COR.faintForte} tracejada>
        Sem leitura de resposta
      </Etiqueta>
    );
  if (s === "nao_procede") return <Etiqueta cor={COR.faint}>Não procede</Etiqueta>;
  return <Etiqueta>Fora de pauta</Etiqueta>;
}

export function ChipRecorrente({ n }: { n?: number }) {
  return (
    <Etiqueta
      cor={COR.recorrente}
      icone={Repeat}
      title={n ? `Citado em ${n} reuniões dentro da janela` : "Citado em duas ou mais reuniões dentro da janela"}
    >
      Recorrente
    </Etiqueta>
  );
}

const chipTipo =
  "inline-flex items-center gap-[5px] rounded border border-linha bg-branco px-[7px] text-[11.5px] leading-[18px] text-ardosia";

export function ChipTipos({ tipos }: { tipos: TipoTema[] }) {
  return (
    <span className="inline-flex flex-wrap gap-1">
      {tipos.includes("risco") && (
        <span className={chipTipo}>
          <Glifo tipo="risco" tamanho={10} />
          Risco
        </span>
      )}
      {tipos.includes("oportunidade") && (
        <span className={chipTipo}>
          <Glifo tipo="oportunidade" tamanho={10} />
          Oportunidade
        </span>
      )}
    </span>
  );
}

export function ChipTipoCliente({ tipo }: { tipo: TipoCliente }) {
  if (tipo === "ativo") return <Etiqueta cor={COR.inkBranco}>Ativo</Etiqueta>;
  if (tipo === "prospect") return <Etiqueta cor={COR.sinal}>Prospect</Etiqueta>;
  return (
    <Etiqueta cor={COR.faintForte} tracejada title="TP_RECURSO vazio: só 1 em cada 5 reuniões do corpus tem a classificação">
      Sem tipo
    </Etiqueta>
  );
}

export function ChipMotor({ motor }: { motor: Motor }) {
  const m = MOTORES[motor] || MOTORES.llm1;
  const contingencia = motor === "local" || motor === "regras";
  const secundaria = motor === "llm2";
  return (
    <Etiqueta
      cor={contingencia ? COR.atencao : secundaria ? COR.inkBranco : COR.ardosiaBranco}
      icone={Cpu}
      title={contingencia ? "Análise em contingência: sem resumo e sem leitura de quem falou" : "Motor que respondeu esta análise"}
    >
      {contingencia ? `Contingência · ${m.curto}` : m.curto}
    </Etiqueta>
  );
}

/** Chips dos temas em pauta de um cliente (lista de clientes). */
export function ChipsTemas({ temas, max = 3, porPadrao }: { temas: Tema[]; max?: number; porPadrao?: boolean }) {
  const lista = temas.filter((t) => t.emPauta);
  if (!lista.length) return <span className="text-xs text-faint">Nenhum em pauta</span>;
  return (
    <span className="flex flex-wrap items-center gap-1">
      {lista.slice(0, max).map((t) => (
        <span
          key={t.id}
          className="inline-flex max-w-[190px] items-center gap-[5px] rounded border border-linha bg-branco px-[7px] py-px text-xs text-ink"
          title={`${t.titulo} · ${ROTULO_SITUACAO[t.situacao]}`}
        >
          <GlifosTema tipos={t.tipos} tratado={t.citacoes[t.citacoes.length - 1]?.tratado ?? null} tamanho={10} />
          <span className="truncate">{porPadrao ? t.padraoNome : t.titulo}</span>
          {t.recorrente && <Repeat size={11} aria-label="recorrente" />}
        </span>
      ))}
      {lista.length > max && <span className="text-xs text-ardosia">+{lista.length - max}</span>}
    </span>
  );
}

