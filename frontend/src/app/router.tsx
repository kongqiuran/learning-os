// 文件说明：前端路由表。BrowserRouter、Routes、Route、Navigate、useParams 来自 react-router-dom，用来根据地址栏路径切换 React 页面。
import { BrowserRouter, Navigate, Route, Routes, useParams } from 'react-router-dom'

import { AdminBillingPage } from '../pages/AdminBillingPage'
import { ProtectedRoute } from '../components/auth/ProtectedRoute'
import { AppShell } from '../components/layout/AppShell'
import { CourseSpacePage } from '../pages/CourseSpacePage'
import { DashboardPage } from '../pages/DashboardPage'
import { DemoPage } from '../pages/DemoPage'
import { KnowledgeDetailPage } from '../pages/KnowledgeDetailPage'
import { LegalPage } from '../pages/LegalPage'
import { LoginPage } from '../pages/LoginPage'
import { RegisterPage } from '../pages/RegisterPage'
import { SettingsPage } from '../pages/SettingsPage'
import { PricingPage } from '../pages/PricingPage'
import { PurchasePage } from '../pages/PurchasePage'

export function AppRouter() {
  return (
    // BrowserRouter 会监听浏览器地址栏的变化。
    // 用户点击链接后，React 不刷新整个网页，而是根据路径切换要显示的组件。
    <BrowserRouter>
      {/* Routes 是“路由表”的外壳，里面每一个 Route 都是一条地址规则。 */}
      <Routes>
        {/* path 是浏览器地址；element 是这个地址应该显示的 React 页面组件。 */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/demo" element={<DemoPage />} />
        <Route path="/legal/privacy" element={<LegalPage kind="privacy" />} />
        <Route path="/legal/terms" element={<LegalPage kind="terms" />} />

        {/*
          下面这一组页面需要登录后才能访问。
          ProtectedRoute 会先检查当前用户是否有登录 session：
          - 已登录：继续显示里面的页面；
          - 未登录：跳转到登录页。
        */}
        <Route element={<ProtectedRoute />}>
          {/*
            AppShell 是登录后的页面外壳，通常包含侧边栏、顶部栏和内容区域。
            里面的子路由会显示在 AppShell 预留的 Outlet 位置。
          */}
          <Route element={<AppShell />}>
            {/* index 表示访问根路径 / 时匹配；Navigate 表示自动跳转。 */}
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<DashboardPage />} />

            {/*
              :courseId 是动态参数。
              例如 /courses/12/follow 中，courseId 的值就是字符串 "12"。
              页面组件可以用 useParams() 读到这个课程 id，然后请求对应课程数据。
            */}
            <Route path="/courses/:courseId" element={<Navigate to="follow" replace />} />
            <Route path="/courses/:courseId/follow" element={<CourseSpacePage scene="follow" />} />
            <Route path="/courses/:courseId/textbooks" element={<CourseSpacePage scene="textbook" />} />
            <Route path="/courses/:courseId/exam" element={<CourseSpacePage scene="exam" />} />
            <Route path="/courses/:courseId/knowledge" element={<LegacyKnowledgeRedirect />} />
            <Route path="/courses/:courseId/knowledge/:knowledgeId" element={<KnowledgeDetailPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="/pricing" element={<PricingPage />} />
            <Route path="/purchase/:orderNo" element={<PurchasePage />} />
            <Route path="/admin/billing" element={<AdminBillingPage />} />
          </Route>
        </Route>

        {/* * 是兜底路由：上面都匹配不到时，就跳回课程列表。 */}
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

function LegacyKnowledgeRedirect() {
  // useParams 会读取当前路由里的动态参数。
  // 这里读取 courseId，是为了把老地址 /courses/:courseId/knowledge
  // 兼容跳转到新的教材解析页 /courses/:courseId/textbooks。
  const { courseId } = useParams()
  return <Navigate to={`/courses/${courseId}/textbooks`} replace />
}
