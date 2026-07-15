import { useQuery } from '@tanstack/react-query'

import { api } from '../lib/api'

export const currentUserQueryKey = ['auth', 'current-user'] as const

export function useCurrentUser() {
  return useQuery({
    queryKey: currentUserQueryKey,
    queryFn: api.currentUser,
  })
}
