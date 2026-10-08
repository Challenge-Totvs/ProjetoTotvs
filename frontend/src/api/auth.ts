import { http } from './http'

export async function login(email: string, senha: string): Promise<{ token: string }> {
    const { data } = await http.post('/api/auth/login', { email, senha })
    return data
}

export async function registrar(nome: string, email: string, senha: string) {
    await http.post('/api/auth/register', { nome, email, senha })
}