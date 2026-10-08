import { useState, type SyntheticEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { registrar } from '../api/auth'
import AuthLayout from '../components/AuthLayout'
import Campo from '../components/Campo'
import Botao from '../components/Botao'

export default function CadastroPage() {
    const navigate = useNavigate()
    const [nome, setNome] = useState('')
    const [email, setEmail] = useState('')
    const [senha, setSenha] = useState('')
    const [erro, setErro] = useState('')
    const [carregando, setCarregando] = useState(false)

    async function handleSubmit(e: SyntheticEvent) {
        e.preventDefault()
        setErro('')
        setCarregando(true)
        try {
            await registrar(nome, email, senha)
            navigate('/login', { state: { cadastroOk: true } })
        } catch (err) {
            console.error(err)
            setErro('Não foi possível concluir o cadastro. Verifique os dados e tente novamente.')
        } finally {
            setCarregando(false)
        }
    }

    return (
        <AuthLayout
            imagem="/images/cadastro-bg.jpg"
            headline="Comece a analisar suas reuniões."
            descricao="Crie sua conta de consultor e tenha um histórico organizado de todas as conversas com seus clientes."
            titulo="Criar conta"
            subtitulo="Leva menos de um minuto."
        >
            <form onSubmit={handleSubmit} className="space-y-4">
                <Campo label="Nome completo" placeholder="Como você quer ser chamado" value={nome} onChange={(e) => setNome(e.target.value)} required />
                <Campo label="E-mail" type="email" placeholder="seu.email@empresa.com" value={email} onChange={(e) => setEmail(e.target.value)} required />
                <Campo label="Senha" type="password" placeholder="Mínimo de 8 caracteres" minLength={8} value={senha} onChange={(e) => setSenha(e.target.value)} required />

                {erro && (
                    <p role="alert" className="rounded-lg bg-red-50 px-3.5 py-2.5 text-xs text-red-700">
                        {erro}
                    </p>
                )}

                <Botao type="submit" disabled={carregando}>
                    {carregando ? 'Criando conta...' : 'Criar conta'}
                </Botao>

                <p className="pt-2 text-xs text-slate-500">
                    Já tem conta?{' '}
                    <Link to="/login" className="font-medium text-brand-navy hover:underline">
                        Entrar
                    </Link>
                </p>
            </form>
        </AuthLayout>
    )
}