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
  chapter_id: number | null
  uploaded_at: string
}

export interface LearningPackage {
  id: number
  status: 'pending' | 'processing' | 'completed' | 'failed'
  version: number
  content: Record<string, unknown>
  current_stage: string | null
  retry_count: number
  error_type: string | null
  error_detail: string | null
  created_at: string
  scene: 'legacy' | 'follow' | 'textbook' | 'exam'
  scope_document_id: number | null
  scope_chapter_id: number | null
  scope_unassigned: boolean
  scope_kind: 'course' | 'chapter' | 'document' | 'unassigned'
  scope_key: string
  source_fingerprint: string | null
  prompt_version: string | null
  is_stale: boolean
}

export interface Chapter {
  id: number
  title: string
  position: number
  document_count: number
  created_at: string
  updated_at: string
}

export interface CourseSpaceResponse {
  course: CourseSummary
  documents: DocumentSummary[]
  learning_package: LearningPackage | null
  chapters: Chapter[]
  scene_packages: Partial<Record<'follow' | 'textbook' | 'exam', LearningPackage | null>>
  scene_completed_packages: Partial<Record<'follow' | 'textbook' | 'exam', LearningPackage | null>>
  chapter_packages: Record<string, LearningPackage>
  chapter_completed_packages: Record<string, LearningPackage>
  document_packages: Record<string, LearningPackage>
  document_completed_packages: Record<string, LearningPackage>
}

export interface AssistantQueryInput {
  question: string
  current_section?: string
  scene?: string
  chapter_id?: number
  textbook_id?: number
  scope_unassigned?: boolean
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

export interface UsageSummaryResponse {
  plan: string
  ai_generations: {
    used: number
    limit: number
    remaining: number
    resets_at: string
  }
  course_entitlements: Array<{
    id: number; course_id: number; course_name: string; product_code: string; amount_cents: number; status: string
    activated_at: string; expires_at: string; follow_remaining: number; textbook_remaining: number; exam_remaining: number; assistant_remaining: number
  }>
}

export interface PrivacyPolicyCurrentResponse {
  policy_version: string
}

export interface PrivacyConsentStatusResponse {
  current_version: string
  accepted: boolean
  requires_reconsent: boolean
}

export interface PrivacyConsentResponse {
  policy_version: string
  accepted_at: string
  created: boolean
}

export interface AccountDeletionResponse {
  deletion_id: string
  status: string
  message: string
}
