// 文件说明：客服联系方式工具。encodeURIComponent 是 JavaScript 全局函数，用来把邮件标题安全放进 mailto 链接。
export const SUPPORT_EMAIL = '3154949097@qq.com'

export function supportMailto(subject: string) {
  return `mailto:${SUPPORT_EMAIL}?subject=${encodeURIComponent(subject)}`
}
