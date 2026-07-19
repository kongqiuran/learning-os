import { useQuery } from '@tanstack/react-query'

import { api } from '../lib/api'


export const usageQueryKey = ['billing', 'usage'] as const
export const privacyPolicyQueryKey = ['privacy', 'current-policy'] as const

export function useUsageSummary() {
  return useQuery({
    queryKey: usageQueryKey,
    queryFn: api.usage,
  })
}

export function usePrivacyPolicy() {
  return useQuery({
    queryKey: privacyPolicyQueryKey,
    queryFn: api.privacyPolicy,
  })
}
