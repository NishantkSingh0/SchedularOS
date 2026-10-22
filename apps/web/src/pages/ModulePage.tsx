import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useLocation } from 'react-router-dom'
import { agentsApi, proposalsApi, analyticsApi } from '../api/services'
import { Card, PageHeader, Btn, StatusBadge, Loading, EmptyState } from '../components/ui'
import { Sparkles } from 'lucide-react'
import { useState } from 'react'

interface ModuleConfig {
  title: string
  subtitle: string
  agent: string
  actionPrefixes: string[]
  capabilities: string[]
  availabilityNote: string
}

const MODULES: Record<string, ModuleConfig> = {
  creative: {
    title: 'Creative Studio', subtitle: 'Generate and manage marketing content',
    agent: 'creative', actionPrefixes: ['content.'],
    capabilities: ['Social posts', 'Ad copy', 'Image generation', 'Landing page copy', 'Brand asset briefs'],
    availabilityNote: 'Generated assets are produced by the creative agent via proposals — approve them in the Approval Center.',
  },
  partnerships: {
    title: 'Influencers & Affiliates', subtitle: 'Creator relationships and partnerships',
    agent: 'partnerships', actionPrefixes: ['partnership.', 'influencer.'],
    capabilities: ['Creator discovery', 'Outreach', 'Collaboration tracking', 'Commission management'],
    availabilityNote: 'No creator database connected yet — proposals from the partnerships agent appear below.',
  },
  followups: {
    title: 'Follow-ups & Automation', subtitle: 'Sequences, triggers and scheduled communication',
    agent: 'followup', actionPrefixes: ['followup.', 'whatsapp.', 'email.'],
    capabilities: ['Email sequences', 'WhatsApp follow-ups', 'Scheduled nudges', 'Consent-gated sends'],
    availabilityNote: 'Automation actions are executed via proposals — see FollowUp actions below.',
  },
  conversion: {
    title: 'Conversion Optimization', subtitle: 'Funnels, experiments and checkout',
    agent: 'conversion', actionPrefixes: ['conversion.', 'pricing.'],
    capabilities: ['Funnel analysis', 'Offer testing', 'Lead scoring'],
    availabilityNote: 'No web analytics source connected — conversion agent proposals appear below.',
  },
  retention: {
    title: 'Customer Retention', subtitle: 'Lifecycle, loyalty and churn',
    agent: 'customer_success', actionPrefixes: ['customer.', 'retention.'],
    capabilities: ['Win-back campaigns', 'Churn risk scoring', 'Feedback collection'],
    availabilityNote: 'No order/subscription data source connected — retention agent proposals appear below.',
  },
  upsell: {
    title: 'Upselling & Cross-selling', subtitle: 'Revenue expansion in the existing base',
    agent: 'sales_development', actionPrefixes: ['sales.', 'upsell.'],
    capabilities: ['Opportunity identification', 'Offer drafting', 'Repeat purchase nudges'],
    availabilityNote: 'No purchase history source connected — expansion agent proposals appear below.',
  },
  campaigns: {
    title: 'Campaigns', subtitle: 'Cross-channel campaign coordination',
    agent: 'orchestrator', actionPrefixes: ['meta.', 'google.'],
    capabilities: ['Campaign planning', 'Channel allocation', 'Budget proposals'],
    availabilityNote: 'Campaign objects live as workflow runs — see the Workflow Builder for execution detail.',
  },
}

export default function ModulePage() {
  const module = useLocation().pathname.slice(1)
  const cfg = MODULES[module]
  const qc = useQueryClient()
  const [goal, setGoal] = useState('')

  const proposals = useQuery({ queryKey: ['proposals', 'all'], queryFn: () => proposalsApi.list() })
  const trust = useQuery({ queryKey: ['trust'], queryFn: analyticsApi.trust })

  const runAgent = useMutation({
    mutationFn: () => agentsApi.run({ agent: cfg.agent, goal }),
    onSuccess: () => { setGoal(''); qc.invalidateQueries({ queryKey: ['workflowRuns'] }) },
  })

  if (!cfg) return <EmptyState title="Unknown module" />

  const all: any[] = Array.isArray(proposals.data) ? proposals.data : (proposals.data?.results || [])
  const moduleProposals = all.filter((p) => cfg.actionPrefixes.some((pre) => p.action_type?.startsWith(pre)))
  const agentTrust = (trust.data?.trust || []).filter((t: any) => t.agent === cfg.agent)

  return (
    <div>
      <PageHeader title={cfg.title} subtitle={cfg.subtitle} />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-4">
        <Card className="p-4 lg:col-span-2">
          <h3 className="text-sm font-medium mb-2">Ask the {cfg.agent} agent</h3>
          <div className="flex gap-2">
            <input
              value={goal}
              onChange={(e) => setGoal(e.target.value)}
              placeholder={`e.g. "${cfg.capabilities[0]} for our product"`}
              className="flex-1 h-9 px-3 rounded-lg border border-[#E5E5E7] text-sm focus:outline-none focus:ring-1 focus:ring-[#111111]"
            />
            <Btn onClick={() => runAgent.mutate()} disabled={!goal.trim() || runAgent.isPending}>
              <Sparkles size={14} /> {runAgent.isPending ? 'Queuing…' : 'Run'}
            </Btn>
          </div>
          <div className="flex flex-wrap gap-1.5 mt-3">
            {cfg.capabilities.map((c) => (
              <button key={c} onClick={() => setGoal(`${c} — `)}
                className="px-2 py-0.5 rounded-full text-[11px] border border-[#E5E5E7] text-[#71717A] hover:bg-[#F7F7F8]">
                {c}
              </button>
            ))}
          </div>
        </Card>

        <Card className="p-4">
          <h3 className="text-sm font-medium mb-2">Agent autonomy</h3>
          {agentTrust.length === 0 ? (
            <p className="text-xs text-[#9CA3AF]">No decisions yet — trust starts at L1 and grows with approvals.</p>
          ) : (
            <ul className="space-y-1.5">
              {agentTrust.map((t: any, i: number) => (
                <li key={i} className="flex justify-between text-sm">
                  <span className="text-[#71717A]">{t.action_type}</span>
                  <span className="font-medium">L{t.trust_level} · {t.approvals}✓ {t.rejections}✗</span>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>

      <Card className="p-4">
        <h3 className="text-sm font-medium mb-1">Related proposals</h3>
        <p className="text-xs text-[#9CA3AF] mb-3">{cfg.availabilityNote}</p>
        {proposals.isLoading ? <Loading /> : moduleProposals.length === 0 ? (
          <EmptyState title="No proposals yet" hint={`Ask the ${cfg.agent} agent to produce proposals for this module.`} />
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-[11px] uppercase tracking-wide text-[#9CA3AF] border-b border-[#E5E5E7]">
                <th className="px-3 py-2">Action</th><th className="px-3 py-2">Tier</th>
                <th className="px-3 py-2">Rationale</th><th className="px-3 py-2">Status</th>
                <th className="px-3 py-2 w-40">Created</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#F4F4F5]">
              {moduleProposals.map((p: any) => (
                <tr key={p.id} className="hover:bg-[#F7F7F8]">
                  <td className="px-3 py-2 font-medium text-[#111111]">{p.action_type}</td>
                  <td className="px-3 py-2"><span className="text-[10px] px-1.5 py-0.5 rounded bg-[#F4F4F5]">T{p.risk_tier}</span></td>
                  <td className="px-3 py-2 text-xs text-[#71717A] max-w-xs truncate">{p.rationale}</td>
                  <td className="px-3 py-2"><StatusBadge status={p.status} /></td>
                  <td className="px-3 py-2 text-xs text-[#9CA3AF]">{new Date(p.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </div>
  )
}
