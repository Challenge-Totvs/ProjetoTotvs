/* Busca e navegação (Ctrl/⌘ K): ações, telas, clientes, temas em pauta e, no gestor, padrões. */

import { useEffect, useMemo, useRef, useState, type KeyboardEvent, type ReactNode } from "react";
import { useNavigate } from "react-router-dom";
import { Building2, LogOut, Plus, Search, Users, type LucideIcon } from "lucide-react";
import * as clientesApi from "../../api/clientes";
import * as gestorApi from "../../api/gestor";
import { useApp } from "../../context/AppContext";
import { PADROES, ROTULO_SITUACAO, rotuloTipoCliente, ultimaCitacao } from "../../lib/dominio";
import { normalizar } from "../../lib/formato";
import { rotas } from "../../lib/rotas";
import type { ClienteResumo, Situacao, Tema, VendedorResumo } from "../../types/api";
import { Kbd } from "../ui/base";
import { Glifo, GlifosTema } from "../ui/glifos";
import { NAV } from "./Sidebar";

interface ItemPaleta {
  id: string;
  l: string;
  sub?: string;
  busca?: string;
  Icone?: LucideIcon;
  glifo?: ReactNode;
  atalho?: string | null;
  acao: () => void;
}

interface GrupoPaleta {
  id: string;
  titulo: string;
  itens: ItemPaleta[];
  limite?: number;
}

/* Mesma ordem dos temas no mapa: atenção, tratados, fora de pauta, não procede; recorrentes antes. */
const GRUPO: Record<Situacao, number> = { sem_retorno: 0, oportunidade_perdida: 0, sem_leitura: 0, tratado_fora: 1, tratado_conversa: 1, fora_de_pauta: 2, nao_procede: 3 };
function compararTemas(a: Tema, b: Tema) {
  if (GRUPO[a.situacao] !== GRUPO[b.situacao]) return GRUPO[a.situacao] - GRUPO[b.situacao];
  if (a.recorrente !== b.recorrente) return a.recorrente ? -1 : 1;
  return b.ultimaAtividade.localeCompare(a.ultimaAtividade);
}

export function Paleta({ fechar, onSair }: { fechar: () => void; onSair: () => void }) {
  const app = useApp();
  const navigate = useNavigate();
  const [q, setQ] = useState("");
  const [i, setI] = useState(0);
  const [clientes, setClientes] = useState<ClienteResumo[]>([]);
  const [vendedores, setVendedores] = useState<VendedorResumo[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);
  const listaRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
    clientesApi
      .listarClientes()
      .then(setClientes)
      .catch(() => undefined);
    // O gestor também busca os vendedores do time, para o grupo "Vendedores".
    if (app.gestor)
      gestorApi
        .listarVendedores()
        .then(setVendedores)
        .catch(() => undefined);
  }, [app.gestor]);

  const ir = (para: string) => {
    fechar();
    navigate(para);
  };

  const grupos = useMemo<GrupoPaleta[]>(() => {
    const p = app.usuario.perfil;
    const navs = [...NAV[p].topo, ...NAV[p].base].map((it) => ({
      id: `nav-${it.k}`,
      l: `Ir para ${it.l}`,
      Icone: it.Icone,
      atalho: it.g ? `G ${it.g}` : null,
      acao: () => ir(it.para),
    }));
    const itensClientes = clientes.map((c) => ({
      id: `cli-${c.id}`,
      l: c.nome,
      sub: `${rotuloTipoCliente(c.tipo)} · ${c.segmento}`,
      busca: c.contatos.map((x) => x.nome).join(" "),
      Icone: Building2,
      acao: () => ir(rotas.cliente(c.id)),
    }));
    const temas = clientes
      .flatMap((c) => c.temasEmPauta)
      .filter((t) => t.emPauta)
      .sort(compararTemas)
      .map((t) => ({
        id: `tema-${t.id}`,
        l: t.titulo,
        sub: t.clienteNome,
        busca: `${t.padraoNome} ${ROTULO_SITUACAO[t.situacao]}`,
        glifo: <GlifosTema tipos={t.tipos} tratado={ultimaCitacao(t)?.tratado ?? null} />,
        acao: () => ir(rotas.cliente(t.clienteId, t.id)),
      }));
    const acoesP: ItemPaleta[] = [];
    if (p === "vendedor") acoesP.push({ id: "nova", l: "Nova transcrição", Icone: Plus, acao: () => ir(rotas.nova()) });
    acoesP.push({
      id: "sair",
      l: "Sair",
      Icone: LogOut,
      acao: () => {
        fechar();
        onSair();
      },
    });
    const lista: GrupoPaleta[] = [
      { id: "acoes", titulo: "Ações", itens: acoesP },
      { id: "telas", titulo: "Telas", itens: navs },
      { id: "clientes", titulo: "Clientes", itens: itensClientes, limite: 5 },
      { id: "temas", titulo: "Temas em pauta", itens: temas, limite: 4 },
    ];
    if (p === "gestor") {
      lista.push({
        id: "padroes",
        titulo: "Padrões",
        limite: 3,
        itens: Object.entries(PADROES).map(([k, v]) => ({
          id: `pad-${k}`,
          l: v.nome,
          sub: v.tipo === "risco" ? "Risco" : "Oportunidade",
          glifo: <Glifo tipo={v.tipo} />,
          acao: () => ir(rotas.padrao(k)),
        })),
      });
      lista.push({
        id: "vend",
        titulo: "Vendedores",
        limite: 3,
        itens: vendedores.map((v) => ({ id: `v-${v.id}`, l: `Visão de ${v.nome}`, Icone: Users, acao: () => ir(rotas.vendedor(v.id)) })),
      });
    }
    return lista;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [app.usuario.perfil, clientes, vendedores]);

  const filtrados = useMemo(() => {
    const termo = normalizar(q.trim());
    return grupos
      .map((g) => {
        const itens = g.itens.filter((c) => !termo || normalizar(`${c.l} ${c.busca || ""}`).includes(termo));
        return { ...g, itens: itens.slice(0, termo ? 8 : g.limite || 8) };
      })
      .filter((g) => g.itens.length);
  }, [grupos, q]);
  const plano = filtrados.flatMap((g) => g.itens);

  useEffect(() => setI(0), [q]);
  useEffect(() => {
    const el = listaRef.current?.querySelector("[aria-selected='true']");
    if (el && "scrollIntoView" in el) el.scrollIntoView({ block: "nearest" });
  }, [i]);

  function onKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setI((x) => Math.min(plano.length - 1, x + 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setI((x) => Math.max(0, x - 1));
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (plano[i]) plano[i].acao();
    } else if (e.key === "Escape") {
      e.preventDefault();
      fechar();
    }
  }

  let idx = -1;
  return (
    <div
      className="fixed inset-0 z-60 flex items-start justify-center bg-[rgba(0,34,51,.32)] p-4 pt-[12vh]"
      onMouseDown={(e) => e.target === e.currentTarget && fechar()}
    >
      <div role="dialog" aria-label="Buscar e navegar" className="w-[560px] max-w-full overflow-hidden rounded-xl border border-linha bg-branco shadow-[0_16px_40px_rgba(0,34,51,.22)]">
        <div className="flex h-[50px] items-center gap-2.5 border-b border-linha px-3.5">
          <Search size={16} className="text-ardosia" aria-hidden="true" />
          <input
            ref={inputRef}
            value={q}
            onChange={(e) => setQ(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder="Buscar cliente, tema, padrão ou tela"
            aria-label="Buscar cliente, tema, padrão ou tela"
            role="combobox"
            aria-expanded="true"
            aria-controls="ic-paleta-lista"
            className="flex-1 border-0 bg-transparent text-sm text-ink outline-none"
          />
          <Kbd>Esc</Kbd>
        </div>
        <div ref={listaRef} id="ic-paleta-lista" role="listbox" className="max-h-[56vh] overflow-y-auto p-1.5">
          {filtrados.map((g) => (
            <div key={g.id} role="group" aria-label={g.titulo}>
              <div className="px-2.5 pt-2 pb-1 text-[11px] font-semibold tracking-[0.04em] text-faint uppercase">{g.titulo}</div>
              {g.itens.map((c) => {
                idx += 1;
                const meu = idx;
                return (
                  <div
                    key={c.id}
                    role="option"
                    aria-selected={meu === i}
                    onMouseEnter={() => setI(meu)}
                    onClick={() => c.acao()}
                    className={`flex cursor-pointer items-center gap-2.5 rounded-md px-2.5 py-2 text-[13.5px] text-ink ${meu === i ? "bg-sinal-fundo" : "bg-transparent"}`}
                  >
                    {c.glifo ? c.glifo : c.Icone ? <c.Icone size={15} className="text-ardosia" aria-hidden="true" /> : null}
                    <span className="min-w-0 flex-1 truncate">{c.l}</span>
                    {c.sub && <span className="text-xs whitespace-nowrap text-faint">{c.sub}</span>}
                    {c.atalho && <Kbd>{c.atalho}</Kbd>}
                  </div>
                );
              })}
            </div>
          ))}
          {!plano.length && <div className="p-3.5 text-[13px] text-ardosia">Nada encontrado para “{q}”.</div>}
        </div>
      </div>
    </div>
  );
}
