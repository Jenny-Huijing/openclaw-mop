// types/index.ts

export interface Content {
  id: string
  workflow_id: string
  titles?: string[]
  body?: string
  tags?: string[]
  image_prompts?: string[]
  images?: ImageItem[]
  status: 'CREATING' | 'reviewing' | 'approved' | 'published' | 'rejected' | 'PUBLISH_FAILED'
  error_message?: string
  created_at: string
  updated_at?: string
}

export interface ImageItem {
  prompt: string
  url?: string
  local_path?: string
  status: 'success' | 'failed'
  error?: string
}

export interface ContentStats {
  total: number
  creating: number
  reviewing: number
  approved: number
  followers: string
}

export interface ToastState {
  show: boolean
  message: string
  type: 'success' | 'error'
}

export type FilterType = 'all' | 'CREATING' | 'reviewing' | 'approved' | 'published' | 'PUBLISH_FAILED'
