/* Prévia do cliente no painel lateral da lista de clientes. */

import { ArrowRight } from "lucide-react";
import { useNavigate } from "react-router-dom";
import type { ClienteResumo } from "../../types/api";
import { useApp } from "../../context/AppContext";
import { fmtData, fmtDiaSemana, fmtHora, paraData, relativo } from "../../lib/datas";
import { cx } from "../../lib/formato";
import { rotas } from "../../lib/rotas";
import { ItemTema } from "../tema/Itens";
import { Etiqueta, Numero } from "../ui/base";
import { btn, lista, listaBorda, numeros } from "../ui/classes";
import { ChipTipoCliente } from "../ui/glifos";

export function PreviaCliente({ cliente }: { cliente: ClienteResumo }) {
  const app = useApp();
  const navigate = useNavigate();
  const ind = cliente.indicadores;
  const temas = cliente.temasEmPauta.filter((t) => t.emPauta);
  const ultima = cliente.ultimaReuniao ? paraData(cliente.ultimaReuniao.dataHora) : null;
  const proxima = cliente.proximaReuniao ? paraData(cliente.proximaReuniao.dataHora) : null;

  return (
    <div>
      {/* Nome, tipo e segmento */}
      <div className="flex items-start gap-2.5">
        <div className="min-w-0 flex-1">
          <div className="text-base font-semibold text-ink">{cliente.nome}</div>
          <div className="mt-1.5 flex flex-wrap gap-1.5">
            <ChipTipoCliente tipo={cliente.tipo} />
            <Etiqueta>{cliente.segmento}</Etiqueta>
          </div>
        </div>
      </div>

      {/* Contatos, vendedor (só para o gestor) e reuniões */}
      <div className="mt-2.5 text-[12.5px] leading-normal text-ardosia">
        {cliente.contatos.map((c) => `${c.nome} (${c.cargo})`).join(" · ")}
        {app.gestor && <div>Vendedor: {cliente.vendedor.nome}</div>}
        {ultima && (
          <div>
            Última reunião: {fmtData(ultima)}, {relativo(ultima)}
          </div>
        )}
        {proxima && (
          <div>
            Próxima: {fmtDiaSemana(proxima)}, {fmtHora(proxima)}
          </div>
        )}
      </div>

      {/* Os dois indicadores principais */}
      <div className={cx(numeros(2), "mt-3.5")}>
        <Numero
          rotulo="Riscos sem retorno"
          valor={ind.riscosSemRetorno}
          tom={ind.riscosSemRetorno ? "critico" : undefined}
          sub={ind.riscosRecorrentes ? `${ind.riscosRecorrentes} recorrente${ind.riscosRecorrentes > 1 ? "s" : ""}` : undefined}
        />
        <Numero
          rotulo="Oportunidades perdidas"
          valor={ind.oportPerdidas}
          tom={ind.oportPerdidas ? "atencao" : undefined}
          sub={ind.oportSemRetorno ? `${ind.oportSemRetorno} sem retorno` : undefined}
        />
      </div>

      {/* Temas em pauta: cada um abre o cliente já com o tema selecionado */}
      <div className="mt-4 mb-1.5 text-xs font-semibold tracking-[0.04em] text-ardosia uppercase">Temas em pauta</div>
      {temas.length ? (
        <div className={cx(lista, listaBorda)}>
          {temas.map((t) => (
            <ItemTema
              key={t.id}
              tema={t}
              onClick={() => navigate(rotas.cliente(cliente.id, t.id))}
              mostrarSituacao
              etiquetasAbaixo
              detalhe={relativo(paraData(t.ultimaAtividade))}
            />
          ))}
        </div>
      ) : (
        <div className="text-[13px] text-faint">Nenhum tema em pauta.</div>
      )}

      <button type="button" className={btn({ primario: true, className: "mt-3.5 w-full justify-center" })} onClick={() => navigate(rotas.cliente(cliente.id))}>
        Abrir cliente
        <ArrowRight size={15} aria-hidden="true" />
      </button>
    </div>
  );
}
