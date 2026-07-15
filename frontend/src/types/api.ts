export interface User {
  id: number
  email: string
  created_at: string
}

export interface AuthResponse {
  user: User
}

export interface ApiErrorPayload {
  error: {
    code: string
    message: string
  }
}

export interface CourseSummary {
  id: number
  name: string
  description: string | null
  created_at: string
  updated_at: string
  document_count: number
}

export interface DashboardResponse {
  course_count: number
  document_count: number
  courses: CourseSummary[]
}

export interface CourseListResponse {
  courses: CourseSummary[]
}

export interface CourseCreateInput {
  name: string
  description?: string
}

export interface FileSummary {
  id: number
  name: string
  type: string
  sizeLabel: string
  status: 'uploaded' | 'processing' | 'completed' | 'failed'
}

export interface KnowledgeSummary {
  id: string
  title: string
  content: string
  courseName: string
  sourceFile: string
  updatedAt: string
  viewed: boolean
  importance?: number
}
