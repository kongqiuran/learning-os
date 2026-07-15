import { useMutation, useQueryClient } from '@tanstack/react-query'
import { LogOut, Sparkles } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { currentUserQueryKey, useCurrentUser } from '../hooks/useCurrentUser'
import { api } from '../lib/api'

export function SettingsPage() {
  const currentUser = useCurrentUser()
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const logout = useMutation({
    mutationFn: api.logout,
    onSuccess: () => {
      queryClient.removeQueries({ queryKey: currentUserQueryKey })
      navigate('/login', { replace: true })
    },
  })

  return (
    <section className="max-w-3xl">
      <p className="text-sm font-semibold text-blue-600">Settings</p>
      <h1 className="mt-2 text-3xl font-semibold tracking-tight text-slate-950">设置</h1>
      <div className="mt-8 space-y-4">
        <Card className="p-5">
          <h2 className="font-semibold text-slate-900">账号</h2>
          <p className="mt-2 text-sm text-slate-500">{currentUser.data?.user.email}</p>
          <Button className="mt-5" variant="secondary" onClick={() => logout.mutate()} disabled={logout.isPending}>
            <LogOut className="size-4" /> {logout.isPending ? '正在退出…' : '退出登录'}
          </Button>
        </Card>
        <Card className="border-blue-100 bg-blue-50 p-5">
          <div className="flex items-center gap-2 font-semibold text-blue-950"><Sparkles className="size-4" />升级 Learning OS</div>
          <p className="mt-2 text-sm leading-6 text-blue-700">商业版本入口已经预留，具体套餐将在首批体验计划确定后开放。</p>
          <Button className="mt-5" variant="secondary" onClick={() => window.alert('升级方案即将开放。')}>查看升级方案</Button>
        </Card>
      </div>
    </section>
  )
}
