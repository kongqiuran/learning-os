import { ArrowRight, BookMarked, Eye, FileText, Star } from 'lucide-react'

import type { KnowledgeSummary } from '../../types/api'
import { Button } from '../ui/Button'
import { Card } from '../ui/Card'

export function KnowledgeCard({ knowledge, onOpen }: { knowledge: KnowledgeSummary; onOpen: () => void }) {
  return (
    <Card className="group flex h-full flex-col p-5 transition-colors hover:border-blue-200">
      <div className="flex items-start justify-between gap-4">
        <span className="grid size-10 place-items-center rounded-xl bg-violet-50 text-violet-600">
          <BookMarked className="size-5" />
        </span>
        <span className={`inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-medium ${knowledge.viewed ? 'bg-green-50 text-green-700' : 'bg-slate-100 text-slate-600'}`}>
          <Eye className="size-3.5" /> {knowledge.viewed ? '已查看' : '未查看'}
        </span>
      </div>

      <div className="mt-5 flex-1">
        <h3 className="text-lg font-semibold leading-7 text-slate-950">{knowledge.title}</h3>
        <p className="mt-2 line-clamp-4 text-sm leading-6 text-slate-500">{knowledge.content || '当前知识点没有独立解释，请进入详情查看来源分析。'}</p>
      </div>

      <div className="mt-5 space-y-3 border-t border-slate-100 pt-4">
        <div className="flex items-center justify-between gap-3">
          <span className="text-xs text-slate-400">重要程度</span>
          {knowledge.importance ? (
            <span className="flex items-center gap-0.5" aria-label={`重要程度 ${knowledge.importance} 星`}>
              {[1, 2, 3, 4, 5].map((level) => <Star key={level} className={`size-3.5 ${level <= knowledge.importance! ? 'fill-orange-500 text-orange-500' : 'text-slate-200'}`} />)}
            </span>
          ) : <span className="text-xs text-slate-400">未标注</span>}
        </div>
        <div className="flex min-w-0 items-center gap-2 text-xs text-slate-500">
          <FileText className="size-3.5 shrink-0" />
          <span className="truncate">{knowledge.source_file}</span>
        </div>
      </div>

      <Button className="mt-4 w-full" variant="secondary" onClick={onOpen}>
        查看知识 <ArrowRight className="size-4 transition-transform group-hover:translate-x-0.5" />
      </Button>
    </Card>
  )
}
