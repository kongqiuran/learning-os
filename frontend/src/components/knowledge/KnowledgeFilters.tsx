import { Filter } from 'lucide-react'
import type { ReactNode } from 'react'

import { Card } from '../ui/Card'

export interface KnowledgeFilterState {
  sourceFile: string
  importance: string
  viewed: string
}

export function KnowledgeFilters({
  value,
  sourceFiles,
  onChange,
}: {
  value: KnowledgeFilterState
  sourceFiles: string[]
  onChange: (value: KnowledgeFilterState) => void
}) {
  return (
    <Card className="p-4">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center">
        <div className="flex items-center gap-2 text-sm font-semibold text-slate-800 lg:mr-auto">
          <span className="grid size-8 place-items-center rounded-lg bg-blue-50 text-blue-600"><Filter className="size-4" /></span>
          筛选知识
        </div>
        <div className="grid gap-3 sm:grid-cols-3 lg:w-[680px]">
          <FilterSelect label="来源文件" value={value.sourceFile} onChange={(sourceFile) => onChange({ ...value, sourceFile })}>
            <option value="all">全部文件</option>
            {sourceFiles.map((file) => <option key={file} value={file}>{file}</option>)}
          </FilterSelect>
          <FilterSelect label="重要程度" value={value.importance} onChange={(importance) => onChange({ ...value, importance })}>
            <option value="all">全部程度</option>
            {[5, 4, 3, 2, 1].map((level) => <option key={level} value={String(level)}>{level} 星</option>)}
            <option value="none">未标注</option>
          </FilterSelect>
          <FilterSelect label="查看状态" value={value.viewed} onChange={(viewed) => onChange({ ...value, viewed })}>
            <option value="all">全部状态</option>
            <option value="not_viewed">未查看</option>
            <option value="viewed">已查看</option>
          </FilterSelect>
        </div>
      </div>
    </Card>
  )
}

function FilterSelect({ label, value, onChange, children }: { label: string; value: string; onChange: (value: string) => void; children: ReactNode }) {
  return (
    <label className="text-xs font-medium text-slate-500">
      {label}
      <select className="mt-1.5 h-10 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm text-slate-700 outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-100" value={value} onChange={(event) => onChange(event.target.value)}>
        {children}
      </select>
    </label>
  )
}
