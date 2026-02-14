// services/scheduler.ts
import { api } from './api'

export interface ScheduledTask {
  id: string
  name: string
  description: string
  schedule_type: string
  schedule_display: string
  interval_seconds?: number
  crontab?: string
  last_run?: string
  next_run?: string
  status: string
  task_module: string
  priority: string
}

export interface SchedulerStatus {
  is_running: boolean
  active_tasks: number
  queued_tasks: number
  last_beat?: string
  uptime?: string
}

export interface TaskExecution {
  task_id: string
  task_name: string
  status: string
  started_at: string
  finished_at?: string
  duration?: number
  error_message?: string
}

export const schedulerApi = {
  getTasks: () =>
    api.get<{ code: number; data: { tasks: ScheduledTask[]; total: number }; message: string }>('/scheduler/tasks'),
  
  getStatus: () =>
    api.get<{ code: number; data: SchedulerStatus; message: string }>('/scheduler/status'),
  
  getExecutions: (limit = 20) =>
    api.get<{ code: number; data: { executions: TaskExecution[]; total: number }; message: string }>(`/scheduler/executions?limit=${limit}`),
  
  runTask: (taskId: string) =>
    api.post<{ code: number; data: any; message: string }>(`/scheduler/tasks/${taskId}/run`)
}
