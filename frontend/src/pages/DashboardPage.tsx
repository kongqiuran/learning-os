import { BookOpen, FileText, List, Plus } from 'lucide-react'
import { useNavigate, useSearchParams } from 'react-router-dom'

import { CourseCard } from '../components/domain/CourseCard'
import { CreateCourseDialog } from '../components/domain/CreateCourseDialog'
import { WelcomeGuide } from '../components/domain/WelcomeGuide'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { StatePanel } from '../components/ui/StatePanel'
import { useDashboard } from '../hooks/useDashboard'
import { useCurrentUser } from '../hooks/useCurrentUser'

export function DashboardPage() {
  const dashboard = useDashboard()
  const currentUser = useCurrentUser()
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const createOpen = searchParams.get('create') === '1'
  const accountName = currentUser.data?.user.email.split('@')[0] ?? ''

  function openCreateDialog() {
    setSearchParams({ create: '1' })
  }

  function closeCreateDialog() {
    setSearchParams({}, { replace: true })
  }

  return (
    <section>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-sm font-semibold text-blue-600">我的学习空间</p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight text-slate-950">欢迎回来{accountName ? `，${accountName}` : ''}</h1>
          <p className="mt-2 text-sm text-slate-500">管理你的课程学习空间。</p>
        </div>
        <Button onClick={openCreateDialog}>
          <Plus className="size-4" /> 创建学习空间
        </Button>
      </div>

      {dashboard.isPending ? (
        <div className="mt-8"><StatePanel variant="loading" title="正在加载学习空间" /></div>
      ) : dashboard.isError ? (
        <div className="mt-8">
          <StatePanel
            variant="error"
            title="学习空间加载失败"
            description="请检查 API 服务后重试。"
            action={<Button variant="secondary" onClick={() => dashboard.refetch()}>重新加载</Button>}
          />
        </div>
      ) : (
        <>
          {dashboard.data.course_count === 0 && currentUser.data && isNewAccount(currentUser.data.user.created_at) ? (
            <WelcomeGuide userId={currentUser.data.user.id} onCreateCourse={openCreateDialog} />
          ) : null}
          <div className="mt-8 grid gap-4 sm:grid-cols-2">
            <MetricCard icon={BookOpen} label="课程数量" value={dashboard.data.course_count} help="你创建的课程学习空间" />
            <MetricCard icon={FileText} label="课程资料" value={dashboard.data.document_count} help="所有课程中的真实资料数量" />
          </div>

          <Card className="mt-6 flex flex-col gap-4 p-5 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="font-semibold text-slate-900">快速入口</h2>
              <p className="mt-1 text-sm text-slate-500">创建新的学习空间，或继续查看已有课程。</p>
            </div>
            <div className="flex flex-wrap gap-3">
              <Button variant="secondary" onClick={() => document.getElementById('courses')?.scrollIntoView({ behavior: 'smooth' })} disabled={dashboard.data.course_count === 0}>
                <List className="size-4" /> 查看课程
              </Button>
              <Button onClick={openCreateDialog}><Plus className="size-4" /> 创建学习空间</Button>
            </div>
          </Card>

          <div id="courses" className="mt-10 scroll-mt-6">
            <div className="flex items-end justify-between gap-4">
              <div>
                <p className="text-sm font-semibold text-blue-600">Courses</p>
                <h2 className="mt-1 text-2xl font-semibold tracking-tight text-slate-950">我的课程</h2>
              </div>
              <span className="text-sm text-slate-400">共 {dashboard.data.course_count} 门</span>
            </div>
            {dashboard.data.courses.length === 0 ? (
              <div className="mt-5">
                <StatePanel
                  variant="empty"
                  title="创建你的第一个学习空间"
                  description="为一门正在学习的课程建立空间，之后可以继续添加资料和整理知识。"
                  action={<Button onClick={openCreateDialog}><Plus className="size-4" /> 创建课程</Button>}
                />
              </div>
            ) : (
              <div className="mt-5 grid gap-4 md:grid-cols-2 2xl:grid-cols-3">
                {dashboard.data.courses.map((course) => (
                  <CourseCard key={course.id} course={course} onOpen={() => navigate(`/courses/${course.id}`)} />
                ))}
              </div>
            )}
          </div>
        </>
      )}
      <CreateCourseDialog open={createOpen} onClose={closeCreateDialog} />
    </section>
  )
}

function isNewAccount(createdAt: string) {
  const accountAge = Date.now() - new Date(createdAt).getTime()
  return accountAge >= 0 && accountAge <= 7 * 24 * 60 * 60 * 1000
}

function MetricCard({ icon: Icon, label, value, help }: { icon: typeof BookOpen; label: string; value: number; help: string }) {
  return (
    <Card className="flex items-center gap-4 p-5">
      <span className="grid size-11 place-items-center rounded-xl bg-blue-50 text-blue-600"><Icon className="size-5" /></span>
      <div>
        <p className="text-sm text-slate-500">{label}</p>
        <strong className="mt-1 block text-2xl font-semibold text-slate-950">{value}</strong>
        <p className="mt-1 text-xs text-slate-400">{help}</p>
      </div>
    </Card>
  )
}
