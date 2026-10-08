import axios from 'axios'

export const TOKEN_KEY = 'insightcall_token'

export const http = axios.create({
    baseURL: import.meta.env.VITE_API_URL ?? 'http://localhost:8080',
})

http.interceptors.request.use((config) => {
    const token = localStorage.getItem(TOKEN_KEY)
    if (token) {
        config.headers.Authorization = `Bearer ${token}`
    }
    return config
})

http.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            localStorage.removeItem(TOKEN_KEY)
            window.location.href = '/login'
        }
        return Promise.reject(error)
    },
)