import { useQuery, useQueryClient } from '@tanstack/react-query'
import { CheckCircle2, Clipboard, LoaderCircle, RefreshCw } from 'lucide-react'
import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { usageQueryKey } from '../hooks/useUserCenter'
import { api, ApiError } from '../lib/api'
import { formatMoney } from '../lib/billing'
import { SUPPORT_EMAIL } from '../lib/support'

export function PurchasePage() {
  const { orderNo = '' } = useParams()
  const queryClient = useQueryClient()
  const [copyState, setCopyState] = useState<'idle' | 'success' | 'error'>('idle')
  const support = (import.meta.env.VITE_SUPPORT_CONTACT as string | undefined) || SUPPORT_EMAIL
  const order = useQuery({
    queryKey: ['billing', 'orders', orderNo],
    queryFn: () => api.paymentOrder(orderNo),
    enabled: Boolean(orderNo),
    refetchInterval: (query) => query.state.data?.status === 'pending' ? 15_000 : false,
  })
  const course = useQuery({
    queryKey: ['courses', order.data?.course_id],
    queryFn: () => api.course(order.data!.course_id),
    enabled: Boolean(order.data?.course_id),
  })

  async function refreshStatus() {
    const result = await order.refetch()
    if (result.data?.status === 'paid') {
      await queryClient.invalidateQueries({ queryKey: usageQueryKey })
    }
  }

  async function copyPurchaseInformation() {
    if (!order.data) return
    const text = [
      'Learning OS 购买申请',
      `订单号：${order.data.order_no}`,
      `课程：${course.data?.name ?? `课程 #${order.data.course_id}`}`,
      `产品：${order.data.product_snapshot.name}`,
      `金额：${formatMoney(order.data.amount_cents, order.data.currency)}`,
      `联系方式：${support}`,
    ].join('\n')
    try {
      await copyText(text)
      setCopyState('success')
    } catch {
      setCopyState('error')
    }
  }

  if (order.isPending) {
    return <Card className="mx-auto flex max-w-2xl items-center justify-center gap-2 p-10 text-sm text-stone-500"><LoaderCircle className="size-4 animate-spin" />正在读取购买申请</Card>
  }
  if (order.isError || !order.data) {
    return (
      <Card className="mx-auto max-w-2xl p-7">
        <h1 className="text-xl font-semibold text-stone-950">购买申请暂时无法读取</h1>
        <p className="mt-2 text-sm text-red-700">{order.error instanceof ApiError ? order.error.message : '请稍后重新加载。'}</p>
        <Button className="mt-5" variant="secondary" onClick={() => order.refetch()}>重新加载</Button>
      </Card>
    )
  }

  const data = order.data
  const paid = data.status === 'paid'
  return (
    <section className="mx-auto max-w-2xl">
      <p className="text-sm font-medium text-teal-700">购买申请</p>
      <h1 className="mt-2 text-3xl font-semibold text-stone-950">{paid ? '课程权益已经开通' : '购买申请已生成'}</h1>
      <p className="mt-3 text-sm leading-6 text-stone-500">
        {paid ? '额度已更新，现在可以返回课程继续使用 AI 功能。' : '请复制下方信息联系人工客服完成付款，确认后系统会激活课程权益。'}
      </p>

      <Card className="mt-7 overflow-hidden">
        <div className={`p-5 ${paid ? 'bg-emerald-50' : 'bg-amber-50'}`}>
          <div className={`flex items-center gap-2 font-semibold ${paid ? 'text-emerald-800' : 'text-amber-900'}`}>
            {paid ? <CheckCircle2 className="size-5" /> : <LoaderCircle className="size-5" />}
            {paid ? '已人工确认并开通' : data.status === 'cancelled' ? '购买申请已取消' : '等待人工确认'}
          </div>
        </div>
        <dl className="grid gap-4 p-6 text-sm sm:grid-cols-[7rem_1fr]">
          <dt className="text-stone-500">订单号</dt><dd className="break-all font-medium text-stone-900">{data.order_no}</dd>
          <dt className="text-stone-500">课程</dt><dd className="font-medium text-stone-900">{course.data?.name ?? `课程 #${data.course_id}`}</dd>
          <dt className="text-stone-500">产品</dt><dd className="font-medium text-stone-900">{data.product_snapshot.name}</dd>
          <dt className="text-stone-500">金额</dt><dd className="font-medium text-stone-900">{formatMoney(data.amount_cents, data.currency)}</dd>
          <dt className="text-stone-500">联系方式</dt><dd className="font-medium text-stone-900">{support}</dd>
        </dl>
      </Card>

      {copyState === 'success' ? <p className="mt-3 text-sm text-emerald-700">购买信息已复制。</p> : null}
      {copyState === 'error' ? <p className="mt-3 text-sm text-red-700">复制失败，请手动复制订单号和联系方式。</p> : null}
      <div className="mt-5 flex flex-wrap gap-3">
        {!paid && data.status === 'pending' ? <Button onClick={copyPurchaseInformation}><Clipboard className="size-4" />复制购买信息</Button> : null}
        <Button variant="secondary" disabled={order.isFetching} onClick={refreshStatus}>
          <RefreshCw className={`size-4 ${order.isFetching ? 'animate-spin' : ''}`} />刷新订单状态
        </Button>
        <Link className="inline-flex min-h-10 items-center justify-center rounded-xl border border-stone-200 bg-white px-4 py-2 text-sm font-semibold text-stone-700 hover:bg-stone-50" to={`/courses/${data.course_id}/follow`}>返回课程</Link>
      </div>
    </section>
  )
}

async function copyText(text: string) {
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(text)
    return
  }
  const textarea = document.createElement('textarea')
  textarea.value = text
  textarea.style.position = 'fixed'
  textarea.style.opacity = '0'
  document.body.appendChild(textarea)
  textarea.select()
  const copied = document.execCommand('copy')
  textarea.remove()
  if (!copied) throw new Error('Copy failed.')
}
