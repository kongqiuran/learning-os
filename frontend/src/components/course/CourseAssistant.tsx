import { BookMarked, FileText, LoaderCircle, Send, Sparkles } from 'lucide-react'
import { useEffect, useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'

import { useCourseAssistant } from '../../hooks/useCourseSpace'
import { ApiError } from '../../lib/api'
import { Button } from '../ui/Button'
import { Card } from '../ui/Card'
import { MarkdownContent } from '../ui/MarkdownContent'

export function CourseAssistant({
  courseId,
  courseName,
  currentSection,
  scene,
  chapterId,
  textbookId,
  scopeUnassigned = false,
  initialQuestion = '',
}: {
  courseId: string | undefined
  courseName: string
  currentSection: string
  scene?: string
  chapterId?: number | null
  textbookId?: number | null
  scopeUnassigned?: boolean
  initialQuestion?: string
}) {
  const [question, setQuestion] = useState('')
  const [submittedQuestion, setSubmittedQuestion] = useState('')
  const assistant = useCourseAssistant(courseId)
  const navigate = useNavigate()
  const creditError = assistant.error instanceof ApiError && ['insufficient_credits', 'assistant_quota_exceeded'].includes(assistant.error.code) ? assistant.error : null
  const hasInsufficientContext = assistant.data?.answer === '当前课程资料中没有足够信息。'

  useEffect(() => {
    if (initialQuestion) setQuestion(`请结合“${initialQuestion}”解释：`)
  }, [initialQuestion])

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    const normalizedQuestion = question.trim()
    if (!normalizedQuestion) return
    setSubmittedQuestion(normalizedQuestion)
    assistant.mutate({ question: normalizedQuestion, current_section: currentSection || undefined, scene, chapter_id: chapterId ?? undefined, textbook_id: textbookId ?? undefined, scope_unassigned: scopeUnassigned })
  }

  return (
    <Card className="overflow-hidden xl:sticky xl:top-24">
      <div className="border-b border-violet-100 bg-violet-50/70 p-5">
        <div className="flex items-center gap-2 text-violet-700"><Sparkles className="size-4" /><span className="text-xs font-semibold uppercase tracking-[0.14em]">课程助手</span></div>
        <h2 className="mt-2 text-lg font-semibold text-slate-950">理解当前课程</h2>
        <p className="mt-1 text-sm leading-6 text-slate-500">回答仅基于已经整理的课程内容与资料分析。</p>
      </div>

      <div className="space-y-4 p-5">
        <ContextRow label="当前课程" value={courseName} icon={BookMarked} />
        <ContextRow label="当前内容" value={currentSection || '全部课程内容'} icon={FileText} />

        <form className="border-t border-slate-100 pt-4" onSubmit={handleSubmit}>
          <label className="text-sm font-semibold text-slate-800" htmlFor="course-assistant-question">你想理解什么？</label>
          <textarea
            id="course-assistant-question"
            className="mt-2 min-h-28 w-full resize-y rounded-xl border border-slate-200 px-3 py-2.5 text-sm leading-6 outline-none focus:border-violet-500 focus:ring-4 focus:ring-violet-100"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            maxLength={1000}
            placeholder="输入关于当前课程的问题"
          />
          <Button className="mt-3 w-full" variant="ai" type="submit" disabled={!question.trim() || assistant.isPending}>
            {assistant.isPending ? <LoaderCircle className="size-4 animate-spin" /> : <Send className="size-4" />}
            {assistant.isPending ? '正在根据课程资料解释' : '询问课程助手'}
          </Button>
        </form>

        {creditError ? (
          <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm leading-6 text-amber-800">
            <p className="font-semibold text-amber-950">课程助手额度不足</p>
            <p className="mt-1">剩余次数：{creditError.details.remaining ?? 0}。开通或续购本课程权益后即可继续提问。</p>
            <Button className="mt-3" variant="secondary" onClick={() => navigate(creditError.details.purchase_url ?? `/pricing?course_id=${courseId}&scene=assistant`)}>查看套餐</Button>
          </div>
        ) : assistant.isError ? (
          <div className="rounded-xl bg-orange-50 p-3 text-sm leading-6 text-orange-700">
            {assistant.error instanceof ApiError ? assistant.error.message : '课程助手暂时无法回答，请稍后重试。'}
          </div>
        ) : null}

        {assistant.data ? (
          <section className="space-y-4 border-t border-slate-100 pt-4" aria-label="课程助手回答">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">你的问题</p>
              <p className="mt-2 text-sm leading-6 text-slate-700">{submittedQuestion}</p>
            </div>
            <div className="rounded-xl border border-violet-100 bg-violet-50/50 p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.12em] text-violet-700">AI 解释</p>
              <div className="mt-2"><MarkdownContent>{assistant.data.answer}</MarkdownContent></div>
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">来源文件</p>
              {assistant.data.source_files.length > 0 ? (
                <ul className="mt-2 space-y-1.5">{assistant.data.source_files.map((file) => <li className="flex items-center gap-2 text-xs text-slate-600" key={file}><FileText className="size-3.5" />{file}</li>)}</ul>
              ) : hasInsufficientContext ? (
                <div className="mt-2 rounded-xl bg-amber-50 p-3 text-xs leading-5 text-amber-800">
                  当前没有可用于回答的来源文件。请先上传当前场景的资料并完成 AI 整理，再回来提问。
                </div>
              ) : (
                <p className="mt-2 text-xs leading-5 text-slate-500">回答来自已生成的课程学习内容，当前版本未保存精确文件引用。</p>
              )}
            </div>
          </section>
        ) : null}
      </div>
    </Card>
  )
}

function ContextRow({ label, value, icon: Icon }: { label: string; value: string; icon: typeof BookMarked }) {
  return (
    <div className="flex items-start gap-3">
      <span className="grid size-8 shrink-0 place-items-center rounded-lg bg-slate-100 text-slate-500"><Icon className="size-4" /></span>
      <div className="min-w-0"><p className="text-xs text-slate-400">{label}</p><p className="mt-0.5 truncate text-sm font-medium text-slate-800">{value}</p></div>
    </div>
  )
}
