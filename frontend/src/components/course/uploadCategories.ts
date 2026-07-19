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
    primary: true,
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
    label: '笔记',
    action: '上传笔记',
    description: '课堂笔记或复习笔记',
    primary: true,
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
    primary: false,
  },
  {
    type: 'OTHER',
    label: '其他资料',
    action: '上传其他资料',
    description: '无法归入以上类别的资料',
    primary: false,
  },
]

export const PRIMARY_UPLOAD_CATEGORIES = UPLOAD_CATEGORIES.filter((category) => category.primary)
