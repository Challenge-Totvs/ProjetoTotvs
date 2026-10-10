/* Células da tabela de clientes, usadas pela tela do vendedor e (depois) pela do gestor. */

import type { ReactNode } from "react";
import { useNavigate } from "react-router-dom";
import type { ClienteResumo, Indicadores } from "../../types/api";
import { fmtData, paraData, relativo } from "../../lib/datas";
import { cx } from "../../lib/formato";
import { rotas } from "../../lib/rotas";
import { direita, linkForte, td, th } from "../ui/classes";
import { ChipTipoCliente, Glifo } from "../ui/glifos";
import { Regua } from "../ui/graficos";

/** Data da última reunião e, embaixo, a régua em miniatura (ou "Aguardando transcrição"). */
export function CelulaUltimaReuniao({ cliente }: { cliente: ClienteResumo }) {
  const ultima = cliente.ultimaReuniao;
  const r = cliente.ultimaAnalisada;
  if (!ultima) return <span className="text-xs text-faint">Sem reuniões</span>;
  const data = paraData(ultima.dataHora);
  return (
    <div className="min-w-[120px]">
      <div className="text-[12.5px] text-ink tabular-nums">
        {fmtData(data)} <span className="text-faint">· {relativo(data)}</span>
      </div>
      {ultima.status === "aguardando" ? (
        <div className="mt-[3px] text-[11.5px] text-atencao">Aguardando transcrição</div>
      ) : (
        r && (
          // Na miniatura só entram os temas; os interesses ficam de fora.
          <Regua
            mini
            turnos={r.turnos}
            marcas={r.marcas.filter((m) => m.tipo !== "interesse")}
            rotulo={`Régua da reunião de ${fmtData(paraData(r.dataHora))}`}
          />
        )
      )}
    </div>
  );
}

/** Cabeçalhos dos dois indicadores. `compacto` (painel aberto) deixa só o glifo. */
export function ThIndicadores({ compacto }: { compacto?: boolean }) {
  return (
    <>
      <th className={cx(th, direita)} title="Riscos sem retorno" aria-label="Riscos sem retorno">
        <span className="inline-flex items-center gap-[5px]">
          <Glifo tipo="risco" tamanho={10} />
          {!compacto && "Sem retorno"}
        </span>
      </th>
      <th className={cx(th, direita)} title="Oportunidades perdidas" aria-label="Oportunidades perdidas">
        <span className="inline-flex items-center gap-[5px]">
          <Glifo tipo="oportunidade" tamanho={10} />
          {!compacto && "Perdidas"}
        </span>
      </th>
    </>
  );
}

/** Os dois números: riscos sem retorno (vermelho) e oportunidades perdidas (âmbar); zero fica apagado. */
export function TdIndicadores({ ind }: { ind: Indicadores }) {
  return (
    <>
      <td className={cx(td, direita, "tabular-nums", ind.riscosSemRetorno ? "font-semibold text-critico" : "font-normal text-faint")}>
        {ind.riscosSemRetorno}
      </td>
      <td className={cx(td, direita, "tabular-nums", ind.oportPerdidas ? "font-semibold text-atencao" : "font-normal text-faint")}>
        {ind.oportPerdidas}
      </td>
    </>
  );
}

/** Nome do cliente (link para a página dele) e a linha de baixo (contato, segmento...). */
export function CelulaCliente({ c, sub, mostrarTipo }: { c: ClienteResumo; sub: ReactNode; mostrarTipo?: boolean }) {
  const navigate = useNavigate();
  return (
    <div className="min-w-0">
      <button
        type="button"
        className={cx(linkForte, "whitespace-nowrap")}
        onClick={(e) => {
          // Não deixa o clique chegar na linha (que só selecionaria).
          e.stopPropagation();
          navigate(rotas.cliente(c.id));
        }}
      >
        {c.nome}
      </button>
      <div className="mt-[3px] flex items-center gap-1.5 text-xs whitespace-nowrap text-ardosia">
        {mostrarTipo && <ChipTipoCliente tipo={c.tipo} />}
        <span>{sub}</span>
      </div>
    </div>
  );
}
