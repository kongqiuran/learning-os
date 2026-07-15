import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api } from '../lib/api'
import type { CourseCreateInput } from '../types/api'

export const dashboardQueryKey = ['dashboard'] as const
export const coursesQueryKey = ['courses'] as const

export function useDashboard() {
  return useQuery({
    queryKey: dashboardQueryKey,
    queryFn: api.dashboard,
  })
}

export function useCourse(courseId: string | undefined) {
  return useQuery({
    queryKey: [...coursesQueryKey, courseId],
    queryFn: () => api.course(courseId!),
    enabled: Boolean(courseId),
  })
}

export function useCreateCourse() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (input: CourseCreateInput) => api.createCourse(input),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: dashboardQueryKey }),
        queryClient.invalidateQueries({ queryKey: coursesQueryKey }),
      ])
    },
  })
}

export function useDeleteCourse() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: api.deleteCourse,
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: dashboardQueryKey }),
        queryClient.invalidateQueries({ queryKey: coursesQueryKey }),
      ])
    },
  })
}
