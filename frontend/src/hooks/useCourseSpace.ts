import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api } from '../lib/api'
import type { AssistantQueryInput } from '../types/api'

export const courseSpaceQueryKey = (courseId: string | undefined) => ['course-space', courseId] as const

export function useCourseSpace(courseId: string | undefined) {
  return useQuery({
    queryKey: courseSpaceQueryKey(courseId),
    queryFn: () => api.courseSpace(courseId!),
    enabled: Boolean(courseId),
  })
}

export function useUploadDocument(courseId: string | undefined) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ file, documentType }: { file: File; documentType: string }) =>
      api.uploadDocument(courseId!, file, documentType),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: courseSpaceQueryKey(courseId) }),
  })
}

export function useDeleteDocument(courseId: string | undefined) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (documentId: number) => api.deleteDocument(courseId!, documentId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: courseSpaceQueryKey(courseId) }),
  })
}

export function useGenerateLearningPackage(courseId: string | undefined) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => api.generateLearningPackage(courseId!),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: courseSpaceQueryKey(courseId) }),
        queryClient.invalidateQueries({ queryKey: ['dashboard'] }),
      ])
    },
  })
}

export function useCourseAssistant(courseId: string | undefined) {
  return useMutation({
    mutationFn: (input: AssistantQueryInput) => api.queryCourseAssistant(courseId!, input),
  })
}
