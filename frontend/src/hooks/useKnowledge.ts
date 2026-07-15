import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api } from '../lib/api'

export const courseKnowledgeQueryKey = (courseId: string | undefined) => ['course-knowledge', courseId] as const
export const knowledgeDetailQueryKey = (knowledgeId: string | undefined) => ['knowledge', knowledgeId] as const

export function useCourseKnowledge(courseId: string | undefined) {
  return useQuery({
    queryKey: courseKnowledgeQueryKey(courseId),
    queryFn: () => api.courseKnowledge(courseId!),
    enabled: Boolean(courseId),
  })
}

export function useKnowledgeDetail(knowledgeId: string | undefined) {
  return useQuery({
    queryKey: knowledgeDetailQueryKey(knowledgeId),
    queryFn: () => api.knowledge(knowledgeId!),
    enabled: Boolean(knowledgeId),
  })
}

export function useMarkKnowledgeViewed(courseId: string | undefined, knowledgeId: string | undefined) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => api.markKnowledgeViewed(knowledgeId!),
    onSuccess: async (viewState) => {
      queryClient.setQueryData(knowledgeDetailQueryKey(knowledgeId), (current: unknown) => {
        if (!current || typeof current !== 'object') return current
        return { ...current, viewed: true, viewed_at: viewState.viewed_at }
      })
      await queryClient.invalidateQueries({ queryKey: courseKnowledgeQueryKey(courseId) })
    },
  })
}
