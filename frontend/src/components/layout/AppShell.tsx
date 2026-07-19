import { useState } from 'react'
import { Outlet } from 'react-router-dom'

import { useCurrentUser } from '../../hooks/useCurrentUser'
import { MobileNavigation } from './MobileNavigation'
import { Sidebar } from './Sidebar'
import { Topbar } from './Topbar'

export function AppShell() {
  const [navigationOpen, setNavigationOpen] = useState(false)
  const currentUser = useCurrentUser()
  const email = currentUser.data?.user.email ?? ''

  return (
    <div className="min-h-screen bg-[#f7f6f2] text-stone-950">
      <div className="fixed inset-y-0 left-0 hidden lg:block">
        <Sidebar />
      </div>
      <MobileNavigation open={navigationOpen} onClose={() => setNavigationOpen(false)} />
      <div className="lg:pl-64">
        <Topbar email={email} onOpenNavigation={() => setNavigationOpen(true)} />
        <main className="mx-auto w-full max-w-[1600px] p-4 sm:p-6 lg:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
