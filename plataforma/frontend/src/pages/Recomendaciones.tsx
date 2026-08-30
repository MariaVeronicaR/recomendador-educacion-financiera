import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../lib/auth'
import { getRecommendations, type RecommendationResponse } from '../lib/api'
import { buildUserProfile } from '../lib/profile'
import { supabase } from '../lib/supabase'

export default function Recomendaciones() {
  const { user } = useAuth()
  const [data, setData] = useState<RecommendationResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [completing, setCompleting] = useState<string | null>(null)

  // Registra una interacción, marca el contenido como completado y registra los
  // conceptos que enseña como dominados (para desbloquear contenidos avanzados).
  async function handleComplete(contentId: string) {
    if (!user) return
    setCompleting(contentId)
    try {
      // 1. Registrar la interacción
      const { error: interError } = await supabase.from('interactions').insert({
        user_id: user.id,
        content_id: contentId,
        interaction_type: 'read',
        completed: true,
      })
      if (interError) throw interError

      // 2. Actualizar el progreso (upsert)
      const { error: progError } = await supabase.from('progress').upsert({
        user_id: user.id,
        content_id: contentId,
        completed: true,
        updated_at: new Date().toISOString(),
      })
      if (progError) throw progError

      // 3. Registrar los conceptos que enseña el contenido como dominados.
      //    Se obtienen del catálogo del servicio IA (campo concepts_taught).
      const catalogRes = await fetch(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/catalog`,
      )
      if (catalogRes.ok) {
        const catalog = await catalogRes.json()
        const content = catalog.find((c: { content_id: string }) => c.content_id === contentId)
        const conceptsTaught = content?.concepts_taught ?? []
        if (conceptsTaught.length > 0) {
          const { error: masteryError } = await supabase.from('mastered_concepts').upsert(
            conceptsTaught.map((cid: string) => ({
              user_id: user.id,
              concept_id: cid,
            })),
          )
          if (masteryError) throw masteryError
        }
      }

      // 4. Recargar recomendaciones (el progreso y mastery cambian el perfil)
      const profile = await buildUserProfile(user.id)
      const resp = await getRecommendations(profile)
      setData(resp)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al registrar el progreso')
    } finally {
      setCompleting(null)
    }
  }

  useEffect(() => {
    async function load() {
      if (!user) return
      setLoading(true)
      setError(null)
      try {
        // Construye el perfil real del usuario desde Supabase (cuestionario +
        // progreso + conceptos dominados) y lo envía al servicio IA.
        const profile = await buildUserProfile(user.id)
        const resp = await getRecommendations(profile)
        setData(resp)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Error al cargar recomendaciones')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [user])

  if (loading) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-16 text-center text-slate-500">
        Cargando recomendaciones…
      </div>
    )
  }

  if (error) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-16">
        <p className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-600">{error}</p>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-12">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Tus recomendaciones</h1>
          <p className="text-sm text-slate-500">
            Contenidos adaptados a tu perfil y a tu progreso
          </p>
        </div>
        {data && (
          <span className="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-600">
            Modelo: {data.source_model}
          </span>
        )}
      </div>

      {data && data.n_filtered > 0 && (
        <p className="mb-4 rounded-lg bg-amber-50 px-4 py-2 text-sm text-amber-700">
          Se filtraron {data.n_filtered} contenidos por no cumplir los prerrequisitos
          pedagógicos.
        </p>
      )}

      <div className="space-y-4">
        {data?.recommendations.map((rec) => (
          <div
            key={rec.content_id}
            className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
          >
            <div className="mb-1 flex items-center gap-2">
              <span className="rounded-full bg-blue-50 px-2 py-0.5 text-xs font-medium text-blue-700">
                {rec.topic}
              </span>
              <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600">
                {rec.difficulty}
              </span>
              {rec.format && (
                <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600">
                  {rec.format}
                </span>
              )}
            </div>
            <h2 className="mb-1 text-lg font-semibold text-slate-900">{rec.title}</h2>
            {rec.summary && (
              <p className="mb-2 text-sm text-slate-600">{rec.summary}</p>
            )}
            <p className="mb-3 text-sm text-slate-500">
              <span className="font-medium text-slate-700">Por qué:</span> {rec.explanation}
            </p>
            <div className="flex items-center gap-3">
              <Link
                to={`/contenido/${rec.content_id}`}
                className="text-sm font-medium text-blue-600 hover:underline"
              >
                Leer contenido →
              </Link>
              <button
                onClick={() => handleComplete(rec.content_id)}
                disabled={completing === rec.content_id}
                className="rounded-lg bg-green-600 px-3 py-1.5 text-xs font-semibold text-white transition hover:bg-green-700 disabled:opacity-50"
              >
                {completing === rec.content_id ? 'Guardando…' : '✓ Marcar como completado'}
              </button>
            </div>
          </div>
        ))}

        {data && data.recommendations.length === 0 && (
          <p className="rounded-lg bg-slate-50 px-4 py-6 text-center text-slate-500">
            No hay recomendaciones disponibles. Completa tu perfil para empezar.
          </p>
        )}
      </div>
    </div>
  )
}
