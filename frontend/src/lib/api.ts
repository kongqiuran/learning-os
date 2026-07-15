import type { ApiErrorPayload, AuthResponse } from '../types/api'

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
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(path, {
    ...options,
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
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
}
