import { Navigate, Outlet, useLocation } from 'react-router-dom'

import { usePrivacyConsentStatus } from '../../hooks/useUserCenter'
import { useCurrentUser } from '../../hooks/useCurrentUser'
import { PrivacyReconsentPage } from '../privacy/PrivacyReconsentPage'
import { StatePanel } from '../ui/StatePanel'

export function ProtectedRoute() {
  const location = useLocation()
  const currentUser = useCurrentUser()
  const consentStatus = usePrivacyConsentStatus(currentUser.isSuccess)

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

  if (consentStatus.isPending) {
    return (
      <main className="grid min-h-screen place-items-center bg-slate-50 p-6">
        <StatePanel variant="loading" title="正在检查隐私协议版本" />
      </main>
    )
  }

  if (consentStatus.isError) {
    return (
      <main className="grid min-h-screen place-items-center bg-slate-50 p-6">
        <StatePanel
          variant="error"
          title="暂时无法确认隐私协议状态"
          description="请检查网络连接后重试。"
          action={<button className="text-sm font-semibold text-blue-600" onClick={() => consentStatus.refetch()}>重新检查</button>}
        />
      </main>
    )
  }

  if (consentStatus.data.requires_reconsent) {
    return <PrivacyReconsentPage currentVersion={consentStatus.data.current_version} />
  }

  return <Outlet />
}
