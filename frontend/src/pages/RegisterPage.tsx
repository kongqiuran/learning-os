import { useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowRight } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { Button } from '../components/ui/Button'
import { currentUserQueryKey } from '../hooks/useCurrentUser'
import { api, ApiError } from '../lib/api'
import { AuthLayout } from './LoginPage'

export function RegisterPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const register = useMutation({
    mutationFn: () => api.register(email, password, confirmPassword),
    onSuccess: (data) => {
      queryClient.setQueryData(currentUserQueryKey, data)
      navigate('/dashboard', { replace: true })
    },
  })

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    if (password !== confirmPassword) return
    register.mutate()
  }

  const mismatch = confirmPassword.length > 0 && password !== confirmPassword

  return (
    <AuthLayout title="创建你的学习空间" subtitle="从第一门课程开始，积累自己的学习资产。">
      <form className="space-y-4" onSubmit={handleSubmit}>
        <Input label="邮箱" type="email" value={email} onChange={setEmail} autoComplete="email" />
        <Input label="密码" type="password" value={password} onChange={setPassword} autoComplete="new-password" />
        <Input label="确认密码" type="password" value={confirmPassword} onChange={setConfirmPassword} autoComplete="new-password" />
        {mismatch ? <p className="text-sm text-orange-700">两次输入的密码不一致。</p> : null}
        {register.isError ? <p className="rounded-xl bg-orange-50 px-3 py-2.5 text-sm text-orange-700">{register.error instanceof ApiError ? register.error.message : '注册失败，请稍后重试。'}</p> : null}
        <Button fullWidth type="submit" disabled={register.isPending || mismatch}>
          {register.isPending ? '正在创建…' : '创建学习空间'} <ArrowRight className="size-4" />
        </Button>
      </form>
      <p className="mt-6 text-center text-sm text-slate-500">
        已有账号？ <Link className="font-semibold text-blue-600 hover:text-blue-700" to="/login">返回登录</Link>
      </p>
    </AuthLayout>
  )
}

function Input({ label, type, value, onChange, autoComplete }: { label: string; type: string; value: string; onChange: (value: string) => void; autoComplete: string }) {
  return (
    <label className="block text-sm font-medium text-slate-700">
      {label}
      <input
        className="mt-2 h-11 w-full rounded-xl border border-slate-200 px-3 outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
        type={type}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        autoComplete={autoComplete}
        required
      />
    </label>
  )
}
