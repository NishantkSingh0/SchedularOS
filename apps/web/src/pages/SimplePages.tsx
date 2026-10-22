import { useQuery } from '@tanstack/react-query'
import { workflowApi, proposalsApi } from '../api/services'
import { Card, PageHeader, StatusBadge, Loading, EmptyState } from '../components/ui'
import { CalendarDays, FolderOpen, Settings as SettingsIcon } from 'lucide-react'

export function CalendarPage() {
  const steps = useQuery({ queryKey: ['allSteps'], queryFn: () => workflowApi.steps(), refetchInterval: 15000 })
  const list: any[] = Array.isArray(steps.data) ? steps.data : (steps.data?.results || [])
  const scheduled = list
    .filter((s) => s.state === 'scheduled' && s.run_at)
    .sort((a, b) => new Date(a.run_at).getTime() - new Date(b.run_at).getTime())

  return (
    <div>
      <PageHeader title="Content Calendar" subtitle="Scheduled agent work — upcoming RunSteps" />
      <Card>
        {steps.isLoading ? <Loading /> : scheduled.length === 0 ? (
          <EmptyState title="Nothing scheduled" hint="Agent steps with future run times appear here." icon={<CalendarDays size={26} />} />
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-[11px] uppercase tracking-wide text-[#9CA3AF] border-b border-[#E5E5E7]">
                <th className="px-4 py-3">When</th><th className="px-4 py-3">Agent</th>
                <th className="px-4 py-3">Step</th><th className="px-4 py-3">State</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#F4F4F5]">
              {scheduled.map((s: any) => (
                <tr key={s.id}>
                  <td className="px-4 py-2.5">{new Date(s.run_at).toLocaleString()}</td>
                  <td className="px-4 py-2.5 font-medium">{s.agent}</td>
                  <td className="px-4 py-2.5 text-xs text-[#71717A] font-mono">{String(s.id).slice(0, 8)}</td>
                  <td className="px-4 py-2.5"><StatusBadge status={s.state} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </div>
  )
}

export function AssetsPage() {
  const proposals = useQuery({ queryKey: ['proposals', 'content'], queryFn: () => proposalsApi.list() })
  const list: any[] = Array.isArray(proposals.data) ? proposals.data : (proposals.data?.results || [])
  const assets = list.filter((p) => p.action_type?.startsWith('content.') || p.action_type?.startsWith('creative.'))

  return (
    <div>
      <PageHeader title="Asset Library" subtitle="Generated content artifacts (produced via proposals)" />
      <Card>
        {proposals.isLoading ? <Loading /> : assets.length === 0 ? (
          <EmptyState title="No assets yet" hint="Content proposals approved in the Approval Center appear here." icon={<FolderOpen size={26} />} />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 p-4">
            {assets.map((p: any) => (
              <div key={p.id} className="border border-[#E5E5E7] rounded-lg p-3">
                <p className="text-sm font-medium">{p.action_type}</p>
                <p className="text-xs text-[#71717A] mt-1 line-clamp-3">{p.rationale}</p>
                <div className="flex justify-between items-center mt-2">
                  <StatusBadge status={p.status} />
                  <span className="text-[10px] text-[#9CA3AF]">{new Date(p.created_at).toLocaleDateString()}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  )
}

export function SettingsPage() {
  return (
    <div>
      <PageHeader title="Settings" subtitle="Workspace configuration" />
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card className="p-4">
          <h3 className="text-sm font-medium flex items-center gap-2"><SettingsIcon size={15} /> Agent safety defaults</h3>
          <ul className="mt-3 space-y-2 text-sm text-[#71717A]">
            <li>· T3 (high-risk) actions always require human approval</li>
            <li>· Rejected proposals are never executed — feedback is recorded</li>
            <li>· Proposals expire after 48h without a decision</li>
            <li>· Trust levels promote after 200 decisions at ≥95% approval</li>
            <li>· WhatsApp consent and opt-out are enforced in code</li>
          </ul>
        </Card>
        <Card className="p-4">
          <h3 className="text-sm font-medium">Environment</h3>
          <p className="text-xs text-[#71717A] mt-2">
            API keys, database, Redis and LLM providers are configured in the backend <code>.env</code> file.
            See the Integrations page for live configuration status.
          </p>
        </Card>
      </div>
    </div>
  )
}
