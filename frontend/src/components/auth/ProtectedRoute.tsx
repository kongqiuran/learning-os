import { Navigate, Outlet, useLocation } from 'react-router-dom'

import { useCurrentUser } from '../../hooks/useCurrentUser'
import { StatePanel } from '../ui/StatePanel'

export function ProtectedRoute() {
  const location = useLocation()
  const currentUser = useCurrentUser()

  if (currentUser.isPending) {
    return (
      <main className="grid min-h-screen place-items-center bg-slate-50 p-6">
        <StatePanel variant="loading" title="正在打开你的学习空间" />
      </main>
    )
  }

  if (currentUser.isError) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }

  return <Outlet />
}
