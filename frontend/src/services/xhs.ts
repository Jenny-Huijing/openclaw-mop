// services/xhs.ts
import { api } from './api'

export interface XHSAccount {
  followers: number
  total_notes: number
  total_likes: number
  avg_engagement: number
  nickname: string
  avatar: string
}

export interface XHSNote {
  note_id: string
  title: string
  likes: number
  comments: number
  collects: number
  views: number
  created_time: string
}

export const xhsApi = {
  async getStats() {
    const res = await api.get<{
      code: number
      data: XHSAccount
      message: string
    }>('/xhs/stats')
    return res
  },

  async refreshStats() {
    const res = await api.post<{
      code: number
      data: XHSAccount
      message: string
    }>('/xhs/stats/refresh')
    return res
  },

  async getAccount() {
    const res = await api.get<{
      code: number
      data: any
      message: string
      setup_guide?: any
    }>('/xhs/account')
    return res
  },

  async getNotes(limit: number = 10) {
    const res = await api.get<{
      code: number
      data: { items: XHSNote[], total: number }
      message: string
    }>(`/xhs/notes?limit=${limit}`)
    return res
  }
}
