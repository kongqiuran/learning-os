import { BookOpenText, CircleAlert, Sparkles } from 'lucide-react'

import type { LearningPackage } from '../../types/api'
import { MarkdownContent } from '../ui/MarkdownContent'
import { Button } from '../ui/Button'
import { Card } from '../ui/Card'
import { StatePanel } from '../ui/StatePanel'

const sectionLabels: Record<string, string> = {
  course_map: '课程地图',
  chapter_summary: '章节总结',
  key_points: '重点内容',
  formula_book: '公式与规则',
  exam_focus: '考试重点',
  questions: '练习问题',
  exam_strategy: '考试策略',
  study_strategy: '学习策略',
}

const sectionOrder = Object.keys(sectionLabels)

export function LearningPackageView({
  learningPackage,
  generating,
  canGenerate,
  onGenerate,
  onSelectSection,
}: {
  learningPackage: LearningPackage | null
  generating: boolean
  canGenerate: boolean
  onGenerate: () => void
  onSelectSection: (section: string) => void
}) {
  const isLoading = generating || learningPackage?.status === 'pending' || learningPackage?.status === 'processing'

  if (!isLoading && learningPackage?.status === 'failed') {
    const diagnostics = [
      learningPackage.current_stage ? `阶段：${learningPackage.current_stage}` : null,
      learningPackage.error_type ? `原因：${learningPackage.error_type}` : null,
      `尝试次数：${learningPackage.retry_count + 1}/3`,
    ].filter(Boolean).join('；')
    return <StatePanel variant="error" title="上次整理没有完成" description={`${diagnostics}。请从左侧重新整理课程内容。`} />
  }

  const completedPackage = learningPackage?.status === 'completed' ? learningPackage : null
  const sections = completedPackage
    ? sectionOrder
        .filter((key) => hasContent(completedPackage.content[key]))
        .map((key) => [key, completedPackage.content[key]] as const)
    : []

  return (
    <div className="space-y-4">
      {isLoading ? (
        <StatePanel variant="loading" title="正在整理课程内容" description="系统正在后台分析资料并生成课程学习内容，你可以离开此页面。" />
      ) : completedPackage ? (
        sections.length > 0 ? (
          <>
            <Card className="flex flex-col gap-3 p-5 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <div className="flex items-center gap-2 text-green-700"><BookOpenText className="size-4" /><span className="text-sm font-semibold">课程内容已就绪</span></div>
                <p className="mt-1 text-xs text-slate-500">版本 {completedPackage.version} · 生成于 {formatDateTime(completedPackage.created_at)}</p>
              </div>
              <span className="inline-flex items-center gap-2 rounded-xl bg-violet-50 px-3 py-2 text-xs font-medium text-violet-700"><Sparkles className="size-3.5" /> 基于当前课程资料</span>
            </Card>
            {sections.map(([key, value]) => (
              <Card key={key} className="p-5 sm:p-6">
                <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 pb-4">
                  <h3 className="text-lg font-semibold text-slate-950">{sectionLabels[key]}</h3>
                  <button type="button" className="text-xs font-medium text-violet-700 hover:text-violet-800" onClick={() => onSelectSection(sectionLabels[key])}>以此部分提问</button>
                </div>
                <div className="mt-5"><ContentValue value={value} /></div>
              </Card>
            ))}
          </>
        ) : (
          <StatePanel variant="empty" title="学习包暂时没有可展示内容" description="可以重新整理课程内容，或检查当前资料是否包含有效文本。" />
        )
      ) : (
        <StatePanel
          variant="empty"
          title="课程内容尚未整理"
          description={canGenerate ? '资料已经准备好，可以让 AI 整理章节重点、公式和练习内容。' : '先上传一份教材或课件，再生成属于这门课程的学习内容。'}
          action={canGenerate ? (
            <Button variant="ai" onClick={onGenerate}><Sparkles className="size-4" /> 开始整理课程内容</Button>
          ) : null}
        />
      )}
    </div>
  )
}

function ContentValue({ value, depth = 0 }: { value: unknown; depth?: number }) {
  if (typeof value === 'string') return <MarkdownContent>{value}</MarkdownContent>
  if (typeof value === 'number' || typeof value === 'boolean') return <p className="text-sm leading-7 text-slate-700">{String(value)}</p>
  if (Array.isArray(value)) {
    if (value.every((item) => typeof item === 'string' || typeof item === 'number')) {
      return <ul className="space-y-2 pl-5 text-sm leading-7 text-slate-700">{value.map((item, index) => <li className="list-disc" key={`${String(item)}-${index}`}><MarkdownContent>{String(item)}</MarkdownContent></li>)}</ul>
    }
    return <div className="space-y-3">{value.map((item, index) => <div className={depth > 0 ? '' : 'rounded-xl border border-slate-100 bg-slate-50/70 p-4'} key={index}><ContentValue value={item} depth={depth + 1} /></div>)}</div>
  }
  if (value && typeof value === 'object') {
    return (
      <div className="space-y-4">
        {Object.entries(value as Record<string, unknown>).filter(([, item]) => hasContent(item)).map(([key, item]) => (
          <div key={key}>
            <h4 className="mb-2 text-sm font-semibold text-slate-800">{formatKey(key)}</h4>
            <ContentValue value={item} depth={depth + 1} />
          </div>
        ))}
      </div>
    )
  }
  return <p className="inline-flex items-center gap-2 text-sm text-slate-400"><CircleAlert className="size-4" />暂无内容</p>
}

function hasContent(value: unknown): boolean {
  if (value === null || value === undefined || value === '') return false
  if (Array.isArray(value)) return value.length > 0
  if (typeof value === 'object') return Object.keys(value as object).length > 0
  return true
}

function formatKey(value: string) {
  const labels: Record<string, string> = {
    topic: '主题', importance: '重要程度', core_explanation: '核心解释', must_master: '必须掌握',
    formulas_or_rules: '公式或规则', question_types: '常见题型', common_errors: '常见错误', memory_tips: '记忆提示',
    study_advice: '学习建议', evidence: '资料依据', chapter: '章节', summary: '概述', key_points: '重点',
  }
  return labels[value] ?? value.replaceAll('_', ' ')
}

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }).format(new Date(value))
}
