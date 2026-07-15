import { BookMarked } from 'lucide-react'

import { StatePanel } from '../components/ui/StatePanel'

export function KnowledgeWorkspacePage() {
  return (
    <section>
      <div className="flex items-start gap-4">
        <span className="grid size-11 place-items-center rounded-xl bg-violet-50 text-violet-600">
          <BookMarked className="size-5" />
        </span>
        <div>
          <p className="text-sm font-semibold text-violet-600">Knowledge</p>
          <h1 className="mt-1 text-3xl font-semibold tracking-tight text-slate-950">课程知识</h1>
          <p className="mt-2 text-sm text-slate-500">从真实 DocumentAnalysis 中呈现课程知识。</p>
        </div>
      </div>
      <div className="mt-8">
        <StatePanel variant="empty" title="暂无可展示的知识" description="知识展示层将在 Step 5 接入，不会复制或虚构课程内容。" />
      </div>
    </section>
  )
}
