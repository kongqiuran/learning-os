import type { LearningPackage } from '../types/api'

export function taskStatus(item: LearningPackage | null | undefined) {
  if (item?.task) return item.task.status
  if (item?.status === 'pending') return 'PENDING'
  if (item?.status === 'processing') return 'RUNNING'
  if (item?.status === 'completed') return 'SUCCESS'
  if (item?.status === 'failed') return 'FAILED'
  return null
}

export function isTaskActive(item: LearningPackage | null | undefined) {
  const status = taskStatus(item)
  return status === 'PENDING' || status === 'RUNNING'
}
