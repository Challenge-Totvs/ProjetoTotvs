/* Sino do gestor: os pedidos de apoio ("Avisar gestor"), com os não lidos em destaque. */

import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Bell } from "lucide-react";
import * as gestorApi from "../../api/gestor";
import { useApp } from "../../context/AppContext";
import { useFecharFora } from "../../hooks/useFecharFora";
import { paraData, quandoAviso } from "../../lib/datas";
import { cx } from "../../lib/formato";
import { rotas } from "../../lib/rotas";
import type { Notificacao, Notificacoes as DadosNotificacoes } from "../../types/api";
import { btn } from "../ui/classes";
import { GlifosTema } from "../ui/glifos";
import { classeFlutuante } from "./MenuUsuario";

export function Notificacoes() {
  const app = useApp();
  const navigate = useNavigate();
  const [aberto, setAberto] = useState(false);
  const [dados, setDados] = useState<DadosNotificacoes>({ naoLidas: 0, itens: [] });
  const ref = useRef<HTMLDivElement>(null);
  const fechar = useCallback(() => setAberto(false), []);
  useFecharFora(aberto, fechar, ref);

  // Busca ao entrar, depois de cada ação e a cada minuto.
  useEffect(() => {
    const buscar = () =>
      gestorApi
        .listarNotificacoes()
        .then(setDados)
        .catch(() => undefined);
    void buscar();
    const timer = setInterval(buscar, 60000);
    return () => clearInterval(timer);
  }, [app.versao]);

  /** Abre o cliente com o tema selecionado e marca o pedido como lido. */
  function abrir(n: Notificacao) {
    setAberto(false);
    setDados((d) => ({
      naoLidas: Math.max(0, d.naoLidas - (n.lida ? 0 : 1)),
      itens: d.itens.map((x) => (x.id === n.id ? { ...x, lida: true } : x)),
    }));
    if (!n.lida) void gestorApi.marcarNotificacaoLida(n.id).catch(() => undefined);
    app.setPainelAberto(true);
    if (n.cliente) navigate(rotas.cliente(n.cliente.id, n.tema ? n.tema.id : null));
  }

  const naoLidas = dados.naoLidas;
  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        className={btn({ className: "relative w-[34px] justify-center px-0!" })}
        onClick={() => setAberto((a) => !a)}
        aria-label={naoLidas ? `Pedidos de apoio, ${naoLidas} não ${naoLidas === 1 ? "lido" : "lidos"}` : "Pedidos de apoio"}
        aria-expanded={aberto}
      >
        <Bell size={16} aria-hidden="true" />
        {naoLidas > 0 && (
          <span
            aria-hidden="true"
            className="absolute -top-[5px] -right-[5px] flex h-[18px] min-w-[18px] items-center justify-center rounded-full bg-critico px-[5px] text-[11px] font-semibold text-branco"
          >
            {naoLidas}
          </span>
        )}
      </button>
      {aberto && (
        <div role="dialog" aria-label="Pedidos de apoio" className={classeFlutuante} style={{ width: 380 }}>
          <div className="border-b border-linha px-3.5 py-3 text-[13px] font-semibold">Pedidos de apoio</div>
          {dados.itens.length === 0 && <div className="p-4 text-[13px] text-ardosia">Nenhum pedido de apoio por enquanto.</div>}
          <ul className="m-0 max-h-[420px] list-none overflow-y-auto p-0">
            {dados.itens.map((n) => (
              <li key={n.id}>
                <button
                  type="button"
                  onClick={() => abrir(n)}
                  className={cx("flex w-full gap-2.5 border-b border-linha px-3.5 py-3 text-left", n.lida ? "bg-branco" : "bg-nevoa")}
                >
                  <span aria-hidden="true" className={cx("mt-1.5 h-2 w-2 flex-none rounded-full", n.lida ? "bg-transparent" : "bg-sinal-texto")} />
                  <span className="min-w-0">
                    <span className="block text-[13px] leading-[1.45] text-ink">
                      {n.de.nome} pediu apoio em {n.cliente ? n.cliente.nome : "cliente removido"}
                    </span>
                    {n.tema && (
                      <span className="mt-1 flex items-center gap-1.5">
                        <GlifosTema tipos={n.tema.tipos} tratado={n.tema.ultimaTratado} tamanho={10} />
                        <span className="text-xs font-medium text-ink">{n.tema.titulo}</span>
                      </span>
                    )}
                    {n.mensagem && <span className="mt-[3px] block text-xs leading-[1.45] text-ardosia">{n.mensagem}</span>}
                    <span className="mt-1 block text-[11px] text-faint">{quandoAviso(paraData(n.criadoEm))}</span>
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
