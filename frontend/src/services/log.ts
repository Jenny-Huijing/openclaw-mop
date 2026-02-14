// services/log.ts - 日志服务

import { api } from './api'

export interface LogQuery {
  service?: string
  level?: string
  limit?: number
  offset?: number
}

export const logApi = {
  async getLogs(params?: LogQuery) {
    const query = new URLSearchParams()
    if (params?.service) query.append('service', params.service)
    if (params?.level) query.append('level', params.level)
    if (params?.limit) query.append('limit', params.limit.toString())
    if (params?.offset) query.append('offset', params.offset.toString())
    
    return api.get(`/logs?${query.toString()}`)
  }
}
