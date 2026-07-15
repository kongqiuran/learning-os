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
  importance: number | null
  course_id: number
  course_name: string
  document_id: number
  source_file: string
  updated_at: string
  viewed: boolean
  viewed_at: string | null
}

export interface KnowledgeDetail extends KnowledgeSummary {
  core_explanation: string
  exam_value: string
  must_master: unknown[]
  memory_tips: string
  reason: string
  source_formulas: unknown[]
  source_errors: unknown[]
}

export interface KnowledgeListResponse {
  course: { id: number; name: string }
  knowledge_count: number
  items: KnowledgeSummary[]
}

export interface KnowledgeViewedResponse {
  knowledge_id: string
  viewed: boolean
  viewed_at: string
}
