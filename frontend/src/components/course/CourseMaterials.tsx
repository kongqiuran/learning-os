import { BookOpen, ClipboardList, FileCheck2, FilePlus2, Files, NotebookPen, Presentation } from 'lucide-react'
import { useState } from 'react'

import { useDeleteDocument } from '../../hooks/useCourseSpace'
import type { DocumentSummary } from '../../types/api'
import { FileCard } from '../domain/FileCard'
import { Button } from '../ui/Button'
import { Card } from '../ui/Card'
import { StatePanel } from '../ui/StatePanel'
import { UploadDocumentDialog } from './UploadDocumentDialog'
import { PRIMARY_UPLOAD_CATEGORIES, type DocumentType } from './uploadCategories'

const categoryIcons = {
  TEXTBOOK: BookOpen,
  SLIDES: Presentation,
  NOTES: NotebookPen,
  EXAM: FileCheck2,
  HOMEWORK: ClipboardList,
  OTHER: Files,
} as const

export function CourseMaterials({ courseId, documents }: { courseId: string | undefined; documents: DocumentSummary[] }) {
  const [uploadOpen, setUploadOpen] = useState(false)
  const [uploadType, setUploadType] = useState<DocumentType>('TEXTBOOK')
  const deleteDocument = useDeleteDocument(courseId)

  function openUpload(documentType: DocumentType) {
    setUploadType(documentType)
    setUploadOpen(true)
  }

  return (
    <section id="course-materials" className="scroll-mt-24">
      <Card className="p-5 sm:p-6">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-blue-600">Materials</p>
            <h2 className="mt-1 text-xl font-semibold text-slate-950">课程资料</h2>
            <p className="mt-1 text-sm text-slate-500">这些资料将作为课程内容整理和理解辅助的基础。</p>
          </div>
          <Button variant="secondary" onClick={() => openUpload('TEXTBOOK')}><FilePlus2 className="size-4" /> 上传教材</Button>
        </div>

        <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          {PRIMARY_UPLOAD_CATEGORIES.map((category) => {
            const Icon = categoryIcons[category.type]
            return (
              <button
                key={category.type}
                type="button"
                className="group rounded-2xl border border-slate-200 bg-white p-4 text-left transition hover:border-blue-300 hover:bg-blue-50/50 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-blue-100"
                onClick={() => openUpload(category.type)}
              >
                <span className="grid size-9 place-items-center rounded-xl bg-blue-50 text-blue-600 group-hover:bg-white">
                  <Icon className="size-4" />
                </span>
                <strong className="mt-3 block text-sm text-slate-900">{category.action}</strong>
                <span className="mt-1 block text-xs leading-5 text-slate-500">{category.description}</span>
              </button>
            )
          })}
        </div>

        {documents.length === 0 ? (
          <div className="mt-5">
            <StatePanel
              variant="empty"
              title="添加第一份课程资料"
              description="从上方选择资料类别。建议先上传教材或课件，再补充笔记和试卷。"
            />
          </div>
        ) : (
          <div className="mt-5 space-y-3">
            {documents.map((document) => (
              <FileCard
                key={document.id}
                file={document}
                deleting={deleteDocument.isPending && deleteDocument.variables === document.id}
                onDelete={() => deleteDocument.mutate(document.id)}
              />
            ))}
          </div>
        )}
        {deleteDocument.isError ? <p className="mt-3 text-sm text-orange-700">资料删除失败，请刷新后重试。</p> : null}
      </Card>
      <UploadDocumentDialog
        courseId={courseId}
        open={uploadOpen}
        initialDocumentType={uploadType}
        onClose={() => setUploadOpen(false)}
      />
    </section>
  )
}
