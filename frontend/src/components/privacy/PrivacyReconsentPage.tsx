import { FileText, ShieldCheck } from 'lucide-react'
import { Link } from 'react-router-dom'

import { useAcceptPrivacyConsent } from '../../hooks/useUserCenter'
import { ApiError } from '../../lib/api'
import { Button } from '../ui/Button'
import { Card } from '../ui/Card'

export function PrivacyReconsentPage({ currentVersion }: { currentVersion: string }) {
  const consent = useAcceptPrivacyConsent()

  return (
    <main className="grid min-h-screen place-items-center bg-slate-50 p-5 sm:p-8">
      <Card className="w-full max-w-xl p-6 sm:p-8">
        <span className="grid size-12 place-items-center rounded-2xl bg-blue-50 text-blue-600">
          <ShieldCheck className="size-6" />
        </span>
        <p className="mt-6 text-sm font-semibold text-blue-600">协议版本更新</p>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight text-slate-950">隐私政策已更新</h1>
        <p className="mt-3 text-sm leading-6 text-slate-500">
          为继续使用 Learning OS，请阅读并同意最新版本的隐私政策和用户协议。
        </p>

        <div className="mt-5 rounded-2xl border border-slate-100 bg-slate-50 p-4">
          <p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">当前版本</p>
          <p className="mt-1 font-semibold text-slate-900">{currentVersion}</p>
        </div>

        <div className="mt-5 flex flex-wrap gap-3">
          <Link className="inline-flex items-center gap-2 text-sm font-semibold text-blue-600 hover:text-blue-700" to="/legal/privacy">
            <FileText className="size-4" /> 查看隐私政策
          </Link>
          <Link className="inline-flex items-center gap-2 text-sm font-semibold text-blue-600 hover:text-blue-700" to="/legal/terms">
            <FileText className="size-4" /> 查看用户协议
          </Link>
        </div>

        {consent.isError ? (
          <p className="mt-5 rounded-xl bg-orange-50 px-3 py-2.5 text-sm text-orange-700">
            {consent.error instanceof ApiError ? consent.error.message : '授权提交失败，请稍后重试。'}
          </p>
        ) : null}

        <Button className="mt-7" fullWidth onClick={() => consent.mutate()} disabled={consent.isPending}>
          {consent.isPending ? '正在提交…' : '同意并继续使用'}
        </Button>
        <p className="mt-3 text-center text-xs leading-5 text-slate-400">
          点击按钮即表示你已阅读并同意当前版本的两份法律文件。
        </p>
      </Card>
    </main>
  )
}
