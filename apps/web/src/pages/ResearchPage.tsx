import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { researchApi } from '../api/services'
import { Card, PageHeader, Btn, Loading, EmptyState } from '../components/ui'
import { Search } from 'lucide-react'

export default function ResearchPage() {
  const [type, setType] = useState<'market' | 'competitors' | 'audience'>('market')
  const [input, setInput] = useState('')
  const [industry, setIndustry] = useState('')

  const research = useMutation({ mutationFn: (data: any) => researchApi.perform(data) })

  const run = () => {
    research.mutate({
      research_type: type,
      industry,
      company_name: type === 'competitors' ? input : undefined,
      product: type === 'audience' ? input : undefined,
      async_mode: false,
    })
  }

  return (
    <div>
      <PageHeader title="Market & Customer Research" subtitle="Research the market, competitors and audiences" />

      <Card className="p-5 mb-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3 items-end">
          <div>
            <label className="text-xs font-medium text-[#71717A]">Type</label>
            <select value={type} onChange={(e) => setType(e.target.value as any)}
              className="mt-1 w-full h-9 px-3 rounded-lg border border-[#E5E5E7] text-sm">
              <option value="market">Market research</option>
              <option value="competitors">Competitors</option>
              <option value="audience">Audience</option>
            </select>
          </div>
          <div>
            <label className="text-xs font-medium text-[#71717A]">Industry</label>
            <input value={industry} onChange={(e) => setIndustry(e.target.value)}
              className="mt-1 w-full h-9 px-3 rounded-lg border border-[#E5E5E7] text-sm" placeholder="e.g. cookware" />
          </div>
          <div>
            <label className="text-xs font-medium text-[#71717A]">{type === 'competitors' ? 'Company' : type === 'audience' ? 'Product' : 'Context'}</label>
            <input value={input} onChange={(e) => setInput(e.target.value)}
              className="mt-1 w-full h-9 px-3 rounded-lg border border-[#E5E5E7] text-sm" />
          </div>
          <Btn onClick={run} disabled={research.isPending}>
            <Search size={14} /> {research.isPending ? 'Researching…' : 'Run research'}
          </Btn>
        </div>
      </Card>

      {research.isPending && <Card><Loading label="Research agent is thinking…" /></Card>}
      {research.data && (
        <Card className="p-5">
          <pre className="text-xs whitespace-pre-wrap font-mono text-[#3F3F46] overflow-x-auto">
            {JSON.stringify(research.data, null, 2)}
          </pre>
        </Card>
      )}
      {!research.data && !research.isPending && (
        <Card><EmptyState title="No research yet" hint="Run a research task above — results are returned by the research agent." /></Card>
      )}
    </div>
  )
}
