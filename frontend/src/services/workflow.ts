// services/workflow.ts - 工作流服务

import { api } from './api'

export const workflowApi = {
  async getLogs() {
    return api.get('/workflow/logs')
  },
  
  async getStatus() {
    return api.get('/workflow/status')
  },
  
  async getGraph() {
    return api.get('/workflow/graph')
  }
}
