<template>
  <div class="max-w-7xl mx-auto px-6">
    <!-- 页面头部 -->
    <div class="mb-6">
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-2xl font-bold text-slate-900">定时任务</h1>
          <p class="text-slate-500 mt-1">系统自动化任务调度管理</p>
        </div>
        <!-- 调度器状态卡片 -->
        <div class="flex items-center gap-4">
          <div class="bg-white rounded-lg border border-slate-200 px-4 py-3 flex items-center gap-3">
            <div 
              :class="[
                'w-3 h-3 rounded-full animate-pulse',
                schedulerStatus?.is_running ? 'bg-emerald-500' : 'bg-red-500'
              ]"></div>
            <div>
              <p class="text-sm font-medium text-slate-900">调度器状态</p>
              <p class="text-xs text-slate-500">{{ schedulerStatus?.is_running ? '运行中' : '已停止' }}</p>
            </div>
          </div>
          
          <div class="bg-white rounded-lg border border-slate-200 px-4 py-3">
            <p class="text-sm font-medium text-slate-900">活跃任务</p>
            <p class="text-xs text-slate-500">{{ schedulerStatus?.active_tasks || 0 }} 个</p>
          </div>
          
          <div class="bg-white rounded-lg border border-slate-200 px-4 py-3">
            <p class="text-sm font-medium text-slate-900">运行时长</p>
            <p class="text-xs text-slate-500">{{ schedulerStatus?.uptime || '-' }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 任务列表 -->
    <div class="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      <!-- 表头 -->
      <div class="grid grid-cols-12 gap-4 px-6 py-4 bg-slate-50 border-b border-slate-200 text-sm font-medium text-slate-600">
        <div class="col-span-3">任务名称</div>
        <div class="col-span-3">任务描述</div>
        <div class="col-span-2">调度规则</div>
        <div class="col-span-1">优先级</div>
        <div class="col-span-1">状态</div>
        <div class="col-span-2 text-right">操作</div>
      </div>

      <!-- 任务行 -->
      <div 
        v-for="task in tasks" 
        :key="task.id"
        class="grid grid-cols-12 gap-4 px-6 py-4 border-b border-slate-100 hover:bg-slate-50 transition-colors"
      >
        <!-- 任务名称 -->
        <div class="col-span-3">
          <div class="flex items-center gap-2">
            <component 
              :is="getTaskIcon(task.id)" 
              class="w-5 h-5 text-slate-400"
            />
            <div>
              <p class="font-medium text-slate-900">{{ task.name }}</p>
              <p class="text-xs text-slate-500 font-mono mt-0.5">{{ task.task_module.split('.').pop() }}</p>
            </div>
          </div>
        </div>

        <!-- 任务描述 -->
        <div class="col-span-3">
          <p class="text-sm text-slate-600 leading-relaxed">{{ task.description }}</p>
        </div>

        <!-- 调度规则 -->
        <div class="col-span-2">
          <div class="flex items-center gap-1.5">
            <ClockIcon class="w-4 h-4 text-slate-400" />
            <span class="text-sm text-slate-600">{{ task.schedule_display }}</span>
          </div>
          <p v-if="task.next_run" class="text-xs text-slate-400 mt-1">
            下次: {{ formatTime(task.next_run) }}
          </p>
        </div>

        <!-- 优先级 -->
        <div class="col-span-1">
          <span :class="[
            'inline-flex items-center px-2 py-0.5 rounded text-xs font-medium',
            priorityClasses[task.priority]
          ]">
            {{ priorityLabels[task.priority] }}
          </span>
        </div>

        <!-- 状态 -->
        <div class="col-span-1">
          <span :class="[
            'inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium',
            statusClasses[task.status]
          ]">
            <span :class="['w-1.5 h-1.5 rounded-full', statusDotClasses[task.status]]"></span>
            {{ statusLabels[task.status] }}
          </span>
        </div>

        <!-- 操作 -->
        <div class="col-span-2 text-right">
          <button 
            @click="runTaskNow(task.id)"
            :disabled="runningTask === task.id"
            class="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded-lg transition-colors disabled:opacity-50 whitespace-nowrap"
          >
            <PlayIcon v-if="runningTask !== task.id" class="w-4 h-4" />
            <ArrowPathIcon v-else class="w-4 h-4 animate-spin" />
            {{ runningTask === task.id ? '执行中' : '立即执行' }}
          </button>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-if="tasks.length === 0" class="py-16 text-center">
        <ClockIcon class="w-16 h-16 mx-auto mb-4 text-slate-300" />
        <p class="text-slate-500">暂无定时任务</p>
      </div>
    </div>

    <!-- 执行历史 -->
    <div class="mt-6 bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      <div class="px-6 py-4 border-b border-slate-200">
        <h3 class="font-semibold text-slate-900">最近执行记录</h3>
      </div>
      
      <div class="divide-y divide-slate-100">
        <div 
          v-for="execution in executions" 
          :key="execution.task_id"
          class="px-6 py-3 flex items-center justify-between hover:bg-slate-50"
        >
          <div class="flex items-center gap-3">
            <div :class="[
              'w-2 h-2 rounded-full',
              execution.status === 'success' ? 'bg-emerald-500' :
              execution.status === 'running' ? 'bg-blue-500 animate-pulse' :
              'bg-red-500'
            ]"></div>
            <div>
              <p class="text-sm font-medium text-slate-900">{{ execution.task_name }}</p>
              <p class="text-xs text-slate-500">{{ formatTime(execution.started_at) }}</p>
            </div>
          </div>
          
          <div class="flex items-center gap-4">
            <span v-if="execution.duration" class="text-sm text-slate-500">
              耗时 {{ execution.duration }}s
            </span>
            <span :class="[
              'inline-flex items-center px-2 py-0.5 rounded text-xs font-medium',
              execution.status === 'success' ? 'bg-emerald-100 text-emerald-700' :
              execution.status === 'running' ? 'bg-blue-100 text-blue-700' :
              'bg-red-100 text-red-700'
            ]">
              {{ execution.status === 'success' ? '成功' : execution.status === 'running' ? '执行中' : '失败' }}
            </span>
          </div>
        </div>

        <div v-if="executions.length === 0" class="py-8 text-center text-slate-500">
          暂无执行记录
        </div>
      </div>
    </div>

    <!-- Toast -->
    <Toast :toast="toast" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { schedulerApi, type ScheduledTask, type SchedulerStatus, type TaskExecution } from '../services/scheduler'
import { useToast } from '../composables/useToast'
import {
  ClockIcon,
  PlayIcon,
  ArrowPathIcon,
  ChartBarIcon,
  FireIcon,
  BellIcon,
  TrashIcon
} from '@heroicons/vue/24/outline'
import Toast from '../components/Toast.vue'

const tasks = ref<ScheduledTask[]>([])
const schedulerStatus = ref<SchedulerStatus | null>(null)
const executions = ref<TaskExecution[]>([])
const loading = ref(false)
const runningTask = ref<string | null>(null)
const { toast, show: showToast } = useToast()

const priorityClasses: Record<string, string> = {
  high: 'bg-rose-100 text-rose-700',
  medium: 'bg-amber-100 text-amber-700',
  low: 'bg-slate-100 text-slate-600'
}

const priorityLabels: Record<string, string> = {
  high: '高',
  medium: '中',
  low: '低'
}

const statusClasses: Record<string, string> = {
  active: 'bg-emerald-100 text-emerald-700',
  paused: 'bg-amber-100 text-amber-700',
  error: 'bg-red-100 text-red-700'
}

const statusDotClasses: Record<string, string> = {
  active: 'bg-emerald-500',
  paused: 'bg-amber-500',
  error: 'bg-red-500'
}

const statusLabels: Record<string, string> = {
  active: '正常',
  paused: '暂停',
  error: '异常'
}

const getTaskIcon = (taskId: string) => {
  const iconMap: Record<string, any> = {
    'fetch-published-analytics': ChartBarIcon,
    'fetch-hotspots': FireIcon,
    'send-daily-hotspot-digest': BellIcon,
    'clean-expired-hotspots': TrashIcon
  }
  return iconMap[taskId] || ClockIcon
}

import { formatLocalTime } from '../utils/date'

const formatTime = (time: string) => {
  if (!time) return '-'
  return formatLocalTime(time)
}

const fetchData = async () => {
  loading.value = true
  try {
    const [tasksRes, statusRes, executionsRes] = await Promise.all([
      schedulerApi.getTasks(),
      schedulerApi.getStatus(),
      schedulerApi.getExecutions()
    ])
    
    if (tasksRes.code === 200) {
      tasks.value = tasksRes.data.tasks
    }
    if (statusRes.code === 200) {
      schedulerStatus.value = statusRes.data
    }
    if (executionsRes.code === 200) {
      executions.value = executionsRes.data.executions
    }
  } catch (e) {
    console.error('获取定时任务数据失败:', e)
    showToast('获取数据失败', 'error')
  } finally {
    loading.value = false
  }
}

const runTaskNow = async (taskId: string) => {
  runningTask.value = taskId
  try {
    const res = await schedulerApi.runTask(taskId)
    if (res.code === 200) {
      showToast('任务已加入执行队列', 'success')
    } else {
      showToast(res.message || '启动任务失败', 'error')
    }
  } catch (e: any) {
    showToast(e.message || '启动任务失败', 'error')
  } finally {
    runningTask.value = null
  }
}

onMounted(fetchData)

// 自动刷新
setInterval(fetchData, 30000)
</script>
