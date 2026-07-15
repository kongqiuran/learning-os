import { Bot, Library, PanelLeft } from 'lucide-react'

import { Card } from '../components/ui/Card'
import { StatePanel } from '../components/ui/StatePanel'

export function CourseSpacePage() {
  return (
    <section>
      <div>
        <p className="text-sm font-semibold text-blue-600">课程学习空间</p>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight text-slate-950">课程内容</h1>
        <p className="mt-2 text-sm text-slate-500">资料导航、知识内容和 AI 学习助手的三栏结构。</p>
      </div>
      <div className="mt-8 grid min-h-[560px] gap-4 xl:grid-cols-[220px_minmax(0,1fr)_320px]">
        <Card className="p-4">
          <PanelLeft className="size-5 text-blue-600" />
          <h2 className="mt-4 font-semibold text-slate-900">章节与资料</h2>
          <p className="mt-2 text-sm leading-6 text-slate-500">真实课程导航将在 Step 4 接入。</p>
        </Card>
        <StatePanel variant="empty" title="选择课程内容开始学习" description="这里不会展示演示章节或虚假知识。" />
        <Card className="p-4">
          <div className="flex items-center gap-2 text-violet-700">
            <Bot className="size-5" />
            <h2 className="font-semibold">AI 学习助手</h2>
          </div>
          <p className="mt-4 text-sm leading-6 text-slate-500">助手将在 Step 4 基于当前课程已有分析内容回答。</p>
          <div className="mt-5 rounded-xl border border-dashed border-violet-200 bg-violet-50 p-4 text-sm text-violet-700">
            <Library className="mb-2 size-4" />等待课程内容接入
          </div>
        </Card>
      </div>
    </section>
  )
}
