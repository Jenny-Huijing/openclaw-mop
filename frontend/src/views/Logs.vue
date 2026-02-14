<template>
  <div class="py-8">
    <div class="max-w-7xl mx-auto px-6">
      <!-- 页面标题 -->
      <div class="mb-8 flex items-center justify-between">
        <div>
          <h1 class="text-2xl font-bold text-slate-900">系统日志</h1>
          <p class="text-slate-500 mt-1">查看平台后台运行日志和错误信息</p>
        </div>
        <div class="flex gap-3">
          <select 
            v-model="selectedService"
            class="px-4 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">所有服务</option>
            <option value="api">API 服务</option>
            <option value="worker">Worker 服务</option>
            <option value="scheduler">调度器</option>
            <option value="nginx">Nginx</option>
          </select>
          
          <select 
            v-model="selectedLevel"
            class="px-4 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">所有级别</option>
            <option value="INFO">INFO</option>
            <option value="WARNING">WARNING</option>
            <option value="ERROR">ERROR</option>
          </select>
          
          <button 
            @click="refreshLogs"
            :disabled="loading"
            class="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
          >
            <svg 
              :class="['w-4 h-4', loading ? 'animate-spin' : '']" 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
            </svg>
            刷新
          </button>
        </div>
      </div>

      <!-- 日志统计 -->
      <div class="grid grid-cols-4 gap-4 mb-6">
        <div class="bg-white rounded-lg border border-slate-200 p-4">
          <div class="text-sm text-slate-500">总日志数</div>
          <div class="text-2xl font-bold text-slate-900 mt-1">{{ stats.total }}</div>
        </div>
        <div class="bg-white rounded-lg border border-slate-200 p-4">
          <div class="text-sm text-slate-500">INFO</div>
          <div class="text-2xl font-bold text-blue-600 mt-1">{{ stats.info }}</div>
        </div>
        <div class="bg-white rounded-lg border border-slate-200 p-4">
          <div class="text-sm text-slate-500">WARNING</div>
          <div class="text-2xl font-bold text-amber-600 mt-1">{{ stats.warning }}</div>
        </div>
        <div class="bg-white rounded-lg border border-slate-200 p-4">
          <div class="text-sm text-slate-500">ERROR</div>
          <div class="text-2xl font-bold text-red-600 mt-1">{{ stats.error }}</div>
        </div>
      </div>

      <!-- 日志列表 -->
      <div class="bg-white rounded-xl border border-slate-200 shadow-sm relative">
        <!-- 固定在顶部的工具栏 -->
        <div class="sticky top-0 z-10 bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between shadow-sm">
          <div class="flex items-center gap-4">
            <input 
              v-model="searchQuery"
              type="text"
              placeholder="搜索日志内容..."
              class="px-4 py-2 border border-slate-300 rounded-lg text-sm w-64 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
            <button 
              @click="clearSearch"
              v-if="searchQuery"
              class="text-slate-400 hover:text-slate-600"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
              </svg>
            </button>
          </div>
          
          <div class="flex items-center gap-2">
            <button 
              @click="autoRefresh = !autoRefresh"
              :class="[
                'px-3 py-1.5 rounded-lg text-sm font-medium flex items-center gap-2',
                autoRefresh ? 'bg-blue-100 text-blue-700' : 'bg-slate-100 text-slate-600'
              ]"
            >
              <span class="w-2 h-2 rounded-full" :class="autoRefresh ? 'bg-blue-500 animate-pulse' : 'bg-slate-400'"></span>
              {{ autoRefresh ? '实时刷新中' : '已暂停' }}
            </button>
          </div>
        </div>
        
        <div ref="logContainer" class="max-h-[600px] overflow-y-auto font-mono text-sm">
          <div v-if="filteredLogs.length === 0" class="p-8 text-center text-slate-500">
            暂无日志
          </div>
          
          <div 
            v-for="(log, index) in filteredLogs" 
            :key="index"
            :class="[
              'px-6 py-3 border-b border-slate-100 flex items-start gap-4 hover:bg-slate-50',
              log.level === 'ERROR' ? 'bg-red-50' : '',
              log.level === 'WARNING' ? 'bg-amber-50' : ''
            ]"
          >
            <!-- 时间 -->
            <div class="text-slate-400 w-36 shrink-0">
              {{ formatTime(log.timestamp) }}
            </div>
            
            <!-- 服务名 -->
            <div class="w-24 shrink-0">
              <span class="px-2 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-600">
                {{ log.service }}
              </span>
            </div>
            
            <!-- 级别 -->
            <div class="w-20 shrink-0">
              <span :class="[
                'px-2 py-0.5 rounded text-xs font-medium',
                levelClasses[log.level]
              ]">
                {{ log.level }}
              </span>
            </div>
            
            <!-- 内容 -->
            <div class="flex-1 break-all" :class="levelTextClasses[log.level]">
              {{ log.message }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { logApi } from '../services/log'

const loading = ref(false)
const logs = ref([])
const selectedService = ref('all')
const selectedLevel = ref('all')
const searchQuery = ref('')
const autoScroll = ref(false)  // 自动滚动功能已禁用
const autoRefresh = ref(true)
const logContainer = ref(null)
let refreshInterval = null

const levelClasses = {
  INFO: 'bg-blue-100 text-blue-700',
  WARNING: 'bg-amber-100 text-amber-700',
  ERROR: 'bg-red-100 text-red-700',
  DEBUG: 'bg-slate-100 text-slate-600'
}

const levelTextClasses = {
  INFO: 'text-slate-700',
  WARNING: 'text-amber-800',
  ERROR: 'text-red-800',
  DEBUG: 'text-slate-500'
}

const stats = computed(() => ({
  total: logs.value.length,
  info: logs.value.filter(l => l.level === 'INFO').length,
  warning: logs.value.filter(l => l.level === 'WARNING').length,
  error: logs.value.filter(l => l.level === 'ERROR').length
}))

const filteredLogs = computed(() => {
  return logs.value.filter(log => {
    if (selectedService.value !== 'all' && log.service !== selectedService.value) {
      return false
    }
    if (selectedLevel.value !== 'all' && log.level !== selectedLevel.value) {
      return false
    }
    if (searchQuery.value && !log.message.toLowerCase().includes(searchQuery.value.toLowerCase())) {
      return false
    }
    return true
  })
})

import { parseLocalTime } from '../utils/date'

const formatTime = (timestamp: string) => {
  if (!timestamp || timestamp === 'Invalid Date') {
    return '--:--:--'
  }
  
  try {
    // 手动解析无时区时间戳，避免 UTC 转换
    const cleanTs = timestamp.split('.')[0]
    if (cleanTs.includes('T')) {
      const [datePart, timePart] = cleanTs.split('T')
      const [year, month, day] = datePart.split('-').map(Number)
      const [hour, minute, second = 0] = timePart.split(':').map(Number)
      const date = new Date(year, month - 1, day, hour, minute, second)
      
      if (isNaN(date.getTime())) {
        return '--:--:--'
      }
      
      return date.toLocaleTimeString('zh-CN', { 
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      })
    }
    
    // 其他格式直接解析
    const date = parseLocalTime(timestamp)
    if (isNaN(date.getTime())) {
      return '--:--:--'
    }
    return date.toLocaleTimeString('zh-CN', { 
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  } catch (e) {
    return '--:--:--'
  }
}

const refreshLogs = async () => {
  if (loading.value) return
  loading.value = true
  
  try {
    const res = await logApi.getLogs({
      service: selectedService.value === 'all' ? undefined : selectedService.value,
      level: selectedLevel.value === 'all' ? undefined : selectedLevel.value,
      limit: 200
    })
    
    if (res.code === 200) {
      logs.value = res.data.logs || []
      // 保持当前滚动位置，不自动滚动
    }
  } catch (e) {
    console.error('获取日志失败:', e)
  } finally {
    loading.value = false
  }
}

const clearSearch = () => {
  searchQuery.value = ''
}

// 监听筛选条件变化
watch([selectedService, selectedLevel], () => {
  refreshLogs()
})

// 自动滚动功能已禁用，保持用户当前滚动位置
// 用户可通过点击"最新"按钮手动滚动到底部

// 滚动功能已移除，日志按倒序显示，最新日志在最上方

// 监听自动刷新
watch(autoRefresh, (val) => {
  if (val) {
    refreshLogs()
    startRefreshInterval()
  } else {
    stopRefreshInterval()
  }
})

const startRefreshInterval = () => {
  stopRefreshInterval()
  // 每 3 秒自动刷新（更实时）
  refreshInterval = setInterval(() => {
    if (!loading.value) {
      refreshLogs()
    }
  }, 3000)
}

const stopRefreshInterval = () => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
    refreshInterval = null
  }
}

onMounted(() => {
  refreshLogs()
  startRefreshInterval()
})

onUnmounted(() => {
  stopRefreshInterval()
})
</script>
