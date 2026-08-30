import { Link } from 'react-router-dom'
import { useAuth } from '../lib/auth'

export default function Inicio() {
  const { user } = useAuth()

  return (
    <div className="mx-auto max-w-3xl px-4 py-16 text-center">
      <h1 className="mb-4 text-4xl font-bold text-slate-900">
        Aprende finanzas personales a tu ritmo
      </h1>
      <p className="mb-8 text-lg text-slate-600">
        Una plataforma que te recomienda contenidos de educación financiera
        adaptados a tu nivel y a tus intereses, respetando la progresión
        pedagógica: no pasarás a temas avanzados sin dominar los básicos.
      </p>

      <div className="mb-10 flex flex-col items-center gap-3 sm:flex-row sm:justify-center">
        <Link
          to="/cuestionario"
          className="rounded-lg bg-blue-600 px-6 py-3 text-sm font-semibold text-white transition hover:bg-blue-700"
        >
          {user ? 'Completar mi perfil' : 'Empezar ahora'}
        </Link>
        <Link
          to="/recomendaciones"
          className="rounded-lg border border-slate-300 bg-white px-6 py-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
        >
          Ver mis recomendaciones
        </Link>
      </div>

      <div className="grid gap-4 text-left sm:grid-cols-3">
        <div className="rounded-xl border border-slate-200 bg-white p-5">
          <div className="mb-2 text-2xl">📊</div>
          <h3 className="mb-1 font-semibold text-slate-900">Perfilado</h3>
          <p className="text-sm text-slate-600">
            Un breve cuestionario para conocer tu nivel y tus intereses.
          </p>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-5">
          <div className="mb-2 text-2xl">🎯</div>
          <h3 className="mb-1 font-semibold text-slate-900">Recomendaciones</h3>
          <p className="text-sm text-slate-600">
            Contenidos personalizados con una explicación de por qué te los
            sugerimos.
          </p>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-5">
          <div className="mb-2 text-2xl">📈</div>
          <h3 className="mb-1 font-semibold text-slate-900">Progreso</h3>
          <p className="text-sm text-slate-600">
            Avanza por el itinerario y desbloquea temas más avanzados.
          </p>
        </div>
      </div>
    </div>
  )
}
