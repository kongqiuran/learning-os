import {
  ArrowDown,
  ArrowLeft,
  ArrowUp,
  BookOpen,
  Bot,
  FileText,
  MoreHorizontal,
  Pencil,
  Plus,
  Trash2,
  X,
} from 'lucide-react'
import { useEffect, useState, type FormEvent } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { NavLink, useNavigate, useParams } from 'react-router-dom'

import { CourseAssistant } from '../components/course/CourseAssistant'
import { CourseMaterials } from '../components/course/CourseMaterials'
import { LearningPackageView } from '../components/course/LearningPackageView'
import { SCENE_UPLOAD_TYPES } from '../components/course/uploadCategories'
import { KnowledgeCard } from '../components/domain/KnowledgeCard'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { StatePanel } from '../components/ui/StatePanel'
import { courseSpaceQueryKey, useCourseSpace, useGenerationTask } from '../hooks/useCourseSpace'
import { useCurrentUser } from '../hooks/useCurrentUser'
import { useCourseKnowledge } from '../hooks/useKnowledge'
import { api, ApiError } from '../lib/api'
import type { Chapter, DocumentSummary, LearningPackage } from '../types/api'

type Scene = 'follow' | 'textbook' | 'exam'
type ChapterEditor = { mode: 'create' } | { mode: 'rename'; chapter: Chapter }
type GenerationScope = { documentId?: number; chapterId?: number; unassigned?: boolean }

const sceneInfo = {
  follow: { label: '跟课资料', description: '按课程进度管理课件、练习和补充资料。', sections: ['chapter_summary', 'key_points'] },
  textbook: { label: '教材解析', description: '把教材整理成知识大纲、公式和知识卡片。', sections: ['course_map', 'formula_book'] },
  exam: { label: '考试冲刺', description: '从真实试卷和练习中提炼考点与行动清单。', sections: ['exam_focus', 'questions', 'exam_strategy', 'study_strategy'] },
} as const

const scenePaths: Record<Scene, string> = {
  follow: 'follow',
  textbook: 'textbooks',
  exam: 'exam',
}

export function CourseSpacePage({ scene }: { scene: Scene }) {
  const { courseId } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const currentUser = useCurrentUser()
  const courseSpace = useCourseSpace(courseId)
  const [assistantOpen, setAssistantOpen] = useState(false)
  const [assistantQuestion, setAssistantQuestion] = useState('')
  const [selectedChapterId, setSelectedChapterId] = useState<number | null | undefined>(undefined)
  const [selectedTextbookId, setSelectedTextbookId] = useState<number | null>(null)
  const [chapterEditor, setChapterEditor] = useState<ChapterEditor | null>(null)
  const [deleteChapter, setDeleteChapter] = useState<Chapter | null>(null)
  const [taskId, setTaskId] = useState<number | null>(null)
  const task = useGenerationTask(courseId, taskId)
  const legacyPackage = courseSpace.data?.learning_package?.scene === 'legacy' ? courseSpace.data.learning_package : null
  const unscopedScenePackage = courseSpace.data?.scene_packages?.[scene] ?? legacyPackage
  const unscopedCompletedPackage = courseSpace.data?.scene_completed_packages?.[scene] ?? (legacyPackage?.status === 'completed' ? legacyPackage : null)

  useEffect(() => {
    if (currentUser.data && courseId) {
      localStorage.setItem(`learning-os:recent-course:${currentUser.data.user.id}`, courseId)
      localStorage.setItem(`learning-os:recent-scene:${currentUser.data.user.id}:${courseId}`, scene)
    }
  }, [courseId, currentUser.data, scene])

  useEffect(() => {
    if (selectedChapterId === undefined && courseSpace.data) {
      const hasUnassignedDocuments = courseSpace.data.documents.some(
        (item) => ['SLIDES', 'HOMEWORK', 'OTHER', 'NOTES'].includes(item.document_type) && item.chapter_id == null,
      )
      setSelectedChapterId(hasUnassignedDocuments ? null : (courseSpace.data.chapters[0]?.id ?? null))
    }
  }, [courseSpace.data, selectedChapterId])

  useEffect(() => {
    if (!selectedTextbookId && courseSpace.data) {
      const firstTextbook = courseSpace.data.documents.find((item) => item.document_type === 'TEXTBOOK')
      setSelectedTextbookId(firstTextbook?.id ?? null)
    }
  }, [courseSpace.data, selectedTextbookId])

  useEffect(() => {
    if (!task.data || !['completed', 'failed'].includes(task.data.status)) return
    if (task.data.status === 'completed' || task.data.status === 'failed') {
      setTaskId(null)
    }
  }, [task.data])

  const refresh = () => queryClient.invalidateQueries({ queryKey: courseSpaceQueryKey(courseId) })
  const createChapter = useMutation({
    mutationFn: (title: string) => api.createChapter(courseId!, title),
    onSuccess: async () => {
      setChapterEditor(null)
      await refresh()
    },
  })
  const updateChapter = useMutation({
    mutationFn: ({ id, title, position }: { id: number; title?: string; position?: number }) => api.updateChapter(courseId!, id, { title, position }),
    onSuccess: async () => {
      setChapterEditor(null)
      await refresh()
    },
  })
  const reorderChapters = useMutation({
    mutationFn: async ({ chapter, target }: { chapter: Chapter; target: Chapter }) => {
      await api.updateChapter(courseId!, chapter.id, { position: target.position })
      await api.updateChapter(courseId!, target.id, { position: chapter.position })
    },
    onSuccess: refresh,
  })
  const removeChapter = useMutation({
    mutationFn: ({ id, action }: { id: number; action: 'keep_unassigned' | 'delete' }) => api.deleteChapter(courseId!, id, action),
    onSuccess: async () => {
      setDeleteChapter(null)
      setSelectedChapterId(null)
      await refresh()
    },
  })
  const moveDocument = useMutation({
    mutationFn: ({ documentId, chapterId }: { documentId: number; chapterId: number | null }) => api.moveDocument(courseId!, documentId, chapterId),
    onSuccess: refresh,
  })
  const generate = useMutation({
    mutationFn: (scope?: GenerationScope) => api.generateScene(courseId!, scene, scope),
    onSuccess: (result) => setTaskId(result.id),
  })

  if (!courseSpace.data) {
    return courseSpace.isPending
      ? <StatePanel variant="loading" title="正在打开课程" />
      : <StatePanel variant="error" title="无法打开课程" action={<Button onClick={() => navigate('/dashboard')}>返回课程列表</Button>} />
  }

  const { course, documents, chapters } = courseSpace.data
  const selectedChapter = chapters.find((item) => item.id === selectedChapterId) ?? null
  const normalizedChapterId = selectedChapterId ?? null
  const filteredDocuments = filterDocuments(documents, scene, normalizedChapterId)
  const unassignedDocumentCount = documents.filter(
    (item) => ['SLIDES', 'HOMEWORK', 'OTHER', 'NOTES'].includes(item.document_type) && item.chapter_id == null,
  ).length
  const textbooks = documents.filter((item) => item.document_type === 'TEXTBOOK')
  const scopedPackage = scene === 'follow'
    ? courseSpace.data.chapter_packages[selectedChapterId == null ? 'unassigned' : String(selectedChapterId)] ?? null
    : scene === 'textbook' && selectedTextbookId != null
      ? courseSpace.data.document_packages[String(selectedTextbookId)] ?? null
      : unscopedScenePackage
  const completedScopedPackage = scene === 'follow'
    ? courseSpace.data.chapter_completed_packages[selectedChapterId == null ? 'unassigned' : String(selectedChapterId)] ?? null
    : scene === 'textbook' && selectedTextbookId != null
      ? courseSpace.data.document_completed_packages[String(selectedTextbookId)] ?? null
      : unscopedCompletedPackage
  const taskMatchesSelection = task.data ? packageMatchesSelection(task.data, scene, selectedChapterId, selectedTextbookId) : false
  const requestMatchesSelection = generate.variables ? scopeMatchesSelection(generate.variables, scene, selectedChapterId, selectedTextbookId) : false
  const displayedPackage = taskMatchesSelection ? task.data! : scopedPackage
  const isGenerating = (generate.isPending && requestMatchesSelection) || displayedPackage?.status === 'pending' || displayedPackage?.status === 'processing'

  function openAssistant(question = '') {
    setAssistantQuestion(question)
    setAssistantOpen(true)
  }

  function moveChapter(chapter: Chapter, direction: -1 | 1) {
    const index = chapters.findIndex((item) => item.id === chapter.id)
    const target = chapters[index + direction]
    if (target) reorderChapters.mutate({ chapter, target })
  }

  return (
    <section className="mx-auto max-w-[1500px]">
      <div className="flex items-center justify-between gap-4">
        <Button variant="ghost" onClick={() => navigate('/dashboard')}><ArrowLeft className="size-4" />我的课程</Button>
        <Button variant="secondary" onClick={() => openAssistant()}><Bot className="size-4" />AI 学习助手</Button>
      </div>
      <header className="mt-4 border-b border-stone-200 pb-0">
        <h1 className="text-3xl font-semibold tracking-tight text-stone-950">{course.name}</h1>
        <p className="mt-2 text-sm text-stone-500">{sceneInfo[scene].description}</p>
        <nav className="mt-6 flex gap-7 overflow-x-auto" aria-label="课程学习场景">
          {(Object.keys(sceneInfo) as Scene[]).map((item) => (
            <NavLink
              key={item}
              to={`/courses/${courseId}/${scenePaths[item]}`}
              className={({ isActive }) => `whitespace-nowrap border-b-2 pb-3 text-sm font-semibold ${isActive ? 'border-teal-700 text-teal-800' : 'border-transparent text-stone-500 hover:text-stone-900'}`}
            >
              {sceneInfo[item].label}
            </NavLink>
          ))}
        </nav>
      </header>

      {scene === 'follow' ? (
        <div className="mt-6 grid gap-5 lg:grid-cols-[270px_minmax(0,1fr)]">
          <Card className="p-4 lg:sticky lg:top-24 lg:self-start">
            <div className="flex items-center justify-between">
              <h2 className="font-semibold text-stone-900">章节</h2>
              <button className="rounded-lg p-2 text-teal-700 hover:bg-teal-50" onClick={() => setChapterEditor({ mode: 'create' })} aria-label="添加章节"><Plus className="size-4" /></button>
            </div>
            <button className={`mt-4 flex w-full items-center justify-between rounded-xl px-3 py-2 text-left text-sm ${selectedChapterId === null ? 'bg-teal-50 text-teal-800' : 'text-stone-600 hover:bg-stone-50'}`} onClick={() => setSelectedChapterId(null)}>
              <span>未分章节</span>
              <span className="text-xs text-stone-400">{unassignedDocumentCount} 份资料</span>
            </button>
            <div className="mt-1 space-y-1">
              {chapters.map((chapter, index) => (
                <div className={`group flex items-center rounded-xl ${chapter.id === selectedChapterId ? 'bg-teal-50' : 'hover:bg-stone-50'}`} key={chapter.id}>
                  <button className="min-w-0 flex-1 px-3 py-2 text-left" onClick={() => setSelectedChapterId(chapter.id)}>
                    <span className="block truncate text-sm font-medium text-stone-800">{chapter.title}</span>
                    <span className="text-xs text-stone-400">{chapter.document_count} 份资料</span>
                  </button>
                  <div className="mr-1 flex opacity-0 transition group-hover:opacity-100 group-focus-within:opacity-100">
                    <button className="rounded-lg p-1.5 text-stone-400 hover:text-stone-700" onClick={() => moveChapter(chapter, -1)} disabled={index === 0 || reorderChapters.isPending} aria-label={`上移${chapter.title}`}><ArrowUp className="size-3.5" /></button>
                    <button className="rounded-lg p-1.5 text-stone-400 hover:text-stone-700" onClick={() => moveChapter(chapter, 1)} disabled={index === chapters.length - 1 || reorderChapters.isPending} aria-label={`下移${chapter.title}`}><ArrowDown className="size-3.5" /></button>
                    <button className="rounded-lg p-1.5 text-stone-400 hover:text-stone-700" onClick={() => setChapterEditor({ mode: 'rename', chapter })} aria-label={`重命名${chapter.title}`}><Pencil className="size-3.5" /></button>
                    <button className="rounded-lg p-1.5 text-stone-400 hover:text-red-600" onClick={() => setDeleteChapter(chapter)} aria-label={`删除${chapter.title}`}><MoreHorizontal className="size-4" /></button>
                  </div>
                </div>
              ))}
            </div>
          </Card>
          <div className="min-w-0 space-y-5">
            <ChapterMaterials documents={filteredDocuments} chapters={chapters} current={selectedChapter} onMove={(documentId, chapterId) => moveDocument.mutate({ documentId, chapterId })} />
            <CourseMaterials
              courseId={courseId}
              documents={filteredDocuments}
              allowedDocumentTypes={SCENE_UPLOAD_TYPES.follow}
              chapterId={normalizedChapterId}
              title={selectedChapter?.title ? `${selectedChapter.title}的资料` : '未分章节资料'}
              description="上传课件、练习或补充资料，新资料会直接归入当前章节。"
            />
            <LearningSection title={selectedChapter?.title ?? '未分章节'} packageData={displayedPackage} previousPackage={completedScopedPackage} generating={isGenerating} canGenerate={filteredDocuments.length > 0} onGenerate={() => generate.mutate(selectedChapterId == null ? { unassigned: true } : { chapterId: selectedChapterId })} onSelectSection={openAssistant} sections={sceneInfo.follow.sections} emptyDescription="先上传当前章节的课件、练习或补充资料，再开始整理。" error={requestMatchesSelection ? generate.error : null} />
          </div>
        </div>
      ) : null}

      {scene === 'textbook' ? (
        <div className="mt-6 space-y-5">
          <CourseMaterials courseId={courseId} documents={textbooks} allowedDocumentTypes={SCENE_UPLOAD_TYPES.textbook} title="我的教材" description="每本教材独立解析，避免不同版本的知识结构互相混合。" showDocumentList={false} />
          <TextbookList documents={textbooks} selectedId={selectedTextbookId} onSelect={setSelectedTextbookId} onGenerate={(id) => generate.mutate({ documentId: id })} generating={isGenerating} />
          <LearningSection packageData={displayedPackage} previousPackage={completedScopedPackage} generating={isGenerating} canGenerate={textbooks.length > 0} onGenerate={() => selectedTextbookId && generate.mutate({ documentId: selectedTextbookId })} onSelectSection={openAssistant} sections={sceneInfo.textbook.sections} showInitialGenerate={false} emptyDescription="先上传一本教材，再为这本教材生成知识大纲。" error={requestMatchesSelection ? generate.error : null} />
          <TextbookKnowledgeSection courseId={courseId} />
        </div>
      ) : null}

      {scene === 'exam' ? (
        <div className="mt-6 space-y-5">
          <CourseMaterials courseId={courseId} documents={filteredDocuments} allowedDocumentTypes={SCENE_UPLOAD_TYPES.exam} title="考试资料" description="上传试卷和练习资料，AI 只会依据这些内容整理考试冲刺建议。" />
          <LearningSection packageData={displayedPackage} previousPackage={completedScopedPackage} generating={isGenerating} canGenerate={filteredDocuments.length > 0} onGenerate={() => generate.mutate({})} onSelectSection={openAssistant} sections={sceneInfo.exam.sections} emptyDescription="先上传试卷或练习资料，再开始整理考试重点。" error={requestMatchesSelection ? generate.error : null} />
        </div>
      ) : null}

      {assistantOpen ? (
        <div className="fixed inset-0 z-50 bg-stone-950/20" onMouseDown={() => setAssistantOpen(false)}>
          <aside className="absolute inset-x-0 bottom-0 max-h-[92vh] overflow-y-auto rounded-t-3xl bg-[#fffdfa] p-4 shadow-2xl sm:inset-y-0 sm:left-auto sm:w-full sm:max-w-md sm:rounded-none" onMouseDown={(event) => event.stopPropagation()} aria-label="AI 学习助手">
            <div className="mb-3 flex justify-end"><button className="rounded-lg p-2 hover:bg-stone-100" onClick={() => setAssistantOpen(false)} aria-label="关闭 AI 学习助手"><X className="size-5" /></button></div>
            <CourseAssistant courseId={courseId} courseName={course.name} currentSection={selectedChapter?.title ?? sceneInfo[scene].label} scene={scene} chapterId={scene === 'follow' ? normalizedChapterId : undefined} textbookId={scene === 'textbook' ? selectedTextbookId : undefined} scopeUnassigned={scene === 'follow' && selectedChapterId == null} initialQuestion={assistantQuestion} />
          </aside>
        </div>
      ) : null}

      {chapterEditor ? <ChapterEditorDialog editor={chapterEditor} pending={createChapter.isPending || updateChapter.isPending} error={createChapter.error ?? updateChapter.error} onCancel={() => setChapterEditor(null)} onSave={(title) => chapterEditor.mode === 'create' ? createChapter.mutate(title) : updateChapter.mutate({ id: chapterEditor.chapter.id, title })} /> : null}
      {deleteChapter ? <DeleteChapterDialog chapter={deleteChapter} pending={removeChapter.isPending} onCancel={() => setDeleteChapter(null)} onKeep={() => removeChapter.mutate({ id: deleteChapter.id, action: 'keep_unassigned' })} onDelete={() => removeChapter.mutate({ id: deleteChapter.id, action: 'delete' })} /> : null}
    </section>
  )
}

function filterDocuments(documents: DocumentSummary[], scene: Scene, chapterId: number | null) {
  if (scene === 'textbook') return documents.filter((item) => item.document_type === 'TEXTBOOK')
  if (scene === 'exam') return documents.filter((item) => ['EXAM', 'HOMEWORK'].includes(item.document_type))
  return documents.filter((item) => ['SLIDES', 'HOMEWORK', 'OTHER', 'NOTES'].includes(item.document_type) && item.chapter_id === chapterId)
}

function packageMatchesSelection(packageData: LearningPackage, scene: Scene, chapterId: number | null | undefined, textbookId: number | null) {
  if (packageData.scene !== scene) return false
  if (scene === 'follow') return chapterId == null ? packageData.scope_unassigned : packageData.scope_chapter_id === chapterId
  if (scene === 'textbook') return packageData.scope_document_id === textbookId
  return true
}

function scopeMatchesSelection(scope: GenerationScope, scene: Scene, chapterId: number | null | undefined, textbookId: number | null) {
  if (scene === 'follow') return chapterId == null ? Boolean(scope.unassigned) : scope.chapterId === chapterId
  if (scene === 'textbook') return scope.documentId === textbookId
  return Object.keys(scope).length === 0
}

function LearningSection({ title, packageData, previousPackage, generating, canGenerate, onGenerate, onSelectSection, sections, showInitialGenerate = true, emptyDescription, error }: { title?: string; packageData: LearningPackage | null; previousPackage?: LearningPackage | null; generating: boolean; canGenerate: boolean; onGenerate: () => void; onSelectSection: (section: string) => void; sections: readonly string[]; showInitialGenerate?: boolean; emptyDescription: string; error: Error | null }) {
  const navigate = useNavigate()
  const creditError = error instanceof ApiError && ['insufficient_credits', 'quota_exceeded', 'course_quota_exceeded', 'assistant_quota_exceeded'].includes(error.code) ? error : null
  return (
    <section>
      <div className="mb-3"><h2 className="text-xl font-semibold text-stone-950">{title ? `${title} · AI 整理结果` : 'AI 整理结果'}</h2><p className="mt-1 text-sm text-stone-500">{title ? '只使用当前章节中的资料，结果不会与其他章节混合。' : '仅根据当前场景中的资料生成。'}</p></div>
      {creditError ? (
        <Card className="mb-4 border-amber-200 bg-amber-50/70 p-5">
          <h3 className="font-semibold text-amber-950">您的 AI 整理额度不足</h3>
          <p className="mt-2 text-sm leading-6 text-amber-800">
            {creditError.details.quota_source === 'free_monthly' ? '本月免费 AI 整理次数已经用完。' : '当前课程对应功能的使用次数已经用完。'}
          </p>
          <p className="mt-2 text-sm text-amber-700">剩余次数：{creditError.details.remaining ?? 0}</p>
          {creditError.details.resets_at ? <p className="mt-1 text-xs text-amber-700">免费额度将在 {new Intl.DateTimeFormat('zh-CN', { month: 'long', day: 'numeric' }).format(new Date(creditError.details.resets_at))} 重置。</p> : null}
          <div className="mt-4 flex flex-wrap gap-3">
            <Button onClick={() => navigate(creditError.details.purchase_url ?? '/pricing')}>查看套餐</Button>
            <Button variant="secondary" onClick={() => navigate(creditError.details.purchase_url ?? '/pricing')}>联系人工开通</Button>
          </div>
        </Card>
      ) : error ? <p className="mb-3 rounded-xl bg-orange-50 px-3 py-2.5 text-sm text-orange-700">{error instanceof ApiError ? error.message : '暂时无法开始整理，请稍后重试。'}</p> : null}
      <LearningPackageView learningPackage={packageData} previousPackage={previousPackage} generating={generating} canGenerate={canGenerate} onGenerate={onGenerate} onSelectSection={onSelectSection} allowedSections={[...sections]} showInitialGenerate={showInitialGenerate} emptyDescription={emptyDescription} />
    </section>
  )
}

function TextbookKnowledgeSection({ courseId }: { courseId: string | undefined }) {
  const knowledge = useCourseKnowledge(courseId)
  const navigate = useNavigate()
  if (knowledge.isPending) return <StatePanel variant="loading" title="正在读取教材知识卡片" />
  if (knowledge.isError || !knowledge.data) return <StatePanel variant="error" title="暂时无法读取知识卡片" action={<Button onClick={() => knowledge.refetch()}>重新加载</Button>} />
  if (!knowledge.data.items.length) return <StatePanel variant="empty" title="还没有教材知识卡片" description="教材完成解析后，知识主题会直接显示在这里。" />
  return (
    <section>
      <div className="flex items-end justify-between gap-4"><div><h2 className="text-xl font-semibold text-stone-950">教材知识卡片</h2><p className="mt-1 text-sm text-stone-500">来自已解析教材的知识主题。</p></div><span className="text-sm text-stone-400">{knowledge.data.knowledge_count} 张</span></div>
      <div className="mt-4 grid gap-4 md:grid-cols-2 xl:grid-cols-3">{knowledge.data.items.map((item) => <KnowledgeCard key={item.id} knowledge={item} onOpen={() => navigate(`/courses/${courseId}/knowledge/${item.id}`)} />)}</div>
    </section>
  )
}

function TextbookList({ documents, selectedId, onSelect, onGenerate, generating }: { documents: DocumentSummary[]; selectedId: number | null; onSelect: (id: number) => void; onGenerate: (id: number) => void; generating: boolean }) {
  if (!documents.length) return <StatePanel variant="empty" title="还没有教材" description="上传教材后，可以为每本教材独立生成知识大纲和公式整理。" />
  return (
    <div className="grid gap-3 md:grid-cols-2">
      {documents.map((item) => (
        <Card className={`p-5 ${selectedId === item.id ? 'border-teal-300 ring-2 ring-teal-100' : ''}`} key={item.id}>
          <button className="flex w-full items-start gap-3 text-left" onClick={() => onSelect(item.id)}>
            <BookOpen className="mt-1 size-5 text-teal-700" />
            <div className="min-w-0 flex-1"><h3 className="truncate font-semibold text-stone-900">{item.name}</h3><p className="mt-1 text-xs text-stone-500">{item.status === 'completed' ? '已完成文本分析' : '等待解析知识大纲'}</p></div>
          </button>
          <Button className="mt-4" variant="secondary" disabled={generating} onClick={() => onGenerate(item.id)}>{generating && selectedId === item.id ? '正在解析' : '解析这本教材'}</Button>
        </Card>
      ))}
    </div>
  )
}

function ChapterMaterials({ documents, chapters, current, onMove }: { documents: DocumentSummary[]; chapters: Chapter[]; current: Chapter | null; onMove: (documentId: number, chapterId: number | null) => void }) {
  if (!documents.length) return null
  return (
    <Card className="p-5">
      <h2 className="font-semibold text-stone-900">{current?.title ?? '未分章节'} · 资料归类</h2>
      <div className="mt-4 space-y-3">
        {documents.map((item) => (
          <div className="flex flex-col gap-2 rounded-xl border border-stone-200 p-3 sm:flex-row sm:items-center" key={item.id}>
            <FileText className="size-4 text-stone-400" /><span className="min-w-0 flex-1 truncate text-sm text-stone-700">{item.name}</span>
            <select className="rounded-lg border border-stone-200 bg-white px-2 py-1.5 text-xs" value={item.chapter_id ?? ''} onChange={(event) => onMove(item.id, event.target.value ? Number(event.target.value) : null)} aria-label={`移动${item.name}到章节`}>
              <option value="">未分章节</option>{chapters.map((chapter) => <option value={chapter.id} key={chapter.id}>{chapter.title}</option>)}
            </select>
          </div>
        ))}
      </div>
    </Card>
  )
}

function ChapterEditorDialog({ editor, pending, error, onCancel, onSave }: { editor: ChapterEditor; pending: boolean; error: Error | null; onCancel: () => void; onSave: (title: string) => void }) {
  const [title, setTitle] = useState(editor.mode === 'rename' ? editor.chapter.title : '')
  function submit(event: FormEvent) { event.preventDefault(); if (title.trim()) onSave(title.trim()) }
  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-stone-950/30 p-4" onMouseDown={onCancel}>
      <Card className="w-full max-w-md p-6" onMouseDown={(event) => event.stopPropagation()}>
        <h2 className="text-xl font-semibold text-stone-950">{editor.mode === 'create' ? '添加章节' : '重命名章节'}</h2>
        <p className="mt-2 text-sm text-stone-500">使用课程大纲中的章节名称，之后仍可调整顺序。</p>
        <form className="mt-5" onSubmit={submit}>
          <label className="text-sm font-medium text-stone-700">章节名称<input className="mt-2 h-11 w-full rounded-xl border border-stone-200 px-3 outline-none focus:border-teal-600 focus:ring-4 focus:ring-teal-100" value={title} onChange={(event) => setTitle(event.target.value)} maxLength={200} autoFocus required /></label>
          {error ? <p className="mt-3 text-sm text-orange-700">章节保存失败，请稍后重试。</p> : null}
          <div className="mt-5 flex justify-end gap-3"><Button variant="secondary" onClick={onCancel} disabled={pending}>取消</Button><Button type="submit" disabled={pending || !title.trim()}>{pending ? '正在保存' : '保存章节'}</Button></div>
        </form>
      </Card>
    </div>
  )
}

function DeleteChapterDialog({ chapter, pending, onCancel, onKeep, onDelete }: { chapter: Chapter; pending: boolean; onCancel: () => void; onKeep: () => void; onDelete: () => void }) {
  const [confirmDanger, setConfirmDanger] = useState(false)
  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-stone-950/30 p-4">
      <Card className="w-full max-w-lg p-6">
        <h2 className="text-xl font-semibold text-stone-950">删除“{chapter.title}”？</h2>
        <p className="mt-2 text-sm leading-6 text-stone-500">这个章节包含 {chapter.document_count} 份资料。请选择如何处理资料。</p>
        {!confirmDanger ? (
          <div className="mt-6 space-y-3">
            <Button fullWidth onClick={onKeep} disabled={pending}>保留资料并移到未分章节</Button>
            <Button fullWidth variant="danger" onClick={() => setConfirmDanger(true)} disabled={pending}><Trash2 className="size-4" />删除章节和其中资料</Button>
            <Button fullWidth variant="secondary" onClick={onCancel} disabled={pending}>取消</Button>
          </div>
        ) : (
          <div className="mt-6 rounded-2xl border border-red-200 bg-red-50 p-4">
            <p className="font-semibold text-red-800">再次确认永久删除</p>
            <p className="mt-2 text-sm leading-6 text-red-700">章节内文件、分析结果和关联内容将被永久删除，无法恢复。</p>
            <div className="mt-4 flex flex-col gap-3 sm:flex-row"><Button variant="danger" onClick={onDelete} disabled={pending}><Trash2 className="size-4" />{pending ? '正在删除' : '确认永久删除'}</Button><Button variant="secondary" onClick={() => setConfirmDanger(false)} disabled={pending}>返回上一步</Button></div>
          </div>
        )}
      </Card>
    </div>
  )
}
