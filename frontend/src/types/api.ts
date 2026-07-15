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

export type DocumentStatus = 'uploaded' | 'processing' | 'completed' | 'failed'

export interface DocumentSummary {
  id: number
  name: string
  mime_type: string
  file_size: number
  status: DocumentStatus
  document_type: string
  uploaded_at: string
}

export interface LearningPackage {
  id: number
  status: 'pending' | 'processing' | 'completed' | 'failed'
  version: number
  content: Record<string, unknown>
  created_at: string
}

export interface CourseSpaceResponse {
  course: CourseSummary
  documents: DocumentSummary[]
  learning_package: LearningPackage | null
}

export interface AssistantQueryInput {
  question: string
  current_section?: string
}

export interface AssistantQueryResponse {
  answer: string
  source_files: string[]
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
