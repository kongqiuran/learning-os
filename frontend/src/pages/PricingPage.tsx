import { useMutation } from '@tanstack/react-query'
import { Check, LoaderCircle, ShieldCheck } from 'lucide-react'
import { useEffect, useMemo, useRef, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'

import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { useDashboard } from '../hooks/useDashboard'
import { useBillingProducts } from '../hooks/useUserCenter'
import { api, ApiError } from '../lib/api'
import { formatMoney } from '../lib/billing'

export function PricingPage() {
  const dashboard = useDashboard()
  const products = useBillingProducts()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [courseId, setCourseId] = useState('')
  const [productCode, setProductCode] = useState('')
  const requestKey = useRef(createRequestKey())
  const requestedScene = searchParams.get('scene')

  useEffect(() => {
    const requestedCourseId = searchParams.get('course_id')
    if (requestedCourseId) setCourseId(requestedCourseId)
  }, [searchParams])

  useEffect(() => {
    if (!productCode && products.data?.products[0]) {
      setProductCode(products.data.products[0].product_code)
    }
  }, [productCode, products.data])

  const selectedCourse = useMemo(
    () => dashboard.data?.courses.find((course) => String(course.id) === courseId),
    [courseId, dashboard.data],
  )
  const selectedProduct = useMemo(
    () => products.data?.products.find((product) => product.product_code === productCode),
    [productCode, products.data],
  )

  const createOrder = useMutation({
    mutationFn: () => api.createPaymentOrder({
      course_id: Number(courseId),
      product_code: productCode,
      request_key: requestKey.current,
    }),
    onSuccess: (order) => navigate(`/purchase/${encodeURIComponent(order.order_no)}`),
  })

  return (
    <section className="mx-auto max-w-4xl">
      <p className="text-sm font-medium text-teal-700">课程权益</p>
      <h1 className="mt-2 text-3xl font-semibold text-stone-950">选择适合当前课程的产品</h1>
      <p className="mt-3 text-sm leading-6 text-stone-500">提交购买申请后，通过人工付款与确认完成开通，不会自动扣款或续费。</p>

      {requestedScene ? (
        <div className="mt-5 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          AI 额度不足，当前功能需要购买课程权益。已为你保留原课程，开通后即可返回继续使用。
        </div>
      ) : null}

      {products.isPending ? (
        <Card className="mt-7 flex items-center justify-center gap-2 p-8 text-sm text-stone-500">
          <LoaderCircle className="size-4 animate-spin" /> 正在读取产品
        </Card>
      ) : products.isError ? (
        <Card className="mt-7 p-6">
          <p className="text-sm text-red-700">产品暂时无法读取。</p>
          <Button className="mt-4" variant="secondary" onClick={() => products.refetch()}>重新加载</Button>
        </Card>
      ) : (
        <div className="mt-7 grid gap-4 md:grid-cols-2">
          {products.data?.products.map((product) => {
            const selected = product.product_code === productCode
            return (
              <Card
                className={`cursor-pointer p-6 transition ${selected ? 'border-teal-600 ring-2 ring-teal-100' : 'hover:border-stone-300'}`}
                key={product.product_code}
                onClick={() => setProductCode(product.product_code)}
              >
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <h2 className="text-lg font-semibold text-stone-950">{product.name}</h2>
                    <p className="mt-2 text-sm leading-6 text-stone-500">{product.description}</p>
                  </div>
                  <span className="whitespace-nowrap text-xl font-semibold text-teal-700">{formatMoney(product.amount_cents, product.currency)}</span>
                </div>
                <ul className="mt-5 space-y-2.5 text-sm text-stone-700">
                  <Benefit label="跟课整理" value={product.follow_allowance} />
                  <Benefit label="教材分析" value={product.textbook_allowance} />
                  <Benefit label="考试冲刺" value={product.exam_allowance} />
                  <Benefit label="课程助手" value={product.assistant_allowance} />
                </ul>
              </Card>
            )
          })}
        </div>
      )}

      <Card className="mt-5 p-6">
        <h2 className="font-semibold text-stone-900">选择要开通的课程</h2>
        <select
          className="mt-3 h-11 w-full rounded-xl border border-stone-200 bg-white px-3 text-sm"
          value={courseId}
          onChange={(event) => setCourseId(event.target.value)}
        >
          <option value="">请选择课程</option>
          {dashboard.data?.courses.map((course) => <option key={course.id} value={course.id}>{course.name}</option>)}
        </select>
        {selectedCourse ? <p className="mt-3 text-sm text-stone-600">当前课程：<strong>{selectedCourse.name}</strong></p> : null}
        <div className="mt-4 rounded-xl bg-[#f5f8f6] p-4 text-sm leading-6 text-stone-600">
          <ShieldCheck className="mr-2 inline size-4 text-teal-700" />
          订单金额和权益以服务器产品配置为准。AI 任务失败、超时或系统中断时，已预占额度会自动返还。
        </div>
        {createOrder.isError ? (
          <p className="mt-4 rounded-xl bg-red-50 px-3 py-2.5 text-sm text-red-700">
            {createOrder.error instanceof ApiError ? createOrder.error.message : '购买申请创建失败，请稍后重试。'}
          </p>
        ) : null}
        <Button
          className="mt-5"
          disabled={!courseId || !selectedProduct || createOrder.isPending}
          onClick={() => createOrder.mutate()}
        >
          {createOrder.isPending ? <LoaderCircle className="size-4 animate-spin" /> : null}
          {createOrder.isPending ? '正在创建购买申请' : '提交购买申请'}
        </Button>
      </Card>

      <Link className="mt-6 inline-block text-sm font-medium text-teal-700" to="/settings">返回用户中心</Link>
    </section>
  )
}

function Benefit({ label, value }: { label: string; value: number }) {
  return <li className="flex items-center gap-2"><Check className="size-4 text-teal-700" />{label} {value} 次</li>
}

function createRequestKey() {
  return `purchase-${Date.now()}-${Math.random().toString(36).slice(2, 12)}`
}
