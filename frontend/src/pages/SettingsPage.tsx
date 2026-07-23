import { useMutation, useQueryClient } from '@tanstack/react-query'
import {
  BookOpen,
  CalendarDays,
  Check,
  Crown,
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
import { useBillingProducts, usePrivacyPolicy, useUsageSummary } from '../hooks/useUserCenter'
import { api, ApiError } from '../lib/api'
import { formatMoney } from '../lib/billing'
import { SUPPORT_EMAIL, supportMailto } from '../lib/support'
import type { BillingProduct, UsageSummaryResponse } from '../types/api'

const ACCOUNT_DELETION_CONFIRMATION = 'DELETE MY ACCOUNT'

export function SettingsPage() {
  const currentUser = useCurrentUser()
  const dashboard = useDashboard()
  const usage = useUsageSummary()
  const products = useBillingProducts()
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
  const aiPercentage = aiUsage?.limit ? Math.round((aiUsage.used / aiUsage.limit) * 100) : 0
  const productsByCode = new Map(products.data?.products.map((product) => [product.product_code, product]) ?? [])
  const entitlements = usage.data?.course_entitlements ?? []
  const activeEntitlements = entitlements.filter(isActiveEntitlement)
  const hasActiveEntitlement = activeEntitlements.length > 0
  const sortedEntitlements = [...entitlements].sort(
    (left, right) => Number(isActiveEntitlement(right)) - Number(isActiveEntitlement(left)),
  )

  return (
    <section className="max-w-5xl">
      <div>
        <p className="text-sm font-semibold text-blue-600">用户中心</p>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight text-slate-950">账号与使用情况</h1>
        <p className="mt-2 text-sm text-slate-500">查看当前套餐、额度与账号设置。</p>
      </div>

      {entitlements.length ? (
        <div className="mt-8">
          <div className={hasActiveEntitlement ? 'rounded-3xl border border-emerald-100 bg-emerald-50/50 p-4 sm:p-6' : ''}>
            <div className="flex flex-wrap items-end justify-between gap-3">
              <div>
                <div className="flex items-center gap-2 text-sm font-semibold text-emerald-700">
                  <Crown className="size-4" />
                  {hasActiveEntitlement ? '付费权益' : '权益记录'}
                </div>
                <h2 className={`${hasActiveEntitlement ? 'mt-2 text-2xl sm:text-3xl' : 'mt-2 text-xl'} font-semibold tracking-tight text-stone-950`}>
                  {hasActiveEntitlement ? '已开通课程权益' : '课程权益记录'}
                </h2>
                {hasActiveEntitlement ? (
                  <p className="mt-2 text-sm text-stone-600">你购买的课程空间、有效期和剩余额度都在这里。</p>
                ) : null}
              </div>
              {hasActiveEntitlement ? (
                <span className="rounded-full bg-white px-3 py-1.5 text-xs font-semibold text-emerald-700 shadow-sm">
                  {activeEntitlements.length} 个权益使用中
                </span>
              ) : null}
            </div>
            <div className={`mt-4 grid gap-4 ${hasActiveEntitlement ? 'lg:grid-cols-2' : 'md:grid-cols-2'}`}>
              {sortedEntitlements.map((item) => (
                <EntitlementCard
                  item={item}
                  product={productsByCode.get(item.product_code)}
                  featured={isActiveEntitlement(item)}
                  key={item.id}
                />
              ))}
            </div>
          </div>
        </div>
      ) : null}

      <div className={`mt-8 grid items-start gap-4 ${hasActiveEntitlement ? 'lg:grid-cols-[0.72fr_1.28fr]' : 'lg:grid-cols-[1.1fr_0.9fr]'}`}>
        <Card className={`overflow-hidden ${hasActiveEntitlement ? 'border-slate-200 bg-slate-50/50 shadow-none' : ''}`}>
          <div className={`border-b border-slate-100 ${hasActiveEntitlement ? 'p-4 sm:p-5' : 'p-5 sm:p-6'}`}>
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <div className={`flex items-center gap-2 text-sm font-semibold ${hasActiveEntitlement ? 'text-slate-500' : 'text-blue-600'}`}>
                  <Sparkles className="size-4" /> 免费使用额度
                </div>
                <div className={`${hasActiveEntitlement ? 'mt-2' : 'mt-3'} flex items-center gap-3`}>
                  <h2 className={`${hasActiveEntitlement ? 'text-xl' : 'text-3xl'} font-semibold tracking-tight text-slate-950`}>
                    每月 AI 额度
                  </h2>
                  <span className="rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-semibold text-emerald-700">
                    <Check className="mr-1 inline size-3" />使用中
                  </span>
                </div>
                <p className={`mt-2 text-sm text-slate-500 ${hasActiveEntitlement ? 'max-w-sm' : ''}`}>
                  {hasActiveEntitlement ? '免费额度会继续保留，可作为课程权益之外的补充。' : '剩余次数与重置时间均由服务器实时返回。'}
                </p>
              </div>
              <span className={`grid place-items-center rounded-2xl ${hasActiveEntitlement ? 'size-10 bg-white text-slate-500' : 'size-12 bg-blue-50 text-blue-600'}`}>
                <Gauge className={hasActiveEntitlement ? 'size-5' : 'size-6'} />
              </span>
            </div>
          </div>

          {hasActiveEntitlement ? (
            <div className="p-4 sm:p-5">
              <div className="flex items-end justify-between gap-4">
                <div>
                  <p className="text-xs font-medium text-slate-500">本月剩余</p>
                  <strong className="mt-1 block text-2xl font-semibold text-slate-900">
                    {aiUsage ? `${aiUsage.remaining} / ${aiUsage.limit}` : '—'}
                  </strong>
                </div>
                <p className="text-right text-xs leading-5 text-slate-400">
                  {aiUsage ? `${formatResetDate(aiUsage.resets_at)} 重置` : '正在读取本月用量'}
                </p>
              </div>
              <div className="mt-4">
                <ProgressBar value={aiPercentage} label="免费额度使用率" />
              </div>
              <Link className="mt-3 inline-flex text-sm font-semibold text-slate-600 hover:text-blue-700" to="/pricing">
                查看其他套餐
              </Link>
              {dashboard.isError || usage.isError || products.isError ? (
                <UsageLoadError onRetry={() => Promise.all([dashboard.refetch(), usage.refetch(), products.refetch()])} />
              ) : null}
            </div>
          ) : (
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
                <Link className="mt-4 inline-flex min-h-10 items-center justify-center rounded-xl bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700" to="/pricing">购买更多额度</Link>
                {dashboard.isError || usage.isError || products.isError ? (
                  <UsageLoadError onRetry={() => Promise.all([dashboard.refetch(), usage.refetch(), products.refetch()])} />
                ) : null}
              </div>
            </div>
          )}
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

function EntitlementCard({
  item,
  product,
  featured,
}: {
  item: UsageSummaryResponse['course_entitlements'][number]
  product?: BillingProduct
  featured: boolean
}) {
  const price = formatMoney(
    product?.amount_cents ?? item.amount_cents,
    product?.currency ?? 'CNY',
  )
  const expiry = new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  }).format(new Date(item.expires_at))

  return (
    <Card className={featured ? 'overflow-hidden border-emerald-200 bg-white shadow-sm' : 'p-5 opacity-75'}>
      <div className={featured ? 'border-b border-emerald-100 bg-gradient-to-r from-emerald-50/80 to-white p-5 sm:p-6' : ''}>
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className={`text-xs font-semibold ${featured ? 'text-emerald-700' : 'text-stone-500'}`}>
              {product?.name ?? item.product_code}
            </p>
            <h3 className={`${featured ? 'mt-2 text-xl sm:text-2xl' : 'mt-1 font-semibold'} text-stone-950`}>
              {item.course_name}
            </h3>
          </div>
          <span className={`shrink-0 rounded-full px-2.5 py-1 text-xs font-semibold ${featured ? 'bg-emerald-100 text-emerald-800' : 'bg-stone-100 text-stone-600'}`}>
            {featured ? '权益使用中' : item.status === 'active' ? '已过期' : item.status}
          </span>
        </div>
        <div className={`mt-4 flex flex-wrap gap-x-5 gap-y-2 ${featured ? 'text-sm' : 'text-xs'} text-stone-600`}>
          <span className="font-semibold text-stone-900">{price}</span>
          <span className="inline-flex items-center gap-1.5">
            <CalendarDays className="size-4 text-emerald-600" />
            有效期至 {expiry}
          </span>
        </div>
      </div>
      <div className={featured ? 'p-5 sm:p-6' : 'mt-4'}>
        {featured ? <p className="text-sm font-semibold text-stone-900">剩余权益</p> : null}
        <div className={`grid grid-cols-2 ${featured ? 'mt-3 gap-3' : 'gap-2'} text-stone-600`}>
          <AllowanceMetric label="跟课整理" remaining={item.follow_remaining} total={product?.follow_allowance} featured={featured} />
          <AllowanceMetric label="教材分析" remaining={item.textbook_remaining} total={product?.textbook_allowance} featured={featured} />
          <AllowanceMetric label="考试冲刺" remaining={item.exam_remaining} total={product?.exam_allowance} featured={featured} />
          <AllowanceMetric label="课程助手" remaining={item.assistant_remaining} total={product?.assistant_allowance} featured={featured} />
        </div>
      </div>
    </Card>
  )
}

function AllowanceMetric({
  label,
  remaining,
  total,
  featured,
}: {
  label: string
  remaining: number
  total?: number
  featured: boolean
}) {
  if (!featured) {
    return <span className="text-xs">{label} {formatAllowance(remaining, total)}</span>
  }
  return (
    <div className="rounded-2xl border border-stone-100 bg-stone-50/80 p-3">
      <p className="text-xs text-stone-500">{label}</p>
      <strong className="mt-1 block text-lg font-semibold text-stone-950">{remaining}</strong>
      <p className="mt-0.5 text-[11px] text-stone-400">{total == null ? '次可用' : `共 ${total} 次`}</p>
    </div>
  )
}

function UsageLoadError({ onRetry }: { onRetry: () => Promise<unknown> }) {
  return (
    <div className="mt-4 flex flex-wrap items-center gap-3 rounded-xl bg-orange-50 px-3 py-2.5 text-sm text-orange-700">
      使用情况暂时无法读取。
      <button className="font-semibold underline underline-offset-2" onClick={() => void onRetry()}>
        重新加载
      </button>
    </div>
  )
}

function isActiveEntitlement(item: UsageSummaryResponse['course_entitlements'][number]) {
  return item.status === 'active' && new Date(item.expires_at).getTime() >= Date.now()
}

function formatAllowance(remaining: number, total?: number) {
  return total == null ? `剩余 ${remaining}` : `${remaining} / ${total}`
}

function formatResetDate(value: string) {
  return new Intl.DateTimeFormat('zh-CN', { month: 'long', day: 'numeric' }).format(new Date(value))
}
