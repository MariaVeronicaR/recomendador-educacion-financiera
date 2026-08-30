import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { getContentDetail, type ContentDetail, type QuizQuestion } from '../lib/api'
import { useAuth } from '../lib/auth'
import { supabase } from '../lib/supabase'
import ContentBlocks from '../components/ContentBlocks'

export default function Contenido() {
  const { contentId } = useParams<{ contentId: string }>()
  const { user } = useAuth()
  const [content, setContent] = useState<ContentDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  // Estado del quiz: respuestas seleccionadas y resultados
  const [answers, setAnswers] = useState<Record<number, number>>({})
  const [results, setResults] = useState<Record<number, boolean>>({})
  const [quizSubmitted, setQuizSubmitted] = useState(false)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    async function load() {
      if (!contentId) return
      setLoading(true)
      setError(null)
      try {
        const data = await getContentDetail(contentId)
        setContent(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Error al cargar el contenido')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [contentId])

  function selectAnswer(qi: number, oi: number) {
    if (quizSubmitted) return
    setAnswers((prev) => ({ ...prev, [qi]: oi }))
  }

  function submitQuiz() {
    if (!content?.quiz) return
    const newResults: Record<number, boolean> = {}
    content.quiz.forEach((q, qi) => {
      newResults[qi] = answers[qi] === q.correct_index
    })
    setResults(newResults)
    setQuizSubmitted(true)
  }

  const correctCount = Object.values(results).filter(Boolean).length
  const quizTotal = content?.quiz?.length ?? 0

  // Al aprobar el quiz, registrar los conceptos dominados en Supabase.
  async function handleQuizPassed() {
    if (!user || !content?.quiz) return
    setSaving(true)
    try {
      const concepts = content.quiz
        .map((q) => q.concept_id)
        .filter((c): c is string => Boolean(c))
      if (concepts.length > 0) {
        const { error: masteryError } = await supabase.from('mastered_concepts').upsert(
          concepts.map((cid) => ({ user_id: user.id, concept_id: cid })),
        )
        if (masteryError) throw masteryError
      }
      // Marcar el contenido como completado
      const { error: progError } = await supabase.from('progress').upsert({
        user_id: user.id,
        content_id: contentId,
        completed: true,
        updated_at: new Date().toISOString(),
      })
      if (progError) throw progError
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al guardar el progreso')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-16 text-center text-slate-500">
        Cargando contenido…
      </div>
    )
  }

  if (error || !content) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-16">
        <p className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-600">
          {error ?? 'Contenido no encontrado'}
        </p>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-12">
      <h1 className="mb-4 text-2xl font-bold text-slate-900">
        {content.title ?? content.content_id}
      </h1>

      {/* Resumen (tldr) */}
      {content.tldr && (
        <div className="mb-6 rounded-2xl border border-blue-100 bg-blue-50 p-5">
          <h2 className="mb-1 text-sm font-semibold text-blue-800">En resumen</h2>
          <p className="text-sm text-blue-900">{content.tldr}</p>
        </div>
      )}

      {/* Puntos clave */}
      {content.key_points && content.key_points.length > 0 && (
        <div className="mb-6 rounded-2xl border border-slate-200 bg-white p-5">
          <h2 className="mb-3 text-sm font-semibold text-slate-700">Puntos clave</h2>
          <ul className="space-y-2">
            {content.key_points.map((kp, i) => (
              <li key={i} className="flex gap-2 text-sm text-slate-700">
                <span className="text-blue-600">•</span>
                {kp}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Texto del contenido (bloques estructurados si hay, si no texto plano) */}
      {content.blocks && content.blocks.length > 0 ? (
        <div className="mb-6 rounded-2xl border border-slate-200 bg-white p-6">
          <h2 className="mb-4 text-sm font-semibold text-slate-700">Contenido</h2>
          <ContentBlocks blocks={content.blocks} />
        </div>
      ) : content.text ? (
        <div className="mb-6 rounded-2xl border border-slate-200 bg-white p-6">
          <h2 className="mb-3 text-sm font-semibold text-slate-700">Contenido</h2>
          <div className="whitespace-pre-wrap text-sm leading-relaxed text-slate-700">
            {content.text}
          </div>
        </div>
      ) : null}

      {/* Quiz de evaluación formativa */}
      {content.quiz && content.quiz.length > 0 && (
        <div className="rounded-2xl border border-slate-200 bg-white p-6">
          <h2 className="mb-1 text-sm font-semibold text-slate-700">
            Comprueba lo aprendido
          </h2>
          <p className="mb-4 text-xs text-slate-500">
            Responde las preguntas para confirmar que dominas los conceptos.
          </p>

          <div className="space-y-6">
            {content.quiz.map((q, qi) => (
              <QuizBlock
                key={qi}
                question={q}
                index={qi}
                selected={answers[qi]}
                result={results[qi]}
                submitted={quizSubmitted}
                onSelect={selectAnswer}
              />
            ))}
          </div>

          {!quizSubmitted ? (
            <button
              onClick={submitQuiz}
              disabled={Object.keys(answers).length < quizTotal}
              className="mt-6 rounded-lg bg-blue-600 px-6 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50"
            >
              Corregir
            </button>
          ) : (
            <div className="mt-6 rounded-xl bg-slate-50 p-4">
              <p className="text-sm font-semibold text-slate-800">
                Has acertado {correctCount} de {quizTotal}
              </p>
              {correctCount === quizTotal ? (
                <div className="mt-2">
                  <p className="text-sm text-green-700">
                    ¡Perfecto! Dominas los conceptos de este contenido.
                  </p>
                  <button
                    onClick={handleQuizPassed}
                    disabled={saving}
                    className="mt-3 rounded-lg bg-green-600 px-4 py-2 text-sm font-semibold text-white hover:bg-green-700 disabled:opacity-50"
                  >
                    {saving ? 'Guardando…' : '✓ Registrar mi progreso'}
                  </button>
                </div>
              ) : (
                <p className="mt-2 text-sm text-amber-700">
                  Repasa el contenido e inténtalo de nuevo para dominar los conceptos.
                </p>
              )}
            </div>
          )}
        </div>
      )}

      {content.url && (
        <p className="mt-6 text-sm text-slate-500">
          Fuente:{' '}
          <a
            href={content.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 hover:underline"
          >
            {content.url}
          </a>
        </p>
      )}
    </div>
  )
}

function QuizBlock({
  question,
  index,
  selected,
  result,
  submitted,
  onSelect,
}: {
  question: QuizQuestion
  index: number
  selected?: number
  result?: boolean
  submitted: boolean
  onSelect: (qi: number, oi: number) => void
}) {
  return (
    <div>
      <p className="mb-2 text-sm font-medium text-slate-800">{question.question}</p>
      <div className="space-y-1.5">
        {question.options.map((opt, oi) => {
          let cls = 'border-slate-200 hover:bg-slate-50'
          if (submitted) {
            if (oi === question.correct_index) cls = 'border-green-500 bg-green-50'
            else if (oi === selected) cls = 'border-red-500 bg-red-50'
            else cls = 'border-slate-200 opacity-60'
          } else if (selected === oi) {
            cls = 'border-blue-500 bg-blue-50'
          }
          return (
            <label
              key={oi}
              className={`flex cursor-pointer items-center gap-3 rounded-lg border px-4 py-2.5 text-sm ${cls}`}
            >
              <input
                type="radio"
                name={`quiz-${index}`}
                checked={selected === oi}
                onChange={() => onSelect(index, oi)}
                disabled={submitted}
                className="accent-blue-600"
              />
              {opt}
            </label>
          )
        })}
      </div>
      {submitted && result === false && question.explanation && (
        <p className="mt-1.5 text-xs text-slate-500">{question.explanation}</p>
      )}
    </div>
  )
}
