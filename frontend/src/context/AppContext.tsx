/* Estado comum das telas logadas: avisos (toasts), painel lateral, atalhos,
   trilha do topo, motores, janela e as ações do vendedor nos temas. */

import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode, type RefObject } from "react";
import * as compromissosApi from "../api/compromissos";
import * as configApi from "../api/configuracoes";
import { mensagemDeErro } from "../api/http";
import * as temasApi from "../api/temas";
import type { Compromisso, StatusMotor, Tema, TratadoForaRequest, Usuario } from "../types/api";
import { nomeAcaoFora, nomeCanal } from "../lib/dominio";

/* ---------- Tipos ---------- */

export interface Toast {
  id: string;
  texto: string;
  tom?: "erro";
  desfazer?: () => void;
}

/** Cadeia de motores: tudo normal, só a principal fora, ou as duas LLMs fora. */
export type EstadoMotores = "normal" | "llm1_fora" | "llms_fora";

export type ModalTema = { tipo: "fora" | "naoProcede" | "avisar"; tema: Tema };

/** Um item da trilha do topo. Com `para`, vira link. */
export interface ItemTrilha {
  l: string;
  para?: string;
}

/** Teclas da tela atual (j, k, Enter...) e a legenda do rodapé. */
export type Teclas = Record<string, (e: KeyboardEvent) => void>;
export type Legenda = [string[], string][];

interface AppData {
  usuario: Usuario;
  gestor: boolean;

  painelAberto: boolean;
  setPainelAberto: (v: boolean) => void;

  toast: (texto: string, opcoes?: { tom?: "erro"; desfazer?: () => void }) => void;
  toasts: Toast[];
  fecharToast: (id: string) => void;

  /** Muda depois de cada ação; as telas usam como dependência para recarregar. */
  versao: number;
  invalidar: () => void;

  janelaDias: number;
  setJanelaDias: (d: number) => void;
  statusMotores: StatusMotor[];
  estadoMotores: EstadoMotores;

  modal: ModalTema | null;
  abrirModal: (tipo: ModalTema["tipo"], tema: Tema) => void;
  fecharModal: () => void;

  acoes: {
    registrarFora: (tema: Tema, reg: TratadoForaRequest) => Promise<void>;
    removerFora: (tema: Tema) => Promise<void>;
    marcarNaoProcede: (tema: Tema, motivo: string | null) => Promise<void>;
    desfazerNaoProcede: (tema: Tema) => Promise<void>;
    avisarGestor: (tema: Tema, mensagem: string) => Promise<void>;
    marcarCompromisso: (cp: Compromisso, cumprido: boolean) => Promise<void>;
  };

  /* Atalhos e trilha (registrados pela tela atual) */
  teclasRef: RefObject<Teclas | null>;
  legenda: Legenda;
  registrarAtalhos: (teclas: Teclas | null, legenda: Legenda | null) => void;
  trilha: ItemTrilha[];
  setTrilha: (t: ItemTrilha[]) => void;
}

const AppContext = createContext<AppData | null>(null);

export function AppProvider({ usuario, children }: { usuario: Usuario; children: ReactNode }) {
  const gestor = usuario.perfil === "gestor";
  // Painel lateral: aberto por padrão no vendedor, recolhido no gestor.
  const [painelAberto, setPainelAberto] = useState(!gestor);
  const [toasts, setToasts] = useState<Toast[]>([]);
  const [versao, setVersao] = useState(0);
  const [janelaDias, setJanelaDias] = useState(30);
  const [statusMotores, setStatusMotores] = useState<StatusMotor[]>([]);
  const [modal, setModal] = useState<ModalTema | null>(null);
  const [legenda, setLegenda] = useState<Legenda>([]);
  const [trilha, setTrilhaState] = useState<ItemTrilha[]>([]);
  const teclasRef = useRef<Teclas | null>(null);

  const invalidar = useCallback(() => setVersao((v) => v + 1), []);

  const fecharToast = useCallback((id: string) => setToasts((l) => l.filter((t) => t.id !== id)), []);

  const toast = useCallback((texto: string, opcoes: { tom?: "erro"; desfazer?: () => void } = {}) => {
    const id = `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
    // No máximo três avisos de cada vez.
    setToasts((l) => [...l.slice(-2), { id, texto, ...opcoes }]);
    setTimeout(() => setToasts((l) => l.filter((t) => t.id !== id)), opcoes.desfazer ? 7000 : 4500);
  }, []);

  // Janela de acompanhamento e estado dos motores (banner de contingência).
  useEffect(() => {
    configApi
      .buscarConfiguracoes()
      .then((c) => setJanelaDias(c.janelaDias))
      .catch(() => undefined);
  }, [versao]);

  useEffect(() => {
    const buscar = () =>
      configApi
        .buscarStatusMotores()
        .then(setStatusMotores)
        .catch(() => undefined);
    void buscar();
    const timer = setInterval(buscar, 60000);
    return () => clearInterval(timer);
  }, []);

  const estadoMotores: EstadoMotores = useMemo(() => {
    const ok = (m: string) => statusMotores.find((s) => s.motor === m)?.ok !== false;
    if (!ok("llm1") && !ok("llm2")) return "llms_fora";
    if (!ok("llm1")) return "llm1_fora";
    return "normal";
  }, [statusMotores]);

  /** Roda uma ação no backend: em caso de erro mostra o aviso; sempre recarrega as telas. */
  const executar = useCallback(
    async (fn: () => Promise<unknown>) => {
      try {
        await fn();
        return true;
      } catch (e) {
        toast(mensagemDeErro(e), { tom: "erro" });
        return false;
      } finally {
        invalidar();
      }
    },
    [toast, invalidar],
  );

  const acoes = useMemo<AppData["acoes"]>(
    () => ({
      registrarFora: async (tema, reg) => {
        const ok = await executar(() => temasApi.registrarFora(tema.id, reg));
        if (!ok) return;
        setModal(null);
        toast(`Registrado: ${nomeAcaoFora(reg.acao).toLowerCase()}, por ${nomeCanal(reg.canal).toLowerCase()}. O tema passa a “Tratado fora da reunião”.`, {
          desfazer: () => void executar(() => temasApi.removerFora(tema.id)),
        });
      },
      removerFora: async (tema) => {
        const anterior = tema.registroFora;
        const ok = await executar(() => temasApi.removerFora(tema.id));
        if (!ok) return;
        toast("Registro fora da reunião removido.", {
          desfazer: anterior
            ? () =>
                void executar(() =>
                  temasApi.registrarFora(tema.id, {
                    acao: anterior.acao,
                    canal: anterior.canal,
                    data: anterior.data,
                    observacao: anterior.observacao ?? "",
                  }),
                )
            : undefined,
        });
      },
      marcarNaoProcede: async (tema, motivo) => {
        const ok = await executar(() => temasApi.marcarNaoProcede(tema.id, motivo));
        if (!ok) return;
        setModal(null);
        toast("Marcado como não procede. Vira contraexemplo para as próximas análises.", {
          desfazer: () => void executar(() => temasApi.desfazerNaoProcede(tema.id)),
        });
      },
      desfazerNaoProcede: async (tema) => {
        const ok = await executar(() => temasApi.desfazerNaoProcede(tema.id));
        if (ok) toast("O tema voltou ao resumo.");
      },
      avisarGestor: async (tema, mensagem) => {
        let avisoId: number | null = null;
        const ok = await executar(async () => {
          avisoId = (await temasApi.avisarGestor(tema.id, mensagem)).id;
        });
        if (!ok) return;
        setModal(null);
        toast(`${usuario.gestor ? usuario.gestor.nome : "A gestão"} recebeu o aviso.`, {
          desfazer: () => {
            if (avisoId != null) {
              const id = avisoId;
              void executar(() => temasApi.desfazerAviso(id));
            }
          },
        });
      },
      marcarCompromisso: async (cp, cumprido) => {
        const ok = await executar(() => compromissosApi.marcarCompromisso(cp.id, cumprido));
        if (ok && cumprido)
          toast("Compromisso marcado como cumprido.", {
            desfazer: () => void executar(() => compromissosApi.marcarCompromisso(cp.id, false)),
          });
      },
    }),
    [executar, toast, usuario.gestor],
  );

  const registrarAtalhos = useCallback((teclas: Teclas | null, leg: Legenda | null) => {
    teclasRef.current = teclas;
    const proxima = leg || [];
    setLegenda((atual) => (JSON.stringify(atual) === JSON.stringify(proxima) ? atual : proxima));
  }, []);

  const setTrilha = useCallback((t: ItemTrilha[]) => {
    setTrilhaState((atual) => (JSON.stringify(atual) === JSON.stringify(t) ? atual : t));
  }, []);

  const valor: AppData = {
    usuario,
    gestor,
    painelAberto,
    setPainelAberto,
    toast,
    toasts,
    fecharToast,
    versao,
    invalidar,
    janelaDias,
    setJanelaDias,
    statusMotores,
    estadoMotores,
    modal,
    abrirModal: (tipo, tema) => setModal({ tipo, tema }),
    fecharModal: () => setModal(null),
    acoes,
    teclasRef,
    legenda,
    registrarAtalhos,
    trilha,
    setTrilha,
  };

  return <AppContext.Provider value={valor}>{children}</AppContext.Provider>;
}

export function useApp() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error("useApp deve ser usado dentro de AppProvider");
  return ctx;
}

/**
 * Registra as teclas da tela (j, k, Enter, v, t, n, a...) e a legenda do rodapé.
 * As teclas são lidas na hora do toque, então podem usar o estado mais recente.
 */
export function useAtalhos(teclas: Teclas, legenda: Legenda) {
  const { registrarAtalhos } = useApp();
  useEffect(() => {
    registrarAtalhos(teclas, legenda);
  });
  useEffect(() => () => registrarAtalhos(null, null), [registrarAtalhos]);
}

/** Define a trilha do topo ("Clientes › Clínica Bem Viver"). */
export function useTrilha(itens: ItemTrilha[]) {
  const { setTrilha } = useApp();
  const chave = JSON.stringify(itens);
  useEffect(() => {
    setTrilha(JSON.parse(chave));
  }, [chave, setTrilha]);
}
