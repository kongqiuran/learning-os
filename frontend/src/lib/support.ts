export const SUPPORT_EMAIL = import.meta.env.VITE_SUPPORT_EMAIL || 'support@learning-os.cn'

export function supportMailto(subject: string) {
  return `mailto:${SUPPORT_EMAIL}?subject=${encodeURIComponent(subject)}`
}
