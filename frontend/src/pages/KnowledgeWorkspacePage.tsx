import { ArrowLeft, BookMarked, Layers3 } from 'lucide-react'
import { useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import { KnowledgeCard } from '../components/domain/KnowledgeCard'
import { KnowledgeFilters, type KnowledgeFilterState } from '../components/knowledge/KnowledgeFilters'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { StatePanel } from '../components/ui/StatePanel'
import { useCourseKnowledge } from '../hooks/useKnowledge'

const initialFilters: KnowledgeFilterState = { sourceFile: 'all', importance: 'all', viewed: 'all' }

export function KnowledgeWorkspacePage() {
  const { courseId } = useParams()
  const navigate = useNavigate()
  const knowledge = useCourseKnowledge(courseId)
  const [filters, setFilters] = useState(initialFilters)

  const sourceFiles = useMemo(
    () => knowledge.data ? Array.from(new Set(knowledge.data.items.map((item) => item.source_file))).sort() : [],
    [knowledge.data],
  )
  const visibleItems = useMemo(() => {
    if (!knowledge.data) return []
    return knowledge.data.items.filter((item) => {
      if (filters.sourceFile !== 'all' && item.source_file !== filters.sourceFile) return false
      if (filters.importance === 'none' && item.importance !== null) return false
      if (filters.importance !== 'all' && filters.importance !== 'none' && item.importance !== Number(filters.importance)) return false
      if (filters.viewed === 'viewed' && !item.viewed) return false
      if (filters.viewed === 'not_viewed' && item.viewed) return false
      return true
    })
  }, [filters, knowledge.data])

  if (knowledge.isPending) return <StatePanel variant="loading" title="正在打开课程知识空间" />

  if (knowledge.isError) {
    return <StatePanel variant="error" title="无法打开课程知识" description="课程不存在，或你没有访问权限。" action={<Button variant="secondary" onClick={() => navigate('/dashboard')}>返回 Dashboard</Button>} />
  }

  return (
    <section>
      <Button variant="ghost" onClick={() => navigate(`/courses/${courseId}`)}><ArrowLeft className="size-4" /> 返回课程空间</Button>
      <Card className="mt-4 p-6 sm:p-8">
        <div className="flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
          <div className="flex items-start gap-4">
            <span className="grid size-11 shrink-0 place-items-center rounded-xl bg-violet-50 text-violet-600"><BookMarked className="size-5" /></span>
            <div>
              <p className="text-sm font-semibold text-violet-600">Knowledge workspace</p>
              <h1 className="mt-1 text-3xl font-semibold tracking-tight text-slate-950">{knowledge.data.course.name} · 课程知识</h1>
              <p className="mt-2 text-sm text-slate-500">来自课程资料分析的知识空间，适合持续查看与复习。</p>
            </div>
          </div>
          <div className="flex items-center gap-3 rounded-xl bg-slate-50 px-4 py-3">
            <Layers3 className="size-5 text-blue-600" />
            <div><strong className="block text-xl text-slate-950">{knowledge.data.knowledge_count}</strong><span className="text-xs text-slate-500">知识卡片</span></div>
          </div>
        </div>
      </Card>

      {knowledge.data.items.length === 0 ? (
        <div className="mt-5"><StatePanel variant="empty" title="暂时没有课程知识" description="课程资料完成分析后，DocumentAnalysis 中的知识主题会显示在这里。" /></div>
      ) : (
        <>
          <div className="mt-5"><KnowledgeFilters value={filters} sourceFiles={sourceFiles} onChange={setFilters} /></div>
          <div className="mt-5 flex items-center justify-between gap-4">
            <h2 className="text-lg font-semibold text-slate-950">知识卡片</h2>
            <span className="text-sm text-slate-400">显示 {visibleItems.length} / {knowledge.data.knowledge_count}</span>
          </div>
          {visibleItems.length === 0 ? (
            <div className="mt-4"><StatePanel variant="empty" title="没有符合筛选条件的知识" description="调整来源文件、重要程度或查看状态后重试。" action={<Button variant="secondary" onClick={() => setFilters(initialFilters)}>清除筛选</Button>} /></div>
          ) : (
            <div className="mt-4 grid gap-4 md:grid-cols-2 2xl:grid-cols-3">
              {visibleItems.map((item) => <KnowledgeCard key={item.id} knowledge={item} onOpen={() => navigate(`/courses/${courseId}/knowledge/${item.id}`)} />)}
            </div>
          )}
        </>
      )}
    </section>
  )
}
