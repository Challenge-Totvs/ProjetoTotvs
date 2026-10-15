/* Desempenho (atalho G depois D, nos dois perfis): as métricas das reuniões na janela —
   do time (gestão, somando os vendedores de /api/vendedores) ou das próprias (vendedor,
   a mesma conta que o Início já mostra, aqui com a tabela por vendedor quando for gestão).
   Números das reuniões, nunca de vendas: valor vendido e fechamento dependem do CRM. */

import { buscarInicio } from "../../api/inicio";
import { listarVendedores } from "../../api/gestor";
import { Aviso, CabecalhoPagina, Carregando, ErroCarregar, Numero, Secao, Segmentado } from "../../components/ui/base";
import { BotaoRelatorio } from "../../components/ui/BotaoRelatorio";
import { card, direita, numeros, tabela, td, th, tr } from "../../components/ui/classes";
import { useApp, useTrilha } from "../../context/AppContext";
import { useApi } from "../../hooks/useApi";
import { useJanelaVisao } from "../../hooks/useJanelaVisao";
import { cx, pct } from "../../lib/formato";
import { relatorioDesempenhoTime, relatorioDesempenhoVendedor } from "../../lib/relatorioDocx";
import type { MetricasVendedor, VendedorResumo } from "../../types/api";

/** Visões de 30/60/90 dias: muda só o que a tela mostra, não a janela configurada do time. */
type JanelaVisao = "30" | "60" | "90";
const OPCOES_JANELA: [JanelaVisao, string][] = [
  ["30", "30 dias"],
  ["60", "60 dias"],
  ["90", "90 dias"],
];

function SeletorJanela({ janela, onChange }: { janela: number; onChange: (dias: number) => void }) {
  return (
    <Segmentado rotulo="Janela" opcoes={OPCOES_JANELA} valor={String(janela) as JanelaVisao} onChange={(v) => onChange(Number(v))} />
  );
}

/** Soma as métricas de todos os vendedores; taxas vêm ponderadas pelo denominador de cada uma. */
function somarTime(vendedores: VendedorResumo[]): MetricasVendedor {
  const s = vendedores.reduce(
    (acc, v) => {
      const m = v.metricas;
      acc.realizadas += m.realizadas;
      acc.analisadas += m.analisadas;
      acc.tratadosConversa += m.tratadosConversa;
      acc.comLeitura += m.comLeitura;
      acc.tratadosFora += m.tratadosFora;
      acc.oportIdentificadas += m.oportIdentificadas;
      acc.oportTratadas += m.oportTratadas;
      acc.riscosSemRetorno += m.riscosSemRetorno;
      acc.oportPerdidas += m.oportPerdidas;
      acc.compromissosVencidos += m.compromissosVencidos;
      acc.clientes += m.clientes;
      if (m.falaVendedor != null) {
        acc.somaFala += m.falaVendedor;
        acc.nFala += 1;
      }
      return acc;
    },
    { realizadas: 0, analisadas: 0, tratadosConversa: 0, comLeitura: 0, tratadosFora: 0, oportIdentificadas: 0, oportTratadas: 0, riscosSemRetorno: 0, oportPerdidas: 0, compromissosVencidos: 0, clientes: 0, somaFala: 0, nFala: 0 },
  );
  return {
    realizadas: s.realizadas,
    analisadas: s.analisadas,
    taxaConversa: s.comLeitura ? s.tratadosConversa / s.comLeitura : null,
    tratadosConversa: s.tratadosConversa,
    comLeitura: s.comLeitura,
    tratadosFora: s.tratadosFora,
    oportIdentificadas: s.oportIdentificadas,
    oportTratadas: s.oportTratadas,
    falaVendedor: s.nFala ? s.somaFala / s.nFala : null,
    riscosSemRetorno: s.riscosSemRetorno,
    oportPerdidas: s.oportPerdidas,
    compromissosVencidos: s.compromissosVencidos,
    clientes: s.clientes,
  };
}

export default function DesempenhoPage() {
  const app = useApp();
  useTrilha([{ l: "Desempenho" }]);
  return app.gestor ? <DesempenhoDoTime /> : <DesempenhoProprio />;
}

/* ---------- Vendedor: as próprias métricas (mesma conta do Início) ---------- */

function DesempenhoProprio() {
  const app = useApp();
  const [janela, setJanela] = useJanelaVisao(app.janelaDias);
  const { dados, erro, carregando, recarregar } = useApi(() => buscarInicio(janela), [app.versao, janela]);
  if (carregando && !dados) return <Carregando />;
  if (!dados) return <ErroCarregar mensagem={erro ?? "Não foi possível carregar o desempenho."} onTentar={() => void recarregar()} />;
  return (
    <>
      <CabecalhoPagina
        titulo="Desempenho"
        texto={`Suas reuniões nos últimos ${dados.janelaDias} dias.`}
        acoes={
          <>
            <SeletorJanela janela={janela} onChange={setJanela} />
            <BotaoRelatorio
              rotulo="Meu relatório (.docx)"
              gerar={() => relatorioDesempenhoVendedor(app.usuario.nome, dados.janelaDias, dados.desempenho)}
            />
          </>
        }
      />
      <BlocoMetricas m={dados.desempenho} janelaDias={dados.janelaDias} />
    </>
  );
}

/* ---------- Gestão: soma do time + tabela por vendedor ---------- */

function DesempenhoDoTime() {
  const app = useApp();
  const [janela, setJanela] = useJanelaVisao(app.janelaDias);
  const { dados, erro, carregando, recarregar } = useApi(() => listarVendedores(janela), [app.versao, janela]);
  if (carregando && !dados) return <Carregando />;
  if (!dados) return <ErroCarregar mensagem={erro ?? "Não foi possível carregar o desempenho do time."} onTentar={() => void recarregar()} />;

  const time = somarTime(dados);
  // Mais atenção primeiro: riscos sem retorno + oportunidades perdidas.
  const ordenados = [...dados].sort((a, b) => b.metricas.riscosSemRetorno + b.metricas.oportPerdidas - (a.metricas.riscosSemRetorno + a.metricas.oportPerdidas));

  return (
    <>
      <CabecalhoPagina
        titulo="Desempenho do time"
        texto={`O time ${app.usuario.time} nos últimos ${janela} dias.`}
        acoes={
          <>
            <SeletorJanela janela={janela} onChange={setJanela} />
            <BotaoRelatorio
              rotulo="Relatório do time (.docx)"
              gerar={() => relatorioDesempenhoTime(app.usuario.time, janela, time, ordenados)}
            />
          </>
        }
      />
      <div className="mb-4">
        <Aviso tom="neutro">
          Sem comparação com o período anterior por aqui ainda: o backend guarda a janela atual, não uma série para comparar. Os números abaixo são do
          período corrente.
        </Aviso>
      </div>
      <BlocoMetricas m={time} janelaDias={janela} />
      <div className="mt-4">
        <Secao titulo="Por vendedor" sub="Ordenado por quem pede mais atenção: riscos sem retorno + oportunidades perdidas." semPadding>
          <div className={cx(card, "overflow-x-auto")}>
            <table className={tabela}>
              <thead>
                <tr>
                  <th className={th}>Vendedor</th>
                  <th className={cx(th, direita)}>Clientes</th>
                  <th className={cx(th, direita)}>Reuniões</th>
                  <th className={cx(th, direita)}>Riscos sem retorno</th>
                  <th className={cx(th, direita)}>Oport. perdidas</th>
                  <th className={cx(th, direita)}>Tratados na conversa</th>
                  <th className={cx(th, direita)}>Compromissos vencidos</th>
                </tr>
              </thead>
              <tbody>
                {ordenados.map((v) => (
                  <tr key={v.id} className={tr}>
                    <td className={td}>{v.nome}</td>
                    <td className={cx(td, direita, "tabular-nums")}>{v.metricas.clientes}</td>
                    <td className={cx(td, direita, "tabular-nums")}>{v.metricas.realizadas}</td>
                    <td className={cx(td, direita, "tabular-nums", v.metricas.riscosSemRetorno ? "font-semibold text-critico" : "text-faint")}>{v.metricas.riscosSemRetorno}</td>
                    <td className={cx(td, direita, "tabular-nums", v.metricas.oportPerdidas ? "font-semibold text-atencao" : "text-faint")}>{v.metricas.oportPerdidas}</td>
                    <td className={cx(td, direita, "tabular-nums")}>{v.metricas.taxaConversa == null ? "—" : pct(v.metricas.taxaConversa)}</td>
                    <td className={cx(td, direita, "tabular-nums", v.metricas.compromissosVencidos ? "font-semibold text-critico" : "text-faint")}>{v.metricas.compromissosVencidos}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Secao>
      </div>
    </>
  );
}

/* ---------- Números em comum (próprio ou do time) ---------- */

function BlocoMetricas({ m, janelaDias }: { m: MetricasVendedor; janelaDias: number }) {
  return (
    <Secao sub={`Medidas das reuniões, não de vendas: valor vendido e taxa de fechamento dependem do CRM. Janela de ${janelaDias} dias.`}>
      <div className={numeros()}>
        <Numero rotulo="Reuniões realizadas" valor={m.realizadas} sub={`${m.analisadas} analisadas`} />
        <Numero
          rotulo="Temas tratados na própria conversa"
          valor={m.taxaConversa == null ? "—" : pct(m.taxaConversa)}
          sub={`${m.tratadosConversa} de ${m.comLeitura} temas citados`}
          tom={m.taxaConversa != null && m.taxaConversa < 0.5 ? "atencao" : undefined}
        />
        <Numero rotulo="Tratados fora da reunião" valor={m.tratadosFora} />
        <Numero rotulo="Oportunidades tratadas" valor={`${m.oportTratadas} de ${m.oportIdentificadas}`} sub="das citadas na janela" />
        <Numero rotulo="Fala do vendedor" valor={m.falaVendedor == null ? "—" : pct(m.falaVendedor)} sub="média, por palavras" />
        <Numero rotulo="Compromissos vencidos" valor={m.compromissosVencidos} tom={m.compromissosVencidos ? "critico" : undefined} />
      </div>
    </Secao>
  );
}
