/* Nova transcrição (Figma 06): escolhe o cliente e a reunião, recebe o texto
   (colado ou .txt) e acompanha a análise até abrir a reunião analisada. */

import { useEffect, useMemo, useRef, useState, type FormEvent } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { FileText, Lock, Send, Upload } from "lucide-react";
import { buscarCliente, criarCliente, listarClientes } from "../../api/clientes";
import { infoErro, mensagemDeErro } from "../../api/http";
import { analisarTranscricao, criarReuniao, enviarTranscricao } from "../../api/reunioes";
import { Andamento } from "../../components/nova/Andamento";
import { etapasIniciais, FALHA_MOTOR, ROTULO_MOTOR, type Etapa, type EstadoEtapa } from "../../components/nova/etapas";
import { dataHoraLocalISO, esperar, lerArquivoTexto } from "../../components/nova/arquivo";
import { Aviso, Carregando, CabecalhoPagina, ErroCarregar, Secao, Segmentado } from "../../components/ui/base";
import { btn, campo, erroCampo, gridForm, input, link, opcional, select, textarea } from "../../components/ui/classes";
import { useApp, useAtalhos, useTrilha } from "../../context/AppContext";
import { useApi } from "../../hooks/useApi";
import { AMOSTRA_CLIENTE, AMOSTRA_REUNIAO, AMOSTRA_TEXTO } from "../../lib/amostra";
import { fmtData, hojeISO, paraData } from "../../lib/datas";
import { LIMITE_CARACTERES, lerTurnos, MOTORES, SEGMENTOS } from "../../lib/dominio";
import { cx, fmtNum, plural } from "../../lib/formato";
import { rotas } from "../../lib/rotas";
import type { Contato, Id, ResultadoAnalisarResponse } from "../../types/api";

/* ---------- Tipos do formulário ---------- */

type TipoNovo = "ativo" | "prospect" | "sem";

interface NovoCliente {
  nome: string;
  tipo: TipoNovo;
  segmento: string;
  contato: string;
  cargo: string;
}

interface NovaReuniao {
  data: string;
  hora: string;
  titulo: string;
  /** Id do contato escolhido, em texto ("" = o primeiro contato do cliente). */
  contatoId: string;
  duracao: string;
}

interface Erros {
  cliente?: string;
  novoNome?: string;
  novoContato?: string;
  reuniao?: string;
  titulo?: string;
  data?: string;
  texto?: string;
}

/** Andamento da análise: etapas e o relógio. */
interface Processo {
  etapas: Etapa[];
  inicio: number;
  agora: number;
}

/** Como escolher a reunião quando o cliente carregar: a pendente, ou a da amostra. */
type Sugestao = "padrao" | "amostra" | null;

/** Texto usado da última vez que a transcrição foi gravada, para não gravar duas vezes. */
interface Gravada {
  reuniaoId: Id;
  texto: string;
  transcricaoId: Id;
}

const NOVA_REUNIAO_VAZIA = (): NovaReuniao => ({ data: hojeISO(), hora: "10:00", titulo: "", contatoId: "", duracao: "" });

/** Contato da amostra (pelo nome) dentro da lista de contatos do cliente. */
function reuniaoDaAmostra(contatos: Contato[]): NovaReuniao {
  const contato = contatos.find((c) => c.nome === AMOSTRA_REUNIAO.contato);
  return {
    data: hojeISO(),
    hora: AMOSTRA_REUNIAO.hora,
    titulo: AMOSTRA_REUNIAO.titulo,
    contatoId: contato ? String(contato.id) : "",
    duracao: AMOSTRA_REUNIAO.duracao,
  };
}

/** A tela recomeça do zero quando os parâmetros da URL mudam (?cliente=&reuniao=). */
export default function NovaTranscricaoPage() {
  const [params] = useSearchParams();
  return <FormularioNova key={params.toString()} clienteInicial={params.get("cliente") ?? ""} reuniaoInicial={params.get("reuniao") ?? ""} />;
}

function FormularioNova({ clienteInicial, reuniaoInicial }: { clienteInicial: string; reuniaoInicial: string }) {
  const app = useApp();
  const navigate = useNavigate();
  useTrilha([{ l: "Nova transcrição" }]);
  useAtalhos({}, []);

  /* ---------- Estado do formulário ---------- */
  const [clienteId, setClienteId] = useState(clienteInicial);
  const [reuniaoId, setReuniaoId] = useState(reuniaoInicial);
  // Com cliente na URL e sem reunião, sugere a pendente quando o cliente carregar.
  const [sugestao, setSugestao] = useState<Sugestao>(clienteInicial && !reuniaoInicial ? "padrao" : null);
  const [novoCliente, setNovoCliente] = useState<NovoCliente>({ nome: "", tipo: "ativo", segmento: SEGMENTOS[0], contato: "", cargo: "" });
  const [novaReuniao, setNovaReuniao] = useState<NovaReuniao>(NOVA_REUNIAO_VAZIA);
  const [texto, setTexto] = useState("");
  const [arquivo, setArquivo] = useState<string | null>(null);
  const [erros, setErros] = useState<Erros>({});
  const [aviso, setAviso] = useState<{ texto: string; detalhe?: string } | null>(null);
  const [arrastando, setArrastando] = useState(false);
  const [proc, setProc] = useState<Processo | null>(null);
  const arquivoRef = useRef<HTMLInputElement>(null);
  const controle = useRef<AbortController | null>(null);
  const gravada = useRef<Gravada | null>(null);
  const montado = useRef(true);

  /* ---------- Dados ---------- */
  // Clientes do vendedor, em ordem alfabética.
  const lista = useApi(listarClientes, []);
  const meus = useMemo(() => [...(lista.dados ?? [])].sort((a, b) => a.nome.localeCompare(b.nome)), [lista.dados]);

  // Cliente escolhido completo (contatos e reuniões). "_novo" e "" não buscam nada.
  const idCliente = /^\d+$/.test(clienteId) ? Number(clienteId) : null;
  const detalhe = useApi(() => (idCliente ? buscarCliente(idCliente) : Promise.resolve(null)), [idCliente]);
  const clienteSel = detalhe.dados && detalhe.dados.id === idCliente ? detalhe.dados : null;

  // Reuniões que podem receber transcrição: aguardando, ou agendadas que já passaram. Mais recente primeiro.
  const reunioesDoCliente = useMemo(() => {
    if (!clienteSel) return [];
    const agora = new Date();
    return clienteSel.reunioes
      .filter((r) => r.status === "aguardando" || (r.status === "agendada" && paraData(r.dataHora) <= agora))
      .sort((a, b) => paraData(b.dataHora).getTime() - paraData(a.dataHora).getTime());
  }, [clienteSel]);

  // Quando o cliente escolhido carrega, sugere a reunião: a primeira aguardando, senão "Nova reunião…".
  // (Ajuste feito durante a renderização, o padrão do React para estado que depende de dados recém-chegados.)
  if (sugestao && clienteSel) {
    const pendente = reunioesDoCliente.find((r) => r.status === "aguardando");
    if (pendente) setReuniaoId(String(pendente.id));
    else {
      setReuniaoId("_nova");
      if (sugestao === "amostra") setNovaReuniao(reuniaoDaAmostra(clienteSel.contatos));
    }
    setSugestao(null);
  }

  // Cronômetro do andamento: atualiza a cada 250 ms enquanto a análise roda.
  const emAndamento = proc !== null;
  useEffect(() => {
    if (!emAndamento) return;
    const relogio = setInterval(() => setProc((p) => (p ? { ...p, agora: Date.now() } : p)), 250);
    return () => clearInterval(relogio);
  }, [emAndamento]);

  // Se a pessoa sair da tela, a análise continua; no fim só chega o aviso (sem trocar de tela).
  useEffect(() => {
    montado.current = true;
    return () => {
      montado.current = false;
    };
  }, []);

  // Contadores ao vivo: turnos e locutores lidos do texto.
  const turnosLidos = useMemo(() => lerTurnos(texto), [texto]);
  const locutores = new Set(turnosLidos.map((t) => t.loc)).size;

  /* ---------- Ações do formulário ---------- */

  function escolherCliente(v: string) {
    setClienteId(v);
    setErros((x) => ({ ...x, cliente: undefined }));
    setReuniaoId("");
    setNovaReuniao((s) => ({ ...s, contatoId: "" }));
    setSugestao(v && v !== "_novo" ? "padrao" : null);
  }

  // "Usar transcrição de exemplo": texto da amostra e o Hospital Santa Luzia, se ele existir.
  function usarExemplo() {
    const cliente = meus.find((c) => c.nome === AMOSTRA_CLIENTE);
    if (cliente) {
      setClienteId(String(cliente.id));
      setReuniaoId("");
      setSugestao("amostra");
    } else {
      // Sem o cliente da amostra: cadastra como novo, com a reunião da amostra.
      setClienteId("_novo");
      setNovoCliente({ nome: AMOSTRA_CLIENTE, tipo: "ativo", segmento: "Saúde", contato: AMOSTRA_REUNIAO.contato, cargo: "" });
      setReuniaoId("");
      setSugestao(null);
      setNovaReuniao(reuniaoDaAmostra([]));
    }
    setTexto(AMOSTRA_TEXTO);
    setArquivo(null);
    setErros({});
  }

  async function aoEscolherArquivo(f: File | null | undefined) {
    if (!f) return;
    if (!/\.txt$/i.test(f.name)) {
      setErros((e) => ({ ...e, texto: "Envie um arquivo .txt." }));
      return;
    }
    const conteudo = await lerArquivoTexto(f);
    setTexto(conteudo.slice(0, LIMITE_CARACTERES));
    setArquivo(f.name);
    setErros((e) => ({
      ...e,
      texto:
        conteudo.length > LIMITE_CARACTERES
          ? `O arquivo tem ${fmtNum(conteudo.length)} caracteres; foram mantidos os primeiros ${fmtNum(LIMITE_CARACTERES)}.`
          : undefined,
    }));
  }

  function validar(): Erros {
    const e: Erros = {};
    if (!clienteId) e.cliente = "Escolha o cliente.";
    if (clienteId === "_novo") {
      if (!novoCliente.nome.trim()) e.novoNome = "Informe o nome da empresa.";
      if (!novoCliente.contato.trim()) e.novoContato = "Informe o nome do contato.";
    }
    if (clienteId && !reuniaoId && clienteId !== "_novo") e.reuniao = "Escolha a reunião.";
    if (reuniaoId === "_nova" || clienteId === "_novo") {
      if (!novaReuniao.titulo.trim()) e.titulo = "Informe o assunto da reunião.";
      if (!novaReuniao.data || novaReuniao.data > hojeISO()) e.data = "A reunião precisa ter acontecido.";
    }
    if (!texto.trim()) e.texto = "Cole a transcrição ou envie um arquivo .txt.";
    else if (texto.length < 80) e.texto = "A transcrição está curta demais para uma análise.";
    return e;
  }

  /* ---------- Envio e análise ---------- */

  // Troca o estado de uma etapa do andamento.
  function marcar(id: string, estado: EstadoEtapa) {
    setProc((p) => (p ? { ...p, etapas: p.etapas.map((x) => (x.id === id ? { ...x, estado } : x)) } : p));
  }

  // Com a resposta em mãos: troca a etapa da LLM principal pelas tentativas reais da cadeia de motores.
  async function mostrarMotores(resp: ResultadoAnalisarResponse, parou: () => boolean) {
    const tentativas = resp.tentativas.length ? resp.tentativas : [{ motor: resp.motor, ok: true }];
    const motores: Etapa[] = tentativas.map((t, i) => ({
      id: `motor-${i}`,
      rotulo: ROTULO_MOTOR[t.motor],
      // A primeira já estava rodando: conclui na hora. As seguintes rodam uma de cada vez.
      estado: i === 0 ? (t.ok ? "ok" : "falhou") : "pendente",
      falha: t.ok ? undefined : FALHA_MOTOR[t.motor],
    }));
    setProc((p) => (p ? { ...p, etapas: p.etapas.flatMap((x) => (x.id === "llm1" ? motores : [x])) } : p));
    for (let i = 1; i < tentativas.length; i++) {
      await esperar(150);
      if (parou()) return;
      marcar(`motor-${i}`, "rodando");
      await esperar(500);
      if (parou()) return;
      marcar(`motor-${i}`, tentativas[i].ok ? "ok" : "falhou");
    }
  }

  async function enviar(ev: FormEvent) {
    ev.preventDefault();
    if (proc) return;
    const e = validar();
    setErros(e);
    if (Object.keys(e).length) return;
    setAviso(null);

    const ctrl = new AbortController();
    controle.current = ctrl;
    const parou = () => ctrl.signal.aborted;
    const inicio = Date.now();
    setProc({ etapas: etapasIniciais().map((x) => (x.id === "pseudo" ? { ...x, estado: "rodando" } : x)), inicio, agora: inicio });

    // A pseudonimização acontece dentro da chamada; na tela ela conclui em ~700 ms e a LLM principal começa.
    const pseudo = esperar(700).then(() => {
      if (parou()) return;
      marcar("pseudo", "ok");
      marcar("llm1", "rodando");
    });

    let fase: "cadastro" | "transcricao" | "analise" = "cadastro";
    try {
      // 1. Cliente novo, se foi o escolhido.
      let cid = idCliente;
      let contatos = clienteSel?.contatos ?? [];
      if (clienteId === "_novo") {
        const criado = await criarCliente({
          nome: novoCliente.nome.trim(),
          tipo: novoCliente.tipo === "sem" ? null : novoCliente.tipo,
          segmento: novoCliente.segmento,
          contato: { nome: novoCliente.contato.trim(), cargo: novoCliente.cargo.trim() || "Contato" },
        });
        cid = criado.id;
        contatos = criado.contatos;
        // O formulário passa a apontar para o cliente criado (se cancelar e reenviar, não duplica).
        setClienteId(String(criado.id));
        setReuniaoId("_nova");
        setSugestao(null);
        void lista.recarregar();
      }
      if (cid == null) throw new Error("Cliente não encontrado.");

      // 2. Reunião nova, se for o caso.
      let rid: Id;
      if (reuniaoId === "_nova" || clienteId === "_novo") {
        const contatoId = Number(novaReuniao.contatoId) || contatos[0]?.id || null;
        const criada = await criarReuniao({
          clienteId: cid,
          titulo: novaReuniao.titulo.trim(),
          dataHora: dataHoraLocalISO(novaReuniao.data, novaReuniao.hora),
          duracaoMin: Number(novaReuniao.duracao) || null,
          contatoId,
          status: "aguardando",
        });
        rid = criada.id;
        // Mesma ideia: a reunião criada fica selecionada no formulário.
        setReuniaoId(String(rid));
        void detalhe.recarregar();
      } else rid = Number(reuniaoId);
      if (parou()) return;

      // 3. Grava o texto (se este mesmo texto já foi gravado nesta reunião, reaproveita).
      fase = "transcricao";
      let transcricaoId: Id;
      const ja = gravada.current;
      if (ja && ja.reuniaoId === rid && ja.texto === texto) transcricaoId = ja.transcricaoId;
      else {
        const t = await enviarTranscricao(rid, { conteudo: texto, formatoOrigem: arquivo ? "ARQUIVO" : "COLADO", nomeArquivo: arquivo });
        transcricaoId = t.transcricaoId;
        gravada.current = { reuniaoId: rid, texto, transcricaoId };
      }
      if (parou()) return;

      // 4. Análise (síncrona). O "Cancelar análise" aborta esta chamada.
      fase = "analise";
      const resp = await analisarTranscricao(transcricaoId, ctrl.signal);
      await pseudo;
      if (parou()) return;

      // 5. Mostra a cadeia de motores e conclui as duas últimas etapas.
      await mostrarMotores(resp, parou);
      for (const id of ["verif", "temas"]) {
        await esperar(150);
        if (parou()) return;
        marcar(id, "rodando");
        await esperar(350);
        if (parou()) return;
        marcar(id, "ok");
      }
      await esperar(150);
      if (parou()) return;

      gravada.current = null;
      app.invalidar();
      if (montado.current) {
        setProc(null);
        navigate(rotas.reuniao(resp.reuniaoId));
      }
      app.toast(
        `Análise concluída por ${MOTORES[resp.motor].curto}: ${plural(resp.novos, "tema novo", "temas novos")}, ${plural(resp.atualizados, "tema atualizado", "temas atualizados")}${resp.compromissos ? `, ${plural(resp.compromissos, "compromisso", "compromissos")}` : ""}.`,
      );
    } catch (err) {
      // Cancelada pela pessoa: o "Cancelar análise" já cuidou da tela.
      if (parou()) return;
      const { status } = infoErro(err);
      setProc(null);
      if (status === 409 && fase === "transcricao") {
        // Transcrição repetida: a mensagem do backend vai no campo do texto.
        setErros({ texto: mensagemDeErro(err, "Esta transcrição já foi enviada.") });
      } else if (status === 503) {
        setAviso({
          texto: "O serviço de análise está fora do ar. A transcrição ficou gravada; tente analisar de novo em instantes.",
          detalhe: mensagemDeErro(err, "") || undefined,
        });
      } else {
        setAviso({ texto: mensagemDeErro(err) });
      }
      if (!montado.current) app.toast(mensagemDeErro(err), { tom: "erro" });
    }
  }

  function cancelar() {
    controle.current?.abort();
    setProc(null);
    app.toast("Análise cancelada. O texto continua no formulário.");
  }

  /* ---------- Tela de andamento ---------- */

  if (proc) return <Andamento etapas={proc.etapas} segundos={Math.floor((proc.agora - proc.inicio) / 1000)} onCancelar={cancelar} />;

  /* ---------- Formulário ---------- */

  if (lista.carregando && !lista.dados) return <Carregando />;
  if (!lista.dados) return <ErroCarregar mensagem={lista.erro ?? "Não foi possível carregar os clientes."} onTentar={() => void lista.recarregar()} />;

  return (
    <>
      <CabecalhoPagina
        titulo="Nova transcrição"
        texto="Envie a transcrição de uma reunião que já aconteceu. A análise atualiza os temas do cliente."
        acoes={
          <button type="button" className={btn()} onClick={usarExemplo}>
            <FileText size={15} aria-hidden="true" />
            Usar transcrição de exemplo
          </button>
        }
      />
      {!meus.length && (
        <div className="mb-4">
          <Aviso tom="info">Você ainda não tem clientes. Cadastre o primeiro aqui mesmo, escolhendo “Novo cliente”.</Aviso>
        </div>
      )}
      {aviso && (
        <div className="mb-4 max-w-[980px]">
          <Aviso tom="erro">
            {aviso.texto}
            {aviso.detalhe && <span className="mt-0.5 block text-xs">{aviso.detalhe}</span>}
          </Aviso>
        </div>
      )}
      <form onSubmit={enviar} noValidate className="grid max-w-[980px] gap-4">
        <Secao id="nova-cliente" titulo="1. Cliente e reunião">
          <div className={gridForm}>
            <label className={campo}>
              Cliente
              <select className={select(true)} value={clienteId} onChange={(e) => escolherCliente(e.target.value)} aria-invalid={erros.cliente ? "true" : "false"}>
                <option value="">Escolha o cliente</option>
                {meus.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.nome}
                  </option>
                ))}
                <option value="_novo">Novo cliente…</option>
              </select>
              {erros.cliente && <span className={erroCampo}>{erros.cliente}</span>}
            </label>
            {clienteId && clienteId !== "_novo" && (
              <label className={campo}>
                Reunião
                <select className={select(true)} value={reuniaoId} onChange={(e) => setReuniaoId(e.target.value)} aria-invalid={erros.reuniao ? "true" : "false"}>
                  <option value="">Escolha a reunião</option>
                  {reunioesDoCliente.map((r) => (
                    <option key={r.id} value={r.id}>{`${fmtData(paraData(r.dataHora))} — ${r.titulo}${r.status === "aguardando" ? " (sem transcrição)" : ""}`}</option>
                  ))}
                  <option value="_nova">Nova reunião…</option>
                </select>
                {erros.reuniao && <span className={erroCampo}>{erros.reuniao}</span>}
                {!erros.reuniao && detalhe.erro && !clienteSel && <span className={erroCampo}>{detalhe.erro}</span>}
              </label>
            )}
          </div>

          {clienteId === "_novo" && (
            <div className={cx(gridForm, "mt-3.5")}>
              <label className={campo}>
                Empresa
                <input
                  className={input}
                  value={novoCliente.nome}
                  onChange={(e) => setNovoCliente((s) => ({ ...s, nome: e.target.value }))}
                  placeholder="Nome da empresa"
                  aria-invalid={erros.novoNome ? "true" : "false"}
                />
                {erros.novoNome && <span className={erroCampo}>{erros.novoNome}</span>}
              </label>
              <label className={campo}>
                Segmento
                <select className={select(true)} value={novoCliente.segmento} onChange={(e) => setNovoCliente((s) => ({ ...s, segmento: e.target.value }))}>
                  {SEGMENTOS.map((s) => (
                    <option key={s}>{s}</option>
                  ))}
                </select>
              </label>
              <div className={campo}>
                Tipo
                <Segmentado<TipoNovo>
                  rotulo="Tipo do cliente"
                  valor={novoCliente.tipo}
                  onChange={(v) => setNovoCliente((s) => ({ ...s, tipo: v }))}
                  opcoes={[
                    ["ativo", "Ativo"],
                    ["prospect", "Prospect"],
                    ["sem", "Sem tipo"],
                  ]}
                />
              </div>
              <label className={campo}>
                Contato
                <input
                  className={input}
                  value={novoCliente.contato}
                  onChange={(e) => setNovoCliente((s) => ({ ...s, contato: e.target.value }))}
                  placeholder="Nome da pessoa"
                  aria-invalid={erros.novoContato ? "true" : "false"}
                />
                {erros.novoContato && <span className={erroCampo}>{erros.novoContato}</span>}
              </label>
              <label className={campo}>
                Cargo do contato <span className={opcional}>opcional</span>
                <input className={input} value={novoCliente.cargo} onChange={(e) => setNovoCliente((s) => ({ ...s, cargo: e.target.value }))} placeholder="Ex.: gerente financeiro" />
              </label>
            </div>
          )}

          {(reuniaoId === "_nova" || clienteId === "_novo") && (
            <div className={cx(gridForm, "mt-3.5")}>
              <label className={campo}>
                Assunto da reunião
                <input
                  className={input}
                  value={novaReuniao.titulo}
                  onChange={(e) => setNovaReuniao((s) => ({ ...s, titulo: e.target.value }))}
                  placeholder="Ex.: Apresentação de proposta"
                  aria-invalid={erros.titulo ? "true" : "false"}
                />
                {erros.titulo && <span className={erroCampo}>{erros.titulo}</span>}
              </label>
              <div className="grid grid-cols-[1fr_110px_110px] gap-2.5">
                <label className={campo}>
                  Data
                  <input
                    type="date"
                    className={input}
                    value={novaReuniao.data}
                    max={hojeISO()}
                    onChange={(e) => setNovaReuniao((s) => ({ ...s, data: e.target.value }))}
                    aria-invalid={erros.data ? "true" : "false"}
                  />
                  {erros.data && <span className={erroCampo}>{erros.data}</span>}
                </label>
                <label className={campo}>
                  Hora
                  <input type="time" className={input} value={novaReuniao.hora} onChange={(e) => setNovaReuniao((s) => ({ ...s, hora: e.target.value }))} />
                </label>
                <label className={campo}>
                  Duração <span className={opcional}>min</span>
                  <input
                    type="number"
                    min="1"
                    className={input}
                    value={novaReuniao.duracao}
                    onChange={(e) => setNovaReuniao((s) => ({ ...s, duracao: e.target.value }))}
                    placeholder="45"
                  />
                </label>
              </div>
              {clienteSel && (
                <label className={campo}>
                  Contato
                  <select className={select(true)} value={novaReuniao.contatoId} onChange={(e) => setNovaReuniao((s) => ({ ...s, contatoId: e.target.value }))}>
                    {clienteSel.contatos.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.nome}
                      </option>
                    ))}
                  </select>
                </label>
              )}
            </div>
          )}
        </Secao>

        <Secao
          id="nova-texto"
          titulo="2. Transcrição"
          sub="Formato do dataset: uma fala por linha, começando com [LOCUTOR n]. O papel de cada locutor é inferido na análise."
        >
          {/* Área de soltar o arquivo .txt (ou escolher pelo botão). */}
          <div
            className="flex flex-wrap items-center justify-center gap-2 rounded-[10px] border border-dashed border-linha-forte bg-nevoa p-5 text-center data-arrastando:border-sinal-texto data-arrastando:bg-sinal-fundo"
            data-arrastando={arrastando ? "1" : undefined}
            onDragOver={(e) => {
              e.preventDefault();
              setArrastando(true);
            }}
            onDragLeave={() => setArrastando(false)}
            onDrop={(e) => {
              e.preventDefault();
              setArrastando(false);
              void aoEscolherArquivo(e.dataTransfer.files?.[0]);
            }}
          >
            <Upload size={18} aria-hidden="true" className="text-ardosia" />
            <span className="text-[13.5px] text-ink">Arraste o arquivo .txt aqui</span>
            <button type="button" className={cx(link, "text-[13px]")} onClick={() => arquivoRef.current?.click()}>
              ou escolha do computador
            </button>
            <input
              ref={arquivoRef}
              type="file"
              accept=".txt,text/plain"
              hidden
              onChange={(e) => {
                void aoEscolherArquivo(e.target.files?.[0]);
                e.target.value = "";
              }}
            />
          </div>
          <label className={cx(campo, "mt-3.5")}>
            Ou cole a transcrição
            <textarea
              className={cx(textarea, "font-mono text-[12.5px]!")}
              rows={10}
              value={texto}
              onChange={(e) => {
                setTexto(e.target.value.slice(0, LIMITE_CARACTERES));
                if (!e.target.value) setArquivo(null);
                setErros((x) => ({ ...x, texto: undefined }));
              }}
              placeholder={"[LOCUTOR 1]: Bom dia, obrigado pelo tempo de vocês.\n[LOCUTOR 2]: Bom dia. Vamos lá."}
              aria-invalid={erros.texto ? "true" : "false"}
            />
          </label>
          <div className="mt-1.5 flex flex-wrap gap-x-3.5 gap-y-1 text-xs text-ardosia tabular-nums">
            <span>
              {fmtNum(texto.length)} de {fmtNum(LIMITE_CARACTERES)} caracteres
            </span>
            {texto.trim() && (
              <span>
                {plural(turnosLidos.length, "turno", "turnos")} · {plural(locutores, "locutor", "locutores")}
              </span>
            )}
            {texto.trim() && !turnosLidos.length && <span className="text-atencao">Sem marcações [LOCUTOR n]: a análise segue, mas sem métricas por locutor.</span>}
          </div>
          {erros.texto && <div className={cx(erroCampo, "mt-1.5")}>{erros.texto}</div>}
          <p className="mt-2.5 mb-0 flex gap-1.5 text-xs leading-normal text-faint">
            <Lock size={12} aria-hidden="true" className="mt-[3px] flex-none" />
            Antes de ir para a LLM, nomes de pessoas, empresas e lugares viram pseudônimos.
          </p>
        </Secao>

        <div className="flex justify-end gap-2">
          <button type="button" className={btn()} onClick={() => navigate(rotas.inicio)}>
            Cancelar
          </button>
          <button type="submit" className={btn({ primario: true })}>
            <Send size={15} aria-hidden="true" />
            Enviar e analisar
          </button>
        </div>
      </form>
    </>
  );
}
