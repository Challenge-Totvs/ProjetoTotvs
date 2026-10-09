/* Rotas da aplicação (SDD 9.3). As telas logadas ficam dentro do AppLayout. */

import type { ReactNode } from "react";
import { BrowserRouter, Navigate, Outlet, Route, Routes } from "react-router-dom";
import { AppLayout } from "./components/layout/AppLayout";
import { Carregando, Vazio } from "./components/ui/base";
import { btn } from "./components/ui/classes";
import { AppProvider } from "./context/AppContext";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { inicialDoPerfil, rotas } from "./lib/rotas";
import CadastroPage from "./pages/acesso/CadastroPage";
import LoginPage from "./pages/acesso/LoginPage";
import ClientePage from "./pages/cliente/ClientePage";
import ClientesPage from "./pages/clientes/ClientesPage";
import ConfiguracoesPage from "./pages/configuracoes/ConfiguracoesPage";
import InicioPage from "./pages/inicio/InicioPage";
import NovaTranscricaoPage from "./pages/nova/NovaTranscricaoPage";
import ReuniaoPage from "./pages/reuniao/ReuniaoPage";
import type { Perfil } from "./types/api";

/** Só entra quem está logado; os dados do usuário ficam disponíveis no AppProvider. */
function RotaProtegida() {
  const { usuario, carregando } = useAuth();
  if (carregando) return <Carregando />;
  if (!usuario) return <Navigate to={rotas.login} replace />;
  return (
    <AppProvider usuario={usuario}>
      <Outlet />
    </AppProvider>
  );
}

/** Telas de acesso: quem já está logado vai direto para a tela inicial do perfil. */
function RotaPublica({ children }: { children: ReactNode }) {
  const { usuario, carregando } = useAuth();
  if (carregando) return <Carregando />;
  if (usuario) return <Navigate to={inicialDoPerfil(usuario.perfil)} replace />;
  return <>{children}</>;
}

/** Rota que existe só para um perfil. Fora dele: "Tela não disponível para o seu perfil". */
function SoPerfil({ perfil, children }: { perfil: Perfil; children: ReactNode }) {
  const { usuario } = useAuth();
  if (usuario && usuario.perfil !== perfil) return <TelaIndisponivel />;
  return <>{children}</>;
}

function TelaIndisponivel() {
  const { usuario } = useAuth();
  return (
    <Vazio
      titulo="Tela não disponível para o seu perfil"
      acao={
        <a className={btn()} href={usuario ? inicialDoPerfil(usuario.perfil) : rotas.login}>
          Voltar
        </a>
      }
    />
  );
}

function RedirecionarInicial() {
  const { usuario, carregando } = useAuth();
  if (carregando) return <Carregando />;
  return <Navigate to={usuario ? inicialDoPerfil(usuario.perfil) : rotas.login} replace />;
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route
            path={rotas.login}
            element={
              <RotaPublica>
                <LoginPage />
              </RotaPublica>
            }
          />
          <Route
            path={rotas.cadastro}
            element={
              <RotaPublica>
                <CadastroPage />
              </RotaPublica>
            }
          />
          <Route element={<RotaProtegida />}>
            <Route element={<AppLayout />}>
              <Route
                path={rotas.inicio}
                element={
                  <SoPerfil perfil="vendedor">
                    <InicioPage />
                  </SoPerfil>
                }
              />
              <Route path={rotas.clientes} element={<ClientesPage />} />
              <Route path="/clientes/:id" element={<ClientePage />} />
              <Route path="/reunioes/:id" element={<ReuniaoPage />} />
              <Route
                path="/transcricoes/nova"
                element={
                  <SoPerfil perfil="vendedor">
                    <NovaTranscricaoPage />
                  </SoPerfil>
                }
              />
              <Route path={rotas.configuracoes} element={<ConfiguracoesPage />} />
              <Route path="*" element={<TelaIndisponivel />} />
            </Route>
          </Route>
          <Route path="/" element={<RedirecionarInicial />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
