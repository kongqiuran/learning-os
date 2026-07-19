import { BookOpenText, CircleAlert, Sparkles } from 'lucide-react'

import type { LearningPackage } from '../../types/api'
import { isTaskActive, taskStatus } from '../../lib/tasks'
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
  previousPackage,
  generating,
  canGenerate,
  onGenerate,
  onSelectSection,
  allowedSections,
  showInitialGenerate = true,
  emptyDescription,
}: {
  learningPackage: LearningPackage | null
  previousPackage?: LearningPackage | null
  generating: boolean
  canGenerate: boolean
  onGenerate: () => void
  onSelectSection: (section: string) => void
  allowedSections?: string[]
  showInitialGenerate?: boolean
  emptyDescription?: string
}) {
  const status = taskStatus(learningPackage)
  const isLoading = generating || isTaskActive(learningPackage)

  if (!isLoading && status === 'FAILED') {
    return (
      <StatePanel
        variant="error"
        title="这次整理没有完成"
        description="服务暂时不可用或资料处理遇到问题。本次不会扣除额度，你可以直接重新整理。"
        action={<Button onClick={onGenerate}>重新整理</Button>}
      />
    )
  }

  const completedPackage = status === 'SUCCESS'
    ? learningPackage
    : taskStatus(previousPackage) === 'SUCCESS'
      ? previousPackage
      : null
  const sections = completedPackage
    ? sectionOrder.filter((key) => !allowedSections || allowedSections.includes(key))
        .filter((key) => hasContent(completedPackage.content[key]))
        .map((key) => [key, completedPackage.content[key]] as const)
    : []

  return (
    <div className="space-y-4">
      {isLoading && !completedPackage ? (
        <StatePanel variant="loading" title={getProgressCopy(learningPackage?.task?.current_stage ?? learningPackage?.current_stage).title} description={progressDescription(learningPackage)} />
      ) : completedPackage ? (
        sections.length > 0 ? (
          <>
            {isLoading ? (
              <StatePanel variant="loading" title={getProgressCopy(learningPackage?.task?.current_stage ?? learningPackage?.current_stage).title} description={`旧结果仍可查看；新结果完成后会自动替换。当前进度 ${learningPackage?.task?.progress ?? 0}%。`} />
            ) : null}
            {completedPackage.is_stale && !isLoading ? (
              <StatePanel
                variant="empty"
                title="当前资料已经发生变化"
                description="这里暂时保留上一次整理结果。重新整理后，AI 会只依据当前章节或当前教材的最新资料生成新版本。"
                action={canGenerate ? <Button variant="ai" onClick={onGenerate}><Sparkles className="size-4" />按最新资料重新整理</Button> : null}
              />
            ) : null}
            <Card className="flex flex-col gap-3 p-5 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <div className="flex items-center gap-2 text-green-700"><BookOpenText className="size-4" /><span className="text-sm font-semibold">课程内容已就绪</span></div>
                <p className="mt-1 text-xs text-slate-500">版本 {completedPackage.version} · 生成于 {formatDateTime(completedPackage.created_at)}</p>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <span className="inline-flex items-center gap-2 rounded-xl bg-violet-50 px-3 py-2 text-xs font-medium text-violet-700"><Sparkles className="size-3.5" /> {completedPackage.is_stale ? '基于上次整理时的资料' : '基于当前所选资料'}</span>
                {!isLoading && canGenerate ? <Button variant="secondary" onClick={onGenerate}>重新整理当前内容</Button> : null}
              </div>
            </Card>
            {sections.length > 1 ? (
              <nav className="sticky top-20 z-10 flex gap-2 overflow-x-auto rounded-2xl border border-stone-200 bg-[#fffdfa]/95 p-3 shadow-sm backdrop-blur" aria-label="AI 整理内容目录">
                {sections.map(([key]) => <a className="whitespace-nowrap rounded-lg px-3 py-1.5 text-xs font-medium text-stone-600 hover:bg-teal-50 hover:text-teal-800" href={`#learning-section-${key}`} key={key}>{sectionLabels[key]}</a>)}
              </nav>
            ) : null}
            {sections.map(([key, value]) => (
              <Card key={key} id={`learning-section-${key}`} className="scroll-mt-36 p-5 sm:p-6">
                <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 pb-4">
                  <h3 className="text-lg font-semibold text-slate-950">{sectionLabels[key]}</h3>
                  <button type="button" className="text-xs font-medium text-violet-700 hover:text-violet-800" onClick={() => onSelectSection(sectionLabels[key])}>以此部分提问</button>
                </div>
                <div className="mx-auto mt-5 max-w-4xl"><ContentValue value={value} /></div>
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
          description={canGenerate ? '资料已经准备好，可以让 AI 整理当前场景的学习内容。' : (emptyDescription ?? '先上传当前场景需要的资料，再开始 AI 整理。')}
          action={canGenerate && showInitialGenerate ? (
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
    overview: '本章概述', learning_objectives: '学习目标', key_concepts: '核心概念', learning_order: '学习顺序',
    common_mistakes: '常见错误', point: '知识点', explanation: '详细解释', master_requirement: '掌握要求',
  }
  return labels[value] ?? value.replaceAll('_', ' ')
}

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }).format(new Date(value))
}

function progressDescription(learningPackage: LearningPackage | null) {
  const stage = learningPackage?.task?.current_stage ?? learningPackage?.current_stage
  const description = getProgressCopy(stage).description
  return learningPackage?.task ? `${description} 当前进度 ${learningPackage.task.progress}%。` : description
}

function getProgressCopy(stage: string | null | undefined) {
  const stages: Record<string, { title: string; description: string }> = {
    queued: { title: '已进入整理队列', description: '任务已提交，通常会很快开始。你可以切换章节或离开此页面。' },
    preparing: { title: '正在准备当前内容', description: '正在确认资料范围和任务配置。' },
    document_analysis: { title: '正在分析课程资料', description: '正在读取文件并提取可用于学习的知识点。' },
    knowledge_generation: { title: '正在生成知识结构', description: '资料分析已完成，正在组织知识块和课程重点。' },
    content_generation: { title: '正在生成整理结果', description: '知识结构已就绪，正在生成最终可阅读内容。' },
    pending: { title: '已进入整理队列', description: '任务已提交，通常会很快开始。你可以切换章节或离开此页面。' },
    recovered: { title: '正在恢复整理任务', description: '系统正在自动恢复任务，不需要重新点击。' },
    retry_queued: { title: '正在自动重试', description: '刚才的处理暂时中断，系统已自动重试，本次不会重复扣除额度。' },
    starting: { title: '正在准备当前内容', description: '正在确认本章节资料范围，只会处理当前选择的内容。' },
    document_analyzer: { title: '正在读取本章节资料', description: '正在提取课件、作业和笔记中的知识点；已分析过的资料会直接复用。' },
    follow_chapter_generator: { title: '正在生成本章知识块', description: '资料读取已完成，正在组织章节总结和重点内容，这是最后一步。' },
    course_analyzer: { title: '正在汇总资料重点', description: '正在建立知识结构，完成后会继续生成可阅读的整理结果。' },
    learning_package_generator: { title: '正在生成整理结果', description: '资料分析已完成，正在生成最终内容，这是最后一步。' },
  }
  return stages[stage ?? ''] ?? { title: '正在整理当前内容', description: '系统正在后台处理，你可以切换页面，完成后结果会自动显示。' }
}
