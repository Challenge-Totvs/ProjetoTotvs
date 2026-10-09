/* Estrutura das telas logadas: barra lateral, topo com trilha, banner de
   contingência, conteúdo, rodapé de atalhos, busca (Ctrl/⌘ K), modais e avisos. */

import { Fragment, useEffect, useRef, useState } from "react";
import { Outlet, useLocation, useNavigate } from "react-router-dom";
import { AlertCircle, AlertTriangle, CheckCircle2, ChevronRight, Keyboard, Search, Undo2, X } from "lucide-react";
import { useApp } from "../../context/AppContext";
import { useAuth } from "../../context/AuthContext";
import { cx } from "../../lib/formato";
import { rotas } from "../../lib/rotas";
import { ATALHO_BUSCA } from "../../lib/teclado";
import { Kbd } from "../ui/base";
import { btn, link, linkNeutro } from "../ui/classes";
import { ModalAvisarGestor, ModalNaoProcede, ModalTratarFora } from "../tema/ModaisTema";
import { MenuUsuario } from "./MenuUsuario";
import { Paleta } from "./Paleta";
import { Sidebar } from "./Sidebar";


export function AppLayout() {
  const app = useApp();
  const { sair } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const mainRef = useRef<HTMLElement>(null);
  const [paleta, setPaleta] = useState(false);
  const estado = useRef({ paleta, modal: !!app.modal, esperandoG: false });
  // O teclado lê o estado por esta referência, atualizada depois de cada render.
  useEffect(() => {
    estado.current.paleta = paleta;
    estado.current.modal = !!app.modal;
  }, [paleta, app.modal]);

  // Cada troca de tela volta o conteúdo para o topo.
  useEffect(() => {
    if (mainRef.current) mainRef.current.scrollTop = 0;
  }, [location.pathname]);

  // Teclado: Ctrl/⌘ K (busca), G + letra (ir para), ] (painel) e as teclas da tela atual.
  useEffect(() => {
    let timerG: ReturnType<typeof setTimeout> | undefined;
    function onKey(e: KeyboardEvent) {
      const st = estado.current;
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setPaleta((p) => !p);
        return;
      }
      if (st.paleta || st.modal) return;
      const alvo = e.target as HTMLElement | null;
      const tag = alvo?.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" || alvo?.isContentEditable) return;
      if (e.metaKey || e.ctrlKey || e.altKey) return;
      const k = e.key.length === 1 ? e.key.toLowerCase() : e.key;
      if (st.esperandoG) {
        st.esperandoG = false;
        clearTimeout(timerG);
        const destinos: Record<string, string> = app.gestor
          ? { c: rotas.clientes, p: rotas.padroes, v: rotas.vendedores }
          : { i: rotas.inicio, c: rotas.clientes };
        if (destinos[k]) {
          e.preventDefault();
          navigate(destinos[k]);
        }
        return;
      }
      if (k === "g") {
        st.esperandoG = true;
        timerG = setTimeout(() => {
          st.esperandoG = false;
        }, 1200);
        return;
      }
      if (k === "]") {
        e.preventDefault();
        app.setPainelAberto(!app.painelAberto);
        return;
      }
      const t = app.teclasRef.current;
      const fn = t && (t[k] || t[e.key]);
      if (fn) {
        if (k === "Enter" && (tag === "BUTTON" || tag === "A")) return;
        e.preventDefault();
        fn(e);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [app, navigate]);

  const modal = app.modal;

  return (
    <>
      <div className="flex h-screen bg-nevoa">
        <Sidebar />
        <div className="flex min-w-0 flex-1 flex-col">
          <header className="flex h-14 flex-none items-center gap-3 border-b border-linha bg-branco pr-5 pl-6 max-[640px]:pr-3 max-[640px]:pl-4">
            <nav aria-label="Você está em" className="flex min-w-0 flex-1 items-center gap-1.5 text-[13px]">
              {app.trilha.map((t, idx) => (
                <Fragment key={`${t.l}-${idx}`}>
                  {idx > 0 && <ChevronRight size={14} className="flex-none text-faint" aria-hidden="true" />}
                  {t.para ? (
                    <button type="button" className={cx(linkNeutro, "whitespace-nowrap text-ardosia")} onClick={() => navigate(t.para as string)}>
                      {t.l}
                    </button>
                  ) : (
                    <span aria-current="page" className="min-w-0 truncate font-medium whitespace-nowrap text-ink">
                      {t.l}
                    </span>
                  )}
                </Fragment>
              ))}
            </nav>
            <div className="flex flex-none items-center gap-2">
              <button type="button" className={btn({ className: "text-ardosia!" })} onClick={() => setPaleta(true)} aria-label="Buscar e navegar">
                <Search size={14} aria-hidden="true" />
                <span className="max-[900px]:hidden">Buscar</span>
                <span className="max-[900px]:hidden">
                  <Kbd>{ATALHO_BUSCA}</Kbd>
                </span>
              </button>
              <MenuUsuario
                onSair={() => {
                  sair();
                  navigate(rotas.login);
                }}
              />
            </div>
          </header>
          <BannerContingencia />
          <main ref={mainRef} id="conteudo" className="flex-1 overflow-x-hidden overflow-y-auto px-7 pt-6 pb-10 max-[640px]:px-4 max-[640px]:pt-4 max-[640px]:pb-8">
            <Outlet />
          </main>
          <Rodape />
        </div>
      </div>

      {paleta && (
        <Paleta
          fechar={() => setPaleta(false)}
          onSair={() => {
            sair();
            navigate(rotas.login);
          }}
        />
      )}

      {modal?.tipo === "fora" && (
        <ModalTratarFora tema={modal.tema} onFechar={app.fecharModal} onConfirmar={(reg) => void app.acoes.registrarFora(modal.tema, reg)} />
      )}
      {modal?.tipo === "naoProcede" && (
        <ModalNaoProcede tema={modal.tema} onFechar={app.fecharModal} onConfirmar={(m) => void app.acoes.marcarNaoProcede(modal.tema, m)} />
      )}
      {modal?.tipo === "avisar" && (
        <ModalAvisarGestor
          tema={modal.tema}
          gestorNome={app.usuario.gestor ? app.usuario.gestor.nome : "A gestão do time"}
          onFechar={app.fecharModal}
          onConfirmar={(m) => void app.acoes.avisarGestor(modal.tema, m)}
        />
      )}

      <Toasts />
    </>
  );
}

/* ---------- Banner de contingência ---------- */

function BannerContingencia() {
  const { estadoMotores } = useApp();
  const navigate = useNavigate();
  if (estadoMotores === "normal") return null;
  const texto =
    estadoMotores === "llm1_fora"
      ? "A LLM principal não está respondendo. As próximas análises seguem pela LLM secundária, sem perda de qualidade esperada."
      : "As duas LLMs não estão respondendo. As próximas análises seguem pelo modelo local, marcadas como contingência: sem resumo e sem leitura de quem falou. Reprocessam quando uma LLM voltar.";
  return (
    <div className="flex items-center gap-2.5 border-b border-atencao-borda bg-atencao-fundo px-6 py-[9px] text-[13px] leading-[1.4] text-atencao max-[640px]:px-4" role="status">
      <AlertTriangle size={15} aria-hidden="true" className="flex-none" />
      <span className="min-w-0 flex-1">{texto}</span>
      <button type="button" className={cx(link, "whitespace-nowrap text-atencao!")} onClick={() => navigate(rotas.configuracoes)}>
        Ver motores
      </button>
    </div>
  );
}

/* ---------- Rodapé com os atalhos da tela ---------- */

function Rodape() {
  const { legenda } = useApp();
  const itens: [string[], string][] = [...legenda, [[ATALHO_BUSCA], "buscar"], [["G", "I C P V"], "ir para"]];
  return (
    <footer
      className="flex h-8 flex-none items-center gap-3.5 overflow-hidden border-t border-linha bg-branco pr-5 pl-6 text-xs text-ardosia max-[640px]:hidden"
      aria-label="Atalhos de teclado desta tela"
    >
      <Keyboard size={13} aria-hidden="true" className="flex-none text-faint" />
      {itens.map(([teclas, rotulo]) => (
        <span key={rotulo} className="inline-flex items-center gap-1 whitespace-nowrap">
          {teclas.map((t) => (
            <Kbd key={t}>{t}</Kbd>
          ))}
          <span>{rotulo}</span>
        </span>
      ))}
    </footer>
  );
}

/* ---------- Avisos (toasts) ---------- */

function Toasts() {
  const { toasts, fecharToast } = useApp();
  return (
    <div
      className="fixed bottom-11 left-[248px] z-70 grid max-w-[min(460px,calc(100vw-32px))] gap-2 max-[900px]:left-20 max-[640px]:bottom-4 max-[640px]:left-4"
      aria-live="polite"
    >
      {toasts.map((t) => (
        <div
          key={t.id}
          className="flex items-center gap-2.5 rounded-[10px] bg-ink px-3 py-2.5 text-[13px] leading-[1.4] text-branco shadow-[0_10px_28px_rgba(0,34,51,.28)]"
          role="status"
        >
          {t.tom === "erro" ? (
            <AlertCircle size={16} className="flex-none text-toast-erro" aria-hidden="true" />
          ) : (
            <CheckCircle2 size={16} className="flex-none text-toast-ok" aria-hidden="true" />
          )}
          <span className="min-w-0 flex-1">{t.texto}</span>
          {t.desfazer && (
            <button
              type="button"
              onClick={() => {
                t.desfazer?.();
                fecharToast(t.id);
              }}
              className="inline-flex items-center gap-1 text-[12.5px] font-semibold text-sinal"
            >
              <Undo2 size={13} aria-hidden="true" />
              Desfazer
            </button>
          )}
          <button type="button" onClick={() => fecharToast(t.id)} aria-label="Fechar aviso" className="text-toast-fechar">
            <X size={14} />
          </button>
        </div>
      ))}
    </div>
  );
}
