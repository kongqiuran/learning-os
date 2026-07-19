import { ArrowRight, BookOpen, BookOpenText, CheckCircle2, FileText, GraduationCap, Layers3 } from 'lucide-react'
import { Link } from 'react-router-dom'

const chapters = ['第一章 信号基础', '第二章 LTI 系统', '第三章 傅里叶变换']

export function DemoPage() {
  return (
    <main className="min-h-screen bg-[#f7f6f2] text-stone-900">
      <header className="border-b border-stone-200 bg-[#fffdfa]">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-5">
          <Link className="flex items-center gap-3 font-bold" to="/demo"><span className="grid size-9 place-items-center rounded-xl bg-teal-700 text-white"><BookOpen className="size-5" /></span>Learning OS</Link>
          <div className="flex items-center gap-4 text-sm font-semibold"><Link className="text-stone-600 hover:text-stone-950" to="/login">登录</Link><Link className="rounded-xl bg-teal-700 px-4 py-2.5 text-white hover:bg-teal-800" to="/register">创建账号</Link></div>
        </div>
      </header>

      <section className="mx-auto max-w-6xl px-5 py-14 sm:py-20">
        <div className="mx-auto max-w-3xl text-center">
          <span className="inline-flex items-center gap-2 rounded-full border border-teal-200 bg-teal-50 px-3 py-1.5 text-xs font-semibold text-teal-800"><GraduationCap className="size-3.5" />只读产品示例</span>
          <h1 className="mt-6 text-4xl font-semibold leading-tight tracking-tight sm:text-5xl">一门课程，从跟课到考试都在同一个空间。</h1>
          <p className="mt-5 text-base leading-7 text-stone-600">下面使用“信号与系统”示例内容展示真实页面结构。示例不会写入账号，也不代表考试预测或学习结果承诺。</p>
        </div>

        <div className="mt-12 overflow-hidden rounded-3xl border border-stone-200 bg-[#fffdfa] shadow-[0_18px_60px_rgba(28,25,23,0.08)]">
          <div className="border-b border-stone-200 px-5 pt-6 sm:px-8"><h2 className="text-2xl font-semibold">信号与系统</h2><nav className="mt-6 flex gap-6 overflow-x-auto text-sm font-semibold"><span className="border-b-2 border-teal-700 pb-3 text-teal-800">跟课资料</span><span className="pb-3 text-stone-400">教材解析</span><span className="pb-3 text-stone-400">考试冲刺</span></nav></div>
          <div className="grid min-h-[480px] lg:grid-cols-[250px_minmax(0,1fr)]">
            <aside className="border-b border-stone-200 bg-stone-50/70 p-5 lg:border-b-0 lg:border-r"><p className="text-sm font-semibold">章节</p><div className="mt-4 space-y-2">{chapters.map((chapter, index) => <div className={`rounded-xl px-3 py-2.5 text-sm ${index === 2 ? 'bg-teal-50 font-semibold text-teal-800' : 'text-stone-600'}`} key={chapter}>{chapter}<span className="mt-1 block text-xs font-normal text-stone-400">{index + 1} 份资料</span></div>)}</div></aside>
            <div className="space-y-5 p-5 sm:p-8">
              <div><p className="text-xs font-semibold uppercase tracking-[0.14em] text-teal-700">第三章</p><h3 className="mt-2 text-2xl font-semibold">傅里叶变换</h3><p className="mt-2 text-sm text-stone-500">课件、练习和补充资料按章节归类。</p></div>
              <div className="grid gap-3 sm:grid-cols-3"><DemoMetric icon={FileText} label="课程资料" value="2 份" /><DemoMetric icon={Layers3} label="练习资料" value="1 份" /><DemoMetric icon={BookOpenText} label="补充资料" value="1 份" /></div>
              <div className="rounded-2xl border border-stone-200 p-5"><div className="flex items-center gap-2 text-sm font-semibold text-emerald-700"><CheckCircle2 className="size-4" />AI 整理结果</div><h4 className="mt-4 font-semibold">本章核心知识</h4><ul className="mt-3 space-y-2 text-sm leading-6 text-stone-600"><li>• 用频域视角描述信号的组成</li><li>• 掌握傅里叶变换的定义与常用性质</li><li>• 能够根据系统特性分析频谱变化</li></ul></div>
            </div>
          </div>
        </div>

        <div className="mt-10 flex flex-col items-center"><p className="text-sm text-stone-500">准备好建立自己的课程空间了吗？</p><Link className="mt-4 inline-flex items-center gap-2 rounded-xl bg-teal-700 px-5 py-3 text-sm font-semibold text-white hover:bg-teal-800" to="/register">创建第一门课程<ArrowRight className="size-4" /></Link></div>
      </section>
    </main>
  )
}

function DemoMetric({ icon: Icon, label, value }: { icon: typeof FileText; label: string; value: string }) {
  return <div className="rounded-2xl border border-stone-200 bg-stone-50/60 p-4"><Icon className="size-4 text-teal-700" /><p className="mt-3 text-xs text-stone-500">{label}</p><strong className="mt-1 block text-sm">{value}</strong></div>
}
