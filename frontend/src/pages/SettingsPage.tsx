import { useMutation, useQueryClient } from '@tanstack/react-query'
import {
  BookOpen,
  Check,
  FileText,
  Gauge,
  LogOut,
  ShieldCheck,
  LifeBuoy,
  Sparkles,
  Trash2,
  UserRound,
} from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { ProgressBar } from '../components/ui/ProgressBar'
import { currentUserQueryKey, useCurrentUser } from '../hooks/useCurrentUser'
import { useDashboard } from '../hooks/useDashboard'
import { usePrivacyPolicy, useUsageSummary } from '../hooks/useUserCenter'
import { api, ApiError } from '../lib/api'
import { SUPPORT_EMAIL, supportMailto } from '../lib/support'

const ACCOUNT_DELETION_CONFIRMATION = 'DELETE MY ACCOUNT'

export function SettingsPage() {
  const currentUser = useCurrentUser()
  const dashboard = useDashboard()
  const usage = useUsageSummary()
  const privacyPolicy = usePrivacyPolicy()
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const [deletionOpen, setDeletionOpen] = useState(false)
  const [password, setPassword] = useState('')
  const [confirmation, setConfirmation] = useState('')

  const logout = useMutation({
    mutationFn: api.logout,
    onSuccess: () => finishSession(),
  })
  const deleteAccount = useMutation({
    mutationFn: () => api.deleteAccount(password, confirmation),
    onSuccess: () => finishSession(),
  })

  function finishSession() {
    queryClient.removeQueries({ queryKey: currentUserQueryKey })
    queryClient.clear()
    navigate('/login', { replace: true })
  }

  function handleDeleteAccount(event: FormEvent) {
    event.preventDefault()
    deleteAccount.mutate()
  }

  const aiUsage = usage.data?.ai_generations
  const aiPercentage = aiUsage ? Math.round((aiUsage.used / aiUsage.limit) * 100) : 0

  return (
    <section className="max-w-5xl">
      <div>
        <p className="text-sm font-semibold text-blue-600">用户中心</p>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight text-slate-950">账号与使用情况</h1>
        <p className="mt-2 text-sm text-slate-500">查看当前套餐、额度与账号设置。</p>
      </div>

      {usage.data?.course_entitlements.length ? <div className="mt-8"><h2 className="text-xl font-semibold text-stone-950">已开通课程权益</h2><div className="mt-4 grid gap-4 md:grid-cols-2">{usage.data.course_entitlements.map((item) => <Card className="p-5" key={item.id}><div className="flex items-start justify-between gap-3"><div><h3 className="font-semibold text-stone-900">{item.course_name}</h3><p className="mt-1 text-xs text-stone-500">99 元单课学期版 · 至 {new Intl.DateTimeFormat('zh-CN').format(new Date(item.expires_at))}</p></div><span className="rounded-full bg-emerald-50 px-2 py-1 text-xs text-emerald-700">{item.status === 'active' ? '使用中' : item.status}</span></div><div className="mt-4 grid grid-cols-2 gap-2 text-xs text-stone-600"><span>跟课整理 {item.follow_remaining}/3</span><span>教材解析 {item.textbook_remaining}/3</span><span>考试冲刺 {item.exam_remaining}/3</span><span>课程问答 {item.assistant_remaining}/100</span></div></Card>)}</div></div> : null}

      <div className="mt-8 grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
        <Card className="overflow-hidden">
          <div className="border-b border-slate-100 p-5 sm:p-6">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <div className="flex items-center gap-2 text-sm font-semibold text-blue-600">
                  <Sparkles className="size-4" /> 当前套餐
                </div>
                <div className="mt-3 flex items-center gap-3">
                  <h2 className="text-3xl font-semibold tracking-tight text-slate-950">Free</h2>
                  <span className="rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-semibold text-emerald-700">
                    <Check className="mr-1 inline size-3" />使用中
                  </span>
                </div>
                <p className="mt-2 text-sm text-slate-500">适合整理少量课程资料并体验 AI 学习内容。</p>
              </div>
              <span className="grid size-12 place-items-center rounded-2xl bg-blue-50 text-blue-600">
                <Gauge className="size-6" />
              </span>
            </div>
          </div>

          <div className="grid gap-4 p-5 sm:grid-cols-2 sm:p-6">
            <UsageMetric
              icon={BookOpen}
              label="课程数量"
              value={dashboard.data ? `${dashboard.data.course_count}` : '—'}
              help="当前创建的课程学习空间"
            />
            <UsageMetric
              icon={Sparkles}
              label="AI 整理次数"
              value={aiUsage ? `${aiUsage.used} / ${aiUsage.limit}` : '—'}
              help={aiUsage ? `${formatResetDate(aiUsage.resets_at)} 重置` : '正在读取本月用量'}
            />
            <div className="sm:col-span-2">
              <ProgressBar value={aiPercentage} label="本月 AI 额度使用率" />
              {dashboard.isError || usage.isError ? (
                <div className="mt-4 flex flex-wrap items-center gap-3 rounded-xl bg-orange-50 px-3 py-2.5 text-sm text-orange-700">
                  使用情况暂时无法读取。
                  <button
                    className="font-semibold underline underline-offset-2"
                    onClick={() => Promise.all([dashboard.refetch(), usage.refetch()])}
                  >
                    重新加载
                  </button>
                </div>
              ) : null}
            </div>
          </div>
        </Card>

        <div className="space-y-4">
          <Card className="p-5 sm:p-6">
            <div className="flex items-center gap-3">
              <span className="grid size-10 place-items-center rounded-xl bg-slate-100 text-slate-600">
                <UserRound className="size-5" />
              </span>
              <div>
                <h2 className="font-semibold text-slate-900">账号</h2>
                <p className="mt-0.5 text-sm text-slate-500">{currentUser.data?.user.email ?? '正在加载账号'}</p>
              </div>
            </div>
            <Button className="mt-5" variant="secondary" onClick={() => logout.mutate()} disabled={logout.isPending}>
              <LogOut className="size-4" /> {logout.isPending ? '正在退出…' : '退出登录'}
            </Button>
          </Card>

          <Card className="p-5 sm:p-6">
            <div className="flex items-start gap-3">
              <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-teal-50 text-teal-700"><LifeBuoy className="size-5" /></span>
              <div><h2 className="font-semibold text-slate-900">帮助与反馈</h2><p className="mt-1 text-sm leading-6 text-slate-500">密码找回、退款、权益激活或产品问题均可人工处理。</p></div>
            </div>
            <a className="mt-5 inline-flex min-h-10 items-center justify-center rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50" href={supportMailto('Learning OS 用户反馈')}>联系 {SUPPORT_EMAIL}</a>
          </Card>

          <Card className="p-5 sm:p-6">
            <div className="flex items-start gap-3">
              <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-emerald-50 text-emerald-600">
                <ShieldCheck className="size-5" />
              </span>
              <div>
                <h2 className="font-semibold text-slate-900">隐私与协议</h2>
                <p className="mt-1 text-sm leading-6 text-slate-500">
                  当前版本：{privacyPolicy.data?.policy_version ?? '正在读取'}
                </p>
              </div>
            </div>
            <div className="mt-5 flex flex-wrap gap-3">
              <Link
                className="inline-flex min-h-10 items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition-colors hover:border-slate-300 hover:bg-slate-50"
                to="/legal/privacy"
              >
                <FileText className="size-4" /> 查看隐私政策
              </Link>
              <Link
                className="inline-flex min-h-10 items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition-colors hover:border-slate-300 hover:bg-slate-50"
                to="/legal/terms"
              >
                <FileText className="size-4" /> 查看用户协议
              </Link>
            </div>
          </Card>
        </div>
      </div>

      <Card className="mt-6 border-red-200 p-5 sm:p-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <div className="flex items-center gap-2 font-semibold text-red-700">
              <Trash2 className="size-4" /> 注销账号
            </div>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">
              永久删除账号、课程、资料、AI 分析结果和学习包。操作完成后无法恢复。
            </p>
          </div>
          {!deletionOpen ? (
            <Button variant="secondary" onClick={() => setDeletionOpen(true)}>开始注销</Button>
          ) : null}
        </div>

        {deletionOpen ? (
          <form className="mt-6 max-w-xl rounded-2xl border border-red-100 bg-red-50/60 p-4 sm:p-5" onSubmit={handleDeleteAccount}>
            <p className="text-sm font-semibold text-red-900">确认永久注销</p>
            <p className="mt-2 text-sm leading-6 text-red-700">
              输入当前密码，并完整输入 <code className="rounded bg-white px-1.5 py-0.5 font-mono text-xs">{ACCOUNT_DELETION_CONFIRMATION}</code>。
            </p>
            <label className="mt-4 block text-sm font-medium text-slate-700">
              当前密码
              <input
                className="mt-2 h-11 w-full rounded-xl border border-red-200 bg-white px-3 text-slate-950 outline-none transition focus:border-red-500 focus:ring-4 focus:ring-red-100"
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                autoComplete="current-password"
                required
              />
            </label>
            <label className="mt-4 block text-sm font-medium text-slate-700">
              确认文字
              <input
                className="mt-2 h-11 w-full rounded-xl border border-red-200 bg-white px-3 font-mono text-sm text-slate-950 outline-none transition focus:border-red-500 focus:ring-4 focus:ring-red-100"
                value={confirmation}
                onChange={(event) => setConfirmation(event.target.value)}
                autoComplete="off"
                required
              />
            </label>
            {deleteAccount.isError ? (
              <p className="mt-4 rounded-xl bg-white px-3 py-2.5 text-sm text-red-700">
                {deleteAccount.error instanceof ApiError ? deleteAccount.error.message : '账号注销失败，请稍后重试。'}
              </p>
            ) : null}
            <div className="mt-5 flex flex-wrap gap-3">
              <Button
                variant="danger"
                type="submit"
                disabled={deleteAccount.isPending || !password || confirmation !== ACCOUNT_DELETION_CONFIRMATION}
              >
                <Trash2 className="size-4" /> {deleteAccount.isPending ? '正在永久删除…' : '永久删除账号'}
              </Button>
              <Button
                variant="secondary"
                onClick={() => {
                  setDeletionOpen(false)
                  setPassword('')
                  setConfirmation('')
                  deleteAccount.reset()
                }}
                disabled={deleteAccount.isPending}
              >
                取消
              </Button>
            </div>
          </form>
        ) : null}
      </Card>
    </section>
  )
}

function UsageMetric({ icon: Icon, label, value, help }: { icon: typeof BookOpen; label: string; value: string; help: string }) {
  return (
    <div className="rounded-2xl border border-slate-100 bg-slate-50/70 p-4">
      <div className="flex items-center gap-2 text-sm font-medium text-slate-600">
        <Icon className="size-4 text-blue-600" /> {label}
      </div>
      <strong className="mt-3 block text-2xl font-semibold text-slate-950">{value}</strong>
      <p className="mt-1 text-xs leading-5 text-slate-400">{help}</p>
    </div>
  )
}

function formatResetDate(value: string) {
  return new Intl.DateTimeFormat('zh-CN', { month: 'long', day: 'numeric' }).format(new Date(value))
}
