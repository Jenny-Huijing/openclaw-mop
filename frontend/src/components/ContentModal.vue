<template>
  <Teleport to="body">
    <div class="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
         @click.self="$emit('close')">
      <div class="bg-white rounded-xl w-full max-w-4xl shadow-2xl flex flex-col max-h-[90vh]">
        
        <!-- 头部 -->
        <div class="px-5 py-3 border-b border-slate-200 flex items-center justify-between shrink-0">
          <div class="flex items-center gap-3">
            <span :class="statusClass(content.status)" class="px-2 py-0.5 text-xs rounded-full font-medium">
              {{ statusText(content.status) }}
            </span>
            <span class="text-sm text-slate-400">{{ formatTime(content.created_at) }}</span>
          </div>
          
          <button 
            @click="copyAll"
            class="px-3 py-1.5 text-sm text-blue-600 hover:bg-blue-50 rounded-lg flex items-center gap-1.5 transition-colors"
          >
            <DocumentDuplicateIcon class="w-4 h-4" />
            复制全部
          </button>
        </div>
        
        <!-- 内容区 - 左右布局 -->
        <div class="flex-1 overflow-hidden flex">
          <!-- 左侧：配图 -->
          <div v-if="content.images?.length" class="w-[45%] bg-slate-100 border-r border-slate-200 flex flex-col">
            <div class="flex-1 overflow-y-auto p-4 space-y-4">
              <div 
                v-for="(img, idx) in content.images" 
                :key="idx"
                class="bg-white rounded-lg overflow-hidden shadow-sm"
              >
                <div v-if="img.status === 'success'" class="relative group">
                  <img 
                    :src="img.url" 
                    :alt="'配图' + (idx + 1)" 
                    class="w-full aspect-[3/4] object-cover"
                  />
                  <a 
                    :href="img.url" 
                    target="_blank" 
                    class="absolute inset-0 flex items-center justify-center bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity"
                  >
                    <EyeIcon class="w-6 h-6 text-white" />
                  </a>
                </div>
                <p class="text-xs text-slate-500 p-3 line-clamp-2">{{ img.prompt }}</p>
              </div>
            </div>
            <div class="px-4 py-2 text-xs text-slate-400 border-t border-slate-200 bg-slate-50">
              AI生成配图 ({{ content.images.length }}张)
            </div>
          </div>
          
          <!-- 右侧：文字内容 -->
          <div class="flex-1 overflow-y-auto">
            <div class="p-5 space-y-4">
              <!-- 候选标题 -->
              <div v-if="content.titles?.length">
                <div class="flex items-center justify-between mb-2">
                  <span class="text-xs font-medium text-slate-400">候选标题 ({{ content.titles.length }}个)</span>
                  <button 
                    v-if="content.titles.length > 1"
                    @click="showAllTitles = !showAllTitles"
                    class="text-xs text-blue-600 hover:text-blue-700"
                  >
                    {{ showAllTitles ? '收起' : '展开' }}
                  </button>
                </div>
                
                <div class="space-y-2">
                  <div 
                    v-for="(title, idx) in displayedTitles" 
                    :key="idx"
                    @click="copyText(title)"
                    class="flex items-start gap-2 p-3 bg-blue-50 rounded-lg border border-blue-100 cursor-pointer hover:border-blue-300 transition-colors group"
                  >
                    <span class="w-5 h-5 bg-blue-600 text-white rounded-full flex items-center justify-center text-xs font-medium shrink-0 mt-0.5">
                      {{ idx + 1 }}
                    </span>
                    <div class="flex-1">
                      <p class="text-sm font-medium text-slate-900">{{ title }}</p>
                    </div>
                    <ClipboardIcon class="w-4 h-4 text-blue-400 group-hover:text-blue-600 shrink-0 mt-0.5" />
                  </div>
                </div>
              </div>
              
              <!-- 正文 -->
              <div>
                <div class="flex items-center justify-between mb-2">
                  <span class="text-xs font-medium text-slate-400">正文</span>
                  <button 
                    @click="copyText(content.body || '')"
                    class="text-xs text-slate-400 hover:text-blue-600 flex items-center gap-1"
                  >
                    <ClipboardIcon class="w-3 h-3" />
                    复制
                  </button>
                </div>
                
                <div class="bg-slate-50 rounded-lg border border-slate-200 overflow-hidden">
                  <div 
                    :class="[
                      'p-3 text-sm text-slate-700 whitespace-pre-line leading-relaxed',
                      !bodyExpanded && content.body && content.body.length > 300 ? 'line-clamp-10' : ''
                    ]"
                  >
                    {{ content.body }}
                  </div>
                  
                  <button 
                    v-if="content.body && content.body.length > 300"
                    @click="bodyExpanded = !bodyExpanded"
                    class="w-full py-2 text-xs text-blue-600 hover:text-blue-700 font-medium border-t border-slate-200 bg-slate-100/50 hover:bg-slate-100 transition-colors"
                  >
                    {{ bodyExpanded ? '收起正文' : '展开全部' }}
                  </button>
                </div>
              </div>
              
              <!-- 标签 -->
              <div v-if="content.tags?.length">
                <span class="text-xs font-medium text-slate-400 mb-2 block">标签</span>
                <div class="flex flex-wrap gap-2">
                  <span 
                    v-for="tag in content.tags" 
                    :key="tag" 
                    class="px-2.5 py-1 bg-blue-50 text-blue-700 text-sm rounded-full font-medium"
                  >
                    #{{ tag }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 底部操作 - 简洁按钮组 -->
        <div class="px-6 py-4 border-t border-slate-100 bg-white shrink-0">
          <!-- 待审核状态 -->
          <div v-if="content.status === 'reviewing'" class="flex justify-end gap-3">
            <button 
              @click="$emit('close')"
              class="px-5 py-2.5 text-sm font-medium text-slate-600 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors"
            >
              取消
            </button>
            <button 
              @click="$emit('regenerate', content.id); $emit('close')"
              class="px-5 py-2.5 text-sm font-medium text-slate-600 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors"
            >
              重新创作
            </button>
            <button 
              @click="$emit('approve', content.id); $emit('close')"
              class="px-5 py-2.5 text-sm font-medium text-white bg-emerald-500 hover:bg-emerald-600 rounded-lg shadow-sm transition-colors"
            >
              确认审核通过
            </button>
          </div>
          
          <!-- 已通过状态 - 自动发布中（审核通过后自动发布，不需要人工点击） -->
          <div v-if="content.status === 'approved'" class="flex items-center justify-center gap-3 py-3 rounded-xl bg-emerald-50 border border-emerald-200">
            <div class="flex items-center justify-center w-8 h-8 rounded-full bg-emerald-100">
              <svg class="w-5 h-5 text-emerald-600 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            </div>
            <span class="text-emerald-700 font-medium">审核通过，自动发布中...</span>
          </div>
          
          <!-- 已发布状态 - 成功提示 -->
          <div 
            v-if="content.status === 'published'"
            class="flex items-center justify-center gap-3 py-3 rounded-xl bg-slate-50 border border-slate-200"
          >
            <div class="flex items-center justify-center w-8 h-8 rounded-full bg-blue-100">
              <CheckIcon class="w-5 h-5 text-blue-600" />
            </div>
            <span class="text-slate-600 font-medium">内容已发布至小红书</span>
          </div>
          
          <!-- 发布失败状态 - 显示错误和重试 -->
          <div v-if="content.status === 'PUBLISH_FAILED'">
            <div class="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
              <div class="flex items-start gap-2">
                <svg class="w-5 h-5 text-red-500 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div>
                  <p class="text-sm font-medium text-red-700">发布失败</p>
                  <p class="text-xs text-red-600 mt-1">{{ content.error_message || '未知错误' }}</p>
                </div>
              </div>
            </div>
            <div class="flex justify-end gap-3">
              <button 
                @click="$emit('close')"
                class="px-5 py-2.5 text-sm font-medium text-slate-600 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors"
              >
                取消
              </button>
              <button 
                @click="$emit('publish', content.id)"
                class="px-5 py-2.5 text-sm font-medium text-white bg-rose-500 hover:bg-rose-600 rounded-lg shadow-sm transition-colors"
              >
                重试发布
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { Content } from '../types'
import {
  DocumentDuplicateIcon,
  ClipboardIcon,
  CheckIcon,
  EyeIcon
} from '@heroicons/vue/24/outline'

const props = defineProps<{
  content: Content
}>()

defineEmits<{
  close: []
  copy: [content: Content]
  approve: [id: string]
  regenerate: [id: string]
  publish: [id: string]
}>()

const showAllTitles = ref(false)
const bodyExpanded = ref(false)

const displayedTitles = computed(() => {
  if (!showAllTitles.value && props.content.titles && props.content.titles.length > 1) {
    return props.content.titles.slice(0, 1)
  }
  return props.content.titles || []
})

const copyText = (text: string) => {
  navigator.clipboard.writeText(text)
}

const copyAll = () => {
  const title = props.content.titles?.[0] || ''
  const body = props.content.body || ''
  const tags = props.content.tags?.map(t => '#' + t).join(' ') || ''
  const fullText = `${title}\n\n${body}\n\n${tags}`
  navigator.clipboard.writeText(fullText)
}

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

import { formatLocalTime } from '../utils/date'

const formatTime = (time: string) => {
  if (!time) return ''
  return formatLocalTime(time)
}
</script>
