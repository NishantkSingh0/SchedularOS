import { useQuery } from '@tanstack/react-query'
import { analyticsApi } from '../api/services'
import { Card, PageHeader, Loading, EmptyState } from '../components/ui'
import { useState } from 'react'

const EVENT_GROUPS: Record<string, string> = {
  'workflow.': 'Workflow',
  'proposal.': 'Proposal',
  'step.': 'Step',
  'agent.': 'Agent',
}

export default function ActivityPage() {
  const [filter, setFilter] = useState('all')
  const { data, isLoading } = useQuery({
    queryKey: ['activity', 'full'],
    queryFn: () => analyticsApi.activity(200),
    refetchInterval: 10000,
  })

  const events: any[] = data?.events || []
  const filtered = filter === 'all' ? events : events.filter((e) => e.event_type.startsWith(filter))

  return (
    <div>
      <PageHeader title="Activity Center" subtitle="Append-only audit trail of agent and system actions" />
      <div className="flex gap-2 mb-4">
        {['all', 'workflow.', 'proposal.', 'step.'].map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-3 py-1 rounded-full text-xs border ${filter === f ? 'bg-[#111111] text-white border-[#111111]' : 'bg-white border-[#E5E5E7] text-[#71717A]'}`}
          >
            {f === 'all' ? 'All' : EVENT_GROUPS[f]}
          </button>
        ))}
      </div>
      <Card>
        {isLoading ? <Loading /> : filtered.length === 0 ? (
          <EmptyState title="No activity" hint="Audit events will appear as agents act." />
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-[11px] uppercase tracking-wide text-[#9CA3AF] border-b border-[#E5E5E7]">
                <th className="px-4 py-3">Event</th>
                <th className="px-4 py-3">Details</th>
                <th className="px-4 py-3">Proposal</th>
                <th className="px-4 py-3 w-44">Time</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#F4F4F5]">
              {filtered.map((e: any) => (
                <tr key={e.id} className="hover:bg-[#F7F7F8]">
                  <td className="px-4 py-2.5 font-medium text-[#111111]">{e.event_type}</td>
                  <td className="px-4 py-2.5 text-[#71717A] text-xs max-w-md truncate">
                    {e.metadata?.agent || e.metadata?.action_type || e.metadata?.decision || JSON.stringify(e.metadata).slice(0, 80)}
                  </td>
                  <td className="px-4 py-2.5 text-xs text-[#9CA3AF] font-mono">{e.proposal_id ? e.proposal_id.slice(0, 12) : '—'}</td>
                  <td className="px-4 py-2.5 text-xs text-[#9CA3AF]">{new Date(e.created_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </div>
  )
}
