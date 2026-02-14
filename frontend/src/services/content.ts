// services/content.ts
import { api } from './api'
import type { Content } from '../types'

export interface ApiResponse<T> {
  code: number
  message: string
  data: T
}

export interface ContentListResponse {
  items: Content[]
  total: number
  limit: number
  offset: number
}

export const contentApi = {
  getList: (limit = 20) => 
    api.get<ApiResponse<ContentListResponse>>(`/contents?limit=${limit}`),
  
  getById: (id: string) => 
    api.get<ApiResponse<Content>>(`/contents/${id}`),
  
  approve: (id: string) => 
    api.post<ApiResponse<Content>>(`/contents/${id}/approve`),
  
  reject: (id: string) => 
    api.post<ApiResponse<Content>>(`/contents/${id}/reject`),
  
  startWorkflow: () => 
    api.post<ApiResponse<{ workflow_id: string; content: Content }>>('/agent/workflow/start'),
  
  autoPublish: (id: string) =>
    api.post<ApiResponse<Content>>(`/contents/${id}/auto-publish`),
  
  regenerate: (id: string) =>
    api.post<ApiResponse<Content>>(`/contents/${id}/regenerate`),

  remove: (id: string) =>
    api.delete<ApiResponse<void>>(`/contents/${id}`)
}
