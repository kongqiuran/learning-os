// 文件说明：前端 API 请求层。fetch/XMLHttpRequest/FormData 是浏览器网络能力；ApiError 是本项目自定义错误类型。
import type {
  ApiErrorPayload,
  AccountDeletionResponse,
  AdminPaymentOrder,
  AdminPaymentOrderListResponse,
  AssistantQueryInput,
  AssistantQueryResponse,
  AuthResponse,
  BillingProductListResponse,
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
  PaymentOrder,
  PaymentOrderCreateInput,
  UsageSummaryResponse,
} from '../types/api'

// ApiError 是前端自己定义的“接口错误类型”。
// 普通 Error 只有 message；这里额外保存 HTTP 状态码、业务错误码和后端返回的详情。
// 这样页面就能根据错误原因显示更友好的中文提示，例如“请先登录”或“AI 额度不足”。
export class ApiError extends Error {
  constructor(
    // public 写在构造函数参数前，TypeScript 会自动把它变成类属性。
    // status 保存 HTTP 状态码，例如 401 未登录、404 不存在、429 额度不足。
    public status: number,
    // code 保存后端返回的业务错误码，例如 authentication_required。
    public code: string,
    message: string,
    // details 保存完整错误详情；如果后端没有返回，就用 code 和 message 组成默认详情。
    public details: ApiErrorPayload['error'] = { code, message },
  ) {
    // super(message) 调用父类 Error 的构造函数，让这个对象仍然是标准错误对象。
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
  course_quota_exceeded: '本课程的 AI 整理次数已用完。',
  assistant_quota_exceeded: '本课程的 AI 助手次数已用完。',
  insufficient_credits: '当前 AI 使用额度不足。',
  admin_access_required: '当前账号没有管理员权限。',
  payment_order_not_found: '购买订单不存在。',
  payment_order_state_invalid: '订单当前状态不允许执行此操作。',
}

// request 是普通 JSON 接口的统一请求函数。
// <T> 是 TypeScript 泛型：调用方会告诉它“成功时应该返回什么数据结构”。
// 例如 request<AuthResponse> 表示成功后会拿到登录用户信息。
async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  // FormData 通常用于上传文件。上传文件时浏览器需要自己生成 multipart 边界，
  // 所以不能手动写 Content-Type: application/json。
  const isFormData = options.body instanceof FormData

  // fetch 是浏览器内置的网络请求函数。
  // path 是请求地址，例如 /api/auth/login；options 是 method、body、headers 等配置。
  const response = await fetch(path, {
    // ...options 表示把调用方传进来的配置展开到这里，例如 method: 'POST'。
    ...options,
    // credentials: 'include' 表示请求时带上 cookie。
    // 本项目后端用 session cookie 判断用户是否登录，所以必须带 cookie。
    credentials: 'include',
    // 如果不是文件上传，就默认告诉后端“我发送的是 JSON”。
    // ...options.headers 放在后面，表示调用方传入的 header 可以覆盖默认值。
    headers: isFormData ? options.headers : { 'Content-Type': 'application/json', ...options.headers },
  })

  // response.ok 代表 HTTP 状态码在 200-299 之间。
  // 如果不是 ok，就说明后端认为请求失败，需要转成 ApiError 抛给页面处理。
  if (!response.ok) {
    // 后端通常会返回 { error: { code, message, ... } }。
    // catch(() => null) 是为了防止后端返回的不是 JSON 时，前端再次报解析错误。
    const payload = (await response.json().catch(() => null)) as ApiErrorPayload | null
    const errorDetails = payload?.error ?? { code: 'request_failed', message: '请求失败，请稍后重试。' }
    throw new ApiError(
      response.status,
      errorDetails.code,
      // 优先使用前端本地化过的中文文案；没有对应中文文案时，再用后端 message。
      localizedMessages[errorDetails.code] ?? errorDetails.message,
      errorDetails,
    )
  }

  // 成功时，把后端返回的 JSON 解析出来，并告诉 TypeScript 它符合 T 类型。
  return response.json() as Promise<T>
}

export interface UploadProgress {
  phase: 'uploading' | 'saving'
  percent: number
}

// uploadRequest 专门处理文件上传。
// 这里不用 fetch，而用 XMLHttpRequest，是因为 XMLHttpRequest 可以监听上传进度。
function uploadRequest<T>(path: string, body: FormData, onProgress?: (progress: UploadProgress) => void): Promise<T> {
  // Promise 把“回调式”的 XMLHttpRequest 包装成 await/then 可以使用的异步结果。
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest()
    // open('POST', path) 表示准备向 path 发一个 POST 请求。
    xhr.open('POST', path)
    // withCredentials = true 表示上传请求也要带 cookie，否则后端不知道当前用户是谁。
    xhr.withCredentials = true

    // progress 事件会在文件上传过程中多次触发。
    xhr.upload.addEventListener('progress', (event) => {
      // lengthComputable 表示浏览器是否知道总大小；不知道总大小就无法计算百分比。
      if (!event.lengthComputable) return
      // loaded 是已上传字节数，total 是总字节数。
      // Math.round 转成整数百分比；Math.min(99, ...) 保留 100% 给“服务器保存中”阶段。
      const percent = Math.min(99, Math.round((event.loaded / event.total) * 100))
      onProgress?.({ phase: 'uploading', percent })
    })
    // 上传传输完成后，服务器还需要保存和解析文件，所以这里切换成 saving 状态。
    xhr.upload.addEventListener('load', () => onProgress?.({ phase: 'saving', percent: 100 }))

    // load 事件表示服务器已经返回响应。
    xhr.addEventListener('load', () => {
      const payload = parseJsonResponse<T | ApiErrorPayload>(xhr.responseText)
      if (xhr.status >= 200 && xhr.status < 300 && payload) {
        // resolve 表示 Promise 成功，调用方会进入 onSuccess 或 await 后续逻辑。
        resolve(payload as T)
        return
      }
      const errorPayload = payload as ApiErrorPayload | null
      const errorDetails = errorPayload?.error ?? { code: 'request_failed', message: '请求失败，请稍后重试。' }
      // reject 表示 Promise 失败，React Query 会把它放到 upload.error 里。
      reject(new ApiError(
        xhr.status,
        errorDetails.code,
        localizedMessages[errorDetails.code] ?? errorDetails.message,
        errorDetails,
      ))
    })
    xhr.addEventListener('error', () => reject(new ApiError(0, 'network_error', '网络连接失败，请稍后重试。')))
    xhr.addEventListener('abort', () => reject(new ApiError(0, 'request_aborted', '上传已取消。')))

    // 先通知页面“开始上传，进度 0%”，然后真正发送 FormData。
    onProgress?.({ phase: 'uploading', percent: 0 })
    xhr.send(body)
  })
}

function parseJsonResponse<T>(responseText: string): T | null {
  try {
    return JSON.parse(responseText) as T
  } catch {
    return null
  }
}

// api 对象是前端调用后端的“方法清单”。
// 页面组件不直接写 fetch('/api/...')，而是调用 api.login、api.uploadDocument 等方法。
// 这样接口地址和错误处理集中在一个文件里，后面维护更容易。
export const api = {
  // currentUser 用来问后端“当前 cookie 对应的是哪个登录用户”。
  currentUser: () => request<AuthResponse>('/api/auth/me'),
  // login 把邮箱和密码转成 JSON 发给后端。
  // JSON.stringify 的作用是把 JS 对象变成网络传输用的字符串。
  login: (email: string, password: string) =>
    request<AuthResponse>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),
  // register 和 login 类似，但额外提交确认密码和是否同意协议。
  // confirm_password / accepted_terms 使用下划线，是因为后端 Python 接口按这个字段名接收。
  register: (email: string, password: string, confirmPassword: string, acceptedTerms: boolean) =>
    request<AuthResponse>('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, confirm_password: confirmPassword, accepted_terms: acceptedTerms }),
    }),
  // logout 告诉后端清除当前 session，用户就退出登录了。
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
  billingProducts: () => request<BillingProductListResponse>('/api/billing/products'),
  createPaymentOrder: (input: PaymentOrderCreateInput) =>
    request<PaymentOrder>('/api/billing/orders', {
      method: 'POST',
      body: JSON.stringify(input),
    }),
  paymentOrder: (orderNo: string) =>
    request<PaymentOrder>(`/api/billing/orders/${encodeURIComponent(orderNo)}`),
  adminPaymentOrders: (status?: string) => {
    const query = status ? `?status=${encodeURIComponent(status)}` : ''
    return request<AdminPaymentOrderListResponse>(`/api/admin/billing/orders${query}`)
  },
  adminPaymentOrder: (orderNo: string) =>
    request<AdminPaymentOrder>(`/api/admin/billing/orders/${encodeURIComponent(orderNo)}`),
  activateAdminPaymentOrder: (orderNo: string, operatorNote?: string) =>
    request<AdminPaymentOrder>(`/api/admin/billing/orders/${encodeURIComponent(orderNo)}/activate`, {
      method: 'POST',
      body: JSON.stringify({ operator_note: operatorNote || null }),
    }),
  cancelAdminPaymentOrder: (orderNo: string, operatorNote?: string) =>
    request<AdminPaymentOrder>(`/api/admin/billing/orders/${encodeURIComponent(orderNo)}/cancel`, {
      method: 'POST',
      body: JSON.stringify({ operator_note: operatorNote || null }),
    }),
  // dashboard 读取首页所需数据，例如最近课程、使用额度等。
  dashboard: () => request<DashboardResponse>('/api/dashboard'),
  // courses 读取当前用户创建过的所有课程。
  courses: () => request<CourseListResponse>('/api/courses'),
  // 反引号 `...${courseId}...` 是模板字符串，用来把变量拼进接口地址。
  course: (courseId: number | string) => request<CourseSummary>(`/api/courses/${courseId}`),
  // createCourse 创建一门新课程。input 里通常包含课程名称等字段。
  createCourse: (input: CourseCreateInput) =>
    request<CourseSummary>('/api/courses', {
      method: 'POST',
      body: JSON.stringify(input),
    }),
  deleteCourse: (courseId: number) =>
    request<{ message: string }>(`/api/courses/${courseId}`, { method: 'DELETE' }),
  // courseSpace 读取一门课程空间的全部展示数据：课程信息、章节、资料、AI 整理结果等。
  courseSpace: (courseId: number | string) =>
    request<CourseSpaceResponse>(`/api/courses/${courseId}/space`),
  // uploadDocument 上传课程资料。
  // file 是浏览器拿到的文件对象；documentType 是资料分类；chapterId 是可选章节。
  uploadDocument: (courseId: number | string, file: File, documentType: string, chapterId?: number | null, onProgress?: (progress: UploadProgress) => void) => {
    // FormData 是浏览器专门用于“表单 + 文件上传”的数据容器。
    const body = new FormData()
    body.append('file', file)
    body.append('document_type', documentType)
    // != null 同时排除 null 和 undefined；只有用户选了章节时才提交 chapter_id。
    if (chapterId != null) body.append('chapter_id', String(chapterId))
    return uploadRequest<DocumentSummary>(`/api/courses/${courseId}/documents`, body, onProgress)
  },
  deleteDocument: (courseId: number | string, documentId: number) =>
    request<{ message: string }>(`/api/courses/${courseId}/documents/${documentId}`, { method: 'DELETE' }),
  generateLearningPackage: (courseId: number | string) =>
    request<LearningPackage>(`/api/courses/${courseId}/learning-package/generate`, { method: 'POST' }),
  // generateScene 触发某个学习场景的 AI 整理，例如 follow / textbook / exam。
  // scope 用来限定整理范围：某份教材、某个章节，或者未分章节资料。
  generateScene: (courseId: number | string, scene: string, scope?: { documentId?: number; chapterId?: number; unassigned?: boolean }) => {
    // URLSearchParams 用来安全拼接 ?a=1&b=2 这种查询参数。
    const params = new URLSearchParams()
    // scope?.documentId 是可选链：scope 不存在时不会报错，只会得到 undefined。
    if (scope?.documentId != null) params.set('scope_document_id', String(scope.documentId))
    if (scope?.chapterId != null) params.set('scope_chapter_id', String(scope.chapterId))
    if (scope?.unassigned) params.set('scope_unassigned', 'true')
    // 如果有参数，就拼成 ?xxx；如果没有参数，就保持空字符串。
    const query = params.size ? `?${params.toString()}` : ''
    return request<LearningPackage>(`/api/courses/${courseId}/generations/${scene}${query}`, { method: 'POST' })
  },
  createChapter: (courseId: number | string, title: string) => request<Chapter>(`/api/courses/${courseId}/chapters`, { method: 'POST', body: JSON.stringify({ title }) }),
  updateChapter: (courseId: number | string, chapterId: number, input: { title?: string; position?: number }) => request<Chapter>(`/api/courses/${courseId}/chapters/${chapterId}`, { method: 'PATCH', body: JSON.stringify(input) }),
  deleteChapter: (courseId: number | string, chapterId: number, materialAction: 'keep_unassigned' | 'delete') => request<{ message: string }>(`/api/courses/${courseId}/chapters/${chapterId}`, { method: 'DELETE', body: JSON.stringify({ material_action: materialAction }) }),
  moveDocument: (courseId: number | string, documentId: number, chapterId: number | null) => request<DocumentSummary>(`/api/courses/${courseId}/documents/${documentId}/chapter`, { method: 'PATCH', body: JSON.stringify({ chapter_id: chapterId }) }),
  learningPackageTask: (courseId: number | string, packageId: number) =>
    request<LearningPackage>(`/api/courses/${courseId}/learning-package/${packageId}`),
  // queryCourseAssistant 把用户的问题发给后端课程助手。
  // 后端会结合课程资料和已生成内容回答，然后返回 answer 和 source_files。
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
