/* Painel lateral do tema na página do cliente: situação, ações do vendedor,
   registro fora da reunião, avisos à gestão e as citações ("Onde apareceu"). */

import { CornerDownRight, Lock, Send, ThumbsDown, Undo2 } from "lucide-react";
import { useNavigate } from "react-router-dom";
import type { Tema } from "../../types/api";
import { useApp } from "../../context/AppContext";
import { fmtData, fmtDataAno, paraData, quandoAviso } from "../../lib/datas";
import { nomeAcaoFora, nomeCanal } from "../../lib/dominio";
import { cx } from "../../lib/formato";
import { rotas } from "../../lib/rotas";
import { Aviso, Kbd } from "../ui/base";
import { Citacao } from "../ui/Citacao";
import { bloco, btn, link, linkNeutro, rotuloBloco } from "../ui/classes";
import { ChipRecorrente, ChipTipos, GlifosTema, TagSituacao } from "../ui/glifos";

/** Chave de uma citação (reunião + turno), usada para abrir um contexto por vez.
    A página usa o mesmo formato na tecla V. */
const chaveCitacao = (reuniaoId: number, turno: number) => `${reuniaoId}-${turno}`;

export function InspetorTema({
  tema,
  podeAgir,
  contextoAberto,
  setContextoAberto,
}: {
  tema: Tema;
  /** O usuário é o vendedor dono do cliente. */
  podeAgir: boolean;
  /** Chave da citação com o contexto aberto (controlado pela página, para a tecla V). */
  contextoAberto: string | null;
  setContextoAberto: (chave: string | null) => void;
}) {
  const app = useApp();
  const navigate = useNavigate();
  // Avisos do mais novo para o mais antigo; citações da mais recente para a mais antiga.
  const avisos = [...tema.avisos].sort((a, b) => paraData(b.criadoEm).getTime() - paraData(a.criadoEm).getTime());
  const cits = [...tema.citacoes].reverse();
  const fora = tema.registroFora;

  return (
    <div>
      {/* Título, tipos e padrão */}
      <h2 className="m-0 text-base leading-[1.35] font-semibold text-ink">{tema.titulo}</h2>
      <div className="mt-2 flex flex-wrap items-center gap-1.5">
        <ChipTipos tipos={tema.tipos} />
        <span className="text-xs text-ardosia">Padrão: {tema.padraoNome || tema.padrao}</span>
      </div>
      {tema.tipos.length > 1 && (
        <p className="mt-1.5 mb-0 text-xs leading-[1.45] text-ardosia">O mesmo trecho recebeu dois rótulos e virou um tema só, com as duas etiquetas.</p>
      )}

      {/* Situação, com a frase explicativa que vem pronta do backend */}
      <div className={cx(bloco, "mt-3.5")}>
        <div className="flex flex-wrap items-center gap-1.5">
          <TagSituacao tema={tema} />
          {tema.recorrente && <ChipRecorrente n={tema.reunioesNaJanela} />}
        </div>
        <p className="mt-2 mb-0 text-[13px] leading-normal text-ink">{tema.explicacao}</p>
        {tema.situacao !== "nao_procede" && tema.leitura && (
          <p className="mt-1.5 mb-0 text-[11.5px] leading-[1.45] text-faint">Quem falou é inferido pela LLM a partir da transcrição; a situação é uma estimativa.</p>
        )}
      </div>

      {/* Parecido com um trecho já marcado como não procede */}
      {tema.semelhanteNaoProcede && !tema.naoProcede && (
        <div className="mt-3">
          <Aviso tom="atencao">
            Parecido com um trecho marcado como não procede antes: “{tema.semelhanteNaoProcede.texto}” ({tema.semelhanteNaoProcede.clienteNome}). Confira
            antes de agir; o aviso nunca esconde o tema sozinho.
          </Aviso>
        </div>
      )}
      {/* O mesmo assunto já foi um tema que saiu de pauta */}
      {tema.anterior && (
        <p className="mt-3 mb-0 text-[12.5px] leading-[1.45] text-ardosia">
          Este assunto já apareceu e saiu de pauta.{" "}
          <button type="button" className={link} onClick={() => tema.anterior && navigate(rotas.cliente(tema.clienteId, tema.anterior.id))}>
            Ver o tema anterior
          </button>
        </p>
      )}

      {/* Ações do vendedor dono (T, N, A) */}
      {podeAgir && (
        <div className="mt-3.5 grid gap-1.5">
          {tema.naoProcede ? (
            <button type="button" className={btn()} onClick={() => void app.acoes.desfazerNaoProcede(tema)}>
              <Undo2 size={14} aria-hidden="true" />
              Desfazer “não procede”
            </button>
          ) : (
            <>
              {fora ? (
                <button type="button" className={btn()} onClick={() => void app.acoes.removerFora(tema)}>
                  <Undo2 size={14} aria-hidden="true" />
                  Remover o registro fora da reunião
                </button>
              ) : (
                <button type="button" className={btn({ primario: true })} onClick={() => app.abrirModal("fora", tema)}>
                  <CornerDownRight size={14} aria-hidden="true" />
                  Tratei fora da reunião
                  <Kbd claro>T</Kbd>
                </button>
              )}
              <div className="grid grid-cols-2 gap-1.5">
                <button type="button" className={btn()} onClick={() => app.abrirModal("naoProcede", tema)}>
                  <ThumbsDown size={14} aria-hidden="true" />
                  Não procede
                  <Kbd>N</Kbd>
                </button>
                <button type="button" className={btn()} onClick={() => app.abrirModal("avisar", tema)}>
                  <Send size={14} aria-hidden="true" />
                  Avisar gestor
                  <Kbd>A</Kbd>
                </button>
              </div>
            </>
          )}
        </div>
      )}
      {app.gestor && (
        <p className="mt-3 mb-0 flex items-center gap-1.5 text-xs text-faint">
          <Lock size={12} aria-hidden="true" />
          Só leitura. As ações no tema são do vendedor.
        </p>
      )}

      {/* Registro "Tratei fora da reunião" */}
      {fora && (
        <div className={cx(bloco, "mt-3.5")}>
          <div className={rotuloBloco}>Registro fora da reunião</div>
          <dl className="m-0 grid grid-cols-[120px_minmax(0,1fr)] gap-x-2.5 gap-y-1.5 text-[13px] [&_dd]:m-0 [&_dd]:text-ink [&_dt]:text-ardosia">
            <dt>O que foi feito</dt>
            <dd>{nomeAcaoFora(fora.acao)}</dd>
            <dt>Canal</dt>
            <dd>{nomeCanal(fora.canal)}</dd>
            <dt>Data</dt>
            <dd>{fmtDataAno(paraData(fora.data))}</dd>
            {fora.observacao && (
              <>
                <dt>Observação</dt>
                <dd>{fora.observacao}</dd>
              </>
            )}
            <dt>Registrado por</dt>
            <dd>{fora.por.nome}</dd>
          </dl>
        </div>
      )}

      {/* Avisos já enviados à gestão sobre este tema */}
      {avisos.length > 0 && (
        <div className="mt-3.5 text-[12.5px] leading-normal text-ardosia">
          {avisos.map((n) => (
            <div key={n.id} className="flex items-start gap-1.5">
              <Send size={12} aria-hidden="true" className="mt-1 flex-none" />
              <span>
                {n.de.id === app.usuario.id ? "Você avisou" : `${n.de.nome} avisou`} a gestão {quandoAviso(paraData(n.criadoEm))}
                {n.mensagem ? `: “${n.mensagem}”` : "."}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Onde apareceu: as citações, da mais recente para a mais antiga */}
      <div className={cx(rotuloBloco, "mt-[18px]")}>Onde apareceu</div>
      <ol className="m-0 grid list-none gap-3.5 p-0">
        {cits.map((c) => {
          const chave = chaveCitacao(c.reuniaoId, c.turno);
          return (
            <li key={chave} className="border-t border-linha pt-3 first:border-t-0 first:pt-0">
              <div className="mb-1.5 flex flex-wrap items-center gap-2">
                <GlifosTema tipos={tema.tipos} tratado={c.tratado} tamanho={11} />
                <button
                  type="button"
                  className={cx(linkNeutro, "text-[12.5px] font-semibold text-ink")}
                  onClick={() => navigate(rotas.reuniao(c.reuniaoId, c.turno))}
                >
                  {fmtData(paraData(c.reuniaoData))} · {c.reuniaoTitulo}
                </button>
                <span className={cx("text-xs", c.tratado === false ? "text-critico" : c.tratado === true ? "text-resolvido" : "text-faint")}>
                  {c.tratado === true ? "respondido na reunião" : c.tratado === false ? "sem resposta" : "sem leitura"}
                </span>
              </div>
              <Citacao
                cit={c}
                compacta
                contextoAberto={contextoAberto === chave}
                onAlternarContexto={() => setContextoAberto(contextoAberto === chave ? null : chave)}
              />
            </li>
          );
        })}
      </ol>
    </div>
  );
}
