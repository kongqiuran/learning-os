import { ArrowRight, Plus } from 'lucide-react'
import { useNavigate, useSearchParams } from 'react-router-dom'

import { CourseCard } from '../components/domain/CourseCard'
import { CreateCourseDialog } from '../components/domain/CreateCourseDialog'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { StatePanel } from '../components/ui/StatePanel'
import { useCurrentUser } from '../hooks/useCurrentUser'
import { useDashboard } from '../hooks/useDashboard'

export function DashboardPage() {
  const dashboard = useDashboard()
  const currentUser = useCurrentUser()
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const createOpen = searchParams.get('create') === '1'
  const recentId = currentUser.data ? localStorage.getItem(`learning-os:recent-course:${currentUser.data.user.id}`) : null
  const recent = dashboard.data?.courses.find((course) => String(course.id) === recentId)

  if (dashboard.isPending) return <StatePanel variant="loading" title="正在加载课程" />
  if (!dashboard.data || dashboard.isError) return <StatePanel variant="error" title="课程加载失败" action={<Button onClick={() => dashboard.refetch()}>重新加载</Button>} />

  const openCourse = (id: number) => navigate(`/courses/${id}/follow`)
  return (
    <section className="mx-auto max-w-6xl">
      <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div><p className="text-sm font-medium text-teal-700">Learning OS</p><h1 className="mt-2 text-3xl font-semibold tracking-tight text-stone-950">我的课程</h1><p className="mt-2 text-sm text-stone-500">选择一门课程，继续整理、理解和复习。</p></div>
        {dashboard.data.courses.length > 0 ? <Button onClick={() => setSearchParams({ create: '1' })}><Plus className="size-4" />创建课程</Button> : null}
      </header>

      {recent ? <Card className="mt-8 border-teal-100 bg-[#f6faf8] p-6 sm:p-7"><p className="text-xs font-semibold uppercase tracking-[0.15em] text-teal-700">继续学习</p><div className="mt-3 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between"><div><h2 className="text-2xl font-semibold text-stone-950">{recent.name}</h2><p className="mt-2 text-sm text-stone-500">最近更新 {formatDate(recent.updated_at)} · {recent.document_count} 份资料</p></div><Button onClick={() => openCourse(recent.id)}>继续学习<ArrowRight className="size-4" /></Button></div></Card> : null}

      <div className="mt-10 flex items-end justify-between"><div><h2 className="text-xl font-semibold text-stone-950">全部课程</h2><p className="mt-1 text-sm text-stone-500">共 {dashboard.data.course_count} 门</p></div></div>
      {dashboard.data.courses.length ? <div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-3">{dashboard.data.courses.map((course) => <CourseCard key={course.id} course={course} onOpen={() => openCourse(course.id)} />)}</div> : <div className="mt-5"><StatePanel variant="empty" title="创建你的第一门课程" description="一门课程里可以管理跟课资料、解析教材，并在考前集中冲刺。" action={<Button onClick={() => setSearchParams({ create: '1' })}><Plus className="size-4" />创建课程</Button>} /></div>}
      <CreateCourseDialog open={createOpen} onClose={() => setSearchParams({}, { replace: true })} />
    </section>
  )
}

function formatDate(value: string) { return new Intl.DateTimeFormat('zh-CN', { month: 'long', day: 'numeric' }).format(new Date(value)) }
