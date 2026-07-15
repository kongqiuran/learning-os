import { Plus } from 'lucide-react'

import { Button } from '../components/ui/Button'
import { StatePanel } from '../components/ui/StatePanel'

export function DashboardPage() {
  return (
    <section>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-sm font-semibold text-blue-600">我的学习空间</p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight text-slate-950">欢迎回来</h1>
          <p className="mt-2 text-sm text-slate-500">课程、资料和知识将在这里持续积累。</p>
        </div>
        <Button disabled title="课程创建将在 Dashboard MVP 中接入">
          <Plus className="size-4" /> 创建学习空间
        </Button>
      </div>
      <div className="mt-8">
        <StatePanel
          variant="empty"
          title="课程数据尚未接入"
          description="React 基础迁移已经完成。下一阶段将接入你的真实课程、文件数量和最近更新信息。"
        />
      </div>
    </section>
  )
}
