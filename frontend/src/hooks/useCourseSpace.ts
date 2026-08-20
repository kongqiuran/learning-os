// 文件说明：课程空间相关 Hook。useQuery/useMutation/useQueryClient 来自 TanStack React Query，用来请求、提交和刷新课程空间数据。
import { useEffect } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api, type UploadProgress } from '../lib/api'
import { isTaskActive, taskStatus } from '../lib/tasks'
import type { AssistantQueryInput, CourseSpaceResponse } from '../types/api'

// React Query 用 queryKey 区分“这份缓存数据属于哪个接口/哪个课程”。
// 例如 ['course-space', '12'] 表示课程 12 的课程空间数据。
export const courseSpaceQueryKey = (courseId: string | undefined) => ['course-space', courseId] as const
// AI 整理任务也需要单独缓存，因为同一门课可能有不同的生成任务。
export const generationTaskQueryKey = (courseId: string | undefined, packageId: number | null) =>
  ['generation-task', courseId, packageId] as const

// useCourseSpace 是一个自定义 Hook。
// 页面只需要调用 useCourseSpace(courseId)，就能拿到课程空间的数据、加载状态和错误状态。
export function useCourseSpace(courseId: string | undefined) {
  return useQuery({
    // queryKey 决定缓存身份：课程 id 不同，缓存也不同。
    queryKey: courseSpaceQueryKey(courseId),
    // queryFn 是真正发请求的函数。courseId! 的 ! 表示告诉 TypeScript：这里我确认 courseId 有值。
    queryFn: () => api.courseSpace(courseId!),
    // enabled 为 false 时不会发请求。这里避免 courseId 还没从路由解析出来就请求接口。
    enabled: Boolean(courseId),
    // 如果课程里有 AI 整理任务还在运行，就每 2 秒刷新一次，页面可以自动看到进度变化。
    // 如果没有运行中的任务，就返回 false，停止轮询，避免浪费请求。
    refetchInterval: (query) => hasActiveGeneration(query.state.data) ? 2000 : false,
  })
}

function hasActiveGeneration(data: CourseSpaceResponse | undefined) {
  // 没有数据时，当然也无法判断有任务在运行，所以返回 false。
  if (!data) return false
  // Object.values 会取出对象里的所有值；... 是展开语法，把多个数组合并进一个大数组。
  // 这里把按场景、按章节、按文档保存的 AI 任务都放到一起检查。
  const packages = [
    ...Object.values(data.scene_packages),
    ...Object.values(data.chapter_packages),
    ...Object.values(data.document_packages),
  ]
  // some 表示“只要有一个符合条件就返回 true”。
  // isTaskActive 会判断任务是否还在 pending/running 状态。
  return packages.some(isTaskActive)
}

export function useUploadDocument(courseId: string | undefined) {
  // queryClient 可以手动操作 React Query 缓存，比如让某个接口重新请求。
  const queryClient = useQueryClient()
  return useMutation({
    // useMutation 适合“会改变服务器数据”的操作，例如上传、删除、创建。
    // mutationFn 接收页面传来的文件和分类，然后调用 api.uploadDocument 发给后端。
    mutationFn: ({ file, documentType, chapterId, onProgress }: { file: File; documentType: string; chapterId?: number | null; onProgress?: (progress: UploadProgress) => void }) =>
      api.uploadDocument(courseId!, file, documentType, chapterId, onProgress),
    // 上传成功后，课程资料列表已经变了，所以让课程空间缓存失效。
    // invalidateQueries 会触发重新请求，页面就能看到新上传的文件。
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
    // 只有 courseId 和 packageId 都存在时才查任务状态。
    enabled: Boolean(courseId && packageId),
    // 根据任务状态决定轮询频率：排队中更频繁，运行中稍慢一点，结束后停止。
    refetchInterval: (query) => {
      const status = taskStatus(query.state.data)
      if (status === 'PENDING') {
        return 1000
      }

      if (status === 'RUNNING') {
        return 2000
      }

      return false
    },
  })

  useEffect(() => {
    const task = generationTask.data
    const status = taskStatus(task)
    // useEffect 会在任务数据变化后运行。
    // 如果任务还没结束，就不更新课程空间缓存。
    if (!task || (status !== 'SUCCESS' && status !== 'FAILED')) {
      return
    }

    // 任务结束后，把最新任务结果写回课程空间缓存。
    // 这样用户不用手动刷新页面，也能立刻看到“整理完成/失败”的状态。
    queryClient.setQueryData<CourseSpaceResponse>(courseSpaceQueryKey(courseId), (current) => {
      if (!current) return current
      if (task.scene === 'follow' || task.scene === 'textbook' || task.scene === 'exam') {
        if (task.scene === 'follow' && (task.scope_chapter_id != null || task.scope_unassigned)) {
          const key = task.scope_unassigned ? 'unassigned' : String(task.scope_chapter_id)
          return {
            ...current,
            chapter_packages: { ...current.chapter_packages, [key]: task },
            chapter_completed_packages: status === 'SUCCESS' ? { ...current.chapter_completed_packages, [key]: task } : current.chapter_completed_packages,
          }
        }
        if (task.scene === 'textbook' && task.scope_document_id != null) {
          const key = String(task.scope_document_id)
          return {
            ...current,
            document_packages: { ...current.document_packages, [key]: task },
            document_completed_packages: status === 'SUCCESS' ? { ...current.document_completed_packages, [key]: task } : current.document_completed_packages,
          }
        }
        return {
          ...current,
          scene_packages: { ...current.scene_packages, [task.scene]: task },
          scene_completed_packages: status === 'SUCCESS' ? { ...current.scene_completed_packages, [task.scene]: task } : current.scene_completed_packages,
        }
      }
      return { ...current, learning_package: task }
    })
    void queryClient.invalidateQueries({ queryKey: courseSpaceQueryKey(courseId) })
    void queryClient.invalidateQueries({ queryKey: ['billing', 'usage'] })
  }, [courseId, generationTask.data, queryClient])

  return generationTask
}

export function useCourseAssistant(courseId: string | undefined) {
  const queryClient = useQueryClient()
  return useMutation({
    // 用户提问是一次 POST 请求，会消耗助手额度，所以用 useMutation。
    mutationFn: (input: AssistantQueryInput) => api.queryCourseAssistant(courseId!, input),
    // onSettled 表示无论成功还是失败都会执行。
    // 因为请求可能消耗额度，所以结束后刷新“使用额度”数据。
    onSettled: () => queryClient.invalidateQueries({ queryKey: ['billing', 'usage'] }),
  })
}
