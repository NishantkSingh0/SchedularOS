import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { knowledgeApi } from '../api/services'
import { Card, PageHeader, Btn, Loading, EmptyState } from '../components/ui'
import { Database, Search } from 'lucide-react'

export default function KnowledgePage() {
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [query, setQuery] = useState('')

  const store = useMutation({ mutationFn: () => knowledgeApi.store({ title, content, source: 'manual' }) })
  const search = useMutation({ mutationFn: () => knowledgeApi.search(query, 5) })

  return (
    <div>
      <PageHeader title="Knowledge Base" subtitle="RAG-backed knowledge that grounds agent reasoning" />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card className="p-5">
          <h3 className="text-sm font-medium mb-3"><Database size={14} className="inline mr-1" />Store document</h3>
          <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Title"
            className="w-full h-9 px-3 rounded-lg border border-[#E5E5E7] text-sm mb-2" />
          <textarea value={content} onChange={(e) => setContent(e.target.value)} placeholder="Content…" rows={6}
            className="w-full rounded-lg border border-[#E5E5E7] p-3 text-sm resize-none" />
          <Btn className="mt-2" onClick={() => store.mutate()} disabled={!title || !content || store.isPending}>
            {store.isPending ? 'Storing…' : 'Store'}
          </Btn>
          {store.isSuccess && <p className="text-xs text-[#166534] mt-2">Stored: {store.data.id}</p>}
        </Card>

        <Card className="p-5">
          <h3 className="text-sm font-medium mb-3"><Search size={14} className="inline mr-1" />Semantic search</h3>
          <div className="flex gap-2">
            <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Query…"
              className="flex-1 h-9 px-3 rounded-lg border border-[#E5E5E7] text-sm" />
            <Btn onClick={() => search.mutate()} disabled={!query || search.isPending}>Search</Btn>
          </div>
          {search.isPending ? <Loading /> : search.data && (
            <ul className="mt-3 space-y-2">
              {(search.data.results || []).map((r: any, i: number) => (
                <li key={i} className="border border-[#E5E5E7] rounded-lg p-3">
                  <p className="text-sm font-medium">{r.title}</p>
                  <p className="text-xs text-[#71717A] mt-1 line-clamp-3">{r.content}</p>
                  {r.score != null && <p className="text-[10px] text-[#9CA3AF] mt-1">score {Number(r.score).toFixed(3)}</p>}
                </li>
              ))}
              {(search.data.results || []).length === 0 && <EmptyState title="No matches" />}
            </ul>
          )}
        </Card>
      </div>
    </div>
  )
}
