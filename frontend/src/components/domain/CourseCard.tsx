import { ArrowRight, BookOpen, FileText } from 'lucide-react'

import type { CourseSummary } from '../../types/api'
import { Button } from '../ui/Button'
import { Card } from '../ui/Card'

interface CourseCardProps {
  course: CourseSummary
  onOpen?: () => void
}

export function CourseCard({ course, onOpen }: CourseCardProps) {
  return (
    <Card className="flex min-h-52 flex-col p-5">
      <div className="flex items-start justify-between gap-4">
        <span className="grid size-10 place-items-center rounded-xl bg-blue-50 text-blue-600">
          <BookOpen className="size-5" />
        </span>
        <span className="text-xs text-slate-400">更新于 {formatDate(course.updated_at)}</span>
      </div>
      <h3 className="mt-5 text-lg font-semibold text-slate-900">{course.name}</h3>
      <div className="mt-5 flex flex-wrap items-center gap-x-4 gap-y-2 border-t border-slate-100 pt-4 text-xs text-slate-500">
        <span className="inline-flex items-center gap-1.5">
          <FileText className="size-3.5" /> {course.document_count} 份资料
        </span>
      </div>
      <div className="mt-auto flex justify-end pt-4">
        <Button variant="ghost" onClick={onOpen} aria-label={`进入${course.name}`}>
          进入课程 <ArrowRight className="size-4" />
        </Button>
      </div>
    </Card>
  )
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).format(new Date(value))
}
