import clsx from 'clsx'
import type { ReactNode } from 'react'
import { Loader2, Inbox } from 'lucide-react'

export function Card({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <div className={clsx('bg-white border border-[#E5E5E7] rounded-xl', className)}>{children}</div>
  )
}

export function ChartCard({ title, subtitle, children, className, action }: {
  title: string; subtitle?: string; children: ReactNode; className?: string; action?: ReactNode
}) {
  return (
    <Card className={clsx('p-5', className)}>
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-sm font-medium text-[#111111]">{title}</h3>
          {subtitle && <p className="text-xs text-[#71717A] mt-0.5">{subtitle}</p>}
        </div>
        {action}
      </div>
      {children}
    </Card>
  )
}

export function KpiCard({ label, value, hint, unavailable }: {
  label: string; value: string | number | null; hint?: string; unavailable?: boolean
}) {
  return (
    <Card className="p-4">
      <p className="text-xs font-medium text-[#71717A] uppercase tracking-wide">{label}</p>
      {unavailable ? (
        <p className="mt-2 text-lg font-medium text-[#9CA3AF]">—</p>
      ) : (
        <p className="mt-2 text-2xl font-semibold text-[#111111] tabular-nums">{value}</p>
      )}
      {hint && <p className="mt-1 text-xs text-[#9CA3AF]">{hint}</p>}
    </Card>
  )
}

const BADGE_STYLES: Record<string, string> = {
  pending: 'bg-[#FFF0D6] text-[#8A5A00]',
  scheduled: 'bg-[#E4EDFF] text-[#1D4ED8]',
  running: 'bg-[#E4EDFF] text-[#1D4ED8]',
  awaiting_human: 'bg-[#EEE5FF] text-[#6D28D9]',
  approved: 'bg-[#DDF3E4] text-[#166534]',
  executed: 'bg-[#DDF3E4] text-[#166534]',
  completed: 'bg-[#DDF3E4] text-[#166534]',
  done: 'bg-[#DDF3E4] text-[#166534]',
  edited: 'bg-[#DDF3E4] text-[#166534]',
  failed: 'bg-[#FCE4E4] text-[#B91C1C]',
  rejected: 'bg-[#FCE4E4] text-[#B91C1C]',
  cancelled: 'bg-[#F4F4F5] text-[#71717A]',
  expired: 'bg-[#F4F4F5] text-[#71717A]',
  paused: 'bg-[#FFF0D6] text-[#8A5A00]',
  planning: 'bg-[#F4F4F5] text-[#71717A]',
}

export function StatusBadge({ status }: { status: string }) {
  return (
    <span className={clsx(
      'inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium capitalize',
      BADGE_STYLES[status] || 'bg-[#F4F4F5] text-[#71717A]'
    )}>
      {status.replace(/_/g, ' ')}
    </span>
  )
}

export function EmptyState({ title, hint, icon }: { title: string; hint?: string; icon?: ReactNode }) {
  return (
    <div className="flex flex-col items-center justify-center py-10 text-center">
      <div className="text-[#9CA3AF] mb-2">{icon || <Inbox size={28} />}</div>
      <p className="text-sm font-medium text-[#111111]">{title}</p>
      {hint && <p className="text-xs text-[#71717A] mt-1 max-w-xs">{hint}</p>}
    </div>
  )
}

export function Loading({ label = 'Loading…' }: { label?: string }) {
  return (
    <div className="flex items-center justify-center py-10 text-[#71717A] gap-2">
      <Loader2 size={16} className="animate-spin" />
      <span className="text-sm">{label}</span>
    </div>
  )
}

export function ErrorState({ message }: { message?: string }) {
  return (
    <div className="flex items-center justify-center py-10">
      <p className="text-sm text-[#B91C1C]">{message || 'Something went wrong.'}</p>
    </div>
  )
}

export function Btn({ children, onClick, variant = 'primary', disabled, className }: {
  children: ReactNode; onClick?: () => void; variant?: 'primary' | 'secondary' | 'danger'; disabled?: boolean; className?: string
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={clsx(
        'inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors disabled:opacity-50',
        variant === 'primary' && 'bg-[#111111] text-white hover:bg-[#1C1C1E]',
        variant === 'secondary' && 'bg-white border border-[#E5E5E7] text-[#111111] hover:bg-[#F7F7F8]',
        variant === 'danger' && 'bg-white border border-[#FCE4E4] text-[#B91C1C] hover:bg-[#FCE4E4]',
        className
      )}
    >
      {children}
    </button>
  )
}

export function PageHeader({ title, subtitle, actions }: { title: string; subtitle?: string; actions?: ReactNode }) {
  return (
    <div className="flex items-start justify-between mb-6">
      <div>
        <h1 className="text-xl font-semibold text-[#111111]">{title}</h1>
        {subtitle && <p className="text-sm text-[#71717A] mt-1">{subtitle}</p>}
      </div>
      {actions && <div className="flex gap-2">{actions}</div>}
    </div>
  )
}
