/* Login (Figma 01, com as sete melhorias do handoff 6.1). */

import { useEffect, useRef, useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { Aviso } from "../../components/ui/base";
import { link } from "../../components/ui/classes";
import { SESSAO_EXPIRADA_KEY } from "../../api/http";
import { useAuth } from "../../context/AuthContext";
import { EMAIL_RE } from "../../lib/dominio";
import { inicialDoPerfil, rotas } from "../../lib/rotas";
import { BotaoEnviar } from "./BotaoEnviar";
import { CampoAcesso } from "./CampoAcesso";
import { LayoutAcesso } from "./LayoutAcesso";

interface Erros {
  email?: string;
  senha?: string;
  geral?: string;
}

export default function LoginPage() {
  const { entrar } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [erros, setErros] = useState<Erros>({});
  const [carregando, setCarregando] = useState(false);
  // Quando o token venceu, o login mostra o aviso de sessão expirada uma vez.
  const [aviso] = useState<string | null>(() =>
    sessionStorage.getItem(SESSAO_EXPIRADA_KEY) ? "Sua sessão expirou. Entre de novo para continuar." : null,
  );
  const emailRef = useRef<HTMLInputElement>(null);
  const senhaRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    sessionStorage.removeItem(SESSAO_EXPIRADA_KEY);
  }, []);

  async function enviar(e: FormEvent) {
    e.preventDefault();
    if (carregando) return;
    const errs: Erros = {};
    const em = email.trim().toLowerCase();
    if (!em) errs.email = "Informe o e-mail.";
    else if (!EMAIL_RE.test(em)) errs.email = "Confira o formato do e-mail.";
    if (!senha) errs.senha = "Informe a senha.";
    if (Object.keys(errs).length) {
      setErros(errs);
      (errs.email ? emailRef : senhaRef).current?.focus();
      return;
    }
    setErros({});
    setCarregando(true);
    try {
      const u = await entrar(em, senha);
      navigate(inicialDoPerfil(u.perfil), { replace: true });
    } catch {
      // Mensagem genérica: não revela se o e-mail existe.
      setErros({ geral: "E-mail ou senha incorretos. Confira os dados e tente de novo." });
      setSenha("");
      senhaRef.current?.focus();
    } finally {
      setCarregando(false);
    }
  }

  return (
    <LayoutAcesso
      titulo="Transforme conversas em oportunidades."
      texto="Centralize as transcrições das suas reuniões e descubra automaticamente os pontos de interesse, objeções e oportunidades de venda de cada cliente."
    >
      <form onSubmit={enviar} noValidate>
        <h1 className="m-0 text-[26px] font-semibold tracking-[-0.01em] text-ink">Entrar na sua conta</h1>
        <p className="mt-2 mb-0 text-sm text-ardosia">Acesse para consultar suas reuniões e análises.</p>
        <div className="mt-6 flex flex-col gap-[18px]">
          {aviso && <Aviso tom="info">{aviso}</Aviso>}
          {erros.geral && <Aviso tom="erro">{erros.geral}</Aviso>}
          <CampoAcesso
            id="login-email"
            label="E-mail"
            type="email"
            value={email}
            onChange={(v) => {
              setEmail(v);
              if (erros.email || erros.geral) setErros({});
            }}
            placeholder="seu.email@empresa.com"
            autoComplete="username"
            autoFocus
            inputRef={emailRef}
            erro={erros.email}
          />
          <CampoAcesso
            id="login-senha"
            label="Senha"
            senha
            value={senha}
            onChange={(v) => {
              setSenha(v);
              if (erros.senha) setErros((x) => ({ ...x, senha: undefined }));
            }}
            placeholder="Sua senha"
            autoComplete="current-password"
            inputRef={senhaRef}
            erro={erros.senha}
          />
          <BotaoEnviar carregando={carregando} rotulo="Entrar" rotuloCarregando="Entrando…" />
        </div>
        <p className="mt-5 mb-0 text-[13px] text-ardosia">
          Não tem conta?{" "}
          <button type="button" className={link} onClick={() => navigate(rotas.cadastro)}>
            Cadastre-se
          </button>
        </p>
      </form>
    </LayoutAcesso>
  );
}
