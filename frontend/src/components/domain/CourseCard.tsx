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
        <span className="text-xs text-slate-400">更新于 {course.updatedAt}</span>
      </div>
      <h3 className="mt-5 text-lg font-semibold text-slate-900">{course.name}</h3>
      <p className="mt-2 line-clamp-2 text-sm leading-6 text-slate-500">
        {course.description || '暂未添加课程说明'}
      </p>
      <div className="mt-auto flex items-center justify-between pt-5">
        <span className="inline-flex items-center gap-1.5 text-sm text-slate-500">
          <FileText className="size-4" /> {course.documentCount} 份资料
        </span>
        <Button variant="ghost" onClick={onOpen} aria-label={`进入${course.name}`}>
          进入课程 <ArrowRight className="size-4" />
        </Button>
      </div>
    </Card>
  )
}
