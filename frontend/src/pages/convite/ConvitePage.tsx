/* Aceite de convite (rota pública /convite/:token): quem foi convidado define nome e senha e já entra.
   Trata também o convite inexistente, o expirado e o já aceito. */

import { useEffect, useRef, useState, type FormEvent } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { buscarConvite } from "../../api/convites";
import { infoErro, mensagemDeErro } from "../../api/http";
import { Aviso, Carregando } from "../../components/ui/base";
import { btn, link } from "../../components/ui/classes";
import { useAuth } from "../../context/AuthContext";
import { inicialDoPerfil, rotas } from "../../lib/rotas";
import type { ConviteDetalhe } from "../../types/api";
import { BotaoEnviar } from "../acesso/BotaoEnviar";
import { CampoAcesso } from "../acesso/CampoAcesso";
import { LayoutAcesso } from "../acesso/LayoutAcesso";

interface Erros {
  nome?: string;
  senha?: string;
  geral?: string;
}

/** Estado da busca do convite: carregando, achado, não existe ou falha de rede/servidor. */
type Busca = { fase: "carregando" } | { fase: "ok"; convite: ConviteDetalhe } | { fase: "inexistente" } | { fase: "falha"; mensagem: string };

const MSG_ACEITO = "Este convite já foi aceito. Entre com o e-mail e a senha que você definiu.";
const MSG_EXPIRADO = "Este convite expirou. Peça um novo convite a quem convidou você.";
const MSG_INEXISTENTE = "Este convite não existe ou o link está incompleto. Confira o endereço ou peça um novo convite a quem convidou você.";

export default function ConvitePage() {
  const { token = "" } = useParams();
  const { aceitarConvite } = useAuth();
  const navigate = useNavigate();
  const [busca, setBusca] = useState<Busca>({ fase: "carregando" });
  const [nome, setNome] = useState("");
  const [senha, setSenha] = useState("");
  const [erros, setErros] = useState<Erros>({});
  const [carregando, setCarregando] = useState(false);
  const nomeRef = useRef<HTMLInputElement>(null);
  const senhaRef = useRef<HTMLInputElement>(null);

  // Muda a cada "Tentar de novo" para buscar o convite outra vez.
  const [tentativa, setTentativa] = useState(0);

  /** Busca os dados do convite pelo token da URL. 404 vira "convite inexistente". */
  useEffect(() => {
    let vivo = true;
    buscarConvite(token)
      .then((convite) => vivo && setBusca({ fase: "ok", convite }))
      .catch((err: unknown) => {
        if (!vivo) return;
        if (infoErro(err).status === 404) setBusca({ fase: "inexistente" });
        else setBusca({ fase: "falha", mensagem: mensagemDeErro(err, "Não foi possível carregar o convite.") });
      });
    // Se o token mudar antes da resposta, a resposta antiga é ignorada.
    return () => {
      vivo = false;
    };
  }, [token, tentativa]);

  function tentarDeNovo() {
    setBusca({ fase: "carregando" });
    setTentativa((t) => t + 1);
  }

  const convite = busca.fase === "ok" ? busca.convite : null;
  // Perfil escrito na frase ("como gestor"/"como vendedor").
  const perfil = convite?.perfil === "gestor" ? "gestor" : "vendedor";

  /** Marca o convite como aceito/expirado na tela quando o backend recusa o aceite por isso. */
  function atualizarConvite(mudanca: Partial<ConviteDetalhe>) {
    setBusca((b) => (b.fase === "ok" ? { fase: "ok", convite: { ...b.convite, ...mudanca } } : b));
  }

  async function enviar(e: FormEvent) {
    e.preventDefault();
    if (carregando || !convite || convite.aceito || convite.expirado) return;
    const errs: Erros = {};
    if (!nome.trim()) errs.nome = "Informe seu nome.";
    if (senha.length < 8) errs.senha = "A senha precisa de pelo menos 8 caracteres.";
    if (Object.keys(errs).length) {
      setErros(errs);
      (errs.nome ? nomeRef : senhaRef).current?.focus();
      return;
    }
    setErros({});
    setCarregando(true);
    try {
      // Cria o acesso, grava a sessão e leva à tela inicial do perfil.
      const u = await aceitarConvite(token, nome.trim(), senha);
      navigate(inicialDoPerfil(u.perfil), { replace: true });
    } catch (err) {
      const { status, codigo } = infoErro(err);
      if (status === 409 || codigo === "convite_aceito") atualizarConvite({ aceito: true });
      else if (status === 410 || codigo === "convite_expirado") atualizarConvite({ expirado: true });
      else if (status === 404) setBusca({ fase: "inexistente" });
      else if (codigo === "senha_curta") {
        setErros({ senha: "A senha precisa de pelo menos 8 caracteres." });
        senhaRef.current?.focus();
      } else setErros({ geral: mensagemDeErro(err, "Não foi possível criar o acesso. Tente de novo.") });
    } finally {
      setCarregando(false);
    }
  }

  /** "Já tem conta? Entrar", no pé de todas as variações da tela. */
  const rodape = (
    <p className="mt-5 mb-0 text-[13px] text-ardosia">
      Já tem conta?{" "}
      <button type="button" className={link} onClick={() => navigate(rotas.login)}>
        Entrar
      </button>
    </p>
  );

  return (
    <LayoutAcesso titulo="Você foi convidado para o InsightCall." texto="Defina sua senha para entrar no time com o perfil indicado no convite.">
      {busca.fase === "carregando" && <Carregando texto="Carregando o convite…" />}

      {/* Convite inexistente ou falha ao buscar: só o aviso e o caminho para entrar. */}
      {(busca.fase === "inexistente" || busca.fase === "falha") && (
        <div>
          <h1 className="m-0 text-[26px] font-semibold tracking-[-0.01em] text-ink">Aceitar convite</h1>
          <div className="mt-6">
            {busca.fase === "inexistente" ? (
              <Aviso tom="erro">{MSG_INEXISTENTE}</Aviso>
            ) : (
              <Aviso
                tom="erro"
                acao={
                  <button type="button" className={btn({ sm: true })} onClick={tentarDeNovo}>
                    Tentar de novo
                  </button>
                }
              >
                {busca.mensagem}
              </Aviso>
            )}
          </div>
          {rodape}
        </div>
      )}

      {convite && (
        <form onSubmit={enviar} noValidate>
          <h1 className="m-0 text-[26px] font-semibold tracking-[-0.01em] text-ink">Aceitar convite</h1>
          <p className="mt-2 mb-0 text-sm leading-normal text-ardosia">
            {convite.convidadoPor} convidou você para entrar como {perfil} no time {convite.time}.
          </p>
          <div className="mt-6 flex flex-col gap-[18px]">
            {convite.aceito && <Aviso tom="info">{MSG_ACEITO}</Aviso>}
            {!convite.aceito && convite.expirado && <Aviso tom="atencao">{MSG_EXPIRADO}</Aviso>}
            {erros.geral && <Aviso tom="erro">{erros.geral}</Aviso>}
            <CampoAcesso id="conv-email" label="E-mail" value={convite.email} readOnly autoComplete="username" />
            {/* Convite expirado não aceita mais: some o formulário, fica só o e-mail. */}
            {!(convite.expirado && !convite.aceito) && (
              <>
                <CampoAcesso
                  id="conv-nome"
                  label="Nome completo"
                  value={nome}
                  onChange={(x) => {
                    setNome(x);
                    if (erros.nome) setErros((s) => ({ ...s, nome: undefined }));
                  }}
                  placeholder="Como você quer ser chamado"
                  autoComplete="name"
                  autoFocus
                  inputRef={nomeRef}
                  erro={erros.nome}
                />
                <CampoAcesso
                  id="conv-senha"
                  label="Senha"
                  senha
                  value={senha}
                  onChange={(x) => {
                    setSenha(x);
                    if (erros.senha) setErros((s) => ({ ...s, senha: undefined }));
                  }}
                  placeholder="Mínimo de 8 caracteres"
                  autoComplete="new-password"
                  inputRef={senhaRef}
                  erro={erros.senha}
                />
                <BotaoEnviar carregando={carregando} rotulo="Criar acesso" rotuloCarregando="Criando acesso…" />
              </>
            )}
          </div>
          {rodape}
        </form>
      )}
    </LayoutAcesso>
  );
}
