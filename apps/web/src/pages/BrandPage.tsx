import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { brandsApi } from '../api/services'
import { Card, PageHeader, Btn, Loading, EmptyState } from '../components/ui'
import { Plus } from 'lucide-react'

export default function BrandPage() {
  const qc = useQueryClient()
  const [show, setShow] = useState(false)
  const [form, setForm] = useState({ name: '', voice: '', rules: '' })
  const brands = useQuery({ queryKey: ['brands'], queryFn: brandsApi.list })
  const create = useMutation({
    mutationFn: (data: any) => brandsApi.create(data),
    onSuccess: () => { setShow(false); qc.invalidateQueries({ queryKey: ['brands'] }) },
  })
  const list: any[] = Array.isArray(brands.data) ? brands.data : (brands.data?.results || [])

  return (
    <div>
      <PageHeader title="Brand Settings" subtitle="Brand voice and rules injected into every agent prompt"
        actions={<Btn onClick={() => setShow(!show)}><Plus size={14} /> New brand</Btn>} />

      {show && (
        <Card className="p-4 mb-4 grid grid-cols-1 md:grid-cols-4 gap-2 items-end">
          <input placeholder="Brand name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}
            className="h-9 px-3 rounded-lg border border-[#E5E5E7] text-sm" />
          <input placeholder="Voice (e.g. friendly, premium)" value={form.voice} onChange={(e) => setForm({ ...form, voice: e.target.value })}
            className="h-9 px-3 rounded-lg border border-[#E5E5E7] text-sm" />
          <input placeholder="Rules (JSON or text)" value={form.rules} onChange={(e) => setForm({ ...form, rules: e.target.value })}
            className="h-9 px-3 rounded-lg border border-[#E5E5E7] text-sm" />
          <Btn onClick={() => form.name && create.mutate(form)} disabled={!form.name || create.isPending}>
            {create.isPending ? 'Saving…' : 'Save'}
          </Btn>
        </Card>
      )}

      {brands.isLoading ? <Loading /> : list.length === 0 ? (
        <Card><EmptyState title="No brands" hint="Create a brand so agents adopt its voice and rules." /></Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
          {list.map((b: any) => (
            <Card key={b.id} className="p-4">
              <p className="text-sm font-medium text-[#111111]">{b.name}</p>
              <p className="text-xs text-[#71717A] mt-1">{b.voice || 'No voice set'}</p>
              <p className="text-[10px] text-[#9CA3AF] mt-2">{new Date(b.created_at).toLocaleDateString()}</p>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
