import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { leadsApi, analyticsApi } from '../api/services'
import { Card, PageHeader, Btn, StatusBadge, Loading, EmptyState } from '../components/ui'
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts'
import { ChartCard } from '../components/ui'
import { Plus } from 'lucide-react'

export default function LeadsPage() {
  const qc = useQueryClient()
  const [stageFilter, setStageFilter] = useState('')
  const [showCreate, setShowCreate] = useState(false)
  const [form, setForm] = useState({ name: '', phone: '', email: '', stage: 'new' })

  const leads = useQuery({
    queryKey: ['leads', stageFilter],
    queryFn: () => leadsApi.list(stageFilter ? { stage: stageFilter } : {}),
  })
  const funnel = useQuery({ queryKey: ['funnel'], queryFn: analyticsApi.funnel })
  const scores = useQuery({ queryKey: ['leadScores'], queryFn: analyticsApi.leadScoreDistribution })

  const create = useMutation({
    mutationFn: (data: any) => leadsApi.create(data),
    onSuccess: () => {
      setShowCreate(false); setForm({ name: '', phone: '', email: '', stage: 'new' })
      qc.invalidateQueries({ queryKey: ['leads'] }); qc.invalidateQueries({ queryKey: ['funnel'] })
    },
  })

  const list: any[] = Array.isArray(leads.data) ? leads.data : (leads.data?.results || [])

  return (
    <div>
      <PageHeader
        title="Lead Generation"
        subtitle="Discover, qualify and organize potential customers"
        actions={<Btn onClick={() => setShowCreate(!showCreate)}><Plus size={14} /> New Lead</Btn>}
      />

      {showCreate && (
        <Card className="p-4 mb-4 grid grid-cols-1 md:grid-cols-5 gap-2 items-end">
          <input placeholder="Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}
            className="h-9 px-3 rounded-lg border border-[#E5E5E7] text-sm" />
          <input placeholder="Phone" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })}
            className="h-9 px-3 rounded-lg border border-[#E5E5E7] text-sm" />
          <input placeholder="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })}
            className="h-9 px-3 rounded-lg border border-[#E5E5E7] text-sm" />
          <select value={form.stage} onChange={(e) => setForm({ ...form, stage: e.target.value })}
            className="h-9 px-3 rounded-lg border border-[#E5E5E7] text-sm">
            {['new','contacted','qualified','proposal','negotiation','won','lost'].map(s => <option key={s}>{s}</option>)}
          </select>
          <Btn onClick={() => form.name && create.mutate(form)} disabled={!form.name || create.isPending}>
            {create.isPending ? 'Saving…' : 'Save'}
          </Btn>
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
        <ChartCard title="Lead Funnel" subtitle="By stage">
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={funnel.data?.stages || []}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E5E5E7" />
              <XAxis dataKey="stage" tick={{ fontSize: 10, fill: '#71717A' }} />
              <YAxis allowDecimals={false} tick={{ fontSize: 10, fill: '#71717A' }} width={30} />
              <Tooltip />
              <Bar dataKey="count" fill="#111111" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
        <ChartCard title="Score Distribution" subtitle="Lead score buckets">
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={scores.data?.buckets || []}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E5E5E7" />
              <XAxis dataKey="range" tick={{ fontSize: 10, fill: '#71717A' }} />
              <YAxis allowDecimals={false} tick={{ fontSize: 10, fill: '#71717A' }} width={30} />
              <Tooltip />
              <Bar dataKey="count" fill="#111111" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      <div className="flex gap-2 mb-3">
        {['', 'new', 'contacted', 'qualified', 'won', 'lost'].map((s) => (
          <button key={s} onClick={() => setStageFilter(s)}
            className={`px-3 py-1 rounded-full text-xs capitalize border ${stageFilter === s ? 'bg-[#111111] text-white border-[#111111]' : 'bg-white border-[#E5E5E7] text-[#71717A]'}`}>
            {s || 'All'}
          </button>
        ))}
      </div>

      <Card>
        {leads.isLoading ? <Loading /> : list.length === 0 ? (
          <EmptyState title="No leads" hint="Add leads manually or let the lead-generation agent discover them." />
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-[11px] uppercase tracking-wide text-[#9CA3AF] border-b border-[#E5E5E7]">
                <th className="px-4 py-3">Name</th>
                <th className="px-4 py-3">Contact</th>
                <th className="px-4 py-3">Stage</th>
                <th className="px-4 py-3">Score</th>
                <th className="px-4 py-3">Tags</th>
                <th className="px-4 py-3">Consent</th>
                <th className="px-4 py-3 w-40">Created</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#F4F4F5]">
              {list.map((l: any) => (
                <tr key={l.id} className="hover:bg-[#F7F7F8]">
                  <td className="px-4 py-2.5 font-medium text-[#111111]">{l.name}</td>
                  <td className="px-4 py-2.5 text-xs text-[#71717A]">{l.phone || l.email || '—'}</td>
                  <td className="px-4 py-2.5"><StatusBadge status={l.stage} /></td>
                  <td className="px-4 py-2.5 tabular-nums">{l.score ?? '—'}</td>
                  <td className="px-4 py-2.5 text-xs text-[#71717A]">{(l.tags || []).join(', ') || '—'}</td>
                  <td className="px-4 py-2.5 text-xs">
                    {l.opted_out_at ? <span className="text-[#B91C1C]">opted out</span> :
                     l.has_whatsapp_consent ? <span className="text-[#166534]">whatsapp</span> : '—'}
                  </td>
                  <td className="px-4 py-2.5 text-xs text-[#9CA3AF]">{new Date(l.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </div>
  )
}
