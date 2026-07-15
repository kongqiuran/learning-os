import { Upload, X } from 'lucide-react'
import { useEffect, useState, type FormEvent } from 'react'

import { useUploadDocument } from '../../hooks/useCourseSpace'
import { ApiError } from '../../lib/api'
import { Button } from '../ui/Button'

export function UploadDocumentDialog({ courseId, open, onClose }: { courseId: string | undefined; open: boolean; onClose: () => void }) {
  const [file, setFile] = useState<File | null>(null)
  const [documentType, setDocumentType] = useState('OTHER')
  const upload = useUploadDocument(courseId)

  useEffect(() => {
    if (!open) return
    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === 'Escape' && !upload.isPending) onClose()
    }
    window.addEventListener('keydown', closeOnEscape)
    return () => window.removeEventListener('keydown', closeOnEscape)
  }, [open, onClose, upload.isPending])

  if (!open) return null

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    if (!file) return
    upload.mutate(
      { file, documentType },
      {
        onSuccess: () => {
          setFile(null)
          setDocumentType('OTHER')
          onClose()
        },
      },
    )
  }

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/30 p-4" onMouseDown={() => !upload.isPending && onClose()}>
      <section
        className="w-full max-w-lg rounded-2xl border border-slate-200 bg-white p-6 shadow-[0_20px_60px_rgba(15,23,42,0.16)]"
        role="dialog"
        aria-modal="true"
        aria-labelledby="upload-document-title"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-sm font-semibold text-blue-600">课程资料</p>
            <h2 id="upload-document-title" className="mt-1 text-xl font-semibold text-slate-950">上传学习资料</h2>
            <p className="mt-2 text-sm leading-6 text-slate-500">支持 PDF、PPTX、TXT 和 MD，单个文件大小遵循当前系统配置。</p>
          </div>
          <button type="button" className="grid size-9 place-items-center rounded-xl text-slate-500 hover:bg-slate-100" onClick={onClose} disabled={upload.isPending} aria-label="关闭上传窗口">
            <X className="size-4" />
          </button>
        </div>
        <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
          <label className="block rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-5 text-center hover:border-blue-300">
            <Upload className="mx-auto size-6 text-blue-600" />
            <span className="mt-2 block text-sm font-medium text-slate-800">{file ? file.name : '选择一份课程资料'}</span>
            <span className="mt-1 block text-xs text-slate-500">PDF · PPTX · TXT · MD</span>
            <input
              className="sr-only"
              type="file"
              accept=".pdf,.pptx,.txt,.md,application/pdf,application/vnd.openxmlformats-officedocument.presentationml.presentation,text/plain,text/markdown"
              onChange={(event) => setFile(event.target.files?.[0] ?? null)}
            />
          </label>
          <label className="block text-sm font-medium text-slate-700">
            资料类型
            <select className="mt-2 h-11 w-full rounded-xl border border-slate-200 bg-white px-3 outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-100" value={documentType} onChange={(event) => setDocumentType(event.target.value)}>
              <option value="OTHER">其他资料</option>
              <option value="TEXTBOOK">教材</option>
              <option value="SLIDES">课程幻灯片</option>
              <option value="NOTES">笔记</option>
              <option value="HOMEWORK">作业</option>
              <option value="EXAM">试卷</option>
            </select>
          </label>
          {upload.isError ? <p className="rounded-xl bg-orange-50 px-3 py-2.5 text-sm text-orange-700">{upload.error instanceof ApiError ? upload.error.message : '资料上传失败，请稍后重试。'}</p> : null}
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="secondary" onClick={onClose} disabled={upload.isPending}>取消</Button>
            <Button type="submit" disabled={!file || upload.isPending}>{upload.isPending ? '正在上传' : '上传资料'}</Button>
          </div>
        </form>
      </section>
    </div>
  )
}
