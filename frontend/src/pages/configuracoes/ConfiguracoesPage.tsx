/* Configurações: sua conta, janela de acompanhamento, motores de análise,
   privacidade e (só gestor) convites para o time. */

import { useEffect, useState, type FormEvent } from "react";
import { Mail, UserPlus } from "lucide-react";
import { buscarConfiguracoes, definirJanela, previaJanela } from "../../api/configuracoes";
import { convidar, listarConvites } from "../../api/convites";
import { mensagemDeErro } from "../../api/http";
import { Aviso, CabecalhoPagina, Etiqueta, Secao } from "../../components/ui/base";
import { COR } from "../../components/ui/cores";
import { bloco, btn, erroCampo, input, num, rotuloMetrica, select } from "../../components/ui/classes";
import { useApp, useAtalhos, useTrilha } from "../../context/AppContext";
import { useApi } from "../../hooks/useApi";
import { paraData, relativo } from "../../lib/datas";
import { DOMINIOS_PESSOAIS, EMAIL_RE, JANELAS, pseudonimizar } from "../../lib/dominio";
import { cx, plural } from "../../lib/formato";
import type { Motor } from "../../types/api";

/** Cadeia de motores, na ordem em que são tentados. */
const MOTORES: [Motor, string, string][] = [
  ["llm1", "LLM principal", "Provedor definido no analise-service"],
  ["llm2", "LLM secundária", "Assume se a principal não responder"],
  ["local", "Modelo local", "Classificador treinado; sem resumo e sem papel do locutor"],
  ["regras", "Regras", "Último recurso da cadeia"],
];

const TEXTO_EXEMPLO = "Helena Prado, da Clínica Bem Viver, vai abrir a unidade de Jundiaí. O Kelwin manda o plano.";

// O exemplo não muda: calcula uma vez só.
const EXEMPLO_PSEUDONIMIZADO = pseudonimizar(TEXTO_EXEMPLO, [
  ["Helena Prado", "PESSOA"],
  ["Clínica Bem Viver", "EMPRESA"],
  ["Jundiaí", "LOCAL"],
  ["Kelwin", "PESSOA"],
]);

export default function ConfiguracoesPage() {
  const app = useApp();
  const u = app.usuario;
  useTrilha([{ l: "Configurações" }]);
  useAtalhos({}, []);

  return (
    <>
      <CabecalhoPagina
        titulo="Configurações"
        texto={app.gestor ? "Sua conta, a janela de acompanhamento do time, os motores de análise e os convites." : "Sua conta, a janela de acompanhamento e os motores de análise."}
      />
      <div className="grid max-w-[860px] gap-4">
        <Secao id="conta" titulo="Sua conta">
          <dl className="m-0 grid grid-cols-[160px_minmax(0,1fr)] gap-x-2.5 gap-y-1.5 text-[13px] [&_dd]:m-0 [&_dd]:text-ink [&_dt]:text-ardosia">
            <dt>Nome</dt>
            <dd>{u.nome}</dd>
            <dt>E-mail</dt>
            <dd>{u.email}</dd>
            <dt>Perfil</dt>
            <dd>{app.gestor ? "Gestor, por convite" : "Vendedor"}</dd>
            <dt>Time</dt>
            <dd>{u.time}</dd>
          </dl>
        </Secao>

        <Secao
          id="janela"
          titulo="Janela de acompanhamento dos temas"
          sub="Define quando um tema é recorrente, quando uma oportunidade sem tratamento vira perdida e quando um tema sai de pauta"
        >
          {app.gestor ? <JanelaGestor /> : <p className="m-0 text-[13.5px] text-ink">{app.janelaDias} dias, definida pela gestão do time.</p>}
        </Secao>

        <Secao id="motores" titulo="Motores de análise" sub="Cada análise segue a cadeia até um motor responder. A reunião fica marcada com o motor que respondeu.">
          <ol className="m-0 grid list-none gap-2 p-0">
            {MOTORES.map(([k, nome, desc], i) => {
              // Motor que não veio no status conta como ok.
              const ok = app.statusMotores.find((s) => s.motor === k)?.ok !== false;
              return (
                <li key={k} className="flex items-center gap-2.5 text-[13.5px]">
                  <span className={cx(num, "w-[18px] text-faint")}>{i + 1}</span>
                  <span aria-hidden="true" className={cx("h-2 w-2 flex-none rounded-full", ok ? "bg-resolvido" : "bg-critico")} />
                  <span className="min-w-[130px] font-medium">{nome}</span>
                  <span className={cx("text-[12.5px]", ok ? "text-ardosia" : "text-critico")}>{ok ? desc : "Sem resposta agora"}</span>
                </li>
              );
            })}
          </ol>
        </Secao>

        <Secao id="privacidade" titulo="Privacidade" sub="LGPD: nada de nome real chega a uma LLM externa">
          <p className="m-0 text-[13.5px] leading-[1.55]">
            Antes de qualquer chamada, pessoas, empresas e lugares viram pseudônimos estáveis e tipados: o mesmo nome vira sempre o mesmo pseudônimo, e o tipo se mantém. O
            texto original fica só no InsightCall.
          </p>
          <div className={cx(bloco, "mt-3 text-[13px] leading-[1.55]")}>
            {/* leading-[1.55]: o text-xs traz altura de linha própria; aqui herda a do bloco, como na demo. */}
            <div className={cx(rotuloMetrica, "leading-[1.55]")}>Exemplo</div>
            <div>{TEXTO_EXEMPLO}</div>
            <div className="mt-1 text-sinal-texto">{EXEMPLO_PSEUDONIMIZADO}</div>
          </div>
        </Secao>

        {app.gestor && <Convites />}
      </div>
    </>
  );
}

/* ---------- Janela (gestor): seletor, prévia, Aplicar e Desfazer ---------- */

function JanelaGestor() {
  const app = useApp();
  const atual = app.janelaDias;
  // Janelas aceitas pelo backend; a lista fixa serve de reserva enquanto carrega ou se falhar.
  const { dados: config } = useApi(buscarConfiguracoes, []);
  const janelas = config?.janelasPermitidas ?? JANELAS;

  // Valor escolhido no seletor. Quando a janela do time muda (Aplicar, Desfazer), volta a ela.
  const [escolhida, setEscolhida] = useState(atual);
  const [base, setBase] = useState(atual);
  if (base !== atual) {
    setBase(atual);
    setEscolhida(atual);
  }

  // Prévia: quantos temas mudam de situação com a janela escolhida (vem do backend).
  const [previa, setPrevia] = useState<{ dias: number; n: number } | null>(null);
  useEffect(() => {
    if (escolhida === atual) return;
    let valida = true;
    previaJanela(escolhida)
      .then((r) => {
        if (valida) setPrevia({ dias: escolhida, n: r.temasQueMudam });
      })
      .catch(() => undefined);
    // Se o valor mudar antes da resposta, ignora a resposta antiga.
    return () => {
      valida = false;
    };
  }, [escolhida, atual]);

  const [aplicando, setAplicando] = useState(false);

  /** Grava a janela no backend e atualiza o app inteiro. */
  async function gravar(dias: number) {
    const c = await definirJanela(dias);
    app.setJanelaDias(c.janelaDias);
    app.invalidar();
    return c.janelaDias;
  }

  async function aplicar() {
    if (aplicando) return;
    const antes = atual;
    setAplicando(true);
    try {
      const nova = await gravar(escolhida);
      // Desfazer volta à janela anterior pela API.
      app.toast(`Janela de acompanhamento: ${nova} dias.`, {
        desfazer: () => {
          gravar(antes).catch((e) => app.toast(mensagemDeErro(e), { tom: "erro" }));
        },
      });
    } catch (e) {
      app.toast(mensagemDeErro(e), { tom: "erro" });
    } finally {
      setAplicando(false);
    }
  }

  const mudou = escolhida !== atual;
  // Só mostra a prévia quando a resposta é da janela escolhida agora.
  const diff = previa && previa.dias === escolhida ? previa.n : null;

  return (
    <div className="grid gap-3">
      <div className="flex flex-wrap items-center gap-2.5">
        <label className="inline-flex items-center gap-2 text-[13.5px]">
          Janela
          <select className={select()} value={escolhida} onChange={(e) => setEscolhida(Number(e.target.value))} aria-label="Janela em dias">
            {janelas.map((j) => (
              <option key={j} value={j}>
                {j} dias
              </option>
            ))}
          </select>
        </label>
        <button type="button" className={btn({ primario: true })} disabled={!mudou || aplicando} onClick={() => void aplicar()}>
          Aplicar
        </button>
        {mudou && diff != null && (
          <span className="text-[12.5px] text-ardosia">
            {diff ? `${plural(diff, "tema muda", "temas mudam")} de situação com ${escolhida} dias.` : `Nenhum tema muda de situação com ${escolhida} dias.`}
          </span>
        )}
      </div>
      <ul className="m-0 list-disc pl-[18px] text-[13px] leading-[1.6] text-ink">
        <li>Recorrente: citado em duas ou mais reuniões dentro da janela</li>
        <li>Oportunidade perdida: sem tratamento na reunião nem nas seguintes, dentro da janela</li>
        <li>Fora de pauta: não aparece há mais tempo que a janela; vai para o histórico</li>
      </ul>
      <Aviso tom="neutro">
        O padrão de 30 dias foi medido no corpus do Challenge: nas reuniões de janeiro e do começo de fevereiro, 30 dias cobrem de 85% a 95% dos retornos do cliente que
        acontecem em até 45 a 60 dias.
      </Aviso>
    </div>
  );
}

/* ---------- Convites (gestor) ---------- */

function Convites() {
  const app = useApp();
  const { dados: convites, recarregar } = useApi(listarConvites, [app.versao]);
  const [email, setEmail] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  async function enviar(e: FormEvent) {
    e.preventDefault();
    if (enviando) return;
    const em = email.trim().toLowerCase();
    // Validação local, igual à demo: formato e domínio pessoal.
    if (!EMAIL_RE.test(em)) return setErro("Confira o formato do e-mail.");
    if (DOMINIOS_PESSOAIS.includes(em.split("@")[1])) return setErro("Use o e-mail da sua empresa. Domínios pessoais não ligam você a um time.");
    setErro(null);
    setEnviando(true);
    try {
      await convidar(em);
      setEmail("");
      app.toast(`Convite enviado para ${em}.`);
      await recarregar();
    } catch (err) {
      // 409 (já tem acesso ou convite) e 422 (domínio sem empresa) aparecem no campo.
      setErro(mensagemDeErro(err));
    } finally {
      setEnviando(false);
    }
  }

  return (
    <Secao id="convites" titulo="Convites para o time" sub="Quem se cadastra sozinho entra como vendedor pelo domínio do e-mail. Convite serve para quem ainda não tem conta.">
      <form onSubmit={(e) => void enviar(e)} className="flex flex-wrap items-start gap-2">
        <div className="min-w-60 flex-1">
          <input
            className={input}
            type="email"
            value={email}
            onChange={(e) => {
              setEmail(e.target.value);
              setErro(null);
            }}
            placeholder="nome@insightcall.com"
            aria-label="E-mail para convite"
            aria-invalid={erro ? "true" : "false"}
          />
          {erro && <div className={cx(erroCampo, "mt-1.5")}>{erro}</div>}
        </div>
        <button type="submit" className={btn({ primario: true, className: "h-11!" })} aria-busy={enviando}>
          <UserPlus size={15} aria-hidden="true" />
          Convidar como vendedor
        </button>
      </form>
      {convites && convites.length > 0 && (
        <ul className="mt-3 mb-0 grid list-none gap-1.5 p-0">
          {convites.map((c) => (
            <li key={c.email} className="flex items-center gap-2 text-[13px]">
              <Mail size={14} aria-hidden="true" className="text-ardosia" />
              {c.email}
              <Etiqueta cor={COR.atencaoBranco}>Pendente</Etiqueta>
              <span className="text-xs text-faint">{relativo(paraData(c.criadoEm))}</span>
            </li>
          ))}
        </ul>
      )}
      <p className="mt-2.5 mb-0 text-xs text-faint">O perfil de gestor só chega por convite da administração.</p>
    </Secao>
  );
}
