/* Uso e plano (gestão, atalho G depois U): consumo de análises do time no ciclo, quanto
   custa e se a IA está ajudando no dia a dia — como na demo.

   DADOS DE EXEMPLO: o backend ainda não registra tokens, ciclo, franquia nem plano
   (não há nenhum desses campos no contrato nem na base hoje), então esta tela usa números
   fixos só para mostrar o formato. A própria demo trata preço e franquia como "valores de
   exemplo para discutir" — nada aqui é cobrança real. Assim que o analise-service passar a
   registrar tokens por análise (e o Java a persistir por ciclo), estes números viram reais. */

import { Aviso, CabecalhoPagina, Numero, Secao } from "../../components/ui/base";
import { btn, card, direita, numeros, tabela, td, th, tr } from "../../components/ui/classes";
import { useApp } from "../../context/AppContext";
import { cx, pct } from "../../lib/formato";

/** Exemplo fixo: um ciclo de 30 dias, franquia de 400 análises, 15 mil tokens por análise. */
const CICLO_EXEMPLO = {
  franquia: 400,
  usadas: 263,
  precoPacote: 49.9,
  porPacote: 100,
  diasRestantes: 12,
};

const USO_POR_VENDEDOR_EXEMPLO: [string, number][] = [
  ["Kelwin Bastos", 71],
  ["João Basta", 58],
  ["Luiz Balbino", 52],
  ["Vitor Mantovani", 44],
  ["Bruno Scuciato", 38],
];

export default function UsoPlanoPage() {
  const app = useApp();
  const c = CICLO_EXEMPLO;
  const pctUsado = c.usadas / c.franquia;
  const tetoAtingido = pctUsado >= 1;

  return (
    <>
      <CabecalhoPagina
        titulo="Uso e plano"
        texto="O consumo de análises do time no ciclo, quanto custa e se a IA está ajudando no dia a dia."
      />
      <div className="mb-4">
        <Aviso tom="info">
          Números de exemplo: o backend ainda não conta tokens nem guarda ciclo ou franquia. Esta tela mostra o formato pensado para a demo; os valores de
          preço e franquia são ilustrativos, a validar com o time.
        </Aviso>
      </div>

      <Secao
        titulo="Uso da IA neste ciclo"
        sub={`Ciclo de 30 dias · ${c.diasRestantes} dias restantes.`}
        acao={
          <span className="flex gap-2">
            <button type="button" className={btn({ sm: true })} disabled>
              Contratar pacote
            </button>
            <button type="button" className={btn({ sm: true })} disabled>
              Mudar de plano
            </button>
          </span>
        }
      >
        <div className={numeros()}>
          <Numero rotulo="Análises usadas" valor={`${c.usadas} de ${c.franquia}`} sub={pct(pctUsado)} tom={tetoAtingido ? "critico" : pctUsado > 0.8 ? "atencao" : undefined} />
          <Numero rotulo="Franquia do plano" valor={c.franquia} sub="análises por ciclo" />
          <Numero rotulo="Pacote extra" valor={`R$ ${c.precoPacote.toFixed(2)}`} sub={`a cada ${c.porPacote} análises`} />
          <Numero rotulo="Regra de conversão" valor="1 análise" sub="= 1 reunião de até 15 mil tokens de transcrição (~55 mil caracteres)" />
        </div>
        {tetoAtingido && (
          <div className="mt-3">
            <Aviso tom="atencao">
              O teto de gasto do ciclo foi atingido. Novas análises ficam pausadas até contratar um pacote extra ou ajustar o teto.
            </Aviso>
          </div>
        )}
      </Secao>

      <div className="mt-4">
        <Secao titulo="Uso por vendedor" sub="Análises consumidas no ciclo, por pessoa do time." semPadding>
          <div className={cx(card, "overflow-x-auto")}>
            <table className={tabela}>
              <thead>
                <tr>
                  <th className={th}>Vendedor</th>
                  <th className={cx(th, direita)}>Análises no ciclo</th>
                  <th className={cx(th, direita)}>% da franquia</th>
                </tr>
              </thead>
              <tbody>
                {USO_POR_VENDEDOR_EXEMPLO.map(([nome, n]) => (
                  <tr key={nome} className={tr}>
                    <td className={td}>{nome}</td>
                    <td className={cx(td, direita, "tabular-nums")}>{n}</td>
                    <td className={cx(td, direita, "tabular-nums")}>{pct(n / c.franquia)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Secao>
      </div>

      <p className="mx-0.5 mt-2.5 mb-0 text-xs leading-[1.5] text-faint">
        Time {app.usuario.time}. "A IA está ajudando?" (comparação de engajamento e taxa de resposta entre quem usa a IA e quem não usa) entra aqui quando
        houver uma base de reuniões sem análise grande o bastante para comparar — ainda não é o caso no corpus do Challenge.
      </p>
    </>
  );
}
