export type DocumentType = 'TEXTBOOK' | 'SLIDES' | 'NOTES' | 'EXAM' | 'HOMEWORK' | 'OTHER'

export interface UploadCategory {
  type: DocumentType
  label: string
  action: string
  description: string
  primary: boolean
}

export const UPLOAD_CATEGORIES: UploadCategory[] = [
  {
    type: 'TEXTBOOK',
    label: '教材',
    action: '上传教材',
    description: '教材、参考书或章节讲义',
    primary: false,
  },
  {
    type: 'SLIDES',
    label: '课件',
    action: '上传课件',
    description: '老师 PPT 或课堂幻灯片',
    primary: true,
  },
  {
    type: 'NOTES',
    label: '补充资料',
    action: '上传补充资料',
    description: '电子笔记、讲义或其他辅助材料',
    primary: false,
  },
  {
    type: 'EXAM',
    label: '试卷',
    action: '上传试卷',
    description: '历年试卷或模拟题',
    primary: true,
  },
  {
    type: 'HOMEWORK',
    label: '作业',
    action: '上传作业',
    description: '平时作业或习题材料',
    primary: true,
  },
  {
    type: 'OTHER',
    label: '补充资料',
    action: '上传补充资料',
    description: '电子资料、补充讲义或参考内容',
    primary: true,
  },
]

export const PRIMARY_UPLOAD_CATEGORIES = UPLOAD_CATEGORIES.filter((category) => category.primary)
