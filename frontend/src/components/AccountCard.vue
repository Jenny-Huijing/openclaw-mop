<template>
  <div class="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
    <!-- 账号头部 -->
    <div class="p-4 border-b border-slate-100">
      <div class="flex items-center gap-3">
        <!-- 头像 -->
        <div class="relative">
          <img 
            v-if="account.avatar" 
            :src="account.avatar" 
            :alt="account.nickname"
            class="w-12 h-12 rounded-full object-cover border-2 border-rose-100"
          />
          <div 
            v-else 
            class="w-12 h-12 rounded-full bg-gradient-to-br from-rose-400 to-pink-500 flex items-center justify-center"
          >
            <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
          </div>
          <!-- 平台标识 -->
          <div class="absolute -bottom-0.5 -right-0.5 w-4 h-4 bg-rose-500 rounded-full flex items-center justify-center border-2 border-white">
            <svg class="w-2.5 h-2.5 text-white" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/>
            </svg>
          </div>
        </div>
        
        <!-- 账号名称 -->
        <div class="flex-1 min-w-0">
          <h3 class="font-semibold text-slate-900 truncate">
            {{ account.nickname || '小红书账号' }}
          </h3>
          <div class="flex items-center gap-1 text-xs text-slate-500 mt-0.5">
            <span>{{ account.nickname ? '数据每小时自动更新' : '配置Cookie后可获取真实数据' }}</span>
            <button 
              @click="handleRefresh"
              :disabled="isRefreshing"
              class="p-0.5 rounded hover:bg-slate-100 transition-colors"
              title="刷新账号数据"
            >
              <svg 
                class="w-3 h-3 text-slate-400" 
                :class="{ 'animate-spin': isRefreshing }"
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 数据概览 -->
    <div class="grid grid-cols-3 divide-x divide-slate-100">
      <div class="p-4 text-center">
        <div class="text-xl font-bold text-slate-900">{{ formatNumber(account.followers) }}</div>
        <div class="text-xs text-slate-500 mt-0.5">粉丝</div>
      </div>
      <div class="p-4 text-center">
        <div class="text-xl font-bold text-slate-900">{{ account.total_notes }}</div>
        <div class="text-xs text-slate-500 mt-0.5">笔记</div>
      </div>
      <div class="p-4 text-center">
        <div class="text-xl font-bold text-rose-600">{{ formatNumber(account.total_likes) }}</div>
        <div class="text-xs text-slate-500 mt-0.5">获赞</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { xhsApi } from '../services/xhs'

interface AccountInfo {
  nickname: string
  avatar: string
  followers: number
  total_notes: number
  total_likes: number
}

defineProps<{
  account: AccountInfo
}>()

const emit = defineEmits<{
  (e: 'refresh', data: any): void
}>()

// 本地刷新状态，完全由组件自己管理
const isRefreshing = ref(false)

// 处理刷新
const handleRefresh = async () => {
  if (isRefreshing.value) return
  
  isRefreshing.value = true
  console.log('[AccountCard] 开始刷新...')
  
  try {
    const res = await xhsApi.refreshStats()
    console.log('[AccountCard] 刷新响应:', res)
    if (res.code === 200 && res.data) {
      // 即使使用的是缓存数据或默认数据，也认为是成功
      emit('refresh', res.data)
    } else {
      // 只有真正的 API 错误才传递 null
      emit('refresh', null)
    }
  } catch (e) {
    console.error('[AccountCard] 刷新失败:', e)
    emit('refresh', null)
  } finally {
    isRefreshing.value = false
    console.log('[AccountCard] 刷新结束')
  }
}

// 格式化数字
const formatNumber = (num: number): string => {
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + 'w'
  }
  return num.toLocaleString()
}
</script>
