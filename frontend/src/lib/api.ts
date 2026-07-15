import type {
  ApiErrorPayload,
  AssistantQueryInput,
  AssistantQueryResponse,
  AuthResponse,
  CourseCreateInput,
  CourseListResponse,
  CourseSummary,
  CourseSpaceResponse,
  DashboardResponse,
  DocumentSummary,
  LearningPackage,
  KnowledgeDetail,
  KnowledgeListResponse,
  KnowledgeViewedResponse,
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
  email_registered: '该邮箱已经注册。',
  invalid_registration: '注册信息不完整，请检查后重试。',
  invalid_request: '提交的信息有误，请检查后重试。',
  invalid_course: '请输入课程名称。',
  course_not_found: '课程不存在或你没有访问权限。',
  invalid_document: '资料上传失败，请检查文件格式和大小。',
  document_not_found: '资料不存在或你没有操作权限。',
  generation_in_progress: '课程内容正在整理，请稍候。',
  generation_failed: '课程内容整理失败，请检查模型配置后重试。',
  assistant_unavailable: '课程助手暂时无法回答，请稍后重试。',
  knowledge_not_found: '知识内容不存在或你没有访问权限。',
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
  register: (email: string, password: string, confirmPassword: string) =>
    request<AuthResponse>('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, confirm_password: confirmPassword }),
    }),
  logout: () => request<{ message: string }>('/api/auth/logout', { method: 'POST' }),
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
  uploadDocument: (courseId: number | string, file: File, documentType: string) => {
    const body = new FormData()
    body.append('file', file)
    body.append('document_type', documentType)
    return request<DocumentSummary>(`/api/courses/${courseId}/documents`, { method: 'POST', body })
  },
  deleteDocument: (courseId: number | string, documentId: number) =>
    request<{ message: string }>(`/api/courses/${courseId}/documents/${documentId}`, { method: 'DELETE' }),
  generateLearningPackage: (courseId: number | string) =>
    request<LearningPackage>(`/api/courses/${courseId}/learning-package/generate`, { method: 'POST' }),
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
