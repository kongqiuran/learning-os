// 文件说明：上传资料弹窗组件。useState/useEffect 来自 React；FormData 和文件选择 input 是浏览器能力；它负责选择文件、显示进度并调用上传接口。
import { Upload, X } from 'lucide-react'
import { useEffect, useState, type FormEvent } from 'react'

import { useUploadDocument } from '../../hooks/useCourseSpace'
import { ApiError, type UploadProgress } from '../../lib/api'
import { Button } from '../ui/Button'
import { UPLOAD_CATEGORIES, type DocumentType } from './uploadCategories'

// UploadDocumentDialog 是“上传课程资料”的弹窗组件。
// 它负责选择文件、选择资料类型、显示上传进度、调用后端上传接口。
export function UploadDocumentDialog({
  // courseId 告诉后端要把文件上传到哪一门课程。
  courseId,
  // open 决定弹窗是否显示。false 时组件直接返回 null，不渲染任何内容。
  open,
  // initialDocumentType 是弹窗打开时默认选中的资料类型。
  initialDocumentType,
  // allowedDocumentTypes 控制当前场景允许上传哪些资料类型。
  allowedDocumentTypes,
  // chapterId 表示资料要归属到哪个章节；可能为空，表示未分章节。
  chapterId,
  // onUploaded 是上传成功后的回调，父组件可用它刷新页面或关闭引导。
  onUploaded,
  // onClose 是关闭弹窗的回调，由父组件控制 open 状态。
  onClose,
}: {
  courseId: string | undefined
  open: boolean
  initialDocumentType: DocumentType
  allowedDocumentTypes: DocumentType[]
  chapterId?: number | null
  onUploaded?: () => void
  onClose: () => void
}) {
  // file 保存用户选择的本地文件。初始为 null，表示还没选文件。
  const [file, setFile] = useState<File | null>(null)
  // documentType 保存当前选中的资料分类，例如教材、课件、笔记等。
  const [documentType, setDocumentType] = useState<DocumentType>(initialDocumentType)
  // progress 保存上传进度，例如 uploading 35% 或 saving 100%。
  const [progress, setProgress] = useState<UploadProgress | null>(null)
  // useUploadDocument 封装上传接口。upload.mutate 会发请求；upload.isPending 表示正在上传。
  const upload = useUploadDocument(courseId)

  useEffect(() => {
    // 弹窗没打开时，不需要绑定键盘事件，也不需要初始化状态。
    if (!open) return
    // 每次打开弹窗，都重置为父组件传入的默认资料类型，并清空上一次上传进度。
    setDocumentType(initialDocumentType)
    setProgress(null)
    function closeOnEscape(event: KeyboardEvent) {
      // event.key === 'Escape' 表示用户按了 Esc 键。
      // 上传中不允许关闭，是为了避免用户误以为上传被正常取消或完成。
      if (event.key === 'Escape' && !upload.isPending) onClose()
    }
    window.addEventListener('keydown', closeOnEscape)
    // return 里的函数叫“清理函数”。组件关闭或依赖变化时会执行，避免重复绑定事件。
    return () => window.removeEventListener('keydown', closeOnEscape)
  }, [initialDocumentType, open, onClose, upload.isPending])

  // React 组件返回 null 表示什么都不显示。
  if (!open) return null

  function handleSubmit(event: FormEvent) {
    // 阻止浏览器默认表单提交刷新页面，改用前端异步上传。
    event.preventDefault()
    // 没选文件时直接退出，不调用接口。
    if (!file) return
    upload.mutate(
      // 第一个参数是 mutationFn 需要的数据。
      // onProgress: setProgress 表示上传函数每次拿到进度时，直接更新本组件 progress 状态。
      { file, documentType, chapterId, onProgress: setProgress },
      {
        // 第二个参数是本次请求的回调配置。上传成功后清空文件并关闭弹窗。
        onSuccess: () => {
          setFile(null)
          onClose()
          // ?. 表示如果父组件传了 onUploaded 就调用；没传也不会报错。
          onUploaded?.()
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
            {/*
              accept 告诉浏览器文件选择器优先展示这些格式；真正安全校验仍然要以后端为准。
              event.target.files 是用户选中的文件列表；?.[0] 取第一份文件。
              ?? null 表示没选到文件时保存 null。
            */}
            <input
              className="sr-only"
              type="file"
              accept=".pdf,.pptx,.txt,.md,application/pdf,application/vnd.openxmlformats-officedocument.presentationml.presentation,text/plain,text/markdown"
              onChange={(event) => setFile(event.target.files?.[0] ?? null)}
            />
          </label>
          <fieldset>
            <legend className="text-sm font-medium text-slate-700">这份资料属于哪一类？</legend>
            <div className="mt-2 grid grid-cols-2 gap-2 sm:grid-cols-3">
              {UPLOAD_CATEGORIES.filter((category) => allowedDocumentTypes.includes(category.type)).map((category) => (
                <button
                  key={category.type}
                  type="button"
                  className={`rounded-xl border px-3 py-2.5 text-left transition ${
                    documentType === category.type
                      ? 'border-blue-500 bg-blue-50 text-blue-800 ring-2 ring-blue-100'
                      : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300'
                  }`}
                  onClick={() => setDocumentType(category.type)}
                  aria-pressed={documentType === category.type}
                >
                  <strong className="block text-sm">{category.label}</strong>
                  <span className="mt-0.5 block text-[11px] leading-4 text-slate-400">{category.description}</span>
                </button>
              ))}
            </div>
          </fieldset>
          {upload.isPending && progress ? (
            <div className="rounded-xl bg-blue-50 px-3 py-3" role="status" aria-live="polite">
              <div className="flex items-center justify-between text-sm font-medium text-blue-800">
                <span>{progress.phase === 'saving' ? '服务器保存中' : '正在上传'}</span>
                <span>{progress.percent}%</span>
              </div>
              <div className="mt-2 h-2 overflow-hidden rounded-full bg-blue-100">
                <div className="h-full rounded-full bg-blue-600 transition-[width] duration-200" style={{ width: `${progress.percent}%` }} />
              </div>
            </div>
          ) : null}
          {upload.isError ? <p className="rounded-xl bg-orange-50 px-3 py-2.5 text-sm text-orange-700">{upload.error instanceof ApiError ? upload.error.message : '资料上传失败，请稍后重试。'} 文件仍已选中，可以直接重新上传。</p> : null}
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="secondary" onClick={onClose} disabled={upload.isPending}>取消</Button>
            <Button type="submit" disabled={!file || upload.isPending}>{upload.isPending ? (progress?.phase === 'saving' ? '服务器保存中' : `正在上传 ${progress?.percent ?? 0}%`) : upload.isError ? '重新上传' : '上传资料'}</Button>
          </div>
        </form>
      </section>
    </div>
  )
}
