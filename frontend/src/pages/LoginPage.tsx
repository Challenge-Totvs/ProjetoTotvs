import { useState, type SyntheticEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import AuthLayout from '../components/AuthLayout'
import Campo from '../components/Campo'
import Botao from '../components/Botao'

export default function LoginPage() {
    const { login } = useAuth()
    const navigate = useNavigate()
    const location = useLocation()
    const cadastroOk = location.state?.cadastroOk

    const [email, setEmail] = useState('')
    const [senha, setSenha] = useState('')
    const [erro, setErro] = useState('')
    const [carregando, setCarregando] = useState(false)

    async function handleSubmit(e: SyntheticEvent) {
        e.preventDefault()
        setErro('')
        setCarregando(true)
        try {
            await login(email, senha)
            navigate('/clientes')
        } catch {
            setErro('E-mail ou senha inválidos.')
        } finally {
            setCarregando(false)
        }
    }

    return (
        <AuthLayout
            imagem="/images/login-bg.jpg"
            headline="Transforme conversas em oportunidades."
            descricao="Centralize as transcrições das suas reuniões e descubra automaticamente os pontos de interesse, objeções e oportunidades de venda de cada cliente."
            titulo="Entrar na sua conta"
            subtitulo="Acesse para consultar suas reuniões e análises."
        >
            <form onSubmit={handleSubmit} className="space-y-4">
                {cadastroOk && (
                    <p className="rounded-lg bg-emerald-50 px-3.5 py-2.5 text-xs text-emerald-700">
                        Cadastro realizado! Faça login para continuar.
                    </p>
                )}

                <Campo label="E-mail" type="email" placeholder="seu.email@empresa.com" value={email} onChange={(e) => setEmail(e.target.value)} required />
                <Campo label="Senha" type="password" placeholder="••••••••" value={senha} onChange={(e) => setSenha(e.target.value)} required />

                {erro && (
                    <p role="alert" className="rounded-lg bg-red-50 px-3.5 py-2.5 text-xs text-red-700">
                        {erro}
                    </p>
                )}

                <Botao type="submit" disabled={carregando}>
                    {carregando ? 'Entrando...' : 'Entrar'}
                </Botao>

                <p className="pt-2 text-xs text-slate-500">
                    Não tem conta?{' '}
                    <Link to="/cadastro" className="font-medium text-brand-navy hover:underline">
                        Cadastre-se
                    </Link>
                </p>
            </form>
        </AuthLayout>
    )
}