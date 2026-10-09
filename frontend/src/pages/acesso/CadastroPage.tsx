/* Cadastro pelo domínio do e-mail corporativo (Figma 02, handoff 6.1). */

import { useRef, useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { link } from "../../components/ui/classes";
import * as authApi from "../../api/auth";
import { infoErro, mensagemDeErro } from "../../api/http";
import { useAuth } from "../../context/AuthContext";
import { DOMINIOS_PESSOAIS, EMAIL_RE } from "../../lib/dominio";
import { inicialDoPerfil, rotas } from "../../lib/rotas";
import { BotaoEnviar } from "./BotaoEnviar";
import { CampoAcesso } from "./CampoAcesso";
import { LayoutAcesso } from "./LayoutAcesso";

interface Erros {
  nome?: string;
  email?: string;
  senha?: string;
}

const MSG_PESSOAL = "Use o e-mail da sua empresa. Domínios pessoais não ligam você a um time.";
const MSG_SEM_ORG = "Este domínio não está ligado a nenhuma empresa no InsightCall. Peça um convite ao seu gestor.";
const DICA_PADRAO = "O domínio do e-mail liga você ao time da sua empresa.";

export default function CadastroPage() {
  const { cadastrar } = useAuth();
  const navigate = useNavigate();
  const [nome, setNome] = useState("");
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [erros, setErros] = useState<Erros>({});
  const [carregando, setCarregando] = useState(false);
  // Resultado da avaliação do domínio ao sair do campo de e-mail.
  const [dominio, setDominio] = useState<{ ok: boolean; msg: string } | null>(null);
  const nomeRef = useRef<HTMLInputElement>(null);
  const emailRef = useRef<HTMLInputElement>(null);
  const senhaRef = useRef<HTMLInputElement>(null);

  /** Avalia o domínio: pessoal (na hora), sem organização ou ligado a um time (pelo backend). */
  async function avaliar(valor: string) {
    const em = valor.trim().toLowerCase();
    if (!EMAIL_RE.test(em)) return setDominio(null);
    if (DOMINIOS_PESSOAIS.includes(em.split("@")[1])) return setDominio({ ok: false, msg: MSG_PESSOAL });
    try {
      const r = await authApi.avaliarDominio(em);
      if (r.situacao === "ok") setDominio({ ok: true, msg: `Você entra no time ${r.time} de ${r.organizacao}, como vendedor.` });
      else if (r.situacao === "pessoal") setDominio({ ok: false, msg: MSG_PESSOAL });
      else setDominio({ ok: false, msg: MSG_SEM_ORG });
    } catch {
      // Sem a consulta no backend, o cadastro valida o domínio ao enviar.
      setDominio(null);
    }
  }

  async function enviar(e: FormEvent) {
    e.preventDefault();
    if (carregando) return;
    const em = email.trim().toLowerCase();
    const errs: Erros = {};
    if (!nome.trim()) errs.nome = "Informe seu nome.";
    if (!em) errs.email = "Informe o e-mail corporativo.";
    else if (!EMAIL_RE.test(em)) errs.email = "Confira o formato do e-mail.";
    else if (DOMINIOS_PESSOAIS.includes(em.split("@")[1])) errs.email = MSG_PESSOAL;
    else if (dominio && !dominio.ok) errs.email = dominio.msg;
    if (senha.length < 8) errs.senha = "A senha precisa de pelo menos 8 caracteres.";
    if (Object.keys(errs).length) {
      setErros(errs);
      (errs.nome ? nomeRef : errs.email ? emailRef : senhaRef).current?.focus();
      return;
    }
    setErros({});
    setCarregando(true);
    try {
      const u = await cadastrar({ nome: nome.trim(), email: em, senha });
      navigate(inicialDoPerfil(u.perfil), { replace: true });
    } catch (err) {
      const { status, codigo } = infoErro(err);
      if (status === 409 || codigo === "email_em_uso") setErros({ email: "Já existe uma conta com este e-mail. Entre com ele." });
      else if (codigo === "dominio_pessoal") setErros({ email: MSG_PESSOAL });
      else if (codigo === "dominio_sem_organizacao") setErros({ email: MSG_SEM_ORG });
      else if (codigo === "senha_curta") setErros({ senha: "A senha precisa de pelo menos 8 caracteres." });
      else setErros({ email: mensagemDeErro(err, "Não foi possível criar a conta. Tente de novo.") });
      emailRef.current?.focus();
    } finally {
      setCarregando(false);
    }
  }

  return (
    <LayoutAcesso titulo="Comece a analisar suas reuniões." texto="Crie sua conta de consultor e tenha um histórico organizado de todas as conversas com seus clientes.">
      <form onSubmit={enviar} noValidate>
        <h1 className="m-0 text-[26px] font-semibold tracking-[-0.01em] text-ink">Criar conta</h1>
        <p className="mt-2 mb-0 text-sm text-ardosia">Leva menos de um minuto.</p>
        <div className="mt-6 flex flex-col gap-[18px]">
          <CampoAcesso
            id="cad-nome"
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
            id="cad-email"
            label="E-mail corporativo"
            type="email"
            value={email}
            onChange={(x) => {
              setEmail(x);
              setDominio(null);
              if (erros.email) setErros((s) => ({ ...s, email: undefined }));
            }}
            onBlur={() => void avaliar(email)}
            placeholder="seu.email@empresa.com"
            autoComplete="email"
            inputRef={emailRef}
            erro={erros.email || (dominio && !dominio.ok ? dominio.msg : null)}
            dica={dominio && dominio.ok ? dominio.msg : DICA_PADRAO}
            dicaOk={!!(dominio && dominio.ok)}
          />
          <CampoAcesso
            id="cad-senha"
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
          <BotaoEnviar carregando={carregando} rotulo="Criar conta" rotuloCarregando="Criando conta…" />
        </div>
        <p className="mt-5 mb-0 text-[13px] text-ardosia">
          Já tem conta?{" "}
          <button type="button" className={link} onClick={() => navigate(rotas.login)}>
            Entrar
          </button>
        </p>
      </form>
    </LayoutAcesso>
  );
}
