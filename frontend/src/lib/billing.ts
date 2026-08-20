// 文件说明：购买和额度工具函数。URLSearchParams 与 Intl.NumberFormat 是浏览器/JavaScript 标准能力，用于拼接链接和格式化金额。
import { ApiError } from './api'

const CREDIT_ERROR_CODES = new Set([
  'insufficient_credits',
  'quota_exceeded',
  'course_quota_exceeded',
  'assistant_quota_exceeded',
])

export function asCreditError(error: Error | null): ApiError | null {
  return error instanceof ApiError && CREDIT_ERROR_CODES.has(error.code) ? error : null
}

export function purchaseUrl(error: ApiError, courseId?: string | number, scene?: string) {
  if (error.details.purchase_url) return error.details.purchase_url
  const params = new URLSearchParams()
  if (courseId != null) params.set('course_id', String(courseId))
  if (scene) params.set('scene', scene)
  return `/pricing${params.size ? `?${params.toString()}` : ''}`
}

export function formatMoney(amountCents: number, currency: string) {
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency,
    minimumFractionDigits: amountCents % 100 === 0 ? 0 : 2,
  }).format(amountCents / 100)
}
