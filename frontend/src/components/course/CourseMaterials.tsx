import { FilePlus2 } from 'lucide-react'
import { useState } from 'react'

import { useDeleteDocument } from '../../hooks/useCourseSpace'
import type { DocumentSummary } from '../../types/api'
import { FileCard } from '../domain/FileCard'
import { Button } from '../ui/Button'
import { Card } from '../ui/Card'
import { StatePanel } from '../ui/StatePanel'
import { UploadDocumentDialog } from './UploadDocumentDialog'

export function CourseMaterials({ courseId, documents }: { courseId: string | undefined; documents: DocumentSummary[] }) {
  const [uploadOpen, setUploadOpen] = useState(false)
  const deleteDocument = useDeleteDocument(courseId)

  return (
    <section id="course-materials" className="scroll-mt-24">
      <Card className="p-5 sm:p-6">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-blue-600">Materials</p>
            <h2 className="mt-1 text-xl font-semibold text-slate-950">课程资料</h2>
            <p className="mt-1 text-sm text-slate-500">这些资料将作为课程内容整理和理解辅助的基础。</p>
          </div>
          <Button variant="secondary" onClick={() => setUploadOpen(true)}><FilePlus2 className="size-4" /> 上传资料</Button>
        </div>

        {documents.length === 0 ? (
          <div className="mt-5">
            <StatePanel
              variant="empty"
              title="添加第一份课程资料"
              description="上传教材、课件或笔记后，即可开始整理课程学习内容。"
              action={<Button onClick={() => setUploadOpen(true)}><FilePlus2 className="size-4" /> 上传资料</Button>}
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
      <UploadDocumentDialog courseId={courseId} open={uploadOpen} onClose={() => setUploadOpen(false)} />
    </section>
  )
}
