import { useQuery } from '@tanstack/react-query'
import { analyticsApi } from '../api/services'
import { KpiCard, ChartCard, PageHeader, Loading, ErrorState, EmptyState } from '../components/ui'
import {
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid,
  BarChart, Bar, PieChart, Pie, Cell, FunnelChart, Funnel, LabelList, LineChart, Line,
} from 'recharts'
import { useState } from 'react'

const GRAY = '#9CA3AF'
const INK = '#111111'
const MID = '#71717A'

function paise(n: number) {
  return `₹${(n / 100).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`
}

export default function OverviewPage() {
  const [days, setDays] = useState(30)
  const kpis = useQuery({ queryKey: ['kpis'], queryFn: analyticsApi.kpis })
  const leadTrend = useQuery({ queryKey: ['leadTrend', days], queryFn: () => analyticsApi.leadTrend(days) })
  const funnel = useQuery({ queryKey: ['funnel'], queryFn: analyticsApi.funnel })
  const wf = useQuery({ queryKey: ['wfStats'], queryFn: analyticsApi.workflowStats })
  const prod = useQuery({ queryKey: ['agentProd'], queryFn: analyticsApi.agentProductivity })
  const spend = useQuery({ queryKey: ['spend', days], queryFn: () => analyticsApi.spendOverTime(days) })
  const activity = useQuery({ queryKey: ['activity'], queryFn: () => analyticsApi.activity(10) })
  const msgs = useQuery({ queryKey: ['msgTrend', days], queryFn: () => analyticsApi.messageTrend(days) })
  const sources = useQuery({ queryKey: ['leadSources'], queryFn: analyticsApi.leadSources })

  if (kpis.isLoading) return <Loading />
  if (kpis.isError) return <ErrorState message="Failed to load dashboard." />
  const k = kpis.data

  const funnelData = (funnel.data?.stages || []).filter((s: any) => s.count > 0 || s.stage === 'new')

  return (
    <div>
      <PageHeader
        title="Overview"
        subtitle="Marketing command center"
        actions={
          <select
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            className="h-9 px-3 rounded-lg border border-[#E5E5E7] bg-white text-sm"
          >
            <option value={7}>Last 7 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
          </select>
        }
      />

      {/* KPI grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 xl:grid-cols-6 gap-3 mb-6">
        <KpiCard label="Total Leads" value={k.total_leads} />
        <KpiCard label="Won" value={k.won_leads} />
        <KpiCard label="Conversion" value={`${k.conversion_rate}%`} />
        <KpiCard label="Spend (executed)" value={paise(k.total_spend_paise)} hint="from executed proposals" />
        <KpiCard label="Active Workflows" value={k.active_workflows} />
        <KpiCard label="Pending Approvals" value={k.pending_proposals} />
        <KpiCard label="Conversations" value={k.conversations} />
        <KpiCard label="Inbound Msgs" value={k.messages_inbound} />
        <KpiCard label="Outbound Msgs" value={k.messages_outbound} />
        <KpiCard label="Revenue" value={null} unavailable hint="no revenue source connected" />
        <KpiCard label="ROAS" value={null} unavailable hint="requires revenue attribution" />
        <KpiCard label="Executed Actions" value={k.executed_proposals} />
      </div>

      {/* Row 1: lead trend + funnel + spend */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-4">
        <ChartCard title="Lead Acquisition" subtitle={`New leads per day, last ${days} days`}>
          {leadTrend.isLoading ? <Loading /> : (
            <ResponsiveContainer width="100%" height={220}>
              <AreaChart data={leadTrend.data?.series || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E5E7" />
                <XAxis dataKey="date" tick={{ fontSize: 10, fill: MID }} tickFormatter={(d) => d.slice(5)} />
                <YAxis allowDecimals={false} tick={{ fontSize: 10, fill: MID }} width={30} />
                <Tooltip />
                <Area type="monotone" dataKey="count" stroke={INK} fill="#F4F4F5" strokeWidth={1.5} />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </ChartCard>

        <ChartCard title="Lead Pipeline Funnel" subtitle="Leads by stage">
          {funnel.isLoading ? <Loading /> : funnelData.length === 0 ? (
            <EmptyState title="No leads yet" hint="Create leads to populate the funnel." />
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <FunnelChart>
                <Tooltip />
                <Funnel dataKey="count" data={funnelData} nameKey="stage" fill={INK}>
                  <LabelList position="right" dataKey="stage" fill={MID} fontSize={11} />
                </Funnel>
              </FunnelChart>
            </ResponsiveContainer>
          )}
        </ChartCard>

        <ChartCard title="Marketing Spend" subtitle={`Executed spend per day, last ${days} days`}>
          {spend.isLoading ? <Loading /> : (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={spend.data?.series || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E5E7" />
                <XAxis dataKey="date" tick={{ fontSize: 10, fill: MID }} tickFormatter={(d) => d.slice(5)} />
                <YAxis tick={{ fontSize: 10, fill: MID }} width={46} tickFormatter={(v) => `₹${v / 100}`} />
                <Tooltip formatter={(v: any) => paise(v)} />
                <Bar dataKey="spend_paise" fill={INK} radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </ChartCard>
      </div>

      {/* Row 2: workflows, agent productivity, messages, sources */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4 mb-4">
        <ChartCard title="Workflow Runs" subtitle="By status">
          {wf.isLoading ? <Loading /> : (wf.data?.by_status || []).length === 0 ? (
            <EmptyState title="No workflow runs" hint="Launch a goal from the AI Agent workspace." />
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie data={wf.data.by_status} dataKey="count" nameKey="status" innerRadius={45} outerRadius={70} strokeWidth={2}>
                  {(wf.data.by_status || []).map((_: any, i: number) => (
                    <Cell key={i} fill={['#111111', '#71717A', '#9CA3AF', '#D4D4D8', '#E4E4E7'][i % 5]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          )}
          <div className="flex flex-wrap gap-2 mt-2">
            {(wf.data?.by_status || []).map((s: any) => (
              <span key={s.status} className="text-[11px] text-[#71717A]">{s.status}: {s.count}</span>
            ))}
          </div>
        </ChartCard>

        <ChartCard title="Agent Productivity" subtitle="Steps by agent and state" className="lg:col-span-2">
          {prod.isLoading ? <Loading /> : (prod.data?.agents || []).length === 0 ? (
            <EmptyState title="No agent runs yet" />
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={prod.data.agents} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E5E7" />
                <XAxis type="number" allowDecimals={false} tick={{ fontSize: 10, fill: MID }} />
                <YAxis type="category" dataKey="agent" tick={{ fontSize: 10, fill: MID }} width={110} />
                <Tooltip />
                <Bar dataKey="done" stackId="a" fill={INK} name="Done" />
                <Bar dataKey="awaiting_human" stackId="a" fill={GRAY} name="Awaiting human" />
                <Bar dataKey="failed" stackId="a" fill="#B91C1C" name="Failed" />
                <Bar dataKey="scheduled" stackId="a" fill="#D4D4D8" name="Scheduled" />
              </BarChart>
            </ResponsiveContainer>
          )}
        </ChartCard>

        <ChartCard title="Messages" subtitle={`Inbound vs outbound, ${days}d`}>
          {msgs.isLoading ? <Loading /> : (
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={(msgs.data?.inbound || []).map((r: any, i: number) => ({
                date: r.date, inbound: r.count, outbound: msgs.data?.outbound?.[i]?.count ?? 0,
              }))}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E5E7" />
                <XAxis dataKey="date" tick={{ fontSize: 10, fill: MID }} tickFormatter={(d) => d.slice(5)} />
                <YAxis allowDecimals={false} tick={{ fontSize: 10, fill: MID }} width={30} />
                <Tooltip />
                <Line dataKey="inbound" stroke={INK} dot={false} name="Inbound" strokeWidth={1.5} />
                <Line dataKey="outbound" stroke={GRAY} dot={false} name="Outbound" strokeWidth={1.5} strokeDasharray="4 4" />
              </LineChart>
            </ResponsiveContainer>
          )}
        </ChartCard>
      </div>

      {/* Row 3: lead sources + activity */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <ChartCard title="Lead Distribution" subtitle="By tag (no source field on leads)">
          {sources.isLoading ? <Loading /> : (sources.data?.sources || []).length === 0 ? (
            <EmptyState title="No lead data" />
          ) : (
            <ResponsiveContainer width="100%" height={180}>
              <PieChart>
                <Pie data={sources.data.sources} dataKey="count" nameKey="name" outerRadius={65} strokeWidth={2}>
                  {(sources.data.sources || []).map((_: any, i: number) => (
                    <Cell key={i} fill={['#111111', '#71717A', '#9CA3AF', '#D4D4D8', '#E4E4E7'][i % 5]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          )}
        </ChartCard>

        <ChartCard title="Recent Activity" subtitle="Latest audit events" className="lg:col-span-2">
          {activity.isLoading ? <Loading /> : (activity.data?.events || []).length === 0 ? (
            <EmptyState title="No activity yet" hint="Agent and proposal events will appear here." />
          ) : (
            <ul className="divide-y divide-[#F4F4F5]">
              {activity.data.events.map((e: any) => (
                <li key={e.id} className="py-2 flex items-center justify-between gap-3">
                  <div className="min-w-0">
                    <p className="text-sm text-[#111111] truncate">{e.event_type}</p>
                    <p className="text-xs text-[#9CA3AF] truncate">{e.metadata?.agent || e.metadata?.decision || ''}</p>
                  </div>
                  <span className="text-xs text-[#9CA3AF] whitespace-nowrap">
                    {new Date(e.created_at).toLocaleString()}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </ChartCard>
      </div>
    </div>
  )
}
