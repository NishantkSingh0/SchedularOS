import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useAuthStore } from './store/auth'
import LoginPage from './pages/LoginPage'
import AppLayout from './components/AppLayout'
import OverviewPage from './pages/OverviewPage'
import AgentPage from './pages/AgentPage'
import ApprovalsPage from './pages/ApprovalsPage'
import ActivityPage from './pages/ActivityPage'
import LeadsPage from './pages/LeadsPage'
import WorkflowsPage from './pages/WorkflowsPage'
import CRMPage from './pages/CRMPage'
import AdvertisingPage from './pages/AdvertisingPage'
import ResearchPage from './pages/ResearchPage'
import KnowledgePage from './pages/KnowledgePage'
import IntegrationsPage from './pages/IntegrationsPage'
import BrandPage from './pages/BrandPage'
import AnalyticsCenterPage from './pages/AnalyticsCenterPage'
import ModulePage from './pages/ModulePage'
import { CalendarPage, AssetsPage, SettingsPage } from './pages/SimplePages'

const queryClient = new QueryClient()

function RequireAuth({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route element={<RequireAuth><AppLayout /></RequireAuth>}>
            <Route path="/" element={<OverviewPage />} />
            <Route path="/agent" element={<AgentPage />} />
            <Route path="/campaigns" element={<ModulePage />} />
            <Route path="/analytics" element={<AnalyticsCenterPage />} />
            <Route path="/research" element={<ResearchPage />} />
            <Route path="/creative" element={<ModulePage />} />
            <Route path="/advertising" element={<AdvertisingPage />} />
            <Route path="/partnerships" element={<ModulePage />} />
            <Route path="/leads" element={<LeadsPage />} />
            <Route path="/crm" element={<CRMPage />} />
            <Route path="/followups" element={<ModulePage />} />
            <Route path="/conversion" element={<ModulePage />} />
            <Route path="/retention" element={<ModulePage />} />
            <Route path="/upsell" element={<ModulePage />} />
            <Route path="/workflows" element={<WorkflowsPage />} />
            <Route path="/calendar" element={<CalendarPage />} />
            <Route path="/assets" element={<AssetsPage />} />
            <Route path="/approvals" element={<ApprovalsPage />} />
            <Route path="/activity" element={<ActivityPage />} />
            <Route path="/knowledge" element={<KnowledgePage />} />
            <Route path="/integrations" element={<IntegrationsPage />} />
            <Route path="/brand" element={<BrandPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App
