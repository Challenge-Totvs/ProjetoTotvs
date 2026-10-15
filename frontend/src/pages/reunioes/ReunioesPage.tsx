/* Lista plana de reuniões (atalho G depois R, nos dois perfis): vendedor vê as próprias,
   gestão vê as do time inteiro, com o vendedor dono de cada cliente. */

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { listarReunioes } from "../../api/reunioes";
import { CabecalhoPagina, Carregando, ErroCarregar, Etiqueta, Vazio } from "../../components/ui/base";
import { COR } from "../../components/ui/cores";
import { btn, card, direita, tabela, td, th, tr } from "../../components/ui/classes";
import { useApp, useTrilha } from "../../context/AppContext";
import { useApi } from "../../hooks/useApi";
import { fmtDiaSemana, fmtHora, paraData } from "../../lib/datas";
import { cx, plural } from "../../lib/formato";
import { rotas } from "../../lib/rotas";
import type { ReuniaoResumo } from "../../types/api";

const TAMANHO_PAGINA = 20;

export default function ReunioesPage() {
  const app = useApp();
  const navigate = useNavigate();
  useTrilha([{ l: "Reuniões" }]);
  const [pagina, setPagina] = useState(0);

  const { dados, erro, carregando, recarregar } = useApi(() => listarReunioes(pagina, TAMANHO_PAGINA), [pagina, app.versao]);

  if (carregando && !dados) return <Carregando />;
  if (!dados) return <ErroCarregar mensagem={erro ?? "Não foi possível carregar as reuniões."} onTentar={() => void recarregar()} />;

  const linhas = dados.content;

  return (
    <>
      <CabecalhoPagina
        titulo="Reuniões"
        texto={app.gestor ? `Todas as reuniões do time, ${plural(dados.totalElements, "no total", "no total")}.` : `Suas reuniões, ${plural(dados.totalElements, "no total", "no total")}.`}
      />
      <div className={cx(card, "overflow-x-auto")}>
        <table className={tabela}>
          <thead>
            <tr>
              <th className={th}>Data</th>
              <th className={th}>Cliente</th>
              <th className={th}>Reunião</th>
              {app.gestor && <th className={th}>Vendedor</th>}
              <th className={th}>Contato</th>
              <th className={cx(th, direita)}>Status</th>
            </tr>
          </thead>
          <tbody>
            {linhas.map((r: ReuniaoResumo) => {
              const data = paraData(r.dataHora);
              return (
                <tr key={r.id} className={tr} onClick={() => navigate(rotas.reuniao(r.id))}>
                  <td className={cx(td, "whitespace-nowrap tabular-nums")}>
                    {fmtDiaSemana(data)}, {fmtHora(data)}
                  </td>
                  <td className={td}>
                    <button
                      type="button"
                      className="font-medium text-ink hover:underline"
                      onClick={(e) => {
                        e.stopPropagation();
                        navigate(rotas.cliente(r.clienteId));
                      }}
                    >
                      {r.cliente}
                    </button>
                  </td>
                  <td className={td}>{r.titulo}</td>
                  {app.gestor && <td className={cx(td, "text-[12.5px] whitespace-nowrap")}>{r.vendedorNome ?? "—"}</td>}
                  <td className={cx(td, "text-[12.5px]")}>{r.contato ?? "—"}</td>
                  <td className={cx(td, direita)}>
                    {r.status === "analisada" && <Etiqueta cor={COR.resolvido}>Analisada</Etiqueta>}
                    {r.status === "agendada" && (
                      <Etiqueta cor={r.confirmada ? COR.resolvido : COR.atencaoBranco}>{r.confirmada ? "Agendada · confirmada" : "Agendada · a confirmar"}</Etiqueta>
                    )}
                    {r.status === "aguardando" && <Etiqueta cor={COR.atencaoBranco}>Aguardando transcrição</Etiqueta>}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
        {!linhas.length && <Vazio titulo="Nenhuma reunião ainda" texto="As reuniões aparecem aqui conforme são agendadas ou analisadas." />}
      </div>
      {dados.totalPages > 1 && (
        <div className="mt-3 flex items-center justify-end gap-2.5">
          <span className="text-[12.5px] text-ardosia tabular-nums">
            Página {dados.number + 1} de {dados.totalPages}
          </span>
          <button type="button" className={btn({ sm: true })} disabled={pagina === 0} onClick={() => setPagina((p) => p - 1)}>
            <ChevronLeft size={14} aria-hidden="true" />
            Anterior
          </button>
          <button type="button" className={btn({ sm: true })} disabled={dados.number + 1 >= dados.totalPages} onClick={() => setPagina((p) => p + 1)}>
            Próxima
            <ChevronRight size={14} aria-hidden="true" />
          </button>
        </div>
      )}
    </>
  );
}
