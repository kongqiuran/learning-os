import { Check, Circle, Sparkles, Upload, X } from 'lucide-react'
import { useEffect, useState } from 'react'

import { Button } from '../ui/Button'
import { Card } from '../ui/Card'

export function FirstCourseGuide({
  courseId,
  hasDocuments,
  generating,
  completed,
}: {
  courseId: string
  hasDocuments: boolean
  generating: boolean
  completed: boolean
}) {
  const storageKey = `learning-os:course-guide-dismissed:${courseId}`
  const [dismissed, setDismissed] = useState(() => window.localStorage.getItem(storageKey) === '1')

  useEffect(() => {
    if (completed) window.localStorage.setItem(storageKey, '1')
  }, [completed, storageKey])

  if (dismissed || completed) return null

  function dismiss() {
    window.localStorage.setItem(storageKey, '1')
    setDismissed(true)
  }

  function goToNextStep() {
    document.getElementById(hasDocuments ? 'ai-learning-section' : 'course-materials')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  return (
    <Card className="relative mt-6 border-teal-200 bg-teal-50/60 p-5 sm:p-6">
      <button type="button" className="absolute right-3 top-3 rounded-lg p-2 text-stone-400 hover:bg-white hover:text-stone-700" onClick={dismiss} aria-label="关闭课程入门引导"><X className="size-4" /></button>
      <p className="text-xs font-semibold uppercase tracking-[0.14em] text-teal-700">第一次使用 · 只需 3 步</p>
      <h2 className="mt-2 pr-8 text-lg font-semibold text-stone-950">{hasDocuments ? (generating ? 'AI 正在整理，完成后会自动显示' : '资料已准备好，开始第一次 AI 整理') : '课程已创建，接下来上传第一份资料'}</h2>
      <div className="mt-4 grid gap-2 sm:grid-cols-3">
        <GuideStep done label="创建课程" />
        <GuideStep done={hasDocuments} active={!hasDocuments} label="上传资料" icon={Upload} />
        <GuideStep done={false} active={hasDocuments} label={generating ? 'AI 整理中' : '生成内容'} icon={Sparkles} />
      </div>
      {!generating ? <Button className="mt-4" onClick={goToNextStep}>{hasDocuments ? '去生成学习内容' : '去上传第一份资料'}</Button> : <p className="mt-4 text-sm text-teal-800">你可以离开此页面，任务会继续运行；无需重复点击。</p>}
    </Card>
  )
}

function GuideStep({ label, done, active = false, icon: Icon = Circle }: { label: string; done: boolean; active?: boolean; icon?: typeof Circle }) {
  return (
    <div className={`flex items-center gap-2 rounded-xl border px-3 py-2.5 text-sm ${active ? 'border-teal-300 bg-white font-semibold text-teal-900' : 'border-teal-100 bg-white/70 text-stone-600'}`}>
      {done ? <Check className="size-4 text-teal-700" /> : <Icon className={`size-4 ${active ? 'text-teal-700' : 'text-stone-400'}`} />}
      {label}
    </div>
  )
}
