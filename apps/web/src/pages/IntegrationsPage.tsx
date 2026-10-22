import { useQuery } from '@tanstack/react-query'
import { analyticsApi } from '../api/services'
import { Card, PageHeader, Loading } from '../components/ui'
import { Plug, CheckCircle2, XCircle } from 'lucide-react'

export default function IntegrationsPage() {
  const { data, isLoading } = useQuery({ queryKey: ['integrations'], queryFn: analyticsApi.integrations })

  return (
    <div>
      <PageHeader
        title="Integrations"
        subtitle="Connection status of external services — status reflects configured credentials, verified server-side"
      />
      {isLoading ? <Loading /> : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
          {(data?.integrations || []).map((i: any) => (
            <Card key={i.name} className="p-4 flex items-start gap-3">
              {i.configured
                ? <CheckCircle2 size={18} className="text-[#166534] mt-0.5" />
                : <XCircle size={18} className="text-[#9CA3AF] mt-0.5" />}
              <div>
                <p className="text-sm font-medium text-[#111111]">{i.name}</p>
                <p className="text-xs text-[#71717A] capitalize">{i.category}</p>
                <p className="text-xs mt-1">
                  {i.configured
                    ? <span className="text-[#166534]">Configured</span>
                    : <span className="text-[#9CA3AF]">Not configured — set credentials in the API .env</span>}
                </p>
              </div>
            </Card>
          ))}
        </div>
      )}
      <Card className="mt-4 p-4">
        <p className="text-xs text-[#71717A]">
          <Plug size={12} className="inline mr-1" />
          Connections are established server-side via environment variables. This page reports whether valid
          credentials are present — it never displays secrets. Unconfigured connectors run in explicit mock mode.
        </p>
      </Card>
    </div>
  )
}
