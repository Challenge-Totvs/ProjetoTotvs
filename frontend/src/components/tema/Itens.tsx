/* Itens de lista compartilhados: tema, compromisso e reunião da agenda. */

import { AlertTriangle, CheckCircle2, Circle } from "lucide-react";
import { useNavigate } from "react-router-dom";
import type { AgendaItem, Compromisso, Tema } from "../../types/api";
import { useApp } from "../../context/AppContext";
import { fmtData, fmtHora, paraData, relativo, SEMANA } from "../../lib/datas";
import { detalheAtencao, rotuloPrazo, ultimaCitacao } from "../../lib/dominio";
import { cx } from "../../lib/formato";
import { rotas } from "../../lib/rotas";
import { Etiqueta } from "../ui/base";
import { COR } from "../ui/cores";
import { btn, item, itemSub, itemTitulo, linkNeutro } from "../ui/classes";
import { ChipRecorrente, GlifosTema, TagSituacao } from "../ui/glifos";

/** Uma linha de tema: glifos, título, cliente e detalhe, com as etiquetas. */
export function ItemTema({
  tema,
  mostrarCliente,
  selecionado,
  onClick,
  detalhe,
  mostrarSituacao,
  etiquetasAbaixo,
}: {
  tema: Tema;
  mostrarCliente?: boolean;
  selecionado?: boolean;
  onClick: () => void;
  detalhe?: string;
  mostrarSituacao?: boolean;
  etiquetasAbaixo?: boolean;
}) {
  const etiquetas = (
    <span className={cx("flex flex-wrap items-center gap-1", etiquetasAbaixo ? "mt-[5px] justify-start" : "justify-end")}>
      {tema.recorrente && <ChipRecorrente n={tema.reunioesNaJanela} />}
      {mostrarSituacao && <TagSituacao tema={tema} compacta />}
      {tema.semelhanteNaoProcede && !tema.naoProcede && (
        <span title="Parecido com um trecho marcado como não procede" className="inline-flex text-atencao">
          <AlertTriangle size={14} aria-label="Parecido com não procede anterior" />
        </span>
      )}
    </span>
  );
  return (
    <button type="button" className={item} aria-current={selecionado ? "true" : undefined} onClick={onClick}>
      <span className="pt-0.5">
        <GlifosTema tipos={tema.tipos} tratado={ultimaCitacao(tema)?.tratado ?? null} />
      </span>
      <span className="min-w-0 flex-1">
        <span className={itemTitulo}>{tema.titulo}</span>
        <span className={itemSub}>
          {mostrarCliente ? `${tema.clienteNome} · ` : ""}
          {detalhe || detalheAtencao(tema)}
        </span>
        {etiquetasAbaixo && etiquetas}
      </span>
      {!etiquetasAbaixo && etiquetas}
    </button>
  );
}

/** Um compromisso do vendedor, com a caixa de "cumprido" para o dono. */
export function ItemCompromisso({ cp, somenteLeitura, mostrarCliente = true }: { cp: Compromisso; somenteLeitura?: boolean; mostrarCliente?: boolean }) {
  const app = useApp();
  const navigate = useNavigate();
  const vencido = cp.estado === "vencido";
  return (
    <li className="flex items-start gap-2.5 border-t border-linha px-4 py-2.5 first:border-t-0">
      {somenteLeitura ? (
        <span aria-hidden="true" className="flex w-4 justify-center pt-0.5">
          {cp.cumprido ? <CheckCircle2 size={15} className="text-resolvido" /> : <Circle size={15} className={vencido ? "text-critico" : "text-faint"} />}
        </span>
      ) : (
        <input
          type="checkbox"
          className="mt-0.5 h-4 w-4 flex-none cursor-pointer accent-resolvido"
          checked={cp.cumprido}
          onChange={(e) => void app.acoes.marcarCompromisso(cp, e.target.checked)}
          aria-label={`Marcar como cumprido: ${cp.texto}`}
        />
      )}
      <span className="min-w-0 flex-1">
        <button
          type="button"
          className={cx(linkNeutro, "text-left text-[13px] leading-[1.45]", cp.cumprido ? "text-faint line-through" : "text-ink")}
          onClick={() => navigate(rotas.reuniao(cp.reuniaoId, cp.turno))}
        >
          “{cp.texto}”
        </button>
        <span className={cx(itemSub, vencido ? "text-critico" : "text-ardosia")}>
          {mostrarCliente ? `${cp.clienteNome} · ` : ""}
          {rotuloPrazo(cp)}
        </span>
      </span>
    </li>
  );
}

/** Uma reunião agendada, com "Preparar" (ou "Ver cliente" na visão do gestor). */
export function ItemReuniaoAgenda({ r, somenteLeitura }: { r: AgendaItem; somenteLeitura?: boolean }) {
  const navigate = useNavigate();
  const data = paraData(r.dataHora);
  return (
    <li className="flex items-center gap-3 border-t border-linha px-4 py-2.5 first:border-t-0">
      <span className="grid w-[52px] flex-none justify-items-center rounded-lg border border-linha py-1 leading-[1.25]">
        <span className="text-[11px] text-ardosia uppercase">{SEMANA[data.getDay()]}</span>
        <span className="text-[15px] font-semibold text-ink tabular-nums">{fmtData(data)}</span>
        <span className="text-[11px] text-ardosia tabular-nums">{fmtHora(data)}</span>
      </span>
      <span className="min-w-0 flex-1">
        <span className={itemTitulo}>{r.clienteNome}</span>
        <span className={itemSub}>
          {r.titulo} · {r.contato}
        </span>
        <span className="mt-[5px] flex flex-wrap items-center gap-1.5">
          {r.confirmada ? <Etiqueta cor={COR.resolvido}>Confirmada</Etiqueta> : <Etiqueta cor={COR.atencaoBranco}>A confirmar</Etiqueta>}
          <span className="text-xs text-faint">{relativo(data)}</span>
        </span>
      </span>
      <button
        type="button"
        className={btn({ sm: true })}
        onClick={() => navigate(rotas.cliente(r.clienteId))}
        title={somenteLeitura ? "Abrir o cliente" : "Abrir o cliente para preparar a reunião"}
      >
        {somenteLeitura ? "Ver cliente" : "Preparar"}
      </button>
    </li>
  );
}
