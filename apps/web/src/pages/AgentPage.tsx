import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { workflowApi, proposalsApi, agentsApi } from '../api/services'
import { Card, PageHeader, Btn, StatusBadge, Loading, EmptyState } from '../components/ui'
import { Send, Pause, Play, XCircle, Clock } from 'lucide-react'

function StepRow({ step }: { step: any }) {
  return (
    <div className="flex items-center gap-3 py-3 border-b border-[#F4F4F5] last:border-0">
      <div className="w-2 h-2 rounded-full bg-[#111111]" />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-[#111111]">{step.agent}</p>
        <p className="text-xs text-[#9CA3AF]">
          {step.run_at && `scheduled ${new Date(step.run_at).toLocaleString()}`}
          {step.completed_at && ` · done ${new Date(step.completed_at).toLocaleTimeString()}`}
        </p>
        {step.error_message && <p className="text-xs text-[#B91C1C] mt-0.5">{step.error_message}</p>}
      </div>
      <StatusBadge status={step.state} />
    </div>
  )
}

export default function AgentPage() {
  const qc = useQueryClient()
  const [goal, setGoal] = useState('')
  const [selectedRun, setSelectedRun] = useState<string | null>(null)

  const runs = useQuery({
    queryKey: ['workflowRuns'],
    queryFn: workflowApi.list,
    refetchInterval: 5000,
  })
  const runDetail = useQuery({
    queryKey: ['workflowRun', selectedRun],
    queryFn: () => workflowApi.detail(selectedRun!),
    enabled: !!selectedRun,
    refetchInterval: selectedRun ? 3000 : false,
  })
  const pendingProposals = useQuery({
    queryKey: ['proposals', 'pending'],
    queryFn: () => proposalsApi.list({ status: 'pending' }),
    refetchInterval: 5000,
  })
  const agents = useQuery({ queryKey: ['agents'], queryFn: agentsApi.list })

  const launch = useMutation({
    mutationFn: (g: string) => workflowApi.launch(g),
    onSuccess: () => {
      setGoal('')
      qc.invalidateQueries({ queryKey: ['workflowRuns'] })
    },
  })

  const control = useMutation({
    mutationFn: ({ id, action }: { id: string; action: 'pause' | 'resume' | 'cancel' }) =>
      workflowApi[action](id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['workflowRuns', 'workflowRun'] }),
  })

  const runList: any[] = Array.isArray(runs.data) ? runs.data : (runs.data?.results || [])
  const selected = runDetail.data || runList.find((r) => String(r.id) === selectedRun)
  const steps = selected?.steps || []

  return (
    <div>
      <PageHeader title="AI Agent" subtitle="Assign marketing objectives in natural language" />

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        {/* Left: conversation / goal input + runs */}
        <div className="space-y-4">
          <Card className="p-4">
            <h3 className="text-sm font-medium mb-3">New Objective</h3>
            <textarea
              value={goal}
              onChange={(e) => setGoal(e.target.value)}
              rows={4}
              placeholder={'e.g. "Create a 30-day campaign: research the audience, prepare creatives, propose a budget…"'}
              className="w-full rounded-lg border border-[#E5E5E7] p-3 text-sm focus:outline-none focus:ring-1 focus:ring-[#111111] resize-none"
            />
            <Btn
              className="mt-3 w-full justify-center"
              disabled={!goal.trim() || launch.isPending}
              onClick={() => launch.mutate(goal.trim())}
            >
              <Send size={14} /> {launch.isPending ? 'Planning…' : 'Launch Agent'}
            </Btn>
            {launch.isError && <p className="text-xs text-[#B91C1C] mt-2">Failed to launch. Check backend.</p>}
          </Card>

          <Card className="p-4">
            <h3 className="text-sm font-medium mb-2">Workflow Runs</h3>
            {runs.isLoading ? <Loading /> : runList.length === 0 ? (
              <EmptyState title="No runs yet" hint="Launch an objective to create a workflow run." />
            ) : (
              <ul className="divide-y divide-[#F4F4F5]">
                {runList.map((r: any) => (
                  <li key={r.id}>
                    <button
                      onClick={() => setSelectedRun(String(r.id))}
                      className={`w-full text-left py-2.5 px-2 rounded-md hover:bg-[#F7F7F8] ${String(r.id) === selectedRun ? 'bg-[#F4F4F5]' : ''}`}
                    >
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
        </div>

        {/* Center: execution plan */}
        <Card className="xl:col-span-2 p-5">
          {!selected ? (
            <EmptyState
              title="Select a workflow run"
              hint="Pick a run on the left, or launch a new objective. The agent's step-by-step execution plan will appear here."
            />
          ) : (
            <>
              <div className="flex items-start justify-between mb-4">
                <div className="min-w-0">
                  <h3 className="text-sm font-medium text-[#111111]">{selected.goal}</h3>
                  <p className="text-xs text-[#71717A] mt-1">
                    {steps.length} step{steps.length !== 1 ? 's' : ''} · created {new Date(selected.created_at).toLocaleString()}
                  </p>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <StatusBadge status={selected.status} />
                  {selected.status === 'running' && (
                    <>
                      <Btn variant="secondary" onClick={() => control.mutate({ id: selected.id, action: 'pause' })}><Pause size={13} /></Btn>
                      <Btn variant="danger" onClick={() => control.mutate({ id: selected.id, action: 'cancel' })}><XCircle size={13} /></Btn>
                    </>
                  )}
                  {selected.status === 'paused' && (
                    <Btn variant="secondary" onClick={() => control.mutate({ id: selected.id, action: 'resume' })}><Play size={13} /></Btn>
                  )}
                </div>
              </div>

              {/* progress bar */}
              {steps.length > 0 && (
                <div className="mb-4">
                  <div className="h-1.5 bg-[#F4F4F5] rounded-full overflow-hidden">
                    <div
                      className="h-full bg-[#111111] transition-all"
                      style={{ width: `${(steps.filter((s: any) => s.state === 'done').length / steps.length) * 100}%` }}
                    />
                  </div>
                  <p className="text-xs text-[#9CA3AF] mt-1">
                    {steps.filter((s: any) => s.state === 'done').length} of {steps.length} steps complete
                  </p>
                </div>
              )}

              <h4 className="text-xs font-semibold uppercase tracking-wide text-[#71717A] mb-1">Execution Plan</h4>
              {runDetail.isLoading ? <Loading /> : steps.length === 0 ? (
                <EmptyState title="No steps" hint="The orchestrator produced no steps for this goal." />
              ) : (
                <div>{steps.map((s: any) => <StepRow key={s.id} step={s} />)}</div>
              )}

              {/* pending proposals for this run */}
              {(pendingProposals.data?.results || pendingProposals.data || [])
                .filter((p: any) => steps.some((s: any) => s.id === p.step)).length > 0 && (
                <div className="mt-4 pt-4 border-t border-[#E5E5E7]">
                  <h4 className="text-xs font-semibold uppercase tracking-wide text-[#71717A] mb-2">
                    <Clock size={12} className="inline mr-1" />Awaiting your approval
                  </h4>
                  <p className="text-sm text-[#71717A]">
                    This run has proposals waiting for review. Open the{' '}
                    <a href="/approvals" className="text-[#111111] underline">Approvals</a> center to decide.
                  </p>
                </div>
              )}
            </>
          )}
        </Card>
      </div>

      {/* Right-ish: registered agents */}
      <Card className="mt-4 p-4">
        <h3 className="text-sm font-medium mb-3">Registered Agents</h3>
        {agents.isLoading ? <Loading /> : (
          <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
            {(agents.data?.agents || []).map((a: any) => (
              <div key={a.name} className="border border-[#E5E5E7] rounded-lg p-2.5">
                <p className="text-xs font-medium text-[#111111]">{a.name}</p>
                <p className="text-[10px] text-[#9CA3AF]">tier {a.model_tier} · {a.queue} · T{a.default_risk_tier}</p>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  )
}
