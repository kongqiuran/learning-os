import { X } from 'lucide-react'

import { Sidebar } from './Sidebar'

interface MobileNavigationProps {
  open: boolean
  onClose: () => void
}

export function MobileNavigation({ open, onClose }: MobileNavigationProps) {
  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 lg:hidden">
      <button className="absolute inset-0 bg-slate-950/30" onClick={onClose} aria-label="关闭导航遮罩" />
      <div className="relative h-full w-64 shadow-xl">
        <button
          className="absolute right-3 top-3 z-10 grid size-8 place-items-center rounded-lg text-slate-500 hover:bg-slate-100"
          onClick={onClose}
          aria-label="关闭导航"
        >
          <X className="size-4" />
        </button>
        <Sidebar onNavigate={onClose} />
      </div>
    </div>
  )
}
