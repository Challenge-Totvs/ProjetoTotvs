import { useState, type SyntheticEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { registrar } from '../api/auth'

export default function CadastroPage() {
    const navigate = useNavigate()
    const [nome, setNome] = useState('')
    const [email, setEmail] = useState('')
    const [senha, setSenha] = useState('')
    const [confirmarSenha, setConfirmarSenha] = useState('')
    const [erro, setErro] = useState('')
    const [carregando, setCarregando] = useState(false)

    async function handleSubmit(e: SyntheticEvent) {
        e.preventDefault()
        setErro('')

        if (senha !== confirmarSenha) {
            setErro('As senhas não conferem.')
            return
        }

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
        <form onSubmit={handleSubmit}>
            <h1>Criar conta</h1>
            <input placeholder="Nome" value={nome} onChange={(e) => setNome(e.target.value)} required />
            <input type="email" placeholder="E-mail" value={email} onChange={(e) => setEmail(e.target.value)} required />
            <input type="password" placeholder="Senha" value={senha} onChange={(e) => setSenha(e.target.value)} required />
            <input type="password" placeholder="Confirmar senha" value={confirmarSenha} onChange={(e) => setConfirmarSenha(e.target.value)} required />
            {erro && <p role="alert">{erro}</p>}
            <button type="submit" disabled={carregando}>{carregando ? 'Cadastrando...' : 'Cadastrar'}</button>
            <p>Já tem conta? <Link to="/login">Entrar</Link></p>
        </form>
    )
}