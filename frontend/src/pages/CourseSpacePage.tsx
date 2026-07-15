import { ArrowLeft, CalendarDays, FileText } from 'lucide-react'
import { useNavigate, useParams } from 'react-router-dom'

import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { StatePanel } from '../components/ui/StatePanel'
import { useCourse } from '../hooks/useDashboard'

export function CourseSpacePage() {
  const { courseId } = useParams()
  const navigate = useNavigate()
  const course = useCourse(courseId)

  if (course.isPending) {
    return <StatePanel variant="loading" title="正在打开课程空间" />
  }

  if (course.isError) {
    return (
      <StatePanel
        variant="error"
        title="无法打开课程"
        description="课程不存在，或你没有访问权限。"
        action={<Button variant="secondary" onClick={() => navigate('/dashboard')}>返回 Dashboard</Button>}
      />
    )
  }

  return (
    <section>
      <Button variant="ghost" onClick={() => navigate('/dashboard')}><ArrowLeft className="size-4" /> 返回课程列表</Button>
      <Card className="mt-5 p-6 sm:p-8">
        <p className="text-sm font-semibold text-blue-600">课程学习空间</p>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight text-slate-950">{course.data.name}</h1>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-500">{course.data.description || '暂未添加课程说明'}</p>
        <div className="mt-6 flex flex-wrap gap-4 border-t border-slate-100 pt-5 text-sm text-slate-500">
          <span className="inline-flex items-center gap-2"><CalendarDays className="size-4" />创建于 {formatDate(course.data.created_at)}</span>
          <span className="inline-flex items-center gap-2"><FileText className="size-4" />{course.data.document_count} 份课程资料</span>
        </div>
      </Card>
      <div className="mt-6">
        <StatePanel
          variant="empty"
          title="课程学习空间正在准备中"
          description="资料导航、学习内容和 AI 学习助手将在课程资料接入后显示。"
        />
      </div>
    </section>
  )
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date(value))
}
