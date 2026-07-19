import { ArrowLeft, BookOpen, Bot, FileText, MoreHorizontal, Plus, Trash2, X } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { NavLink, useNavigate, useParams } from 'react-router-dom'

import { CourseAssistant } from '../components/course/CourseAssistant'
import { CourseMaterials } from '../components/course/CourseMaterials'
import { LearningPackageView } from '../components/course/LearningPackageView'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { StatePanel } from '../components/ui/StatePanel'
import { courseSpaceQueryKey, useCourseSpace, useGenerationTask } from '../hooks/useCourseSpace'
import { useCurrentUser } from '../hooks/useCurrentUser'
import { api } from '../lib/api'
import type { Chapter, DocumentSummary } from '../types/api'

type Scene = 'follow' | 'textbook' | 'exam'
const sceneInfo = {
  follow: { label: '跟课资料', description: '按老师进度管理课件、练习和补充资料。', sections: ['chapter_summary', 'key_points'] },
  textbook: { label: '教材解析', description: '把教材整理成知识大纲、公式和知识卡片。', sections: ['course_map', 'formula_book'] },
  exam: { label: '考试冲刺', description: '从真实试卷和练习中提炼考点与行动清单。', sections: ['exam_focus', 'questions', 'exam_strategy', 'study_strategy'] },
} as const

export function CourseSpacePage({ scene }: { scene: Scene }) {
  const { courseId } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const currentUser = useCurrentUser()
  const courseSpace = useCourseSpace(courseId)
  const [assistantOpen, setAssistantOpen] = useState(false)
  const [selectedChapterId, setSelectedChapterId] = useState<number | null>(null)
  const [deleteChapter, setDeleteChapter] = useState<Chapter | null>(null)
  const [taskId, setTaskId] = useState<number | null>(null)
  const task = useGenerationTask(courseId, taskId)
  const scenePackage = courseSpace.data?.scene_packages?.[scene] ?? courseSpace.data?.learning_package ?? null

  useEffect(() => { if (currentUser.data && courseId) { localStorage.setItem(`learning-os:recent-course:${currentUser.data.user.id}`, courseId); localStorage.setItem(`learning-os:recent-scene:${currentUser.data.user.id}:${courseId}`, scene) } }, [courseId, currentUser.data, scene])
  useEffect(() => { if (!selectedChapterId && courseSpace.data?.chapters.length) setSelectedChapterId(courseSpace.data.chapters[0].id) }, [courseSpace.data?.chapters, selectedChapterId])
  useEffect(() => { if (task.data?.status === 'completed' || task.data?.status === 'failed') { void queryClient.invalidateQueries({ queryKey: courseSpaceQueryKey(courseId) }); setTaskId(null) } }, [courseId, queryClient, task.data?.status])

  const refresh = () => queryClient.invalidateQueries({ queryKey: courseSpaceQueryKey(courseId) })
  const createChapter = useMutation({ mutationFn: (title: string) => api.createChapter(courseId!, title), onSuccess: async (chapter) => { setSelectedChapterId(chapter.id); await refresh() } })
  const removeChapter = useMutation({ mutationFn: ({ id, action }: { id: number; action: 'keep_unassigned' | 'delete' }) => api.deleteChapter(courseId!, id, action), onSuccess: async () => { setDeleteChapter(null); setSelectedChapterId(null); await refresh() } })
  const moveDocument = useMutation({ mutationFn: ({ documentId, chapterId }: { documentId: number; chapterId: number | null }) => api.moveDocument(courseId!, documentId, chapterId), onSuccess: refresh })
  const generate = useMutation({ mutationFn: (scopeDocumentId?: number) => api.generateScene(courseId!, scene, scopeDocumentId), onSuccess: (result) => setTaskId(result.id) })

  if (!courseSpace.data) return courseSpace.isPending ? <StatePanel variant="loading" title="正在打开课程" /> : <StatePanel variant="error" title="无法打开课程" action={<Button onClick={() => navigate('/dashboard')}>返回课程列表</Button>} />
  const { course, documents, chapters } = courseSpace.data
  const displayedPackage = task.data ?? scenePackage
  const isGenerating = generate.isPending || displayedPackage?.status === 'pending' || displayedPackage?.status === 'processing'
  const selectedChapter = chapters.find((item) => item.id === selectedChapterId) ?? null
  const filteredDocuments = filterDocuments(documents, scene, selectedChapterId)

  function addChapter() { const title = window.prompt('输入章节名称'); if (title?.trim()) createChapter.mutate(title.trim()) }

  return <section className="mx-auto max-w-[1500px]">
    <div className="flex items-center justify-between gap-4"><Button variant="ghost" onClick={() => navigate('/dashboard')}><ArrowLeft className="size-4" />我的课程</Button><Button variant="secondary" onClick={() => setAssistantOpen(true)}><Bot className="size-4" />AI 学习助手</Button></div>
    <header className="mt-4 border-b border-stone-200 pb-0"><h1 className="text-3xl font-semibold tracking-tight text-stone-950">{course.name}</h1><p className="mt-2 text-sm text-stone-500">{sceneInfo[scene].description}</p><nav className="mt-6 flex gap-7 overflow-x-auto">{(['follow','textbook','exam'] as Scene[]).map((item) => <NavLink key={item} to={`/courses/${courseId}/${item}`} className={({isActive}) => `border-b-2 pb-3 text-sm font-semibold whitespace-nowrap ${isActive ? 'border-teal-700 text-teal-800' : 'border-transparent text-stone-500 hover:text-stone-900'}`}>{sceneInfo[item].label}</NavLink>)}</nav></header>

    {scene === 'follow' ? <div className="mt-6 grid gap-5 lg:grid-cols-[250px_minmax(0,1fr)]"><Card className="p-4 lg:sticky lg:top-24"><div className="flex items-center justify-between"><h2 className="font-semibold text-stone-900">章节</h2><button className="rounded-lg p-2 text-teal-700 hover:bg-teal-50" onClick={addChapter} aria-label="添加章节"><Plus className="size-4" /></button></div><button className={`mt-4 w-full rounded-xl px-3 py-2 text-left text-sm ${selectedChapterId === null ? 'bg-teal-50 text-teal-800' : 'text-stone-600 hover:bg-stone-50'}`} onClick={() => setSelectedChapterId(null)}>未分章节</button><div className="mt-1 space-y-1">{chapters.map((chapter) => <div className={`group flex items-center rounded-xl ${chapter.id === selectedChapterId ? 'bg-teal-50' : 'hover:bg-stone-50'}`} key={chapter.id}><button className="min-w-0 flex-1 px-3 py-2 text-left" onClick={() => setSelectedChapterId(chapter.id)}><span className="block truncate text-sm font-medium text-stone-800">{chapter.title}</span><span className="text-xs text-stone-400">{chapter.document_count} 份资料</span></button><button className="mr-1 rounded-lg p-2 text-stone-400 opacity-0 group-hover:opacity-100" onClick={() => setDeleteChapter(chapter)} aria-label={`删除${chapter.title}`}><MoreHorizontal className="size-4" /></button></div>)}</div></Card><div className="min-w-0 space-y-5"><ChapterMaterials documents={filteredDocuments} chapters={chapters} current={selectedChapter} courseId={courseId!} onMove={(documentId, chapterId) => moveDocument.mutate({documentId, chapterId})} /><CourseMaterials courseId={courseId} documents={filteredDocuments} /><LearningSection packageData={displayedPackage} generating={isGenerating} canGenerate={documents.some((item) => ['SLIDES','HOMEWORK','OTHER','NOTES'].includes(item.document_type))} onGenerate={() => generate.mutate(undefined)} sections={sceneInfo.follow.sections} /></div></div> : null}

    {scene === 'textbook' ? <div className="mt-6 space-y-5"><CourseMaterials courseId={courseId} documents={filteredDocuments} /><TextbookList documents={filteredDocuments} onGenerate={(id) => generate.mutate(id)} generating={isGenerating} /><LearningSection packageData={displayedPackage} generating={isGenerating} canGenerate={filteredDocuments.length > 0} onGenerate={() => filteredDocuments[0] && generate.mutate(filteredDocuments[0].id)} sections={sceneInfo.textbook.sections} /><Button variant="secondary" onClick={() => navigate(`/courses/${courseId}/knowledge`)}><BookOpen className="size-4" />查看知识卡片</Button></div> : null}
    {scene === 'exam' ? <div className="mt-6 space-y-5"><CourseMaterials courseId={courseId} documents={filteredDocuments} /><LearningSection packageData={displayedPackage} generating={isGenerating} canGenerate={filteredDocuments.length > 0} onGenerate={() => generate.mutate(undefined)} sections={sceneInfo.exam.sections} /></div> : null}

    {assistantOpen ? <div className="fixed inset-0 z-50 bg-stone-950/20" onMouseDown={() => setAssistantOpen(false)}><aside className="absolute inset-y-0 right-0 w-full max-w-md overflow-y-auto bg-[#fffdfa] p-4 shadow-2xl" onMouseDown={(event) => event.stopPropagation()}><div className="mb-3 flex justify-end"><button className="rounded-lg p-2 hover:bg-stone-100" onClick={() => setAssistantOpen(false)}><X className="size-5" /></button></div><CourseAssistant courseId={courseId} courseName={course.name} currentSection={selectedChapter?.title ?? sceneInfo[scene].label} scene={scene} chapterId={selectedChapterId} /></aside></div> : null}
    {deleteChapter ? <DeleteChapterDialog chapter={deleteChapter} pending={removeChapter.isPending} onCancel={() => setDeleteChapter(null)} onKeep={() => removeChapter.mutate({id: deleteChapter.id, action:'keep_unassigned'})} onDelete={() => { if (window.confirm(`将永久删除“${deleteChapter.title}”中的全部资料和生成内容，确定继续吗？`)) removeChapter.mutate({id: deleteChapter.id, action:'delete'}) }} /> : null}
  </section>
}

function filterDocuments(documents: DocumentSummary[], scene: Scene, chapterId: number | null) { if (scene === 'textbook') return documents.filter((item) => item.document_type === 'TEXTBOOK'); if (scene === 'exam') return documents.filter((item) => ['EXAM','HOMEWORK'].includes(item.document_type)); return documents.filter((item) => ['SLIDES','HOMEWORK','OTHER','NOTES'].includes(item.document_type) && item.chapter_id === chapterId) }
function LearningSection({packageData, generating, canGenerate, onGenerate, sections}:{packageData:any;generating:boolean;canGenerate:boolean;onGenerate:()=>void;sections:readonly string[]}) { return <section><div className="mb-3 flex items-center justify-between"><div><h2 className="text-xl font-semibold text-stone-950">AI 整理结果</h2><p className="mt-1 text-sm text-stone-500">仅根据当前场景中的资料生成。</p></div></div><LearningPackageView learningPackage={packageData} generating={generating} canGenerate={canGenerate} onGenerate={onGenerate} onSelectSection={() => {}} allowedSections={[...sections]} /></section> }
function TextbookList({documents,onGenerate,generating}:{documents:DocumentSummary[];onGenerate:(id:number)=>void;generating:boolean}) { return documents.length ? <div className="grid gap-3 md:grid-cols-2">{documents.map((item) => <Card className="p-5" key={item.id}><div className="flex items-start gap-3"><BookOpen className="mt-1 size-5 text-teal-700"/><div className="min-w-0 flex-1"><h3 className="truncate font-semibold text-stone-900">{item.name}</h3><p className="mt-1 text-xs text-stone-500">{item.status === 'completed' ? '已完成文本分析' : '等待解析知识大纲'}</p></div></div><Button className="mt-4" variant="secondary" disabled={generating} onClick={() => onGenerate(item.id)}>解析这本教材</Button></Card>)}</div> : null }
function ChapterMaterials({documents,chapters,current,onMove}:{documents:DocumentSummary[];chapters:Chapter[];current:Chapter|null;courseId:string;onMove:(documentId:number,chapterId:number|null)=>void}) { return documents.length ? <Card className="p-5"><h2 className="font-semibold text-stone-900">{current?.title ?? '未分章节'} · 资料归类</h2><div className="mt-4 space-y-3">{documents.map((item) => <div className="flex flex-col gap-2 rounded-xl border border-stone-200 p-3 sm:flex-row sm:items-center" key={item.id}><FileText className="size-4 text-stone-400"/><span className="min-w-0 flex-1 truncate text-sm text-stone-700">{item.name}</span><select className="rounded-lg border border-stone-200 bg-white px-2 py-1.5 text-xs" value={item.chapter_id ?? ''} onChange={(event) => onMove(item.id, event.target.value ? Number(event.target.value) : null)}><option value="">未分章节</option>{chapters.map((chapter) => <option value={chapter.id} key={chapter.id}>{chapter.title}</option>)}</select></div>)}</div></Card> : null }
function DeleteChapterDialog({chapter,pending,onCancel,onKeep,onDelete}:{chapter:Chapter;pending:boolean;onCancel:()=>void;onKeep:()=>void;onDelete:()=>void}) { return <div className="fixed inset-0 z-50 grid place-items-center bg-stone-950/30 p-4"><Card className="w-full max-w-lg p-6"><h2 className="text-xl font-semibold text-stone-950">删除“{chapter.title}”？</h2><p className="mt-2 text-sm leading-6 text-stone-500">这个章节包含 {chapter.document_count} 份资料。请选择如何处理资料。</p><div className="mt-6 space-y-3"><Button fullWidth onClick={onKeep} disabled={pending}>保留资料并移到未分章节</Button><Button fullWidth variant="danger" onClick={onDelete} disabled={pending}><Trash2 className="size-4"/>删除章节和其中资料</Button><Button fullWidth variant="secondary" onClick={onCancel} disabled={pending}>取消</Button></div></Card></div> }
