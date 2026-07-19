import { GraduationCap, Sparkles, Upload, X } from 'lucide-react'
import { useState } from 'react'

import { Button } from '../ui/Button'
import { Card } from '../ui/Card'

const steps = [
  { icon: Upload, title: '1. 上传课程资料', description: '先添加教材、课件、笔记或试卷。' },
  { icon: Sparkles, title: '2. AI 整理知识', description: '让系统生成章节重点、公式和练习。' },
  { icon: GraduationCap, title: '3. 开始学习', description: '阅读学习内容，并向课程助手提问。' },
]

export function WelcomeGuide({ userId, onCreateCourse }: { userId: number; onCreateCourse: () => void }) {
  const storageKey = `learning-os:onboarding-dismissed:${userId}`
  const [dismissed, setDismissed] = useState(() => window.localStorage.getItem(storageKey) === '1')

  if (dismissed) return null

  function dismiss() {
    window.localStorage.setItem(storageKey, '1')
    setDismissed(true)
  }

  return (
    <Card className="relative mt-8 overflow-hidden border-blue-200 bg-gradient-to-br from-blue-50 to-white p-5 sm:p-6">
      <button
        type="button"
        className="absolute right-4 top-4 grid size-9 place-items-center rounded-xl text-slate-400 hover:bg-white hover:text-slate-700"
        onClick={dismiss}
        aria-label="关闭首次使用引导"
      >
        <X className="size-4" />
      </button>
      <p className="text-sm font-semibold text-blue-600">欢迎使用 Learning OS</p>
      <h2 className="mt-2 pr-10 text-2xl font-semibold tracking-tight text-slate-950">三步建立你的课程学习空间</h2>
      <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">
        从一门正在学习的课程开始，整个过程通常只需要几分钟。引导不会阻止你使用其他功能。
      </p>

      <div className="mt-5 grid gap-3 md:grid-cols-3">
        {steps.map(({ icon: Icon, title, description }) => (
          <div className="rounded-2xl border border-blue-100 bg-white/80 p-4" key={title}>
            <span className="grid size-9 place-items-center rounded-xl bg-blue-50 text-blue-600"><Icon className="size-4" /></span>
            <strong className="mt-3 block text-sm text-slate-900">{title}</strong>
            <p className="mt-1 text-xs leading-5 text-slate-500">{description}</p>
          </div>
        ))}
      </div>

      <Button className="mt-5" onClick={onCreateCourse}>创建第一门课程</Button>
    </Card>
  )
}
