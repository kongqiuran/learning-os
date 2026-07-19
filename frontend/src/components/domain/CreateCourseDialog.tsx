import { X } from 'lucide-react'
import { useEffect, useState, type FormEvent } from 'react'

import { useCreateCourse } from '../../hooks/useDashboard'
import { ApiError } from '../../lib/api'
import { Button } from '../ui/Button'

interface CreateCourseDialogProps {
  open: boolean
  onClose: () => void
}

export function CreateCourseDialog({ open, onClose }: CreateCourseDialogProps) {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const createCourse = useCreateCourse()

  useEffect(() => {
    if (!open) return
    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', closeOnEscape)
    return () => window.removeEventListener('keydown', closeOnEscape)
  }, [open, onClose])

  if (!open) return null

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    createCourse.mutate(
      { name, description: description || undefined },
      {
        onSuccess: () => {
          setName('')
          setDescription('')
          onClose()
        },
      },
    )
  }

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/30 p-4" onMouseDown={onClose}>
      <section
        className="w-full max-w-lg rounded-2xl border border-slate-200 bg-white p-6 shadow-[0_20px_60px_rgba(15,23,42,0.16)]"
        role="dialog"
        aria-modal="true"
        aria-labelledby="create-course-title"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-sm font-semibold text-blue-600">新课程</p>
            <h2 id="create-course-title" className="mt-1 text-xl font-semibold text-slate-950">创建课程</h2>
            <p className="mt-2 text-sm leading-6 text-slate-500">先建立课程，下一步再添加对应的学习资料。</p>
          </div>
          <button className="grid size-9 place-items-center rounded-xl text-slate-500 hover:bg-slate-100" onClick={onClose} aria-label="关闭创建课程窗口">
            <X className="size-4" />
          </button>
        </div>
        <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
          <label className="block text-sm font-medium text-slate-700">
            课程名称
            <input
              className="mt-2 h-11 w-full rounded-xl border border-slate-200 px-3 outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
              value={name}
              onChange={(event) => setName(event.target.value)}
              placeholder="例如：信号与系统"
              maxLength={200}
              autoFocus
              required
            />
          </label>
          <label className="block text-sm font-medium text-slate-700">
            课程描述 <span className="font-normal text-slate-400">（可选）</span>
            <textarea
              className="mt-2 min-h-24 w-full resize-y rounded-xl border border-slate-200 px-3 py-2.5 outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              placeholder="记录学期或课程目标"
            />
          </label>
          {createCourse.isError ? (
            <p className="rounded-xl bg-orange-50 px-3 py-2.5 text-sm text-orange-700">
              {createCourse.error instanceof ApiError ? createCourse.error.message : '创建课程失败，请稍后重试。'}
            </p>
          ) : null}
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="secondary" onClick={onClose}>取消</Button>
            <Button type="submit" disabled={createCourse.isPending || !name.trim()}>
              {createCourse.isPending ? '正在创建…' : '创建课程'}
            </Button>
          </div>
        </form>
      </section>
    </div>
  )
}
