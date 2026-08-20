// 文件说明：Markdown 渲染组件。ReactMarkdown 来自 react-markdown；remarkGfm 来自 remark-gfm，用于支持表格、任务列表等 GFM 语法。
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

export function MarkdownContent({ children }: { children: string }) {
  return (
    <div className="learning-markdown text-sm leading-7 text-slate-700">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{children}</ReactMarkdown>
    </div>
  )
}
