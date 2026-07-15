import { CircleAlert, CircleCheck, Clock3, FileText, LoaderCircle, MoreHorizontal, Trash2 } from 'lucide-react'
import { useState } from 'react'

import type { DocumentSummary } from '../../types/api'
import { Card } from '../ui/Card'

const statusView = {
  uploaded: { label: '等待整理', icon: Clock3, className: 'bg-slate-100 text-slate-600' },
  processing: { label: '正在处理', icon: LoaderCircle, className: 'bg-blue-50 text-blue-700' },
  completed: { label: '已生成内容', icon: CircleCheck, className: 'bg-green-50 text-green-700' },
  failed: { label: '处理失败', icon: CircleAlert, className: 'bg-orange-50 text-orange-700' },
}

export function FileCard({
  file,
  onDelete,
  deleting = false,
}: {
  file: DocumentSummary
  onDelete?: () => void
  deleting?: boolean
}) {
  const [menuOpen, setMenuOpen] = useState(false)
  const status = statusView[file.status]
  const StatusIcon = status.icon

  return (
    <Card className="flex items-start gap-3 p-4">
      <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-slate-100 text-slate-600">
        <FileText className="size-5" />
      </span>
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div className="min-w-0">
            <h3 className="truncate text-sm font-semibold text-slate-900">{file.name}</h3>
            <p className="mt-1 text-xs text-slate-500">{fileTypeLabel(file)} · {formatBytes(file.file_size)}</p>
          </div>
          <span className={`inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-medium ${status.className}`}>
            <StatusIcon className={file.status === 'processing' ? 'size-3.5 animate-spin' : 'size-3.5'} />
            {status.label}
          </span>
        </div>
        <p className="mt-3 text-xs text-slate-400">上传于 {formatDateTime(file.uploaded_at)}</p>
      </div>
      {onDelete ? (
        <div className="relative shrink-0">
          <button
            type="button"
            className="grid size-8 place-items-center rounded-lg text-slate-400 hover:bg-slate-100 hover:text-slate-700"
            aria-label={`${file.name} 更多操作`}
            aria-expanded={menuOpen}
            onClick={() => setMenuOpen((open) => !open)}
          >
            <MoreHorizontal className="size-4" />
          </button>
          {menuOpen ? (
            <div className="absolute right-0 top-9 z-20 w-32 rounded-xl border border-slate-200 bg-white p-1.5 shadow-lg">
              <button
                type="button"
                className="flex w-full items-center gap-2 rounded-lg px-2.5 py-2 text-left text-xs font-medium text-orange-700 hover:bg-orange-50 disabled:opacity-50"
                onClick={() => { setMenuOpen(false); onDelete() }}
                disabled={deleting}
              >
                <Trash2 className="size-3.5" /> {deleting ? '正在删除' : '删除资料'}
              </button>
            </div>
          ) : null}
        </div>
      ) : null}
    </Card>
  )
}

function fileTypeLabel(file: DocumentSummary) {
  const extension = file.name.split('.').pop()?.toUpperCase()
  return extension || file.document_type || file.mime_type
}

function formatBytes(value: number) {
  if (value < 1024) return `${value} B`
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`
  return `${(value / (1024 * 1024)).toFixed(1)} MB`
}

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}
