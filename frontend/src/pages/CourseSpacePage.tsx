import { ArrowLeft, CalendarDays, FileText } from 'lucide-react'
import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import { CourseAssistant } from '../components/course/CourseAssistant'
import { CourseMaterials } from '../components/course/CourseMaterials'
import { CourseNavigation } from '../components/course/CourseNavigation'
import { LearningPackageView } from '../components/course/LearningPackageView'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { StatePanel } from '../components/ui/StatePanel'
import { useCourseSpace, useGenerateLearningPackage } from '../hooks/useCourseSpace'
import { ApiError } from '../lib/api'

export function CourseSpacePage() {
  const { courseId } = useParams()
  const navigate = useNavigate()
  const courseSpace = useCourseSpace(courseId)
  const generation = useGenerateLearningPackage(courseId)
  const [currentSection, setCurrentSection] = useState('')

  if (courseSpace.isPending) {
    return <StatePanel variant="loading" title="正在打开课程学习空间" />
  }

  if (courseSpace.isError) {
    return (
      <StatePanel
        variant="error"
        title="无法打开课程"
        description="课程不存在，或你没有访问权限。"
        action={<Button variant="secondary" onClick={() => navigate('/dashboard')}>返回 Dashboard</Button>}
      />
    )
  }

  const { course, documents, learning_package: learningPackage } = courseSpace.data

  function selectSection(section: string) {
    setCurrentSection(section)
    document.getElementById('course-assistant')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  return (
    <section>
      <Button variant="ghost" onClick={() => navigate('/dashboard')}><ArrowLeft className="size-4" /> 返回课程列表</Button>
      <Card className="mt-4 p-5 sm:p-6">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm font-semibold text-blue-600">课程学习空间</p>
            <h1 className="mt-2 text-3xl font-semibold tracking-tight text-slate-950">{course.name}</h1>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-500">{course.description || '暂未添加课程说明'}</p>
          </div>
          <div className="flex flex-wrap gap-4 text-sm text-slate-500">
            <span className="inline-flex items-center gap-2"><CalendarDays className="size-4" />创建于 {formatDate(course.created_at)}</span>
            <span className="inline-flex items-center gap-2"><FileText className="size-4" />{documents.length} 份课程资料</span>
          </div>
        </div>
      </Card>

      {generation.isError ? (
        <div className="mt-4 rounded-xl border border-orange-200 bg-orange-50 px-4 py-3 text-sm text-orange-700">
          {generation.error instanceof ApiError ? generation.error.message : '课程内容整理失败，请稍后重试。'}
        </div>
      ) : null}

      <div className="mt-5 grid items-start gap-5 xl:grid-cols-[220px_minmax(0,1fr)_340px]">
        <CourseNavigation
          courseName={course.name}
          documentCount={documents.length}
          learningPackage={learningPackage}
          generating={generation.isPending}
          onGenerate={() => generation.mutate()}
        />

        <main className="min-w-0 space-y-5">
          <CourseMaterials courseId={courseId} documents={documents} />
          <section id="learning-content" className="scroll-mt-24">
            <div className="mb-4">
              <p className="text-xs font-semibold uppercase tracking-[0.14em] text-blue-600">Learning content</p>
              <h2 className="mt-1 text-xl font-semibold text-slate-950">课程学习内容</h2>
            </div>
            <LearningPackageView learningPackage={learningPackage} generating={generation.isPending} onSelectSection={selectSection} />
          </section>
        </main>

        <aside id="course-assistant" className="scroll-mt-24">
          <CourseAssistant courseId={courseId} courseName={course.name} currentSection={currentSection} />
        </aside>
      </div>
    </section>
  )
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date(value))
}
