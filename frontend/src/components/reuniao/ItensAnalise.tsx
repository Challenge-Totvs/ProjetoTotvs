/* Itens das listas da análise: um tema citado (risco ou oportunidade) e um ponto de interesse. */

import { useNavigate } from "react-router-dom";
import type { InteresseItem, TemaNaReuniao, TurnoTranscricao } from "../../types/api";
import { cx } from "../../lib/formato";
import { rotas } from "../../lib/rotas";
import { linkNeutro } from "../ui/classes";
import { Citacao } from "../ui/Citacao";
import { GlifosTema } from "../ui/glifos";

/** Classes da linha de cada item (linha entre os itens, sem linha no primeiro). */
export const itemAnalise = "border-t border-linha px-4 py-3 first:border-t-0";
export const listaAnalise = "m-0 list-none p-0";

/** Tema citado nesta reunião: glifos, título (abre o tema no cliente), estado da resposta e a citação. */
export function ItemAnalise({ item, turnos }: { item: TemaNaReuniao; turnos: TurnoTranscricao[] | null }) {
  const navigate = useNavigate();
  const { tema, citacao } = item;
  // Cor e texto do estado da resposta, como na demo.
  const estado =
    citacao.tratado === true
      ? { texto: "respondido na reunião", cor: "text-resolvido" }
      : citacao.tratado === false
        ? { texto: "sem resposta", cor: "text-critico" }
        : { texto: "sem leitura de resposta", cor: "text-faint" };
  return (
    <li className={itemAnalise}>
      <div className="flex flex-wrap items-center gap-2">
        <GlifosTema tipos={tema.tipos} tratado={citacao.tratado} />
        <button
          type="button"
          className={cx(linkNeutro, "text-left text-[13.5px] font-semibold text-ink")}
          onClick={() => navigate(rotas.cliente(tema.clienteId, tema.id))}
        >
          {tema.titulo}
        </button>
        <span className={cx("text-xs", estado.cor)}>{estado.texto}</span>
      </div>
      <div className="mt-1.5">
        <Citacao cit={citacao} turnos={turnos} />
      </div>
    </li>
  );
}

/** Ponto de interesse: o que o cliente demonstrou e o trecho que comprova. */
export function ItemInteresse({ x, turnos }: { x: InteresseItem; turnos: TurnoTranscricao[] | null }) {
  return (
    <li className={itemAnalise}>
      <div className="text-[13.5px] font-medium text-ink">{x.texto}</div>
      <div className="mt-1.5">
        <Citacao cit={{ turno: x.turno, texto: x.citacao, conferida: x.conferida, locutor: x.locutor, papel: x.papel }} turnos={turnos} />
      </div>
    </li>
  );
}
