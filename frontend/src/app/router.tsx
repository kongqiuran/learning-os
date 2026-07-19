import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import { ProtectedRoute } from '../components/auth/ProtectedRoute'
import { AppShell } from '../components/layout/AppShell'
import { CourseSpacePage } from '../pages/CourseSpacePage'
import { DashboardPage } from '../pages/DashboardPage'
import { DemoPage } from '../pages/DemoPage'
import { KnowledgeWorkspacePage } from '../pages/KnowledgeWorkspacePage'
import { KnowledgeDetailPage } from '../pages/KnowledgeDetailPage'
import { LegalPage } from '../pages/LegalPage'
import { LoginPage } from '../pages/LoginPage'
import { RegisterPage } from '../pages/RegisterPage'
import { SettingsPage } from '../pages/SettingsPage'
import { PricingPage } from '../pages/PricingPage'

export function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/demo" element={<DemoPage />} />
        <Route path="/legal/privacy" element={<LegalPage kind="privacy" />} />
        <Route path="/legal/terms" element={<LegalPage kind="terms" />} />
        <Route element={<ProtectedRoute />}>
          <Route element={<AppShell />}>
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/courses/:courseId" element={<Navigate to="follow" replace />} />
            <Route path="/courses/:courseId/follow" element={<CourseSpacePage scene="follow" />} />
            <Route path="/courses/:courseId/textbooks" element={<CourseSpacePage scene="textbook" />} />
            <Route path="/courses/:courseId/exam" element={<CourseSpacePage scene="exam" />} />
            <Route path="/courses/:courseId/knowledge" element={<KnowledgeWorkspacePage />} />
            <Route path="/courses/:courseId/knowledge/:knowledgeId" element={<KnowledgeDetailPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="/pricing" element={<PricingPage />} />
          </Route>
        </Route>
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
