import type {
  ApiErrorPayload,
  AccountDeletionResponse,
  AssistantQueryInput,
  AssistantQueryResponse,
  AuthResponse,
  CourseCreateInput,
  CourseListResponse,
  CourseSummary,
  CourseSpaceResponse,
  Chapter,
  DashboardResponse,
  DocumentSummary,
  LearningPackage,
  KnowledgeDetail,
  KnowledgeListResponse,
  KnowledgeViewedResponse,
  PrivacyPolicyCurrentResponse,
  PrivacyConsentResponse,
  PrivacyConsentStatusResponse,
  UsageSummaryResponse,
} from '../types/api'

export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

const localizedMessages: Record<string, string> = {
  authentication_required: '请先登录后继续。',
  session_expired: '登录状态已失效，请重新登录。',
  invalid_credentials: '邮箱或密码错误。',
  password_mismatch: '两次输入的密码不一致。',
  weak_password: '密码至少需要 8 个字符。',
  terms_consent_required: '请先阅读并同意隐私政策和用户协议。',
  email_registered: '该邮箱已经注册。',
  invalid_registration: '注册信息不完整，请检查后重试。',
  invalid_request: '提交的信息有误，请检查后重试。',
  invalid_course: '请输入课程名称。',
  course_not_found: '课程不存在或你没有访问权限。',
  invalid_document: '资料上传失败，请检查文件格式和大小。',
  document_not_found: '资料不存在或你没有操作权限。',
  generation_in_progress: '课程内容正在整理，请稍候。',
  generation_failed: '课程内容整理失败，请检查模型配置后重试。',
  generation_task_not_found: '课程整理任务不存在或已经失效。',
  assistant_unavailable: '课程助手暂时无法回答，请稍后重试。',
  knowledge_not_found: '知识内容不存在或你没有访问权限。',
  confirmation_required: '请输入完整确认文字后再注销账号。',
  quota_exceeded: '本月 AI 整理次数已用完。',
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const isFormData = options.body instanceof FormData
  const response = await fetch(path, {
    ...options,
    credentials: 'include',
    headers: isFormData ? options.headers : { 'Content-Type': 'application/json', ...options.headers },
  })

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as ApiErrorPayload | null
    throw new ApiError(
      response.status,
      payload?.error.code ?? 'request_failed',
      localizedMessages[payload?.error.code ?? ''] ?? payload?.error.message ?? '请求失败，请稍后重试。',
    )
  }

  return response.json() as Promise<T>
}

export const api = {
  currentUser: () => request<AuthResponse>('/api/auth/me'),
  login: (email: string, password: string) =>
    request<AuthResponse>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),
  register: (email: string, password: string, confirmPassword: string, acceptedTerms: boolean) =>
    request<AuthResponse>('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, confirm_password: confirmPassword, accepted_terms: acceptedTerms }),
    }),
  logout: () => request<{ message: string }>('/api/auth/logout', { method: 'POST' }),
  deleteAccount: (password: string, confirmation: string) =>
    request<AccountDeletionResponse>('/api/account', {
      method: 'DELETE',
      body: JSON.stringify({ password, confirmation }),
    }),
  privacyPolicy: () => request<PrivacyPolicyCurrentResponse>('/api/privacy/current'),
  privacyConsentStatus: () => request<PrivacyConsentStatusResponse>('/api/privacy/status'),
  acceptPrivacyConsent: () =>
    request<PrivacyConsentResponse>('/api/privacy/consent', {
      method: 'POST',
      body: JSON.stringify({ accepted: true }),
    }),
  usage: () => request<UsageSummaryResponse>('/api/billing/usage'),
  dashboard: () => request<DashboardResponse>('/api/dashboard'),
  courses: () => request<CourseListResponse>('/api/courses'),
  course: (courseId: number | string) => request<CourseSummary>(`/api/courses/${courseId}`),
  createCourse: (input: CourseCreateInput) =>
    request<CourseSummary>('/api/courses', {
      method: 'POST',
      body: JSON.stringify(input),
    }),
  deleteCourse: (courseId: number) =>
    request<{ message: string }>(`/api/courses/${courseId}`, { method: 'DELETE' }),
  courseSpace: (courseId: number | string) =>
    request<CourseSpaceResponse>(`/api/courses/${courseId}/space`),
  uploadDocument: (courseId: number | string, file: File, documentType: string, chapterId?: number | null) => {
    const body = new FormData()
    body.append('file', file)
    body.append('document_type', documentType)
    if (chapterId != null) body.append('chapter_id', String(chapterId))
    return request<DocumentSummary>(`/api/courses/${courseId}/documents`, { method: 'POST', body })
  },
  deleteDocument: (courseId: number | string, documentId: number) =>
    request<{ message: string }>(`/api/courses/${courseId}/documents/${documentId}`, { method: 'DELETE' }),
  generateLearningPackage: (courseId: number | string) =>
    request<LearningPackage>(`/api/courses/${courseId}/learning-package/generate`, { method: 'POST' }),
  generateScene: (courseId: number | string, scene: string, scopeDocumentId?: number) =>
    request<LearningPackage>(`/api/courses/${courseId}/generations/${scene}${scopeDocumentId ? `?scope_document_id=${scopeDocumentId}` : ''}`, { method: 'POST' }),
  createChapter: (courseId: number | string, title: string) => request<Chapter>(`/api/courses/${courseId}/chapters`, { method: 'POST', body: JSON.stringify({ title }) }),
  updateChapter: (courseId: number | string, chapterId: number, input: { title?: string; position?: number }) => request<Chapter>(`/api/courses/${courseId}/chapters/${chapterId}`, { method: 'PATCH', body: JSON.stringify(input) }),
  deleteChapter: (courseId: number | string, chapterId: number, materialAction: 'keep_unassigned' | 'delete') => request<{ message: string }>(`/api/courses/${courseId}/chapters/${chapterId}`, { method: 'DELETE', body: JSON.stringify({ material_action: materialAction }) }),
  moveDocument: (courseId: number | string, documentId: number, chapterId: number | null) => request<DocumentSummary>(`/api/courses/${courseId}/documents/${documentId}/chapter`, { method: 'PATCH', body: JSON.stringify({ chapter_id: chapterId }) }),
  learningPackageTask: (courseId: number | string, packageId: number) =>
    request<LearningPackage>(`/api/courses/${courseId}/learning-package/${packageId}`),
  queryCourseAssistant: (courseId: number | string, input: AssistantQueryInput) =>
    request<AssistantQueryResponse>(`/api/courses/${courseId}/assistant/query`, {
      method: 'POST',
      body: JSON.stringify(input),
    }),
  courseKnowledge: (courseId: number | string) =>
    request<KnowledgeListResponse>(`/api/courses/${courseId}/knowledge`),
  knowledge: (knowledgeId: string) =>
    request<KnowledgeDetail>(`/api/knowledge/${encodeURIComponent(knowledgeId)}`),
  markKnowledgeViewed: (knowledgeId: string) =>
    request<KnowledgeViewedResponse>(`/api/knowledge/${encodeURIComponent(knowledgeId)}/viewed`, {
      method: 'PATCH',
    }),
}
