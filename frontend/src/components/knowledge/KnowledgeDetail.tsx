import { BookOpenCheck, CircleCheck, FileText, Lightbulb, Star, TriangleAlert } from 'lucide-react'

import type { KnowledgeDetail as KnowledgeDetailData } from '../../types/api'
import { Button } from '../ui/Button'
import { Card } from '../ui/Card'
import { MarkdownContent } from '../ui/MarkdownContent'

export function KnowledgeDetail({
  knowledge,
  marking,
  onMarkViewed,
}: {
  knowledge: KnowledgeDetailData
  marking: boolean
  onMarkViewed: () => void
}) {
  return (
    <div className="space-y-5">
      <Card className="p-6 sm:p-8">
        <div className="flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between">
          <div className="max-w-3xl">
            <p className="text-sm font-semibold text-violet-600">课程知识</p>
            <h1 className="mt-2 text-3xl font-semibold tracking-tight text-slate-950">{knowledge.title}</h1>
            <div className="mt-4"><MarkdownContent>{knowledge.core_explanation || knowledge.content}</MarkdownContent></div>
          </div>
          <KnowledgeStatus knowledge={knowledge} />
        </div>
        <div className="mt-6 flex flex-wrap gap-x-5 gap-y-2 border-t border-slate-100 pt-5 text-sm text-slate-500">
          <span className="inline-flex items-center gap-2"><BookOpenCheck className="size-4" />{knowledge.course_name}</span>
          <span className="inline-flex items-center gap-2"><FileText className="size-4" />{knowledge.source_file}</span>
          <span>分析于 {formatDate(knowledge.updated_at)}</span>
        </div>
      </Card>

      <div className="grid gap-5 lg:grid-cols-2">
        <DetailSection title="为什么重要" icon={Star} value={knowledge.exam_value || knowledge.reason} />
        <DetailSection title="必须掌握" icon={BookOpenCheck} value={knowledge.must_master} />
        <DetailSection title="记忆与理解提示" icon={Lightbulb} value={knowledge.memory_tips} />
        <DetailSection title="资料判断依据" icon={CircleCheck} value={knowledge.reason} />
      </div>

      {knowledge.source_formulas.length > 0 ? (
        <DetailSection title="同源资料中的公式与规则" icon={BookOpenCheck} value={knowledge.source_formulas} fullWidth />
      ) : null}
      {knowledge.source_errors.length > 0 ? (
        <DetailSection title="同源资料中的常见错误" icon={TriangleAlert} value={knowledge.source_errors} fullWidth tone="warning" />
      ) : null}

      <Card className="flex flex-col gap-4 p-5 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="font-semibold text-slate-900">查看状态</h2>
          <p className="mt-1 text-sm text-slate-500">仅记录是否查看，不计算掌握度、学习时长或完成率。</p>
        </div>
        <Button onClick={onMarkViewed} disabled={knowledge.viewed || marking}>
          <CircleCheck className="size-4" /> {knowledge.viewed ? '已标记为查看' : marking ? '正在保存' : '标记为已查看'}
        </Button>
      </Card>
    </div>
  )
}

function KnowledgeStatus({ knowledge }: { knowledge: KnowledgeDetailData }) {
  return (
    <div className="shrink-0 space-y-2 sm:text-right">
      <span className={`inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-medium ${knowledge.viewed ? 'bg-green-50 text-green-700' : 'bg-slate-100 text-slate-600'}`}>
        <CircleCheck className="size-3.5" /> {knowledge.viewed ? '已查看' : '未查看'}
      </span>
      <div className="flex items-center gap-0.5 sm:justify-end" aria-label={knowledge.importance ? `重要程度 ${knowledge.importance} 星` : '重要程度未标注'}>
        {knowledge.importance ? [1, 2, 3, 4, 5].map((level) => <Star key={level} className={`size-4 ${level <= knowledge.importance! ? 'fill-orange-500 text-orange-500' : 'text-slate-200'}`} />) : <span className="text-xs text-slate-400">重要程度未标注</span>}
      </div>
    </div>
  )
}

function DetailSection({ title, icon: Icon, value, fullWidth = false, tone = 'default' }: { title: string; icon: typeof Star; value: unknown; fullWidth?: boolean; tone?: 'default' | 'warning' }) {
  if (!hasContent(value)) return null
  return (
    <Card className={`${fullWidth ? '' : 'h-full'} p-5 sm:p-6 ${tone === 'warning' ? 'border-orange-200 bg-orange-50/30' : ''}`}>
      <div className={`flex items-center gap-2 ${tone === 'warning' ? 'text-orange-700' : 'text-violet-700'}`}><Icon className="size-4" /><h2 className="font-semibold">{title}</h2></div>
      <div className="mt-4"><KnowledgeValue value={value} /></div>
    </Card>
  )
}

function KnowledgeValue({ value }: { value: unknown }) {
  if (typeof value === 'string') return <MarkdownContent>{value}</MarkdownContent>
  if (Array.isArray(value)) return <div className="space-y-3">{value.map((item, index) => <div className="rounded-xl border border-slate-100 bg-white/70 p-3" key={index}><KnowledgeValue value={item} /></div>)}</div>
  if (value && typeof value === 'object') {
    return <div className="space-y-3">{Object.entries(value as Record<string, unknown>).filter(([, item]) => hasContent(item)).map(([key, item]) => <div key={key}><p className="text-xs font-semibold text-slate-400">{formatKey(key)}</p><div className="mt-1"><KnowledgeValue value={item} /></div></div>)}</div>
  }
  return <p className="text-sm text-slate-500">{String(value)}</p>
}

function hasContent(value: unknown) {
  if (value === null || value === undefined || value === '') return false
  if (Array.isArray(value)) return value.length > 0
  if (typeof value === 'object') return Object.keys(value as object).length > 0
  return true
}

function formatKey(value: string) {
  const labels: Record<string, string> = { name: '名称', formula: '公式', meaning: '含义', usage: '使用条件', variables: '变量', example_application: '应用示例', common_error: '常见错误', question_type: '题型' }
  return labels[value] ?? value.replaceAll('_', ' ')
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }).format(new Date(value))
}
