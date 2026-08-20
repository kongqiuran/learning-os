import { BookMarked, FileText, LoaderCircle, Send, Sparkles } from 'lucide-react'
import { useEffect, useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'

import { useCourseAssistant } from '../../hooks/useCourseSpace'
import { ApiError } from '../../lib/api'
import { asCreditError, purchaseUrl } from '../../lib/billing'
import { Button } from '../ui/Button'
import { Card } from '../ui/Card'
import { MarkdownContent } from '../ui/MarkdownContent'

// CourseAssistant 是“AI 学习助手”组件。
// 它负责显示提问框、把问题提交给后端、展示 AI 回答和来源文件。
export function CourseAssistant({
  // courseId 来自路由参数，用来告诉后端“用户正在问哪一门课”。
  courseId,
  // courseName 只用于页面展示，让用户知道当前上下文是哪门课。
  courseName,
  // currentSection 表示当前正在看的内容范围，会一起发给后端帮助限定回答范围。
  currentSection,
  // scene 表示学习场景，例如 follow/textbook/exam。
  scene,
  // chapterId / textbookId 用于把问题限定到某个章节或某本教材。
  chapterId,
  textbookId,
  // scopeUnassigned 表示是否限定在“未分章节资料”。默认 false。
  scopeUnassigned = false,
  // initialQuestion 是外部传入的预填问题，比如用户点击某个知识点后自动生成问题开头。
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
  // question 保存输入框里正在编辑的问题。
  // setQuestion 是修改 question 的函数；React 状态变化后会自动重新渲染界面。
  const [question, setQuestion] = useState('')
  // submittedQuestion 保存“已经提交出去的那个问题”。
  // 这样用户提交后继续编辑输入框时，回答区域仍能显示当时的问题。
  const [submittedQuestion, setSubmittedQuestion] = useState('')
  // useCourseAssistant 封装了调用 /api/courses/:courseId/assistant/query 的逻辑。
  // assistant 里面会有 mutate、isPending、data、error 等状态。
  const assistant = useCourseAssistant(courseId)
  // navigate 用来在代码里跳转页面，例如额度不足时跳到购买页。
  const navigate = useNavigate()
  // asCreditError 会判断当前错误是不是“额度不足”类型，方便展示购买入口。
  const creditError = asCreditError(assistant.error)
  // ?. 是可选链：assistant.data 不存在时不会报错。
  const hasInsufficientContext = assistant.data?.answer === '当前课程资料中没有足够信息。'

  useEffect(() => {
    // 当外部传入 initialQuestion 时，自动帮用户把输入框填成一个“解释这个内容”的问题。
    if (initialQuestion) setQuestion(`请结合“${initialQuestion}”解释：`)
  }, [initialQuestion])

  function handleSubmit(event: FormEvent) {
    // 表单默认提交会刷新整个页面；preventDefault 阻止这个默认行为，交给 React 自己处理。
    event.preventDefault()
    // trim 去掉前后空格，防止用户只输入空格也发请求。
    const normalizedQuestion = question.trim()
    if (!normalizedQuestion) return
    setSubmittedQuestion(normalizedQuestion)
    // mutate 会真正触发接口请求。
    // 这里对象里的字段名使用 current_section/chapter_id，是为了匹配后端 FastAPI 的请求字段。
    // ?? 表示“左边是 null 或 undefined 时用右边”；这样没有章节/教材时就不传具体 id。
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

        {/* onSubmit 绑定上面的 handleSubmit，用户点击按钮或按回车提交时都会走同一套逻辑。 */}
        <form className="border-t border-slate-100 pt-4" onSubmit={handleSubmit}>
          <label className="text-sm font-semibold text-slate-800" htmlFor="course-assistant-question">你想理解什么？</label>
          {/*
            value={question} 表示这个输入框由 React 状态控制，显示内容永远等于 question。
            onChange 会在用户输入时触发，把最新文字写回 question 状态。
          */}
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
            <p className="font-semibold text-amber-950">AI 额度不足</p>
            <p className="mt-1">当前功能需要购买课程权益。剩余次数：{creditError.details.remaining ?? 0}。</p>
            <Button className="mt-3" variant="secondary" onClick={() => navigate(purchaseUrl(creditError, courseId, 'assistant'))}>查看套餐</Button>
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
