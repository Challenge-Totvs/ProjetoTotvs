/* Painel lateral de um padrão: números, onde aparece na conversa, segmentos,
   vendedores, motivos de "não procede" e uma amostra de citações. */

import { useNavigate } from "react-router-dom";
import type { PadraoAgregado } from "../../types/api";
import { fmtData, paraData } from "../../lib/datas";
import { nomeMotivo } from "../../lib/dominio";
import { cx, pct, plural } from "../../lib/formato";
import { rotas } from "../../lib/rotas";
import { Numero } from "../ui/base";
import { Citacao } from "../ui/Citacao";
import { linkNeutro, numeros, rotuloBloco } from "../ui/classes";
import { Glifo } from "../ui/glifos";
import { Distribuicao } from "../ui/graficos";

/** Frase sobre o terço da conversa em que o padrão mais aparece. */
const FRASE_TERCO: Record<string, string> = {
  Início: "no começo, ainda na qualificação",
  Meio: "no meio da conversa",
  Fim: "no fim das reuniões, perto do fechamento",
};

export function InspetorPadrao({ g }: { g: PadraoAgregado }) {
  const navigate = useNavigate();
  const risco = g.tipo === "risco";

  // Início, meio e fim da conversa, com a quantidade de citações em cada terço.
  const ondes: [string, number][] = [
    ["Início", g.terco[0]],
    ["Meio", g.terco[1]],
    ["Fim", g.terco[2]],
  ];
  const totalCit = g.terco.reduce((s, n) => s + n, 0);
  // O terço com mais citações (no empate fica o primeiro). Sem citações, nenhum.
  const maiorTerco = totalCit ? ondes.reduce((m, x) => (x[1] > m[1] ? x : m), ondes[0])[0] : null;

  // Motivos chegam como chave ("nao_cliente"); a tela mostra o nome.
  const motivos: [string, number][] = g.motivos.map(([k, n]) => [nomeMotivo(k), n]);

  // Segundo número: recorrentes (risco) ou viraram perdidas (oportunidade).
  const segundo = risco ? g.recorrentes : g.perdidas;
  const tomAlerta = risco ? "critico" : "atencao";

  return (
    <div>
      {/* Título com o glifo do tipo */}
      <div className="flex items-center gap-2">
        <Glifo tipo={g.tipo} tamanho={14} />
        <h2 className="m-0 text-base font-semibold text-ink">{g.nome}</h2>
      </div>
      <p className="mt-1 mb-0 text-[12.5px] text-ardosia">
        {risco ? "Risco" : "Oportunidade"} · {plural(g.total, "tema", "temas")} em {plural(g.clientes, "cliente", "clientes")}
      </p>

      {/* Quatro números do padrão */}
      <div className={cx(numeros(2), "mt-3.5")}>
        <Numero rotulo="Sem retorno" valor={g.semRetorno} tom={g.semRetorno ? tomAlerta : undefined} />
        <Numero rotulo={risco ? "Recorrentes" : "Viraram perdidas"} valor={segundo} tom={segundo ? tomAlerta : undefined} />
        <Numero rotulo="Tratados na conversa" valor={g.taxaConversa == null ? "—" : pct(g.taxaConversa)} sub="estimativa, papel inferido" />
        <Numero rotulo="Não procede" valor={pct(g.taxaNaoProcede)} sub={`${g.naoProcede} de ${g.total} temas marcados`} />
      </div>

      {/* Onde na conversa (por terço do turno) */}
      <div className={cx(rotuloBloco, "mt-[18px]")}>Onde na conversa</div>
      <Distribuicao itens={ondes} />
      {maiorTerco && (
        <p className="mt-1.5 mb-0 text-xs leading-[1.45] text-ardosia">
          A maior parte aparece {FRASE_TERCO[maiorTerco]}. Posição pelo turno, em terços.
        </p>
      )}

      {/* Por segmento e por vendedor (já ordenados pelo backend) */}
      <div className={cx(rotuloBloco, "mt-[18px]")}>Por segmento</div>
      <Distribuicao itens={g.porSegmento} />
      <div className={cx(rotuloBloco, "mt-[18px]")}>Por vendedor</div>
      <Distribuicao itens={g.porVendedor} />

      {/* Motivos de "não procede", só quando houve marcação */}
      {g.naoProcede > 0 && (
        <>
          <div className={cx(rotuloBloco, "mt-[18px]")}>Motivos de “não procede”</div>
          <Distribuicao itens={motivos} />
          <p className="mt-1.5 mb-0 text-xs leading-[1.45] text-ardosia">
            Cada marcação vira contraexemplo para a LLM. A taxa por padrão é a medida de que o aprendizado funciona: ela precisa cair com o tempo.
          </p>
        </>
      )}

      {/* Até três citações mais recentes, com link para o tema no cliente */}
      <div className={cx(rotuloBloco, "mt-[18px]")}>Amostra de citações</div>
      <ol className="m-0 grid list-none gap-3.5 p-0">
        {g.amostra.map((c) => (
          <li key={`${c.reuniaoId}-${c.turno}`}>
            <div className="mb-1.5 flex flex-wrap items-center gap-1.5 text-[12.5px]">
              <button type="button" className={cx(linkNeutro, "font-semibold text-ink")} onClick={() => navigate(rotas.cliente(c.cliente.id, c.temaId))}>
                {c.cliente.nome}
              </button>
              <span className="text-ardosia">
                · {fmtData(paraData(c.reuniaoData))} · {c.vendedorNome}
              </span>
            </div>
            <Citacao cit={c} compacta />
          </li>
        ))}
      </ol>
    </div>
  );
}
