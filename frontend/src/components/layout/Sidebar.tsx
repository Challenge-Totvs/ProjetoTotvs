/* Barra lateral: Nova transcrição (vendedor), itens do perfil e Configurações na base. */

import { Building2, CalendarClock, Home, Layers, Plus, Settings, TrendingUp, Users, Wallet, type LucideIcon } from "lucide-react";
import { useLocation, useNavigate } from "react-router-dom";
import { useApp } from "../../context/AppContext";
import { cx } from "../../lib/formato";
import { rotas } from "../../lib/rotas";
import { Logo, LogoIcone } from "../ui/base";
import { btn } from "../ui/classes";

interface ItemNav {
  k: string;
  l: string;
  Icone: LucideIcon;
  para: string;
  g?: string;
}

const NAV: Record<"vendedor" | "gestor", { topo: ItemNav[]; base: ItemNav[] }> = {
  vendedor: {
    topo: [
      { k: "inicio", l: "Início", Icone: Home, para: rotas.inicio, g: "I" },
      { k: "reunioes", l: "Reuniões", Icone: CalendarClock, para: rotas.reunioesLista, g: "R" },
      { k: "clientes", l: "Clientes", Icone: Building2, para: rotas.clientes, g: "C" },
      { k: "desempenho", l: "Desempenho", Icone: TrendingUp, para: rotas.desempenho, g: "D" },
    ],
    base: [{ k: "configuracoes", l: "Configurações", Icone: Settings, para: rotas.configuracoes }],
  },
  gestor: {
    topo: [
      { k: "clientes", l: "Clientes", Icone: Building2, para: rotas.clientes, g: "C" },
      { k: "reunioes", l: "Reuniões", Icone: CalendarClock, para: rotas.reunioesLista, g: "R" },
      { k: "padroes", l: "Padrões", Icone: Layers, para: rotas.padroes, g: "P" },
      { k: "vendedores", l: "Vendedores", Icone: Users, para: rotas.vendedores, g: "V" },
      { k: "desempenho", l: "Desempenho", Icone: TrendingUp, para: rotas.desempenho, g: "D" },
    ],
    base: [
      { k: "uso", l: "Uso e plano", Icone: Wallet, para: rotas.uso, g: "U" },
      { k: "configuracoes", l: "Configurações", Icone: Settings, para: rotas.configuracoes },
    ],
  },
};

export { NAV };

/** Seção da barra lateral que fica marcada para cada endereço. */
function secaoDaRota(caminho: string): string {
  if (caminho.startsWith("/inicio")) return "inicio";
  // A lista plana (sem id) marca "Reuniões"; a reunião em si (com id) marca "Clientes", de onde normalmente se chega a ela.
  if (caminho === rotas.reunioesLista) return "reunioes";
  if (caminho.startsWith("/clientes") || caminho.startsWith("/reunioes")) return "clientes";
  if (caminho.startsWith("/padroes")) return "padroes";
  if (caminho.startsWith("/vendedores")) return "vendedores";
  if (caminho.startsWith("/desempenho")) return "desempenho";
  if (caminho.startsWith("/uso")) return "uso";
  if (caminho.startsWith("/configuracoes")) return "configuracoes";
  if (caminho.startsWith("/transcricoes")) return "nova";
  return "";
}

const classeItem =
  "flex h-[38px] w-full items-center gap-2.5 rounded-lg px-3 text-left text-[13.5px] text-ardosia hover:bg-hover hover:text-ink aria-[current=page]:bg-sinal-fundo aria-[current=page]:font-medium aria-[current=page]:text-ink aria-[current=page]:shadow-[inset_3px_0_0_var(--color-sinal-texto)] ate-900:justify-center ate-900:px-0";

export function Sidebar() {
  const { usuario } = useApp();
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const nav = NAV[usuario.perfil];
  const secao = secaoDaRota(pathname);

  const Item = ({ it }: { it: ItemNav }) => (
    <button
      type="button"
      className={classeItem}
      aria-current={secao === it.k ? "page" : undefined}
      onClick={() => navigate(it.para)}
      title={it.g ? `${it.l} (G depois ${it.g})` : it.l}
    >
      <it.Icone size={17} aria-hidden="true" className="flex-none" />
      <span className="ate-900:hidden">{it.l}</span>
    </button>
  );

  return (
    <aside className="flex w-[232px] flex-none flex-col border-r border-linha bg-branco ate-900:w-16" aria-label="Navegação principal">
      <div className="flex h-14 flex-none items-center border-b border-linha px-[18px]">
        <span className="ate-900:hidden">
          <Logo tamanho={18} />
        </span>
        <span className="hidden ate-900:block">
          <LogoIcone tamanho={22} />
        </span>
      </div>
      <div className="flex min-h-0 flex-1 flex-col gap-1 p-3">
        {usuario.perfil === "vendedor" && (
          <button
            type="button"
            className={btn({
              primario: true,
              className: cx(
                "mb-2.5 h-9! w-full justify-center aria-[current=page]:shadow-[0_0_0_2px_var(--color-sinal-fundo)] ate-900:px-0",
              ),
            })}
            aria-current={secao === "nova" ? "page" : undefined}
            onClick={() => navigate(rotas.nova())}
            title="Nova transcrição"
          >
            <Plus size={16} aria-hidden="true" />
            <span className="ate-900:hidden">Nova transcrição</span>
          </button>
        )}
        <nav className="flex flex-col gap-0.5">
          {nav.topo.map((it) => (
            <Item key={it.k} it={it} />
          ))}
        </nav>
        <div className="mt-auto border-t border-linha pt-3">
          {nav.base.map((it) => (
            <Item key={it.k} it={it} />
          ))}
        </div>
      </div>
    </aside>
  );
}
