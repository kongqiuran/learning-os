import { ArrowRight, BookOpen, LayoutDashboard, LockKeyhole } from 'lucide-react'
import { Link } from 'react-router-dom'

export function DemoPage() {
  return (
    <main className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-5">
          <Link className="flex items-center gap-3 font-bold text-slate-950" to="/demo">
            <span className="grid size-9 place-items-center rounded-xl bg-blue-600 text-white"><BookOpen className="size-5" /></span>
            Learning OS
          </Link>
          <div className="flex items-center gap-4 text-sm font-semibold">
            <Link className="text-slate-600 hover:text-slate-950" to="/login">登录</Link>
            <Link className="rounded-xl bg-blue-600 px-4 py-2.5 text-white hover:bg-blue-700" to="/register">创建学习空间</Link>
          </div>
        </div>
      </header>
      <section className="mx-auto grid max-w-6xl gap-12 px-5 py-20 lg:grid-cols-[1fr_0.9fr] lg:items-center">
        <div>
          <span className="inline-flex items-center gap-2 rounded-full border border-violet-200 bg-violet-50 px-3 py-1.5 text-xs font-semibold text-violet-700">
            <LockKeyhole className="size-3.5" /> 公开只读 Demo 入口
          </span>
          <h1 className="mt-6 text-4xl font-semibold leading-tight tracking-tight text-slate-950 sm:text-5xl">先看清楚产品，再决定是否开始。</h1>
          <p className="mt-5 max-w-xl text-base leading-7 text-slate-600">真实 Demo Course 将在课程空间完成后接入。当前页面不注入演示统计，也不会将演示数据写入生产用户数据库。</p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link className="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white hover:bg-blue-700" to="/register">创建我的学习空间 <ArrowRight className="size-4" /></Link>
            <Link className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-5 py-3 text-sm font-semibold text-slate-700 hover:bg-slate-100" to="/login">已有账号，去登录</Link>
          </div>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-[0_12px_40px_rgba(15,23,42,0.07)]">
          <div className="flex items-center justify-between border-b border-slate-100 pb-4">
            <div className="flex items-center gap-2 font-semibold text-slate-900"><LayoutDashboard className="size-4 text-blue-600" />产品预览区域</div>
            <span className="rounded-lg bg-slate-100 px-2 py-1 text-xs text-slate-500">准备中</span>
          </div>
          <div className="mt-5 grid min-h-72 place-items-center rounded-xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center">
            <div><BookOpen className="mx-auto size-7 text-slate-400" /><p className="mt-4 text-sm font-semibold text-slate-700">等待真实课程空间接入</p><p className="mt-2 text-xs leading-5 text-slate-500">不使用虚假生产数据</p></div>
          </div>
        </div>
      </section>
    </main>
  )
}
