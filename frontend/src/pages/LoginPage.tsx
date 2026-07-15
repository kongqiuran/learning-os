import { useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowRight, BookOpen } from 'lucide-react'
import { useState, type FormEvent, type ReactNode } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'

import { Button } from '../components/ui/Button'
import { currentUserQueryKey } from '../hooks/useCurrentUser'
import { api, ApiError } from '../lib/api'

export function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const navigate = useNavigate()
  const location = useLocation()
  const queryClient = useQueryClient()
  const destination = (location.state as { from?: string } | null)?.from ?? '/dashboard'
  const login = useMutation({
    mutationFn: () => api.login(email, password),
    onSuccess: (data) => {
      queryClient.setQueryData(currentUserQueryKey, data)
      navigate(destination, { replace: true })
    },
  })

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    login.mutate()
  }

  return (
    <AuthLayout title="欢迎回到学习空间" subtitle="继续整理、理解和积累你的课程知识。">
      <form className="space-y-4" onSubmit={handleSubmit}>
        <Field label="邮箱" type="email" value={email} onChange={setEmail} autoComplete="email" />
        <Field label="密码" type="password" value={password} onChange={setPassword} autoComplete="current-password" />
        {login.isError ? <FormError error={login.error} /> : null}
        <Button fullWidth type="submit" disabled={login.isPending}>
          {login.isPending ? '正在登录…' : '进入 Learning OS'} <ArrowRight className="size-4" />
        </Button>
      </form>
      <p className="mt-6 text-center text-sm text-slate-500">
        还没有账号？ <Link className="font-semibold text-blue-600 hover:text-blue-700" to="/register">创建账号</Link>
      </p>
      <Link className="mt-3 block text-center text-sm font-medium text-violet-600 hover:text-violet-700" to="/demo">
        先查看公开 Demo
      </Link>
    </AuthLayout>
  )
}

export function AuthLayout({ title, subtitle, children }: { title: string; subtitle: string; children: ReactNode }) {
  return (
    <main className="grid min-h-screen bg-slate-50 lg:grid-cols-[1.1fr_0.9fr]">
      <section className="hidden bg-slate-950 p-12 text-white lg:flex lg:flex-col lg:justify-between">
        <Link className="flex items-center gap-3" to="/demo">
          <span className="grid size-10 place-items-center rounded-xl bg-blue-600"><BookOpen className="size-5" /></span>
          <span className="text-lg font-bold">Learning OS</span>
        </Link>
        <div className="max-w-xl">
          <span className="text-sm font-semibold text-blue-300">你的 AI 学习空间</span>
          <h1 className="mt-5 text-5xl font-semibold leading-tight tracking-tight">把课程资料，变成可以持续使用的学习资产。</h1>
          <p className="mt-6 max-w-lg text-base leading-7 text-slate-300">从资料整理、知识理解到复习辅助，让每一门课程拥有清晰的学习空间。</p>
        </div>
        <p className="text-xs text-slate-500">Learning OS · Built for university learning</p>
      </section>
      <section className="flex items-center justify-center p-5 sm:p-10">
        <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-6 shadow-[0_8px_30px_rgba(15,23,42,0.06)] sm:p-8">
          <div className="mb-7 lg:hidden"><strong className="text-lg text-slate-950">Learning OS</strong></div>
          <h2 className="text-2xl font-semibold tracking-tight text-slate-950">{title}</h2>
          <p className="mt-2 text-sm leading-6 text-slate-500">{subtitle}</p>
          <div className="mt-7">{children}</div>
        </div>
      </section>
    </main>
  )
}

function Field({ label, type, value, onChange, autoComplete }: { label: string; type: string; value: string; onChange: (value: string) => void; autoComplete: string }) {
  return (
    <label className="block text-sm font-medium text-slate-700">
      {label}
      <input
        className="mt-2 h-11 w-full rounded-xl border border-slate-200 bg-white px-3 text-slate-950 outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
        type={type}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        autoComplete={autoComplete}
        required
      />
    </label>
  )
}

function FormError({ error }: { error: Error }) {
  const message = error instanceof ApiError ? error.message : '请求失败，请稍后重试。'
  return <p className="rounded-xl bg-orange-50 px-3 py-2.5 text-sm text-orange-700">{message}</p>
}
