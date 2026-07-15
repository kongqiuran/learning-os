import { AlertCircle, Inbox, LoaderCircle } from 'lucide-react'
import type { ReactNode } from 'react'

type StateVariant = 'empty' | 'loading' | 'error'

interface StatePanelProps {
  variant: StateVariant
  title: string
  description?: string
  action?: ReactNode
}

const icons = {
  empty: Inbox,
  loading: LoaderCircle,
  error: AlertCircle,
}

export function StatePanel({ variant, title, description, action }: StatePanelProps) {
  const Icon = icons[variant]

  return (
    <div className="flex min-h-56 flex-col items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-white px-6 py-10 text-center">
      <span className="mb-4 grid size-11 place-items-center rounded-xl bg-slate-100 text-slate-500">
        <Icon className={variant === 'loading' ? 'size-5 animate-spin' : 'size-5'} />
      </span>
      <h2 className="text-base font-semibold text-slate-900">{title}</h2>
      {description ? <p className="mt-2 max-w-md text-sm leading-6 text-slate-500">{description}</p> : null}
      {action ? <div className="mt-5">{action}</div> : null}
    </div>
  )
}
