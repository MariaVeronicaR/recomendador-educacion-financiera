import { useEffect, useState } from 'react'
import { useAuth } from '../lib/auth'
import { supabase } from '../lib/supabase'

interface ProgressRow {
  content_id: string
  completed: boolean
  updated_at: string
}

interface CatalogContent {
  content_id: string
  title: string
  topic: string
}

export default function Progreso() {
  const { user } = useAuth()
  const [rows, setRows] = useState<ProgressRow[]>([])
  const [mastered, setMastered] = useState<string[]>([])
  const [catalog, setCatalog] = useState<Record<string, CatalogContent>>({})
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      if (!user) return
      setLoading(true)

      // Progreso de contenidos
      const { data: progData, error: progError } = await supabase
        .from('progress')
        .select('content_id, completed, updated_at')
        .eq('user_id', user.id)
        .order('updated_at', { ascending: false })
      if (!progError && progData) setRows(progData as ProgressRow[])

      // Conceptos dominados
      const { data: masData, error: masError } = await supabase
        .from('mastered_concepts')
        .select('concept_id')
        .eq('user_id', user.id)
      if (!masError && masData) setMastered(masData.map((r) => r.concept_id))

      // Catálogo (para mostrar títulos en lugar de IDs)
      try {
        const res = await fetch(
          `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/catalog`,
        )
        if (res.ok) {
          const list = (await res.json()) as CatalogContent[]
          const map: Record<string, CatalogContent> = {}
          list.forEach((c) => (map[c.content_id] = c))
          setCatalog(map)
        }
      } catch {
        // Si el backend no está, mostramos los IDs
      }

      setLoading(false)
    }
    load()
  }, [user])

  const completed = rows.filter((r) => r.completed).length
  const pct = rows.length ? Math.round((completed / rows.length) * 100) : 0

  return (
    <div className="mx-auto max-w-3xl px-4 py-12">
      <h1 className="mb-2 text-2xl font-bold text-slate-900">Tu progreso</h1>
      <p className="mb-6 text-slate-500">
        Contenidos que has completado y conceptos que dominas.
      </p>

      <div className="mb-8 rounded-2xl border border-slate-200 bg-white p-6">
        <div className="mb-2 flex items-center justify-between">
          <span className="text-sm font-medium text-slate-700">Contenidos completados</span>
          <span className="text-sm font-semibold text-slate-900">
            {completed} / {rows.length} ({pct}%)
          </span>
        </div>
        <div className="h-2.5 w-full overflow-hidden rounded-full bg-slate-100">
          <div
            className="h-full rounded-full bg-blue-600 transition-all"
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>

      {mastered.length > 0 && (
        <div className="mb-8 rounded-2xl border border-slate-200 bg-white p-6">
          <h2 className="mb-3 text-sm font-semibold text-slate-700">
            Conceptos que dominas ({mastered.length})
          </h2>
          <div className="flex flex-wrap gap-2">
            {mastered.map((cid) => (
              <span
                key={cid}
                className="rounded-full bg-green-100 px-3 py-1 text-xs font-medium text-green-700"
              >
                {cid}
              </span>
            ))}
          </div>
        </div>
      )}

      {loading ? (
        <p className="text-center text-slate-500">Cargando…</p>
      ) : rows.length === 0 ? (
        <p className="rounded-lg bg-slate-50 px-4 py-6 text-center text-slate-500">
          Aún no has completado ningún contenido. Empieza con tus recomendaciones.
        </p>
      ) : (
        <div className="space-y-2">
          {rows.map((row) => (
            <div
              key={row.content_id}
              className="flex items-center justify-between rounded-lg border border-slate-200 bg-white px-4 py-3"
            >
              <div>
                <span className="text-sm font-medium text-slate-800">
                  {catalog[row.content_id]?.title ?? row.content_id}
                </span>
                {catalog[row.content_id]?.topic && (
                  <span className="ml-2 rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-500">
                    {catalog[row.content_id]?.topic}
                  </span>
                )}
              </div>
              <span
                className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                  row.completed
                    ? 'bg-green-100 text-green-700'
                    : 'bg-slate-100 text-slate-600'
                }`}
              >
                {row.completed ? 'Completado' : 'En curso'}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
