import { useEffect } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api, type UploadProgress } from '../lib/api'
import type { AssistantQueryInput, CourseSpaceResponse } from '../types/api'

export const courseSpaceQueryKey = (courseId: string | undefined) => ['course-space', courseId] as const
export const generationTaskQueryKey = (courseId: string | undefined, packageId: number | null) =>
  ['generation-task', courseId, packageId] as const

export function useCourseSpace(courseId: string | undefined) {
  return useQuery({
    queryKey: courseSpaceQueryKey(courseId),
    queryFn: () => api.courseSpace(courseId!),
    enabled: Boolean(courseId),
    refetchInterval: (query) => hasActiveGeneration(query.state.data) ? 2000 : false,
  })
}

function hasActiveGeneration(data: CourseSpaceResponse | undefined) {
  if (!data) return false
  const packages = [
    ...Object.values(data.scene_packages),
    ...Object.values(data.chapter_packages),
    ...Object.values(data.document_packages),
  ]
  return packages.some((item) => item?.status === 'pending' || item?.status === 'processing')
}

export function useUploadDocument(courseId: string | undefined) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ file, documentType, chapterId, onProgress }: { file: File; documentType: string; chapterId?: number | null; onProgress?: (progress: UploadProgress) => void }) =>
      api.uploadDocument(courseId!, file, documentType, chapterId, onProgress),
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

export function useGenerationTask(courseId: string | undefined, packageId: number | null) {
  const queryClient = useQueryClient()
  const generationTask = useQuery({
    queryKey: generationTaskQueryKey(courseId, packageId),
    queryFn: () => api.learningPackageTask(courseId!, packageId!),
    enabled: Boolean(courseId && packageId),
    refetchInterval: (query) => {
      const status = query.state.data?.status
      if (status === 'pending') {
        return 1000
      }

      if (status === 'processing') {
        return 2000
      }

      return false
    },
  })

  useEffect(() => {
    const task = generationTask.data
    if (!task || (task.status !== 'completed' && task.status !== 'failed')) {
      return
    }

    queryClient.setQueryData<CourseSpaceResponse>(courseSpaceQueryKey(courseId), (current) => {
      if (!current) return current
      if (task.scene === 'follow' || task.scene === 'textbook' || task.scene === 'exam') {
        if (task.scene === 'follow' && (task.scope_chapter_id != null || task.scope_unassigned)) {
          const key = task.scope_unassigned ? 'unassigned' : String(task.scope_chapter_id)
          return {
            ...current,
            chapter_packages: { ...current.chapter_packages, [key]: task },
            chapter_completed_packages: task.status === 'completed' ? { ...current.chapter_completed_packages, [key]: task } : current.chapter_completed_packages,
          }
        }
        if (task.scene === 'textbook' && task.scope_document_id != null) {
          const key = String(task.scope_document_id)
          return {
            ...current,
            document_packages: { ...current.document_packages, [key]: task },
            document_completed_packages: task.status === 'completed' ? { ...current.document_completed_packages, [key]: task } : current.document_completed_packages,
          }
        }
        return {
          ...current,
          scene_packages: { ...current.scene_packages, [task.scene]: task },
          scene_completed_packages: task.status === 'completed' ? { ...current.scene_completed_packages, [task.scene]: task } : current.scene_completed_packages,
        }
      }
      return { ...current, learning_package: task }
    })
    void queryClient.invalidateQueries({ queryKey: courseSpaceQueryKey(courseId) })
  }, [courseId, generationTask.data, queryClient])

  return generationTask
}

export function useCourseAssistant(courseId: string | undefined) {
  return useMutation({
    mutationFn: (input: AssistantQueryInput) => api.queryCourseAssistant(courseId!, input),
  })
}
