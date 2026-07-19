import { ArrowLeft, BookOpen, ShieldCheck } from 'lucide-react'
import { Link } from 'react-router-dom'

import { Card } from '../components/ui/Card'
import { MarkdownContent } from '../components/ui/MarkdownContent'
import { usePrivacyPolicy } from '../hooks/useUserCenter'
import {
  LEGAL_EFFECTIVE_DATE,
  legalDocuments,
  type LegalDocumentKind,
} from '../legal/legalContent'

export function LegalPage({ kind }: { kind: LegalDocumentKind }) {
  const document = legalDocuments[kind]
  const privacyPolicy = usePrivacyPolicy()

  return (
    <main className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-5xl items-center justify-between gap-4 px-5 py-4 sm:px-8">
          <Link className="flex items-center gap-3 font-semibold text-slate-950" to="/">
            <span className="grid size-9 place-items-center rounded-xl bg-blue-600 text-white">
              <BookOpen className="size-4" />
            </span>
            Learning OS
          </Link>
          <Link className="inline-flex items-center gap-2 text-sm font-semibold text-slate-600 hover:text-blue-600" to="/">
            <ArrowLeft className="size-4" /> 返回产品
          </Link>
        </div>
      </header>

      <section className="mx-auto max-w-5xl px-5 py-10 sm:px-8 sm:py-14">
        <div className="max-w-3xl">
          <div className="flex items-center gap-2 text-sm font-semibold text-blue-600">
            <ShieldCheck className="size-4" /> 法律与隐私
          </div>
          <h1 className="mt-3 text-3xl font-semibold tracking-tight text-slate-950 sm:text-4xl">{document.title}</h1>
          <p className="mt-3 text-sm leading-6 text-slate-500">{document.description}</p>
          <div className="mt-5 flex flex-wrap gap-x-6 gap-y-2 text-xs text-slate-500">
            <span>协议版本：{privacyPolicy.data?.policy_version ?? '正在读取'}</span>
            <span>生效日期：{LEGAL_EFFECTIVE_DATE}</span>
          </div>
        </div>

        <div className="mt-8 grid items-start gap-6 lg:grid-cols-[minmax(0,1fr)_220px]">
          <Card className="p-5 sm:p-8">
            <MarkdownContent>{document.content}</MarkdownContent>
          </Card>
          <Card className="p-4 lg:sticky lg:top-6">
            <p className="px-2 text-xs font-semibold uppercase tracking-[0.14em] text-slate-400">法律文件</p>
            <nav className="mt-2 space-y-1" aria-label="法律文件">
              <LegalNavigationLink active={kind === 'privacy'} to="/legal/privacy">隐私政策</LegalNavigationLink>
              <LegalNavigationLink active={kind === 'terms'} to="/legal/terms">用户协议</LegalNavigationLink>
            </nav>
          </Card>
        </div>
      </section>
    </main>
  )
}

function LegalNavigationLink({ active, to, children }: { active: boolean; to: string; children: string }) {
  return (
    <Link
      className={`block rounded-xl px-3 py-2.5 text-sm font-semibold transition-colors ${
        active ? 'bg-blue-50 text-blue-700' : 'text-slate-600 hover:bg-slate-50 hover:text-slate-950'
      }`}
      to={to}
    >
      {children}
    </Link>
  )
}
