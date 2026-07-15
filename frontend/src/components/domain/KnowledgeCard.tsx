import { ArrowUpRight, BookMarked, Eye, FileText } from 'lucide-react'

import type { KnowledgeSummary } from '../../types/api'
import { Card } from '../ui/Card'

export function KnowledgeCard({ knowledge }: { knowledge: KnowledgeSummary }) {
  return (
    <Card className="group p-5 transition-colors hover:border-blue-200">
      <div className="flex items-start justify-between gap-4">
        <span className="grid size-10 place-items-center rounded-xl bg-violet-50 text-violet-600">
          <BookMarked className="size-5" />
        </span>
        <span className="inline-flex items-center gap-1 text-xs text-slate-400">
          <Eye className="size-3.5" /> {knowledge.viewed ? '已查看' : '未查看'}
        </span>
      </div>
      <div className="mt-5 flex items-start justify-between gap-4">
        <div>
          <h3 className="text-base font-semibold text-slate-900">{knowledge.title}</h3>
          <p className="mt-2 line-clamp-3 text-sm leading-6 text-slate-500">{knowledge.content}</p>
        </div>
        <ArrowUpRight className="size-4 shrink-0 text-slate-300 transition-colors group-hover:text-blue-600" />
      </div>
      <div className="mt-5 flex items-center gap-2 border-t border-slate-100 pt-4 text-xs text-slate-500">
        <FileText className="size-3.5" />
        <span className="truncate">{knowledge.sourceFile}</span>
      </div>
    </Card>
  )
}
