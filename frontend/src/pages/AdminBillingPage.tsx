import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { CheckCircle2, LoaderCircle, RefreshCw, XCircle } from 'lucide-react'
import { useState } from 'react'

import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { api, ApiError } from '../lib/api'
import { formatMoney } from '../lib/billing'
import type { AdminPaymentOrder, PaymentOrderStatus } from '../types/api'

type StatusFilter = 'all' | PaymentOrderStatus

const statusOptions: Array<{ value: StatusFilter; label: string }> = [
  { value: 'all', label: '全部' },
  { value: 'pending', label: '待处理' },
  { value: 'paid', label: '已支付' },
  { value: 'cancelled', label: '已取消' },
]

export function AdminBillingPage() {
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('pending')
  const [notes, setNotes] = useState<Record<string, string>>({})
  const queryClient = useQueryClient()
  const orders = useQuery({
    queryKey: ['admin', 'billing', 'orders', statusFilter],
    queryFn: () => api.adminPaymentOrders(statusFilter === 'all' ? undefined : statusFilter),
  })
  const activate = useMutation({
    mutationFn: (orderNo: string) => api.activateAdminPaymentOrder(orderNo, notes[orderNo]),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin', 'billing', 'orders'] }),
  })
  const cancel = useMutation({
    mutationFn: (orderNo: string) => api.cancelAdminPaymentOrder(orderNo, notes[orderNo]),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin', 'billing', 'orders'] }),
  })
  const actionError = activate.error ?? cancel.error

  return (
    <section className="mx-auto max-w-7xl">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-sm font-semibold text-teal-700">运营管理</p>
          <h1 className="mt-2 text-3xl font-semibold text-stone-950">购买订单</h1>
          <p className="mt-2 text-sm text-stone-500">确认人工收款后开通课程权益，或取消无效申请。</p>
        </div>
        <Button variant="secondary" disabled={orders.isFetching} onClick={() => orders.refetch()}>
          <RefreshCw className={`size-4 ${orders.isFetching ? 'animate-spin' : ''}`} />
          刷新订单
        </Button>
      </div>

      <div className="mt-6 flex flex-wrap gap-2">
        {statusOptions.map((option) => (
          <button
            className={`min-h-10 rounded-xl border px-4 text-sm font-semibold transition ${
              statusFilter === option.value
                ? 'border-teal-700 bg-teal-700 text-white'
                : 'border-stone-200 bg-white text-stone-600 hover:border-stone-300'
            }`}
            key={option.value}
            onClick={() => setStatusFilter(option.value)}
          >
            {option.label}
          </button>
        ))}
      </div>

      {orders.isPending ? (
        <Card className="mt-5 flex items-center justify-center gap-2 p-10 text-sm text-stone-500">
          <LoaderCircle className="size-4 animate-spin" /> 正在读取订单
        </Card>
      ) : orders.isError ? (
        <Card className="mt-5 p-6">
          <h2 className="font-semibold text-red-800">订单暂时无法读取</h2>
          <p className="mt-2 text-sm text-red-700">{errorMessage(orders.error)}</p>
          <Button className="mt-4" variant="secondary" onClick={() => orders.refetch()}>重新加载</Button>
        </Card>
      ) : orders.data.orders.length === 0 ? (
        <Card className="mt-5 p-10 text-center">
          <h2 className="font-semibold text-stone-900">当前没有符合条件的订单</h2>
          <p className="mt-2 text-sm text-stone-500">切换状态筛选或稍后刷新查看。</p>
        </Card>
      ) : (
        <Card className="mt-5 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[1050px] text-left text-sm">
              <thead className="border-b border-stone-200 bg-stone-50 text-xs uppercase tracking-wide text-stone-500">
                <tr>
                  <th className="px-5 py-4">订单 / 用户</th>
                  <th className="px-5 py-4">课程 / 产品</th>
                  <th className="px-5 py-4">金额</th>
                  <th className="px-5 py-4">状态</th>
                  <th className="px-5 py-4">创建时间</th>
                  <th className="px-5 py-4">操作</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-stone-100">
                {orders.data.orders.map((order) => (
                  <OrderRow
                    key={order.order_no}
                    order={order}
                    note={notes[order.order_no] ?? ''}
                    busy={(activate.isPending && activate.variables === order.order_no) || (cancel.isPending && cancel.variables === order.order_no)}
                    onNoteChange={(value) => setNotes((current) => ({ ...current, [order.order_no]: value }))}
                    onActivate={() => activate.mutate(order.order_no)}
                    onCancel={() => cancel.mutate(order.order_no)}
                  />
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {actionError ? (
        <p className="mt-4 rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700">{errorMessage(actionError)}</p>
      ) : null}
    </section>
  )
}

function OrderRow({
  order,
  note,
  busy,
  onNoteChange,
  onActivate,
  onCancel,
}: {
  order: AdminPaymentOrder
  note: string
  busy: boolean
  onNoteChange: (value: string) => void
  onActivate: () => void
  onCancel: () => void
}) {
  return (
    <tr className="align-top">
      <td className="px-5 py-5">
        <strong className="block font-medium text-stone-900">{order.order_no}</strong>
        <span className="mt-1 block text-xs text-stone-500">{order.user_email}</span>
      </td>
      <td className="px-5 py-5">
        <strong className="block font-medium text-stone-900">{order.course_name}</strong>
        <span className="mt-1 block text-xs text-stone-500">{order.product_name}</span>
      </td>
      <td className="whitespace-nowrap px-5 py-5 font-medium text-stone-900">
        {formatMoney(order.amount_cents, order.currency)}
      </td>
      <td className="px-5 py-5"><StatusBadge status={order.status} /></td>
      <td className="whitespace-nowrap px-5 py-5 text-stone-600">
        {new Intl.DateTimeFormat('zh-CN', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(order.created_at))}
      </td>
      <td className="px-5 py-5">
        {order.status === 'pending' ? (
          <div className="w-72 space-y-3">
            <input
              className="h-10 w-full rounded-xl border border-stone-200 bg-white px-3 text-sm outline-none focus:border-teal-600 focus:ring-4 focus:ring-teal-100"
              maxLength={1000}
              placeholder="操作备注（可选）"
              value={note}
              onChange={(event) => onNoteChange(event.target.value)}
            />
            <div className="flex gap-2">
              <Button disabled={busy} onClick={onActivate}>
                {busy ? <LoaderCircle className="size-4 animate-spin" /> : <CheckCircle2 className="size-4" />}
                确认付款
              </Button>
              <Button variant="danger" disabled={busy} onClick={onCancel}>
                <XCircle className="size-4" />取消
              </Button>
            </div>
          </div>
        ) : (
          <div className="max-w-72 text-xs leading-5 text-stone-500">
            <span>{order.status === 'paid' ? '权益已开通' : '订单已取消'}</span>
            {order.operator_note ? <span className="mt-1 block break-words">{order.operator_note}</span> : null}
          </div>
        )}
      </td>
    </tr>
  )
}

function StatusBadge({ status }: { status: PaymentOrderStatus }) {
  const styles = {
    pending: 'bg-amber-50 text-amber-800',
    paid: 'bg-emerald-50 text-emerald-700',
    cancelled: 'bg-stone-100 text-stone-600',
  }
  const labels = { pending: '待处理', paid: '已支付', cancelled: '已取消' }
  return <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${styles[status]}`}>{labels[status]}</span>
}

function errorMessage(error: Error | null) {
  return error instanceof ApiError ? error.message : '请求失败，请稍后重试。'
}
