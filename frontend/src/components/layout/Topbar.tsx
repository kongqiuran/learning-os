import { Menu, Search } from 'lucide-react'

interface TopbarProps {
  email: string
  onOpenNavigation: () => void
}

export function Topbar({ email, onOpenNavigation }: TopbarProps) {
  return (
    <header className="flex h-16 items-center justify-between border-b border-slate-200 bg-white px-4 sm:px-6 lg:px-8">
      <div className="flex items-center gap-3">
        <button
          className="grid size-10 place-items-center rounded-xl text-slate-600 hover:bg-slate-100 lg:hidden"
          onClick={onOpenNavigation}
          aria-label="打开导航"
        >
          <Menu className="size-5" />
        </button>
        <div className="hidden items-center gap-2 text-sm text-slate-400 sm:flex">
          <Search className="size-4" />
          <span>搜索课程与知识</span>
          <span className="rounded-md border border-slate-200 bg-slate-50 px-2 py-0.5 text-xs">即将开放</span>
        </div>
      </div>
      <div className="flex items-center gap-3">
        <span className="hidden text-sm text-slate-500 sm:block">{email}</span>
        <span className="grid size-9 place-items-center rounded-full bg-slate-900 text-sm font-semibold text-white">
          {email.slice(0, 1).toUpperCase()}
        </span>
      </div>
    </header>
  )
}
