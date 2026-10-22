import { useQuery } from '@tanstack/react-query'
import { analyticsApi, agentsApi } from '../api/services'
import { Card, PageHeader, Btn, StatusBadge, Loading, EmptyState, ChartCard } from '../components/ui'
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts'
import { Radio, Sparkles } from 'lucide-react'
import { useState } from 'react'
import apiClient from '../api/client'

async function fetchAdCampaigns() {
  return (await apiClient.get('/analytics/ad_campaigns/')).data
}

export default function AdvertisingPage() {
  const [running, setRunning] = useState(false)
  const campaigns = useQuery({ queryKey: ['adCampaigns'], queryFn: fetchAdCampaigns })
  const spend = useQuery({ queryKey: ['spend'], queryFn: () => analyticsApi.spendOverTime(30) })
  const proposals = useQuery({ queryKey: ['proposalStats'], queryFn: analyticsApi.proposalStats })

  const launchAgent = async () => {
    setRunning(true)
    try { await agentsApi.run({ agent: 'paid_media', goal: 'Review and optimize our paid advertising campaigns' }) }
    finally { setRunning(false) }
  }

  return (
    <div>
      <PageHeader
        title="Paid Advertising"
        subtitle="Campaign management across connected ad accounts"
        actions={<Btn onClick={launchAgent} disabled={running}><Sparkles size={14} /> {running ? 'Queued…' : 'Ask paid_media agent'}</Btn>}
      />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
        <ChartCard title="Spend Over Time" subtitle="Executed ad spend (30d)">
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={spend.data?.series || []}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E5E5E7" />
              <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#71717A' }} tickFormatter={(d) => d.slice(5)} />
              <YAxis tick={{ fontSize: 10, fill: '#71717A' }} width={46} tickFormatter={(v) => `₹${v / 100}`} />
              <Tooltip formatter={(v: any) => `₹${(v / 100).toFixed(2)}`} />
              <Bar dataKey="spend_paise" fill="#111111" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Ad Actions Proposed" subtitle="Top action types from agents">
          {(proposals.data?.top_actions || []).length === 0 ? <EmptyState title="No proposals yet" /> : (
            <ul className="divide-y divide-[#F4F4F5]">
              {(proposals.data.top_actions || []).map((a: any) => (
                <li key={a.action_type} className="flex justify-between py-2 text-sm">
                  <span className="text-[#111111]">{a.action_type}</span>
                  <span className="text-[#71717A] tabular-nums">{a.c}</span>
                </li>
              ))}
            </ul>
          )}
        </ChartCard>
      </div>

      <Card>
        {campaigns.isLoading ? <Loading /> : !campaigns.data?.available ? (
          <EmptyState
            title={campaigns.data?.reason || 'No ad account connected'}
            hint="Connect Meta Ads or Google Ads in Integrations to see live campaign data. Nothing is fabricated — this table fills once credentials are configured."
            icon={<Radio size={26} />}
          />
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-[11px] uppercase tracking-wide text-[#9CA3AF] border-b border-[#E5E5E7]">
                <th className="px-4 py-3">Campaign</th><th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Objective</th><th className="px-4 py-3">Budget</th>
                <th className="px-4 py-3">Spend</th><th className="px-4 py-3">Impressions</th>
                <th className="px-4 py-3">Clicks</th><th className="px-4 py-3">Conversions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#F4F4F5]">
              {(campaigns.data.campaigns || []).map((c: any) => (
                <tr key={c.id} className="hover:bg-[#F7F7F8]">
                  <td className="px-4 py-2.5 font-medium">{c.name}</td>
                  <td className="px-4 py-2.5"><StatusBadge status={String(c.status).toLowerCase()} /></td>
                  <td className="px-4 py-2.5 text-xs text-[#71717A]">{c.objective}</td>
                  <td className="px-4 py-2.5 tabular-nums">{c.budget}</td>
                  <td className="px-4 py-2.5 tabular-nums">{c.spend}</td>
                  <td className="px-4 py-2.5 tabular-nums">{c.impressions}</td>
                  <td className="px-4 py-2.5 tabular-nums">{c.clicks}</td>
                  <td className="px-4 py-2.5 tabular-nums">{c.conversions}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </div>
  )
}
