<template>
  <div class="p-5 border-b border-slate-100 last:border-0 hover:bg-slate-50 transition-colors cursor-pointer"
       @click="$emit('click')">
    <div class="flex items-start justify-between gap-4">
      <div class="flex-1 min-w-0">
        <div class="flex items-center gap-2 mb-2">
          <span :class="statusClass(content.status)" class="px-2 py-0.5 text-xs rounded-full font-medium">
            {{ statusText(content.status) }}
          </span>
          <span class="text-sm text-slate-400">{{ formatTime(content.created_at) }}</span>
        </div>
        
        <h3 class="font-semibold text-slate-900 mb-2 truncate">
          {{ content.titles?.[0] || '无标题' }}
        </h3>
        
        <div v-if="content.tags?.length" class="flex flex-wrap gap-1.5 mb-2">
          <span v-for="tag in content.tags.slice(0, 5)" :key="tag" 
                class="px-2 py-0.5 bg-slate-100 text-slate-600 text-xs rounded">
            #{{ tag }}
          </span>
        </div>
        
        <p v-if="content.body" class="text-sm text-slate-500 line-clamp-2">
          {{ content.body.substring(0, 120) }}
        </p>
        
        <!-- 错误原因显示 -->
        <p v-if="content.status === 'PUBLISH_FAILED' && content.error_message" 
           class="mt-2 text-xs text-red-600 bg-red-50 px-2 py-1 rounded line-clamp-2">
          ❌ 失败原因: {{ content.error_message }}
        </p>
      </div>
      
      <div class="flex items-center gap-2 flex-shrink-0">
        <button @click.stop="$emit('copy', content)" 
                class="p-2 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                title="复制内容">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
          </svg>
        </button>
        <button v-if="content.status === 'reviewing'"
                @click.stop="$emit('approve', content.id)"
                class="px-3 py-1.5 text-sm bg-emerald-600 text-white hover:bg-emerald-700 rounded-lg transition-colors">
          通过
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Content } from '../types'

defineProps<{
  content: Content
}>()

defineEmits<{
  click: []
  copy: [content: Content]
  approve: [id: string]
}>()

const statusClass = (status: string) => {
  const map: Record<string, string> = {
    reviewing: 'bg-amber-100 text-amber-700',
    approved: 'bg-emerald-100 text-emerald-700',
    published: 'bg-blue-100 text-blue-700',
    rejected: 'bg-slate-100 text-slate-600',
    CREATING: 'bg-blue-100 text-blue-700',
    PUBLISH_FAILED: 'bg-red-100 text-red-700',
  }
  return map[status] || 'bg-slate-100 text-slate-600'
}

const statusText = (status: string) => {
  const map: Record<string, string> = {
    reviewing: '待审核',
    approved: '已通过',
    published: '已发布',
    rejected: '已拒绝',
    CREATING: '创作中',
    PUBLISH_FAILED: '发布失败',
  }
  return map[status] || status
}

import { parseLocalTime } from '../utils/date'

const formatTime = (time: string) => {
  if (!time) return ''
  const date = parseLocalTime(time)
  const now = new Date()
  
  // 使用本地日期字符串比较是否为同一天
  const dateStr = date.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' })
  const nowStr = now.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' })
  
  if (dateStr === nowStr) {
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  }
  
  return date.toLocaleDateString('zh-CN', { 
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' 
  })
}
</script>
