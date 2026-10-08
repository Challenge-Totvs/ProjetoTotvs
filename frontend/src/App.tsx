import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'
import LoginPage from './pages/LoginPage'
import CadastroPage from './pages/CadastroPage'

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/cadastro" element={<CadastroPage />} />
          <Route element={<ProtectedRoute />}>
            <Route path="/clientes" element={<div>Clientes (em breve)</div>} />
          </Route>
          <Route path="*" element={<Navigate to="/clientes" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}