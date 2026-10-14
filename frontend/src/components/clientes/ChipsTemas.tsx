/* Chips dos temas em pauta de um cliente (lista de clientes). Cada chip é um botão de
   verdade: ao clicar, abre um pop-up dedicado (ModalTema) com os detalhes do tema — onde
   foi levantado, de que resultou, e um botão direto para a reunião específica — em vez de
   navegar para a página do cliente. */

import { useState } from "react";
import { Repeat } from "lucide-react";
import type { Id, Tema } from "../../types/api";
import { useApp } from "../../context/AppContext";
import { ROTULO_SITUACAO } from "../../lib/dominio";
import { ModalTema } from "../tema/ModalTema";
import { GlifosTema } from "../ui/glifos";

export function ChipsTemas({
  temas,
  max = 3,
  porPadrao,
  vendedorId,
}: {
  temas: Tema[];
  max?: number;
  porPadrao?: boolean;
  /** Id do vendedor dono do cliente — decide se os botões de ação aparecem no pop-up. */
  vendedorId?: Id;
}) {
  const app = useApp();
  const [abertoId, setAbertoId] = useState<Id | null>(null);
  const lista = temas.filter((t) => t.emPauta);
  if (!lista.length) return <span className="text-xs text-faint">Nenhum em pauta</span>;
  const aberto = abertoId != null ? temas.find((t) => t.id === abertoId) ?? null : null;
  const podeAgir = !app.gestor && vendedorId === app.usuario.id;

  return (
    <>
      <span className="flex flex-wrap items-center gap-1">
        {lista.slice(0, max).map((t) => (
          <button
            key={t.id}
            type="button"
            className="inline-flex max-w-[190px] cursor-pointer items-center gap-[5px] rounded border border-linha bg-branco px-[7px] py-px text-xs text-ink hover:border-sinal-texto hover:bg-sinal-fundo hover:text-sinal-texto focus-visible:outline-2 focus-visible:outline-sinal-texto focus-visible:outline-offset-1"
            title={`Abrir detalhes: ${t.titulo} · ${ROTULO_SITUACAO[t.situacao]}`}
            onClick={(e) => {
              // Não deixa o clique chegar na linha (que só selecionaria).
              e.stopPropagation();
              setAbertoId(t.id);
            }}
          >
            <GlifosTema tipos={t.tipos} tratado={t.citacoes[0]?.tratado ?? null} />
            <span className="truncate">{porPadrao ? t.padraoNome : t.titulo}</span>
            {t.recorrente && <Repeat size={11} aria-label="recorrente" />}
          </button>
        ))}
        {lista.length > max && <span className="text-xs text-ardosia">+{lista.length - max}</span>}
      </span>
      {aberto && <ModalTema tema={aberto} podeAgir={podeAgir} onFechar={() => setAbertoId(null)} />}
    </>
  );
}
