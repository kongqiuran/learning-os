import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api } from '../lib/api'


export const usageQueryKey = ['billing', 'usage'] as const
export const billingProductsQueryKey = ['billing', 'products'] as const
export const privacyPolicyQueryKey = ['privacy', 'current-policy'] as const
export const privacyConsentStatusQueryKey = ['privacy', 'consent-status'] as const

export function useUsageSummary() {
  return useQuery({
    queryKey: usageQueryKey,
    queryFn: api.usage,
  })
}

export function useBillingProducts() {
  return useQuery({
    queryKey: billingProductsQueryKey,
    queryFn: api.billingProducts,
  })
}

export function usePrivacyPolicy() {
  return useQuery({
    queryKey: privacyPolicyQueryKey,
    queryFn: api.privacyPolicy,
  })
}

export function usePrivacyConsentStatus(enabled = true) {
  return useQuery({
    queryKey: privacyConsentStatusQueryKey,
    queryFn: api.privacyConsentStatus,
    enabled,
  })
}

export function useAcceptPrivacyConsent() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: api.acceptPrivacyConsent,
    onSuccess: (consent) => {
      queryClient.setQueryData(privacyConsentStatusQueryKey, {
        current_version: consent.policy_version,
        accepted: true,
        requires_reconsent: false,
      })
      queryClient.setQueryData(privacyPolicyQueryKey, {
        policy_version: consent.policy_version,
      })
    },
  })
}
