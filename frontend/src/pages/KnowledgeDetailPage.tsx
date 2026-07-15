import { ArrowLeft } from 'lucide-react'
import { useNavigate, useParams } from 'react-router-dom'

import { KnowledgeDetail } from '../components/knowledge/KnowledgeDetail'
import { Button } from '../components/ui/Button'
import { StatePanel } from '../components/ui/StatePanel'
import { useKnowledgeDetail, useMarkKnowledgeViewed } from '../hooks/useKnowledge'

export function KnowledgeDetailPage() {
  const { courseId, knowledgeId } = useParams()
  const navigate = useNavigate()
  const knowledge = useKnowledgeDetail(knowledgeId)
  const markViewed = useMarkKnowledgeViewed(courseId, knowledgeId)

  if (knowledge.isPending) return <StatePanel variant="loading" title="正在打开知识详情" />
  if (knowledge.isError) return <StatePanel variant="error" title="无法打开知识内容" description="知识不存在，或你没有访问权限。" action={<Button variant="secondary" onClick={() => navigate(`/courses/${courseId}/knowledge`)}>返回知识空间</Button>} />

  if (String(knowledge.data.course_id) !== courseId) {
    return <StatePanel variant="error" title="知识不属于当前课程" action={<Button variant="secondary" onClick={() => navigate(`/courses/${courseId}/knowledge`)}>返回知识空间</Button>} />
  }

  return (
    <section>
      <Button variant="ghost" onClick={() => navigate(`/courses/${courseId}/knowledge`)}><ArrowLeft className="size-4" /> 返回课程知识</Button>
      <div className="mt-4">
        <KnowledgeDetail knowledge={knowledge.data} marking={markViewed.isPending} onMarkViewed={() => markViewed.mutate()} />
      </div>
      {markViewed.isError ? <p className="mt-4 rounded-xl border border-orange-200 bg-orange-50 px-4 py-3 text-sm text-orange-700">查看状态保存失败，请稍后重试。</p> : null}
    </section>
  )
}
