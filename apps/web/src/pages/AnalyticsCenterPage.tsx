import { useQuery } from '@tanstack/react-query'
import { analyticsApi } from '../api/services'
import { Card, PageHeader, Loading, EmptyState, ChartCard } from '../components/ui'
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid,
  PieChart, Pie, Cell, AreaChart, Area,
} from 'recharts'

const SHADES = ['#111111', '#71717A', '#9CA3AF', '#D4D4D8', '#E4E4E7']

export default function AnalyticsCenterPage() {
  const stats = useQuery({ queryKey: ['proposalStats'], queryFn: analyticsApi.proposalStats })
  const wf = useQuery({ queryKey: ['wfStats'], queryFn: analyticsApi.workflowStats })
  const prod = useQuery({ queryKey: ['agentProd'], queryFn: analyticsApi.agentProductivity });
  void prod
  const msgs = useQuery({ queryKey: ['msgTrend'], queryFn: () => analyticsApi.messageTrend(30) })
  const trust = useQuery({ queryKey: ['trust'], queryFn: analyticsApi.trust })

  return (
    <div>
      <PageHeader title="Analytics Center" subtitle="Cross-module metrics aggregated from real execution data" />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
        <ChartCard title="Proposals by Status" subtitle="Agent action decisions">
          {(stats.data?.by_status || []).length === 0 ? <EmptyState title="No proposals" /> : (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={stats.data.by_status}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E5E7" />
                <XAxis dataKey="status" tick={{ fontSize: 10, fill: '#71717A' }} />
                <YAxis allowDecimals={false} tick={{ fontSize: 10, fill: '#71717A' }} width={30} />
                <Tooltip />
                <Bar dataKey="count" fill="#111111" radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </ChartCard>

        <ChartCard title="Proposals by Risk Tier" subtitle="T0 lowest risk → T3 always human">
          {(stats.data?.by_risk_tier || []).length === 0 ? <EmptyState title="No proposals" /> : (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={stats.data.by_risk_tier}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E5E7" />
                <XAxis dataKey="tier" tick={{ fontSize: 10, fill: '#71717A' }} tickFormatter={(t) => `T${t}`} />
                <YAxis allowDecimals={false} tick={{ fontSize: 10, fill: '#71717A' }} width={30} />
                <Tooltip />
                <Bar dataKey="count" fill="#111111" radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </ChartCard>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-4">
        <ChartCard title="Step States" subtitle="All workflow steps by state">
          {Object.keys(wf.data?.step_states || {}).length === 0 ? <EmptyState title="No steps" /> : (
            <ResponsiveContainer width="100%" height={190}>
              <PieChart>
                <Pie data={Object.entries(wf.data?.step_states || {}).map(([status, count]) => ({ status, count }))}
                  dataKey="count" nameKey="status" innerRadius={40} outerRadius={65} strokeWidth={2}>
                  {Object.keys(wf.data?.step_states || {}).map((_, i) => <Cell key={i} fill={SHADES[i % 5]} />)}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          )}
        </ChartCard>

        <ChartCard title="Message Volume" subtitle="Inbound + outbound (30d)">
          <ResponsiveContainer width="100%" height={190}>
            <AreaChart data={msgs.data?.inbound || []}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E5E5E7" />
              <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#71717A' }} tickFormatter={(d) => d.slice(5)} />
              <YAxis allowDecimals={false} tick={{ fontSize: 10, fill: '#71717A' }} width={30} />
              <Tooltip />
              <Area type="monotone" dataKey="count" stroke="#111111" fill="#F4F4F5" strokeWidth={1.5} />
            </AreaChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Decision Latency" subtitle="Avg human decision time">
          <div className="flex items-center justify-center h-[190px]">
            {stats.data?.avg_decision_seconds == null ? (
              <EmptyState title="No decisions yet" />
            ) : (
              <p className="text-4xl font-semibold tabular-nums">
                {stats.data.avg_decision_seconds > 3600
                  ? `${(stats.data.avg_decision_seconds / 3600).toFixed(1)}h`
                  : `${(stats.data.avg_decision_seconds / 60).toFixed(1)}m`}
              </p>
            )}
          </div>
        </ChartCard>
      </div>

      <Card className="p-5">
        <h3 className="text-sm font-medium mb-3">Agent Trust Levels</h3>
        {trust.isLoading ? <Loading /> : (trust.data?.trust || []).length === 0 ? (
          <EmptyState title="No trust data" hint="Trust accrues as proposals are approved/rejected." />
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-[11px] uppercase tracking-wide text-[#9CA3AF] border-b border-[#E5E5E7]">
                <th className="px-3 py-2">Agent</th><th className="px-3 py-2">Action</th>
                <th className="px-3 py-2">Level</th><th className="px-3 py-2">Approvals</th>
                <th className="px-3 py-2">Rejections</th><th className="px-3 py-2">Decisions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#F4F4F5]">
              {trust.data.trust.map((t: any, i: number) => (
                <tr key={i}>
                  <td className="px-3 py-2 font-medium">{t.agent}</td>
                  <td className="px-3 py-2 text-xs text-[#71717A]">{t.action_type}</td>
                  <td className="px-3 py-2 font-semibold">L{t.trust_level}</td>
                  <td className="px-3 py-2 tabular-nums">{t.approvals}</td>
                  <td className="px-3 py-2 tabular-nums">{t.rejections}</td>
                  <td className="px-3 py-2 tabular-nums">{t.total_decisions}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </div>
  )
}
