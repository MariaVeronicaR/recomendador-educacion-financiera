import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../lib/auth'

export default function Layout() {
  const { user, signOut } = useAuth()
  const navigate = useNavigate()

  async function handleSignOut() {
    await signOut()
    navigate('/login')
  }

  const navLinkClass = ({ isActive }: { isActive: boolean }) =>
    `rounded-lg px-3 py-2 text-sm font-medium transition ${
      isActive ? 'bg-blue-50 text-blue-700' : 'text-slate-600 hover:bg-slate-100'
    }`

  return (
    <div className="flex min-h-screen flex-col">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
          <Link to="/" className="text-lg font-bold text-slate-900">
            Finanzas<span className="text-blue-600">IA</span>
          </Link>
          <nav className="flex items-center gap-1">
            <NavLink to="/" className={navLinkClass} end>
              Inicio
            </NavLink>
            <NavLink to="/cuestionario" className={navLinkClass}>
              Perfil
            </NavLink>
            <NavLink to="/recomendaciones" className={navLinkClass}>
              Recomendaciones
            </NavLink>
            <NavLink to="/progreso" className={navLinkClass}>
              Progreso
            </NavLink>
            {user ? (
              <button
                onClick={handleSignOut}
                className="ml-2 rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
              >
                Salir
              </button>
            ) : (
              <Link
                to="/login"
                className="ml-2 rounded-lg bg-blue-600 px-3 py-2 text-sm font-semibold text-white hover:bg-blue-700"
              >
                Entrar
              </Link>
            )}
          </nav>
        </div>
      </header>

      <main className="flex-1">
        <Outlet />
      </main>

      <footer className="border-t border-slate-200 bg-white py-4 text-center text-xs text-slate-400">
        Prototipo TFM — Plataforma de educación financiera personalizada
      </footer>
    </div>
  )
}
