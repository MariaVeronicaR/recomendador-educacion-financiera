import type { ContentBlock } from '../lib/api'

// Renderiza los bloques del contenido (headings, párrafos, listas) de forma
// legible y con buen aspecto.
export default function ContentBlocks({ blocks }: { blocks: ContentBlock[] }) {
  return (
    <div className="space-y-4">
      {blocks.map((block, i) => {
        switch (block.type) {
          case 'heading': {
            const level = block.level ?? 2
            if (level === 1) {
              return (
                <h2 key={i} className="pt-2 text-xl font-bold text-slate-900">
                  {block.text}
                </h2>
              )
            }
            return (
              <h3 key={i} className="pt-2 text-lg font-semibold text-slate-800">
                {block.text}
              </h3>
            )
          }
          case 'list': {
            const items = block.items ?? []
            const ordered = block.style === 'ol'
            return (
              <div key={i} className="pl-1">
                {ordered ? (
                  <ol className="list-decimal space-y-1.5 pl-5 text-sm leading-relaxed text-slate-700">
                    {items.map((item, j) => (
                      <li key={j}>{item}</li>
                    ))}
                  </ol>
                ) : (
                  <ul className="list-disc space-y-1.5 pl-5 text-sm leading-relaxed text-slate-700">
                    {items.map((item, j) => (
                      <li key={j}>{item}</li>
                    ))}
                  </ul>
                )}
              </div>
            )
          }
          case 'paragraph':
          default:
            return (
              <p key={i} className="text-sm leading-relaxed text-slate-700">
                {block.text}
              </p>
            )
        }
      })}
    </div>
  )
}
