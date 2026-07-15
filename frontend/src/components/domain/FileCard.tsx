import { CircleAlert, CircleCheck, Clock3, FileText, LoaderCircle } from 'lucide-react'

import type { FileSummary } from '../../types/api'
import { Card } from '../ui/Card'

const statusView = {
  uploaded: { label: '等待整理', icon: Clock3, className: 'bg-slate-100 text-slate-600' },
  processing: { label: '正在整理', icon: LoaderCircle, className: 'bg-blue-50 text-blue-700' },
  completed: { label: '已生成知识', icon: CircleCheck, className: 'bg-green-50 text-green-700' },
  failed: { label: '整理失败', icon: CircleAlert, className: 'bg-orange-50 text-orange-700' },
}

export function FileCard({ file }: { file: FileSummary }) {
  const status = statusView[file.status]
  const StatusIcon = status.icon

  return (
    <Card className="flex items-center gap-4 p-4">
      <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-slate-100 text-slate-600">
        <FileText className="size-5" />
      </span>
      <div className="min-w-0 flex-1">
        <h3 className="truncate text-sm font-semibold text-slate-900">{file.name}</h3>
        <p className="mt-1 text-xs text-slate-500">{file.type} · {file.sizeLabel}</p>
      </div>
      <span className={`inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-medium ${status.className}`}>
        <StatusIcon className={file.status === 'processing' ? 'size-3.5 animate-spin' : 'size-3.5'} />
        {status.label}
      </span>
    </Card>
  )
}
