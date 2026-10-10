/* Clientes do vendedor: busca, filtro de tipo, ordenação, tabela e prévia no painel lateral. */

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Search } from "lucide-react";
import type { ClienteResumo } from "../../types/api";
import { useApp, useAtalhos } from "../../context/AppContext";
import { fmtDiaSemana, fmtHora, paraData } from "../../lib/datas";
import { cx, normalizar } from "../../lib/formato";
import { rotas } from "../../lib/rotas";
import { CabecalhoPagina, Segmentado, Vazio } from "../ui/base";
import { barraFerramentas, busca as classeBusca, card, comPainel, conteudo, select, tabela, td, th, tr } from "../ui/classes";
import { ChipsTemas, ChipTipoCliente } from "../ui/glifos";
import { BotaoPainel, PainelLateral } from "../ui/Sobrepostos";
import { CelulaCliente, CelulaUltimaReuniao, TdIndicadores, ThIndicadores } from "./Celulas";
import { PreviaCliente } from "./PreviaCliente";

type FiltroTipo = "todos" | "ativo" | "prospect" | "sem";
type Ordem = "atencao" | "recente" | "nome";

/** Momento da última reunião em milissegundos (0 quando não há). */
const quandoUltima = (c: ClienteResumo) => (c.ultimaReuniao ? paraData(c.ultimaReuniao.dataHora).getTime() : 0);

/** O cliente passa no filtro de tipo? ("sem" = cliente sem tipo definido) */
const doTipo = (c: ClienteResumo, t: FiltroTipo) => t === "todos" || (t === "sem" ? !c.tipo : c.tipo === t);

export function ClientesVendedor({ clientes: todos }: { clientes: ClienteResumo[] }) {
  const app = useApp();
  const navigate = useNavigate();
  const [busca, setBusca] = useState("");
  const [tipo, setTipo] = useState<FiltroTipo>("todos");
  const [ordem, setOrdem] = useState<Ordem>("atencao");
  const [selId, setSelId] = useState<number | null>(null);

  const contar = (t: FiltroTipo) => todos.filter((c) => doTipo(c, t)).length;

  // Filtra por tipo e pela busca (sem acento, em nome, contatos e segmento) e ordena.
  const termo = normalizar(busca.trim());
  const lista = todos
    .filter((c) => doTipo(c, tipo))
    .filter((c) => !termo || normalizar(`${c.nome} ${c.contatos.map((x) => x.nome).join(" ")} ${c.segmento}`).includes(termo))
    .sort((a, b) => {
      if (ordem === "nome") return a.nome.localeCompare(b.nome);
      if (ordem === "recente") return quandoUltima(b) - quandoUltima(a);
      return b.indicadores.atencao - a.indicadores.atencao || a.nome.localeCompare(b.nome);
    });

  // Sem seleção (ou se a selecionada saiu do filtro), a primeira linha fica selecionada.
  const selecionado = lista.find((c) => c.id === selId) || lista[0] || null;
  const idx = selecionado ? lista.indexOf(selecionado) : -1;
  // Com o painel aberto, a tabela perde as colunas Tipo e Próxima reunião.
  const compacto = app.painelAberto && !!selecionado;

  const abrir = (c: ClienteResumo) => navigate(rotas.cliente(c.id));

  useAtalhos(
    {
      j: () => lista[idx + 1] && setSelId(lista[idx + 1].id),
      k: () => idx > 0 && setSelId(lista[idx - 1].id),
      Enter: () => selecionado && abrir(selecionado),
    },
    [
      [["J", "K"], "mover"],
      [["Enter"], "abrir cliente"],
      [["]"], "painel"],
    ],
  );

  return (
    <>
      <CabecalhoPagina
        titulo="Clientes"
        texto={`Seus ${todos.length} clientes e os temas acompanhados em cada um.`}
        acoes={<BotaoPainel aberto={app.painelAberto} onClick={() => app.setPainelAberto(!app.painelAberto)} />}
      />
      <div className={comPainel}>
        <div className={conteudo}>
          {/* Busca, tipo de cliente e ordenação */}
          <div className={barraFerramentas}>
            {/* Campo com o recuo e a cor de placeholder padrão do navegador, e ícone que encolhe, como na demo */}
            <label className={cx(classeBusca, "[&_input]:px-0.5 [&_input]:py-px [&_input]:placeholder:text-[#757575]")}>
              <Search size={14} aria-hidden="true" className="text-faint" />
              <input value={busca} onChange={(e) => setBusca(e.target.value)} placeholder="Buscar cliente ou contato" aria-label="Buscar cliente ou contato" />
            </label>
            <Segmentado<FiltroTipo>
              rotulo="Tipo de cliente"
              valor={tipo}
              onChange={setTipo}
              opcoes={[
                ["todos", "Todos", todos.length],
                ["ativo", "Ativos", contar("ativo")],
                ["prospect", "Prospects", contar("prospect")],
                ["sem", "Sem tipo", contar("sem")],
              ]}
            />
            <label className="inline-flex items-center gap-1.5 text-[12.5px] text-ardosia">
              Ordenar
              <select className={select()} value={ordem} onChange={(e) => setOrdem(e.target.value as Ordem)}>
                <option value="atencao">Mais atenção</option>
                <option value="recente">Última reunião</option>
                <option value="nome">Nome</option>
              </select>
            </label>
          </div>

          {/* Tabela: clique seleciona, duplo clique abre o cliente */}
          <div className={cx(card, "overflow-x-auto")}>
            <table className={tabela}>
              <thead>
                <tr>
                  <th className={th}>Cliente</th>
                  {!compacto && <th className={th}>Tipo</th>}
                  <th className={th}>Última reunião</th>
                  <th className={th}>Temas em pauta</th>
                  <ThIndicadores compacto={compacto} />
                  {!compacto && <th className={th}>Próxima reunião</th>}
                </tr>
              </thead>
              <tbody>
                {lista.map((c) => {
                  const sel = selecionado?.id === c.id;
                  const contato = c.contatos[0] ? c.contatos[0].nome : "—";
                  const proxima = c.proximaReuniao ? paraData(c.proximaReuniao.dataHora) : null;
                  return (
                    <tr key={c.id} className={tr} aria-selected={sel} onClick={() => setSelId(c.id)} onDoubleClick={() => abrir(c)}>
                      <td className={td}>
                        <CelulaCliente c={c} sub={compacto ? contato : `${contato} · ${c.segmento}`} mostrarTipo={compacto} />
                      </td>
                      {!compacto && (
                        <td className={td}>
                          <ChipTipoCliente tipo={c.tipo} />
                        </td>
                      )}
                      <td className={td}>
                        <CelulaUltimaReuniao cliente={c} />
                      </td>
                      <td className={cx(td, compacto ? "max-w-[240px]" : "max-w-[320px]")}>
                        <ChipsTemas temas={c.temasEmPauta} max={compacto ? 2 : 3} />
                      </td>
                      <TdIndicadores ind={c.indicadores} />
                      {!compacto && (
                        <td className={cx(td, "text-[12.5px] whitespace-nowrap tabular-nums", proxima ? "text-ink" : "text-faint")}>
                          {proxima ? `${fmtDiaSemana(proxima)}, ${fmtHora(proxima)}` : "—"}
                        </td>
                      )}
                    </tr>
                  );
                })}
              </tbody>
            </table>
            {!lista.length && (
              // O ícone fica na linha de base do texto, como na demo (o Tailwind o centraliza).
              <div className="[&_svg]:align-baseline">
                <Vazio
                  titulo="Nenhum cliente neste filtro"
                  texto={todos.length ? "Mude o tipo ou a busca." : "Os clientes aparecem quando a primeira transcrição é enviada."}
                />
              </div>
            )}
          </div>
        </div>

        {/* Painel lateral com a prévia do cliente selecionado */}
        {app.painelAberto && selecionado && (
          <PainelLateral titulo="Cliente" onFechar={() => app.setPainelAberto(false)}>
            <PreviaCliente cliente={selecionado} />
          </PainelLateral>
        )}
      </div>
    </>
  );
}
