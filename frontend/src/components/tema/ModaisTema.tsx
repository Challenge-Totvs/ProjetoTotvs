/* Modais das ações do vendedor no tema: Tratei fora, Não procede e Avisar gestor. */

import { useMemo, useState, type FormEvent } from "react";
import { Send } from "lucide-react";
import type { Tema, TratadoForaRequest } from "../../types/api";
import { hojeISO } from "../../lib/datas";
import { ACOES_FORA, CANAIS, MOTIVOS_NAO_PROCEDE, temOport, temRisco, ultimaCitacao } from "../../lib/dominio";
import { Aviso } from "../ui/base";
import { btn, input, opcional, textarea } from "../ui/classes";
import { GlifosTema, TagSituacao } from "../ui/glifos";
import { GrupoRadio, Modal } from "../ui/Sobrepostos";

export function ModalTratarFora({ tema, onConfirmar, onFechar }: { tema: Tema; onConfirmar: (reg: TratadoForaRequest) => void; onFechar: () => void }) {
  // Tema duplo mostra as duas listas (oportunidade e risco).
  const opcoes = useMemo(() => {
    const lista: [string, string][] = [];
    if (temOport(tema)) lista.push(...ACOES_FORA.oportunidade);
    if (temRisco(tema)) lista.push(...ACOES_FORA.risco.filter(([k]) => !lista.some(([x]) => x === k)));
    return lista;
  }, [tema]);
  const [acao, setAcao] = useState<string | null>(null);
  const [canal, setCanal] = useState("email");
  const [data, setData] = useState(hojeISO());
  const [obs, setObs] = useState("");
  const [erro, setErro] = useState<string | null>(null);

  function enviar(e: FormEvent) {
    e.preventDefault();
    if (!acao) return setErro("Escolha o que foi feito.");
    if (!data || data > hojeISO()) return setErro("A data não pode ser no futuro.");
    onConfirmar({ acao, canal, data, observacao: obs.trim() });
  }

  return (
    <Modal
      titulo="Tratei fora da reunião"
      descricao={`${tema.titulo}. Registre o que foi feito: o tema passa a "Tratado fora da reunião" e o registro aparece no mapa e na linha do tempo do cliente.`}
      onFechar={onFechar}
      largura={560}
    >
      <form onSubmit={enviar} className="grid gap-4">
        <GrupoRadio
          nome="acao"
          rotulo="O que foi feito"
          opcoes={opcoes}
          valor={acao}
          onChange={(v) => {
            setAcao(v);
            setErro(null);
          }}
          colunas={2}
        />
        <GrupoRadio nome="canal" rotulo="Canal" opcoes={CANAIS} valor={canal} onChange={setCanal} colunas={3} />
        <div className="grid grid-cols-[180px_1fr] gap-3">
          <label className="grid gap-1.5 text-[13px] font-medium">
            Data
            <input type="date" className={input} value={data} max={hojeISO()} onChange={(e) => setData(e.target.value)} />
          </label>
          <label className="grid gap-1.5 text-[13px] font-medium">
            Observação <span className={`${opcional} -mt-1`}>opcional</span>
            <textarea className={textarea} rows={2} value={obs} onChange={(e) => setObs(e.target.value)} placeholder="Ex.: proposta com as duas filiais enviada à Marina" />
          </label>
        </div>
        {erro && <Aviso tom="erro">{erro}</Aviso>}
        <div className="flex justify-end gap-2">
          <button type="button" className={btn()} onClick={onFechar}>
            Cancelar
          </button>
          <button type="submit" className={btn({ primario: true })}>
            Registrar
          </button>
        </div>
      </form>
    </Modal>
  );
}

export function ModalNaoProcede({ tema, onConfirmar, onFechar }: { tema: Tema; onConfirmar: (motivo: string | null) => void; onFechar: () => void }) {
  const [motivo, setMotivo] = useState<string | null>(null);
  return (
    <Modal
      titulo="Marcar como não procede"
      descricao={`${tema.titulo}. O tema sai do resumo e vira contraexemplo para as próximas análises; a taxa de "não procede" do padrão aparece para a gestão.`}
      onFechar={onFechar}
    >
      <form
        onSubmit={(e) => {
          e.preventDefault();
          onConfirmar(motivo);
        }}
        className="grid gap-4"
      >
        <GrupoRadio nome="motivo" rotulo="Motivo (opcional)" opcoes={MOTIVOS_NAO_PROCEDE} valor={motivo} onChange={setMotivo} colunas={2} />
        <div className="flex justify-end gap-2">
          <button type="button" className={btn()} onClick={onFechar}>
            Cancelar
          </button>
          <button type="submit" className={btn({ primario: true })} data-autofoco>
            Marcar como não procede
          </button>
        </div>
      </form>
    </Modal>
  );
}

export function ModalAvisarGestor({
  tema,
  gestorNome,
  onConfirmar,
  onFechar,
}: {
  tema: Tema;
  gestorNome: string;
  onConfirmar: (mensagem: string) => void;
  onFechar: () => void;
}) {
  const [msg, setMsg] = useState("");
  return (
    <Modal titulo="Avisar gestor" descricao={`${gestorNome} recebe uma notificação que leva direto a este tema. Não abre fila nem muda a situação.`} onFechar={onFechar}>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          onConfirmar(msg.trim());
        }}
        className="grid gap-4"
      >
        <div className="flex items-center gap-2 text-[13px]">
          <GlifosTema tipos={tema.tipos} tratado={ultimaCitacao(tema)?.tratado ?? null} />
          <strong className="font-semibold">{tema.titulo}</strong>
          <TagSituacao tema={tema} compacta />
        </div>
        <label className="grid gap-1.5 text-[13px] font-medium">
          Mensagem <span className={`${opcional} -mt-1`}>opcional</span>
          <textarea className={textarea} rows={3} value={msg} onChange={(e) => setMsg(e.target.value)} placeholder="Ex.: preciso de apoio para acionar a liderança do suporte" />
        </label>
        <div className="flex justify-end gap-2">
          <button type="button" className={btn()} onClick={onFechar}>
            Cancelar
          </button>
          <button type="submit" className={btn({ primario: true })}>
            <Send size={14} aria-hidden="true" />
            Enviar aviso
          </button>
        </div>
      </form>
    </Modal>
  );
}
