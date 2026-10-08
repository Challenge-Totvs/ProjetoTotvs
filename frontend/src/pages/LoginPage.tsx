import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function LoginPage() {
    const { login } = useAuth()
    const navigate = useNavigate()
    const [email, setEmail] = useState('')
    const [senha, setSenha] = useState('')
    const [erro, setErro] = useState('')
    const [carregando, setCarregando] = useState(false)

    async function handleSubmit(e: FormEvent) {
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
        <form onSubmit={handleSubmit}>
            <h1>InsightCall</h1>
            <input type="email" placeholder="E-mail" value={email} onChange={(e) => setEmail(e.target.value)} required />
            <input type="password" placeholder="Senha" value={senha} onChange={(e) => setSenha(e.target.value)} required />
            {erro && <p role="alert">{erro}</p>}
            <button type="submit" disabled={carregando}>{carregando ? 'Entrando...' : 'Entrar'}</button>
        </form>
    )
}