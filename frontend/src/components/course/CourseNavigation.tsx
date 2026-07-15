import { BookOpenText, FileText, LoaderCircle, Sparkles } from 'lucide-react'

import type { LearningPackage } from '../../types/api'
import { Button } from '../ui/Button'
import { Card } from '../ui/Card'

export function CourseNavigation({
  courseName,
  documentCount,
  learningPackage,
  generating,
  onGenerate,
}: {
  courseName: string
  documentCount: number
  learningPackage: LearningPackage | null
  generating: boolean
  onGenerate: () => void
}) {
  const status = getCourseStatus(documentCount, learningPackage, generating)

  return (
    <Card className="p-4 xl:sticky xl:top-24">
      <p className="text-xs font-semibold uppercase tracking-[0.14em] text-blue-600">当前课程</p>
      <h2 className="mt-2 text-base font-semibold text-slate-950">{courseName}</h2>
      <div className={`mt-3 inline-flex items-center gap-2 rounded-lg px-2.5 py-1.5 text-xs font-medium ${status.className}`}>
        {generating ? <LoaderCircle className="size-3.5 animate-spin" /> : <span className="size-1.5 rounded-full bg-current" />}
        {status.label}
      </div>

      <nav className="mt-5 space-y-1" aria-label="课程空间导航">
        <NavigationButton icon={FileText} label={`课程资料 · ${documentCount}`} target="course-materials" />
        <NavigationButton icon={BookOpenText} label="学习内容" target="learning-content" />
      </nav>

      <div className="mt-5 border-t border-slate-100 pt-5">
        <p className="text-xs leading-5 text-slate-500">根据已上传资料整理当前课程内容。</p>
        <Button className="mt-3 w-full" variant="ai" onClick={onGenerate} disabled={documentCount === 0 || generating}>
          {generating ? <LoaderCircle className="size-4 animate-spin" /> : <Sparkles className="size-4" />}
          {generating ? '正在整理课程内容' : learningPackage?.status === 'completed' ? '重新整理课程内容' : '整理课程内容'}
        </Button>
        {documentCount === 0 ? <p className="mt-2 text-xs text-slate-400">上传至少一份资料后可开始整理。</p> : null}
      </div>
    </Card>
  )
}

function NavigationButton({ icon: Icon, label, target }: { icon: typeof FileText; label: string; target: string }) {
  return (
    <button
      type="button"
      className="flex w-full items-center gap-2 rounded-xl px-3 py-2.5 text-left text-sm text-slate-600 hover:bg-slate-100 hover:text-slate-950"
      onClick={() => document.getElementById(target)?.scrollIntoView({ behavior: 'smooth', block: 'start' })}
    >
      <Icon className="size-4" /> {label}
    </button>
  )
}

function getCourseStatus(documentCount: number, learningPackage: LearningPackage | null, generating: boolean) {
  if (generating || learningPackage?.status === 'processing') return { label: '正在整理', className: 'bg-blue-50 text-blue-700' }
  if (learningPackage?.status === 'completed') return { label: '学习内容已就绪', className: 'bg-green-50 text-green-700' }
  if (learningPackage?.status === 'failed') return { label: '上次整理失败', className: 'bg-orange-50 text-orange-700' }
  if (documentCount > 0) return { label: '资料已上传', className: 'bg-violet-50 text-violet-700' }
  return { label: '等待课程资料', className: 'bg-slate-100 text-slate-600' }
}
