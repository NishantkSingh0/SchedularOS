import { useState, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { workflowApi } from '../api/services'
import { Card, PageHeader, Btn, StatusBadge, Loading, EmptyState } from '../components/ui'
import { ReactFlow, Background, Controls } from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { Pause, Play, XCircle } from 'lucide-react'

const STATE_COLORS: Record<string, string> = {
  done: '#166534', scheduled: '#1D4ED8', running: '#1D4ED8',
  awaiting_human: '#6D28D9', failed: '#B91C1C', cancelled: '#9CA3AF',
}

function FlowGraph({ steps }: { steps: any[] }) {
  const nodes = useMemo(() => steps.map((s, i) => ({
    id: String(s.id),
    position: { x: 60 + i * 210, y: 80 },
    data: { label: `${i + 1}. ${s.agent}` },
    style: {
      border: `1.5px solid ${STATE_COLORS[s.state] || '#9CA3AF'}`,
      borderRadius: 10, background: '#fff', fontSize: 11, padding: 8, width: 170,
    },
  })), [steps])
  const edges = useMemo(() => steps.slice(1).map((s, i) => ({
    id: `e${i}`, source: String(steps[i].id), target: String(s.id), animated: s.state === 'running',
    style: { stroke: '#9CA3AF' },
  })), [steps])

  return (
    <div style={{ height: 220 }}>
      <ReactFlow nodes={nodes} edges={edges} fitView proOptions={{ hideAttribution: true }} nodesDraggable={false}>
        <Background gap={20} color="#E5E5E7" />
        <Controls showInteractive={false} />
      </ReactFlow>
    </div>
  )
}

export default function WorkflowsPage() {
  const qc = useQueryClient()
  const [selectedRun, setSelectedRun] = useState<string | null>(null)
  const runs = useQuery({ queryKey: ['workflowRuns'], queryFn: workflowApi.list, refetchInterval: 5000 })
  const detail = useQuery({
    queryKey: ['workflowRun', selectedRun],
    queryFn: () => workflowApi.detail(selectedRun!),
    enabled: !!selectedRun,
    refetchInterval: 3000,
  })
  const control = useMutation({
    mutationFn: ({ id, action }: { id: string; action: 'pause' | 'resume' | 'cancel' }) => workflowApi[action](id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['workflowRun', 'workflowRuns'] }),
  })

  const list: any[] = Array.isArray(runs.data) ? runs.data : (runs.data?.results || [])
  const run = detail.data

  return (
    <div>
      <PageHeader title="Workflow Builder" subtitle="Agent execution plans and their dependency state" />
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        <Card className="p-4 xl:col-span-1 max-h-[70vh] overflow-y-auto">
          <h3 className="text-sm font-medium mb-2">Runs</h3>
          {runs.isLoading ? <Loading /> : list.length === 0 ? (
            <EmptyState title="No runs" hint="Launch an objective in the AI Agent workspace." />
          ) : (
            <ul className="divide-y divide-[#F4F4F5]">
              {list.map((r: any) => (
                <li key={r.id}>
                  <button onClick={() => setSelectedRun(String(r.id))}
                    className={`w-full text-left py-2.5 px-2 rounded-md hover:bg-[#F7F7F8] ${String(r.id) === selectedRun ? 'bg-[#F4F4F5]' : ''}`}>
                    <div className="flex items-center justify-between gap-2">
                      <p className="text-sm text-[#111111] truncate">{r.goal}</p>
                      <StatusBadge status={r.status} />
                    </div>
                    <p className="text-xs text-[#9CA3AF] mt-0.5">{new Date(r.created_at).toLocaleString()}</p>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </Card>

        <Card className="p-5 xl:col-span-2">
          {!run ? <EmptyState title="Select a run" /> : (
            <>
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h3 className="text-sm font-medium">{run.goal}</h3>
                  <p className="text-xs text-[#71717A] mt-1">{run.steps?.length || 0} steps</p>
                </div>
                <div className="flex gap-2 items-center">
                  <StatusBadge status={run.status} />
                  {run.status === 'running' && <Btn variant="secondary" onClick={() => control.mutate({ id: run.id, action: 'pause' })}><Pause size={13} /></Btn>}
                  {run.status === 'paused' && <Btn variant="secondary" onClick={() => control.mutate({ id: run.id, action: 'resume' })}><Play size={13} /></Btn>}
                  {['running', 'paused', 'awaiting_human'].includes(run.status) && (
                    <Btn variant="danger" onClick={() => control.mutate({ id: run.id, action: 'cancel' })}><XCircle size={13} /></Btn>
                  )}
                </div>
              </div>
              {run.steps?.length > 0 && <FlowGraph steps={run.steps} />}
              <div className="mt-4 border-t border-[#E5E5E7] pt-3">
                {(run.steps || []).map((s: any, i: number) => (
                  <div key={s.id} className="flex items-center gap-3 py-2 border-b border-[#F4F4F5] last:border-0">
                    <span className="text-xs text-[#9CA3AF] w-5">{i + 1}</span>
                    <div className="flex-1">
                      <p className="text-sm text-[#111111]">{s.agent}</p>
                      {s.error_message && <p className="text-xs text-[#B91C1C]">{s.error_message}</p>}
                    </div>
                    <StatusBadge status={s.state} />
                  </div>
                ))}
              </div>
            </>
          )}
        </Card>
      </div>
    </div>
  )
}
