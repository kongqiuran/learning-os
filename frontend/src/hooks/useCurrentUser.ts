// 文件说明：当前用户 Hook。useQuery 来自 TanStack React Query；它调用 /api/auth/me 获取当前登录用户。
import { useQuery } from '@tanstack/react-query'

import { api } from '../lib/api'

export const currentUserQueryKey = ['auth', 'current-user'] as const

export function useCurrentUser() {
  return useQuery({
    queryKey: currentUserQueryKey,
    queryFn: api.currentUser,
  })
}
