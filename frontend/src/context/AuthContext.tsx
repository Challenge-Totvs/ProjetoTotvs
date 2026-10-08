import { createContext, useContext, useState, type ReactNode } from 'react'
import { TOKEN_KEY } from '../api/http'
import * as authApi from '../api/auth'

interface AuthContextData {
    isAuthenticated: boolean
    login: (email: string, senha: string) => Promise<void>
    logout: () => void
}

const AuthContext = createContext<AuthContextData | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
    const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_KEY))

    async function login(email: string, senha: string) {
        const { token } = await authApi.login(email, senha)
        localStorage.setItem(TOKEN_KEY, token)
        setToken(token)
    }

    function logout() {
        localStorage.removeItem(TOKEN_KEY)
        setToken(null)
    }

    return (
        <AuthContext.Provider value={{ isAuthenticated: !!token, login, logout }}>
            {children}
        </AuthContext.Provider>
    )
}

export function useAuth() {
    const ctx = useContext(AuthContext)
    if (!ctx) throw new Error('useAuth deve ser usado dentro de AuthProvider')
    return ctx
}