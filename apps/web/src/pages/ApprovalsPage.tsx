import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { proposalsApi, analyticsApi } from '../api/services'
import { Card, PageHeader, Btn, StatusBadge, Loading, EmptyState } from '../components/ui'
import { Check, X, Pencil } from 'lucide-react'

function ProposalCard({ p }: { p: any }) {
  const qc = useQueryClient()
  const [note, setNote] = useState('')
  const [editing, setEditing] = useState(false)
  const [editedJson, setEditedJson] = useState('')

  const decide = useMutation({
    mutationFn: (data: any) => proposalsApi.decide(p.id, data),
    onSuccess: () => {
      setNote(''); setEditing(false)
      qc.invalidateQueries({ queryKey: ['proposals'] })
      qc.invalidateQueries({ queryKey: ['proposalStats'] })
    },
  })

  return (
    <Card className="p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <p className="text-sm font-medium text-[#111111]">{p.action_type}</p>
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-[#F4F4F5] text-[#71717A]">T{p.risk_tier}</span>
            <StatusBadge status={p.status} />
          </div>
          <p className="text-xs text-[#71717A] mt-1">{p.rationale}</p>
          <pre className="mt-2 text-[11px] bg-[#F7F7F8] rounded-lg p-2 overflow-x-auto text-[#3F3F46]">
            {JSON.stringify(p.payload, null, 2)}
          </pre>
          <p className="text-[11px] text-[#9CA3AF] mt-2">
            {new Date(p.created_at).toLocaleString()}
            {p.expires_at && ` · expires ${new Date(p.expires_at).toLocaleString()}`}
          </p>
        </div>
      </div>
      {p.status === 'pending' && (
        <div className="mt-3 pt-3 border-t border-[#F4F4F5] space-y-2">
          <input
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="Decision note (required for rejection)"
            className="w-full h-8 px-2.5 rounded-md border border-[#E5E5E7] text-xs focus:outline-none focus:ring-1 focus:ring-[#111111]"
          />
          {editing && (
            <textarea
              value={editedJson}
              onChange={(e) => setEditedJson(e.target.value)}
              rows={3}
              placeholder='Edited payload JSON'
              className="w-full rounded-md border border-[#E5E5E7] p-2 text-xs font-mono focus:outline-none"
            />
          )}
          <div className="flex gap-2">
            <Btn onClick={() => decide.mutate({ decision: 'approved', note })} disabled={decide.isPending}>
              <Check size={13} /> Approve
            </Btn>
            <Btn
              variant="secondary"
              onClick={() => {
                if (!editing) { setEditing(true); setEditedJson(JSON.stringify(p.payload, null, 2)); return }
                try { decide.mutate({ decision: 'edited', note, edited_payload: JSON.parse(editedJson) }) }
                catch { alert('Invalid JSON in edited payload') }
              }}
              disabled={decide.isPending}
            >
              <Pencil size={13} /> {editing ? 'Confirm edit' : 'Edit'}
            </Btn>
            <Btn
              variant="danger"
              onClick={() => {
                if (!note.trim()) { alert('A note is required when rejecting'); return }
                decide.mutate({ decision: 'rejected', note })
              }}
              disabled={decide.isPending}
            >
              <X size={13} /> Reject
            </Btn>
          </div>
        </div>
      )}
    </Card>
  )
}

export default function ApprovalsPage() {
  const [status, setStatus] = useState('pending')
  const proposals = useQuery({
    queryKey: ['proposals', status],
    queryFn: () => proposalsApi.list(status !== 'all' ? { status } : {}),
    refetchInterval: 5000,
  })
  const stats = useQuery({ queryKey: ['proposalStats'], queryFn: analyticsApi.proposalStats })

  const list: any[] = Array.isArray(proposals.data) ? proposals.data : (proposals.data?.results || [])

  return (
    <div>
      <PageHeader title="Approval Center" subtitle="Review consequential agent actions before they execute" />

      {/* stats strip */}
      {stats.data && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-5">
          {['pending', 'approved', 'executed', 'rejected', 'expired'].map((s) => {
            const row = (stats.data.by_status || []).find((r: any) => r.status === s)
            return (
              <Card key={s} className="p-3">
                <p className="text-[10px] uppercase tracking-wide text-[#71717A] font-medium">{s}</p>
                <p className="text-xl font-semibold mt-1 tabular-nums">{row?.count ?? 0}</p>
              </Card>
            )
          })}
        </div>
      )}

      <div className="flex gap-2 mb-4">
        {['pending', 'approved', 'executed', 'rejected', 'expired', 'all'].map((s) => (
          <button
            key={s}
            onClick={() => setStatus(s)}
            className={`px-3 py-1 rounded-full text-xs capitalize border ${
              status === s ? 'bg-[#111111] text-white border-[#111111]' : 'bg-white border-[#E5E5E7] text-[#71717A]'
            }`}
          >
            {s}
          </button>
        ))}
      </div>

      {proposals.isLoading ? <Loading /> : list.length === 0 ? (
        <Card><EmptyState title={`No ${status} proposals`} hint="Agent proposals requiring human review appear here." /></Card>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
          {list.map((p: any) => <ProposalCard key={p.id} p={p} />)}
        </div>
      )}
    </div>
  )
}
