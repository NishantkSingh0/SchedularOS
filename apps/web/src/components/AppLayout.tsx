import { useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import clsx from 'clsx'
import {
  LayoutDashboard, Bot, Megaphone, BarChart3, Search, Palette, Radio,
  Users, UserPlus, KanbanSquare, Repeat, MousePointerClick, HeartHandshake,
  TrendingUp, GitBranch, CalendarDays, FolderOpen, CheckSquare, Activity,
  Plug, Building2, Bell, Settings, ChevronLeft, ChevronRight, LogOut,
} from 'lucide-react'
import { useAuthStore } from '../store/auth'

const NAV_SECTIONS = [
  {
    title: 'WORKSPACE',
    items: [
      { to: '/', label: 'Overview', icon: LayoutDashboard, end: true },
      { to: '/agent', label: 'AI Agent', icon: Bot },
      { to: '/campaigns', label: 'Campaigns', icon: Megaphone },
      { to: '/analytics', label: 'Analytics', icon: BarChart3 },
    ],
  },
  {
    title: 'MARKETING MODULES',
    items: [
      { to: '/research', label: 'Market Research', icon: Search },
      { to: '/creative', label: 'Creative Studio', icon: Palette },
      { to: '/advertising', label: 'Paid Advertising', icon: Radio },
      { to: '/partnerships', label: 'Influencers & Affiliates', icon: Users },
      { to: '/leads', label: 'Lead Generation', icon: UserPlus },
      { to: '/crm', label: 'Sales CRM', icon: KanbanSquare },
      { to: '/followups', label: 'Follow-ups & Automation', icon: Repeat },
      { to: '/conversion', label: 'Conversion Optimization', icon: MousePointerClick },
      { to: '/retention', label: 'Customer Retention', icon: HeartHandshake },
      { to: '/upsell', label: 'Upselling & Cross-selling', icon: TrendingUp },
    ],
  },
  {
    title: 'OPERATIONS',
    items: [
      { to: '/workflows', label: 'Workflow Builder', icon: GitBranch },
      { to: '/calendar', label: 'Content Calendar', icon: CalendarDays },
      { to: '/assets', label: 'Asset Library', icon: FolderOpen },
      { to: '/approvals', label: 'Approvals', icon: CheckSquare },
      { to: '/activity', label: 'Activity Center', icon: Activity },
      { to: '/knowledge', label: 'Knowledge Base', icon: FolderOpen },
    ],
  },
  {
    title: 'CONFIGURATION',
    items: [
      { to: '/integrations', label: 'Integrations', icon: Plug },
      { to: '/brand', label: 'Brand Settings', icon: Building2 },
      { to: '/settings', label: 'Settings', icon: Settings },
    ],
  },
]

function Sidebar({ collapsed, onToggle }: { collapsed: boolean; onToggle: () => void }) {
  return (
    <aside className={clsx(
      'fixed inset-y-0 left-0 z-30 flex flex-col bg-white border-r border-[#E5E5E7] transition-all duration-200',
      collapsed ? 'w-14' : 'w-60'
    )}>
      <div className="flex items-center justify-between h-14 px-3 border-b border-[#E5E5E7]">
        {!collapsed && <span className="font-semibold text-sm text-[#111111]">SchedularOS</span>}
        <button onClick={onToggle} className="p-1.5 rounded-md hover:bg-[#F4F4F5] text-[#71717A]">
          {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </button>
      </div>
      <nav className="flex-1 overflow-y-auto py-3 px-2 space-y-4">
        {NAV_SECTIONS.map((section) => (
          <div key={section.title}>
            {!collapsed && (
              <p className="px-2 mb-1 text-[10px] font-semibold tracking-wider text-[#9CA3AF]">{section.title}</p>
            )}
            <ul className="space-y-0.5">
              {section.items.map(({ to, label, icon: Icon, end }) => (
                <li key={to}>
                  <NavLink
                    to={to}
                    end={end}
                    title={label}
                    className={({ isActive }) => clsx(
                      'flex items-center gap-2.5 rounded-md px-2 py-1.5 text-[13px] transition-colors',
                      isActive ? 'bg-[#F4F4F5] text-[#111111] font-medium' : 'text-[#71717A] hover:bg-[#F7F7F8] hover:text-[#111111]'
                    )}
                  >
                    <Icon size={16} className="shrink-0" />
                    {!collapsed && <span className="truncate">{label}</span>}
                  </NavLink>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </nav>
    </aside>
  )
}

function Topbar() {
  const user = useAuthStore((s: any) => s.user)
  const logout = useAuthStore((s: any) => s.logout)
  const navigate = useNavigate()

  return (
    <header className="sticky top-0 z-20 h-14 bg-white/90 backdrop-blur border-b border-[#E5E5E7] flex items-center gap-3 px-4">
      <div className="flex-1 max-w-md">
        <input
          placeholder="Search… (⌘K)"
          className="w-full h-9 px-3 rounded-lg border border-[#E5E5E7] bg-[#F7F7F8] text-sm focus:outline-none focus:ring-1 focus:ring-[#111111]"
          onKeyDown={(e) => { if (e.key === 'Enter') navigate('/leads') }}
        />
      </div>
      <div className="flex-1" />
      <button className="p-2 rounded-md hover:bg-[#F4F4F5] text-[#71717A]" title="Notifications">
        <Bell size={17} />
      </button>
      <div className="flex items-center gap-2">
        <div className="w-7 h-7 rounded-full bg-[#111111] text-white flex items-center justify-center text-xs font-medium">
          {(user?.username || 'U')[0].toUpperCase()}
        </div>
        <button
          onClick={() => { logout(); navigate('/login') }}
          className="p-2 rounded-md hover:bg-[#F4F4F5] text-[#71717A]"
          title="Sign out"
        >
          <LogOut size={16} />
        </button>
      </div>
    </header>
  )
}

export default function AppLayout() {
  const [collapsed, setCollapsed] = useState(false)
  return (
    <div className="min-h-screen bg-[#F7F7F8]">
      <Sidebar collapsed={collapsed} onToggle={() => setCollapsed(!collapsed)} />
      <div className={clsx('transition-all duration-200', collapsed ? 'ml-14' : 'ml-60')}>
        <Topbar />
        <main className="p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
