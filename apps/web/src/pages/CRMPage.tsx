import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { leadsApi } from '../api/services'
import apiClient from '../api/client'
import { Card, PageHeader, StatusBadge, Loading, EmptyState } from '../components/ui'
import { MessageSquare } from 'lucide-react'

async function fetchConversations() {
  return (await apiClient.get('/conversations/')).data
}
async function fetchMessages(id: number) {
  return (await apiClient.get(`/conversations/${id}/messages/`)).data
}

export default function CRMPage() {
  const [selected, setSelected] = useState<number | null>(null)
  const convs = useQuery({ queryKey: ['conversations'], queryFn: fetchConversations, refetchInterval: 10000 })
  const msgs = useQuery({ queryKey: ['convMessages', selected], queryFn: () => fetchMessages(selected!), enabled: !!selected })
  const leads = useQuery({ queryKey: ['leads', 'pipeline'], queryFn: () => leadsApi.list() })

  const convList: any[] = Array.isArray(convs.data) ? convs.data : []
  const leadList: any[] = Array.isArray(leads.data) ? leads.data : (leads.data?.results || [])
  const lead = convList.find((c) => c.id === selected)?.lead

  return (
    <div>
      <PageHeader title="Sales CRM & Conversations" subtitle="Conversation inbox and lead pipeline" />

      <div className="grid grid-cols-1 xl:grid-cols-4 gap-4">
        {/* conversation list */}
        <Card className="p-3 xl:col-span-1 max-h-[70vh] overflow-y-auto">
          <h3 className="text-xs font-semibold uppercase tracking-wide text-[#71717A] px-1 mb-2">Inbox</h3>
          {convs.isLoading ? <Loading /> : convList.length === 0 ? (
            <EmptyState title="No conversations" hint="Inbound WhatsApp/webhook messages appear here." icon={<MessageSquare size={24} />} />
          ) : (
            convList.map((c: any) => (
              <button key={c.id} onClick={() => setSelected(c.id)}
                className={`w-full text-left p-2.5 rounded-lg mb-1 hover:bg-[#F7F7F8] ${selected === c.id ? 'bg-[#F4F4F5]' : ''}`}>
                <div className="flex justify-between items-center">
                  <p className="text-sm font-medium text-[#111111]">{c.lead?.name || 'Unknown'}</p>
                  <span className="text-[10px] text-[#9CA3AF]">{c.channel}</span>
                </div>
                <p className="text-xs text-[#71717A] truncate mt-0.5">{c.last_message?.body || '—'}</p>
              </button>
            ))
          )}
        </Card>

        {/* active conversation */}
        <Card className="p-4 xl:col-span-2 max-h-[70vh] overflow-y-auto">
          {!selected ? <EmptyState title="Select a conversation" /> : msgs.isLoading ? <Loading /> : (
            <div className="space-y-2">
              {(msgs.data || []).map((m: any) => (
                <div key={m.id} className={`max-w-[75%] rounded-xl px-3 py-2 text-sm ${
                  m.direction === 'inbound' ? 'bg-[#F4F4F5] text-[#111111]' : 'bg-[#111111] text-white ml-auto'
                }`}>
                  <p>{m.body}</p>
                  <p className={`text-[10px] mt-1 ${m.direction === 'inbound' ? 'text-[#9CA3AF]' : 'text-[#9CA3AF]'}`}>
                    {new Date(m.created_at).toLocaleTimeString()}
                  </p>
                </div>
              ))}
              {(msgs.data || []).length === 0 && <EmptyState title="No messages" />}
            </div>
          )}
        </Card>

        {/* lead profile */}
        <Card className="p-4 xl:col-span-1">
          <h3 className="text-xs font-semibold uppercase tracking-wide text-[#71717A] mb-3">Lead Profile</h3>
          {lead ? (
            <div className="space-y-2 text-sm">
              <p className="font-medium text-[#111111]">{lead.name}</p>
              <div className="flex items-center gap-2"><StatusBadge status={lead.stage} /></div>
              <p className="text-xs text-[#71717A]">ID {lead.id}</p>
            </div>
          ) : <EmptyState title="No lead selected" />}
        </Card>
      </div>

      {/* pipeline summary */}
      <Card className="mt-4 p-4">
        <h3 className="text-sm font-medium mb-3">Pipeline ({leadList.length} leads)</h3>
        <div className="flex gap-1 h-6 rounded-lg overflow-hidden">
          {['new','contacted','qualified','proposal','negotiation','won','lost'].map((stage, i) => {
            const n = leadList.filter((l: any) => l.stage === stage).length
            if (!n) return null
            return <div key={stage} title={`${stage}: ${n}`} className="h-full"
              style={{ flexGrow: n, background: ['#E4E4E7','#D4D4D8','#A1A1AA','#71717A','#52525B','#111111','#B91C1C'][i] }} />
          })}
        </div>
        <div className="flex flex-wrap gap-3 mt-2">
          {['new','contacted','qualified','proposal','negotiation','won','lost'].map((stage) => {
            const n = leadList.filter((l: any) => l.stage === stage).length
            return n ? <span key={stage} className="text-[11px] text-[#71717A]">{stage} {n}</span> : null
          })}
        </div>
      </Card>
    </div>
  )
}
