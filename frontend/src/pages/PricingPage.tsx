import { Check, ShieldCheck } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { useDashboard } from '../hooks/useDashboard'

const benefits = ['跟课资料 AI 整理成功 3 次', '教材解析成功 3 次', '考试冲刺成功 3 次', '该课程 AI 助手问答 100 次', '课程内资料上传、章节管理和已生成内容查看']

export function PricingPage() {
  const dashboard = useDashboard()
  const [searchParams] = useSearchParams()
  const [courseId, setCourseId] = useState('')
  const [confirmed, setConfirmed] = useState(false)
  const support = (import.meta.env.VITE_SUPPORT_CONTACT as string | undefined) ?? '请通过产品客服渠道联系我们'
  const requestedScene = searchParams.get('scene')
  useEffect(() => {
    const requestedCourseId = searchParams.get('course_id')
    if (requestedCourseId) setCourseId(requestedCourseId)
  }, [searchParams])
  return <section className="mx-auto max-w-3xl"><p className="text-sm font-medium text-teal-700">单课权益</p><h1 className="mt-2 text-3xl font-semibold text-stone-950">99 元 · 单课学期版</h1><p className="mt-3 text-sm leading-6 text-stone-500">仅解锁你选择的一门课程，有效期至人工激活时约定的本学期结束日期，不自动续费。</p>
    {requestedScene ? <div className="mt-5 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">当前功能额度已用完，已为你保留原课程选择。开通后即可返回继续使用。</div> : null}
    <Card className="mt-7 p-6"><h2 className="text-lg font-semibold text-stone-900">本课程包含</h2><ul className="mt-4 space-y-3">{benefits.map((item) => <li className="flex gap-3 text-sm text-stone-700" key={item}><Check className="size-4 shrink-0 text-teal-700" />{item}</li>)}</ul><div className="mt-5 rounded-xl bg-[#f5f8f6] p-4 text-sm leading-6 text-stone-600"><ShieldCheck className="mr-2 inline size-4 text-teal-700" />只有成功生成才扣次数；失败、超时或系统中断自动返还。该商品不是无限次会员。</div></Card>
    <Card className="mt-5 p-6"><h2 className="font-semibold text-stone-900">选择要开通的课程</h2><select className="mt-3 h-11 w-full rounded-xl border border-stone-200 bg-white px-3 text-sm" value={courseId} onChange={(event) => setCourseId(event.target.value)}><option value="">请选择课程</option>{dashboard.data?.courses.map((course) => <option key={course.id} value={course.id}>{course.name}</option>)}</select><label className="mt-4 flex items-start gap-3 text-sm leading-6 text-stone-600"><input className="mt-1" type="checkbox" checked={confirmed} onChange={(event) => setConfirmed(event.target.checked)} />我确认价格为99元，仅开通所选课程；权益有明确到期日，不自动续费，并已了解生成次数、失败返还和退款需人工处理。</label><Button className="mt-5" disabled={!courseId || !confirmed} onClick={() => window.alert(`请联系人工客服完成付款与激活：${support}`)}>联系人工开通</Button><p className="mt-3 text-xs leading-5 text-stone-500">人工处理与退款联系：{support}</p></Card>
    <Link className="mt-6 inline-block text-sm font-medium text-teal-700" to="/settings">返回用户中心</Link>
  </section>
}
