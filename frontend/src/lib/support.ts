export const SUPPORT_EMAIL = '3154949097@qq.com'

export function supportMailto(subject: string) {
  return `mailto:${SUPPORT_EMAIL}?subject=${encodeURIComponent(subject)}`
}
