import { BookOpen, CircleUserRound, CreditCard, FlaskConical, LayoutDashboard } from 'lucide-react'
import { NavLink, useNavigate } from 'react-router-dom'

import { Button } from '../ui/Button'

const navigation = [
  { to: '/dashboard', label: '我的课程', icon: LayoutDashboard },
  { to: '/settings', label: '用户中心', icon: CircleUserRound },
]

interface SidebarProps {
  onNavigate?: () => void
}

export function Sidebar({ onNavigate }: SidebarProps) {
  const navigate = useNavigate()
  function handleUpgrade() {
    navigate('/pricing')
  }

  return (
    <aside className="flex h-full w-64 flex-col border-r border-stone-200 bg-[#fffdfa] px-4 py-5">
      <button
        className="flex items-center gap-3 rounded-xl px-2 text-left focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-blue-100"
        onClick={() => {
          navigate('/dashboard')
          onNavigate?.()
        }}
      >
        <span className="grid size-9 place-items-center rounded-xl bg-teal-700 text-white">
          <BookOpen className="size-5" />
        </span>
        <span>
          <strong className="block text-sm font-bold text-slate-950">Learning OS</strong>
          <small className="text-xs text-slate-400">AI 学习空间</small>
        </span>
      </button>

      <nav className="mt-8 space-y-1" aria-label="主导航">
        {navigation.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            onClick={onNavigate}
            className={({ isActive }) =>
              `flex min-h-10 items-center gap-3 rounded-xl px-3 text-sm font-medium transition-colors ${
                isActive ? 'bg-blue-50 text-blue-700' : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
              }`
            }
          >
            <Icon className="size-4" /> {label}
          </NavLink>
        ))}
      </nav>

      <div className="mt-auto space-y-3">
        <NavLink
          to="/demo"
          onClick={onNavigate}
          className="flex min-h-10 items-center gap-3 rounded-xl px-3 text-sm font-medium text-slate-600 transition-colors hover:bg-violet-50 hover:text-violet-700"
        >
          <FlaskConical className="size-4" /> 体验 Demo
        </NavLink>
        <div className="rounded-2xl border border-blue-100 bg-blue-50 p-4">
          <div className="flex items-center gap-2 text-sm font-semibold text-blue-950">
            <CreditCard className="size-4" /> 升级学习空间
          </div>
          <p className="mt-2 text-xs leading-5 text-blue-700">为更多课程和学习能力预留。</p>
          <Button className="mt-3" variant="secondary" fullWidth onClick={handleUpgrade}>
            查看升级方案
          </Button>
        </div>
      </div>
    </aside>
  )
}
