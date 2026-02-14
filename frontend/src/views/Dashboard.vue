<template>
  <div class="max-w-7xl mx-auto px-6">
    <!-- 页面头部 -->
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-slate-900">工作台</h1>
      <p class="text-slate-500 mt-1">{{ today }} · 管理你的内容创作与发布</p>
    </div>

    <!-- 主内容区：左右分栏 -->
    <div class="grid grid-cols-12 gap-6">
      <!-- 左侧：账号信息 + 统计 -->
      <div class="col-span-3 space-y-6">
        <!-- 账号信息卡片 -->
        <AccountCard 
          :account="accountData"
          @refresh="handleAccountRefresh"
        />

        <!-- 统计概览 -->
        <div class="bg-white rounded-xl border border-slate-200 p-4">
          <h3 class="text-sm font-medium text-slate-900 mb-4">数据统计</h3>
          <div class="space-y-4">
            <div v-for="stat in statItems" :key="stat.key" class="flex items-center justify-between">
              <div class="flex items-center gap-3">
                <div :class="[
                  'w-8 h-8 rounded-lg flex items-center justify-center',
                  stat.color === 'blue' ? 'bg-blue-100 text-blue-600' :
                  stat.color === 'amber' ? 'bg-amber-100 text-amber-600' :
                  'bg-emerald-100 text-emerald-600'
                ]">
                  <component :is="stat.icon" class="w-4 h-4" />
                </div>
                <span class="text-sm text-slate-600">{{ stat.label }}</span>
              </div>
              <span class="text-lg font-semibold text-slate-900">{{ stat.value }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧：内容列表 -->
      <div class="col-span-9">
        <!-- 筛选栏 -->
        <div class="bg-white rounded-xl border border-slate-200 p-4 mb-4">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <button
                v-for="filter in filters"
                :key="filter.key"
                @click="currentFilter = filter.key"
                :class="[
                  'px-4 py-1.5 rounded-lg text-sm font-medium transition-colors',
                  currentFilter === filter.key
                    ? 'bg-rose-100 text-rose-700'
                    : 'text-slate-600 hover:bg-slate-100'
                ]"
              >
                {{ filter.label }}
                <span 
                  v-if="getFilterCount(filter.key) > 0"
                  :class="[
                    'ml-1.5 px-1.5 py-0.5 rounded text-xs',
                    currentFilter === filter.key ? 'bg-rose-200 text-rose-800' : 'bg-slate-200 text-slate-600'
                  ]"
                >
                  {{ getFilterCount(filter.key) }}
                </span>
              </button>
            </div>

            <!-- 自动刷新指示器 -->
            <div v-if="hasCreatingContent" class="flex items-center gap-2 text-sm text-blue-600 mr-2">
              <ArrowPathIcon class="w-4 h-4 animate-spin" />
              <span>自动刷新中...</span>
            </div>
            
            <button 
              @click="handleCreate"
              :disabled="isCreating"
              class="flex items-center gap-1.5 px-3 py-1.5 bg-rose-600 text-white rounded-lg hover:bg-rose-700 disabled:opacity-50 transition-colors text-sm font-medium"
            >
              <PlusIcon v-if="!isCreating" class="w-4 h-4" />
              <ArrowPathIcon v-else class="w-4 h-4 animate-spin" />
              <span>{{ isCreating ? '创作中...' : '创作' }}</span>
            </button>
          </div>
        </div>

        <!-- 内容表格 -->
        <div class="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <!-- 表头 -->
          <div class="grid grid-cols-12 gap-4 px-6 py-3 bg-slate-50 border-b border-slate-200 text-sm font-medium text-slate-500">
            <div class="col-span-5">内容</div>
            <div class="col-span-2">状态</div>
            <div class="col-span-2">创建时间</div>
            <div class="col-span-3 text-right">操作</div>
          </div>

          <!-- 内容行 -->
          <div 
            v-for="content in filteredContents" 
            :key="content.id"
            @click="viewContent(content)"
            class="grid grid-cols-12 gap-4 px-6 py-4 border-b border-slate-100 hover:bg-slate-50 transition-colors cursor-pointer"
          >
            <!-- 内容信息 -->
            <div class="col-span-5">
              <div class="flex items-start gap-3">
                <!-- 配图缩略图 -->
                <div 
                  v-if="content.images && content.images.length > 0"
                  class="w-16 h-16 rounded-lg bg-slate-100 flex-shrink-0 overflow-hidden"
                >
                  <img 
                    :src="content.images[0].url || content.images[0]" 
                    class="w-full h-full object-cover"
                    alt="配图"
                  >
                </div>
                <div v-else class="w-16 h-16 rounded-lg bg-slate-100 flex items-center justify-center flex-shrink-0">
                  <PhotoIcon class="w-6 h-6 text-slate-300" />
                </div>

                <div class="flex-1 min-w-0">
                  <h4 class="text-sm font-medium text-slate-900 line-clamp-1" :title="content.titles?.[0]">
                    {{ content.titles?.[0] || '无标题' }}
                  </h4>
                  <p class="text-xs text-slate-500 mt-1 line-clamp-2">
                    {{ content.body || '暂无内容' }}
                  </p>
                  <div class="flex items-center gap-2 mt-2">
                    <span 
                      v-for="tag in (content.tags || []).slice(0, 3)" 
                      :key="tag"
                      class="text-xs text-slate-400"
                    >
                      #{{ tag }}
                    </span>
                    <span v-if="(content.tags || []).length > 3" class="text-xs text-slate-400">
                      +{{ content.tags.length - 3 }}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <!-- 状态 -->
            <div class="col-span-2 flex items-center">
              <span :class="[
                'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium',
                statusClasses[content.status]
              ]">
                <span :class="['w-1.5 h-1.5 rounded-full', statusDotClasses[content.status]]"></span>
                {{ statusLabels[content.status] || content.status }}
              </span>
            </div>

            <!-- 创建时间 -->
            <div class="col-span-2 flex items-center text-sm text-slate-500">
              {{ formatTime(content.created_at) }}
            </div>

            <!-- 操作按钮 -->
            <div class="col-span-3 flex items-center justify-end gap-2" @click.stop>
              <!-- 失败或创作中状态：显示删除按钮 -->
              <template v-if="content.status === 'failed' || content.status === 'CREATING'">
                <button 
                  v-if="content.status === 'failed'"
                  @click="handleDelete(content.id)"
                  class="px-3 py-1.5 text-sm text-red-600 hover:text-red-700 hover:bg-red-50 rounded-lg transition-colors"
                >
                  删除
                </button>
              </template>
              
              <!-- 待审核状态 -->
              <template v-if="content.status === 'reviewing'">
                <button 
                  @click="handleRegenerate(content.id)"
                  class="px-3 py-1.5 text-sm text-slate-600 hover:text-slate-700 hover:bg-slate-50 rounded-lg transition-colors"
                >
                  重新创作
                </button>
                <button 
                  @click="handleApprove(content.id)"
                  class="px-3 py-1.5 text-sm text-emerald-600 hover:text-emerald-700 hover:bg-emerald-50 rounded-lg transition-colors font-medium"
                >
                  通过
                </button>
              </template>
              
            </div>
          </div>

          <!-- 空状态 -->
          <div v-if="filteredContents.length === 0" class="py-16 text-center">
            <div class="w-16 h-16 mx-auto mb-4 rounded-full bg-slate-100 flex items-center justify-center">
              <InboxIcon class="w-8 h-8 text-slate-300" />
            </div>
            <p class="text-slate-500 mb-4">{{ currentFilter === 'all' ? '暂无内容，开始创作你的第一篇笔记吧' : '该状态下暂无内容' }}</p>
            <div v-if="currentFilter === 'all'" class="flex items-center justify-center gap-3">
              <button 
                @click="handleCreate"
                :disabled="isCreating"
                class="flex items-center gap-2 px-4 py-2 bg-rose-600 text-white rounded-lg text-sm font-medium hover:bg-rose-700 disabled:opacity-50 transition-colors"
              >
                <PlusIcon v-if="!isCreating" class="w-4 h-4" />
                <ArrowPathIcon v-else class="w-4 h-4 animate-spin" />
                {{ isCreating ? '创作中...' : '开始创作' }}
              </button>
              <router-link 
                to="/hotspots"
                class="flex items-center gap-2 px-4 py-2 border border-slate-300 text-slate-700 rounded-lg text-sm font-medium hover:bg-slate-50 transition-colors"
              >
                <FireIcon class="w-4 h-4" />
                浏览热点
              </router-link>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 详情弹窗 -->
    <ContentModal 
      v-if="showModal && selectedContent"
      :content="selectedContent"
      @close="showModal = false"
      @copy="copyContent"
      @approve="handleApprove"
      @regenerate="handleRegenerate"
      @publish="handlePublish"
    />

    <!-- 发布确认弹窗 -->
    <div v-if="showPublishModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div class="bg-white rounded-xl shadow-xl w-full max-w-md mx-4 p-6">
        <div class="flex items-center gap-3 mb-4">
          <div class="w-10 h-10 rounded-full bg-rose-100 flex items-center justify-center">
            <RocketLaunchIcon class="w-5 h-5 text-rose-600" />
          </div>
          <h3 class="text-lg font-semibold text-slate-900">确认发布</h3>
        </div>
        
        <p class="text-slate-600 mb-6">
          确定要将此内容发布到小红书吗？发布后内容将公开可见。
        </p>
        
        <div class="flex gap-3 justify-end">
          <button 
            @click="showPublishModal = false; publishTargetId = null"
            class="px-4 py-2 text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
          >
            取消
          </button>
          <button 
            @click="confirmPublish"
            :disabled="publishing"
            class="px-4 py-2 bg-rose-600 text-white rounded-lg hover:bg-rose-700 disabled:opacity-50 transition-colors flex items-center gap-2"
          >
            <ArrowPathIcon v-if="publishing" class="w-4 h-4 animate-spin" />
            {{ publishing ? '发布中...' : '确认发布' }}
          </button>
        </div>
      </div>
    </div>
    
    <!-- Toast -->
    <Toast :toast="toast" />
    
    <!-- 删除确认弹窗 -->
    <div v-if="showDeleteModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div class="bg-white rounded-xl shadow-xl w-full max-w-sm mx-4 p-6">
        <h3 class="text-lg font-semibold text-slate-900 mb-2">确认删除</h3>
        <p class="text-slate-600 mb-6">确定要删除这条失败的内容记录吗？删除后不可恢复。</p>
        <div class="flex gap-3 justify-end">
          <button 
            @click="showDeleteModal = false; deleteTargetId = null"
            class="px-4 py-2 text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
          >
            取消
          </button>
          <button 
            @click="confirmDelete"
            class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
          >
            删除
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onUnmounted } from 'vue'
import { useContents } from '../composables/useContents'
import { useWorkflow } from '../composables/useWorkflow'
import { useToast } from '../composables/useToast'
import { contentApi } from '../services/content'
import type { Content } from '../types'

// 图标
import {
  PlusIcon,
  ArrowPathIcon,
  FireIcon,
  PhotoIcon,
  InboxIcon,
  RocketLaunchIcon,
  DocumentTextIcon,
  ClockIcon,
  CheckCircleIcon,
  PaperAirplaneIcon
} from '@heroicons/vue/24/outline'

// 组件
import AccountCard from '../components/AccountCard.vue'
import ContentModal from '../components/ContentModal.vue'
import Toast from '../components/Toast.vue'

const { contents, stats, xhsStats, currentFilter, filteredContents, fetchData, refreshAll, approveContent, loading } = useContents()
const { start: startWorkflow } = useWorkflow(fetchData)

// 检查是否有正在创作中的内容
const hasCreatingContent = computed(() => 
  contents.value.some(c => c.status === 'CREATING')
)

// 本地创作状态（用于点击后的即时反馈）
const isCreatingLocal = ref(false)

// 综合判断：有正在创作的内容 或 本地正在创作
const isCreating = computed(() => hasCreatingContent.value || isCreatingLocal.value)
const { toast, show: showToast } = useToast()

const showModal = ref(false)
const selectedContent = ref<Content | null>(null)
const showPublishModal = ref(false)
const publishTargetId = ref<string | null>(null)
const publishing = ref(false)

// 删除确认弹窗状态
const showDeleteModal = ref(false)
const deleteTargetId = ref<string | null>(null)

const today = new Date().toLocaleDateString('zh-CN', { 
  month: 'long', day: 'numeric', weekday: 'long' 
})

const statItems = computed(() => [
  { key: 'total', label: '今日生成', value: stats.value.total, color: 'blue', icon: DocumentTextIcon },
  { key: 'creating', label: '创作中', value: stats.value.creating, color: 'blue', icon: ClockIcon },
  { key: 'reviewing', label: '待确认', value: stats.value.reviewing, color: 'amber', icon: CheckCircleIcon },
  { key: 'published', label: '累计发布', value: stats.value.published, color: 'emerald', icon: PaperAirplaneIcon },
])

const filters = [
  { key: 'all', label: '全部' },
  { key: 'CREATING', label: '创作中' },
  { key: 'reviewing', label: '待审核' },
  { key: 'approved', label: '已通过' },
  { key: 'published', label: '已发布' },
]

const statusClasses: Record<string, string> = {
  CREATING: 'bg-blue-100 text-blue-700',
  reviewing: 'bg-amber-100 text-amber-700',
  approved: 'bg-emerald-100 text-emerald-700',
  published: 'bg-purple-100 text-purple-700',
  rejected: 'bg-red-100 text-red-700',
  failed: 'bg-red-100 text-red-700',
  PUBLISH_FAILED: 'bg-red-100 text-red-700'
}

const statusDotClasses: Record<string, string> = {
  CREATING: 'bg-blue-500',
  reviewing: 'bg-amber-500',
  approved: 'bg-emerald-500',
  published: 'bg-purple-500',
  rejected: 'bg-red-500',
  failed: 'bg-red-500',
  PUBLISH_FAILED: 'bg-red-500'
}

const statusLabels: Record<string, string> = {
  CREATING: '创作中',
  reviewing: '待审核',
  approved: '已通过',
  published: '已发布',
  rejected: '已拒绝',
  failed: '失败',
  PUBLISH_FAILED: '发布失败'
}

const getFilterCount = (key: string) => {
  if (key === 'all') return contents.value.length
  return contents.value.filter(c => c.status === key).length
}

import { parseLocalTime } from '../utils/date'

const formatTime = (time: string) => {
  if (!time) return '-'
  const date = parseLocalTime(time)
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const viewContent = (content: Content) => {
  selectedContent.value = content
  showModal.value = true
}

const handleCreate = async () => {
  // 如果已经有正在创作的内容，提示用户
  if (hasCreatingContent.value) {
    showToast('已有内容正在创作中，请稍候...', 'info')
    return
  }
  
  isCreatingLocal.value = true
  const result = await startWorkflow()
  if (result.success) {
    showToast('创作任务已启动', 'success')
  } else {
    showToast(result.error || '创作失败', 'error')
    isCreatingLocal.value = false
  }
}

const handleApprove = async (id: string) => {
  const result = await approveContent(id)
  if (result.success) {
    // 检查是否自动发布成功
    const status = result.data?.status
    if (status === 'published') {
      showToast('✅ 审核通过并自动发布成功！', 'success')
    } else if (status === 'PUBLISH_FAILED') {
      showToast('⚠️ 审核通过，但自动发布失败', 'error')
    } else {
      showToast('✅ 审核通过，正在自动发布...', 'success')
    }
    await fetchData()
  } else {
    showToast(result.error || '操作失败', 'error')
  }
}

const handleRegenerate = async (id: string) => {
  // 调用重新创作 API
  try {
    const res = await contentApi.regenerate(id)
    if (res.code === 200) {
      showToast('已重新创作，请稍候...', 'success')
      await fetchData()
    } else {
      showToast(res.message || '重新创作失败', 'error')
    }
  } catch (e: any) {
    showToast(e.message || '重新创作失败', 'error')
  }
}

const handleDelete = (id: string) => {
  deleteTargetId.value = id
  showDeleteModal.value = true
}

const confirmDelete = async () => {
  if (!deleteTargetId.value) return
  
  try {
    const res = await contentApi.remove(deleteTargetId.value)
    if (res.code === 200) {
      showToast('已删除', 'success')
      await fetchData()
      showDeleteModal.value = false
      deleteTargetId.value = null
    } else {
      showToast(res.message || '删除失败', 'error')
    }
  } catch (e: any) {
    showToast(e.message || '删除失败', 'error')
  }
}

const handlePublish = async (id: string) => {
  publishTargetId.value = id
  showPublishModal.value = true
}

const confirmPublish = async () => {
  if (!publishTargetId.value) return
  
  publishing.value = true
  try {
    const res = await contentApi.autoPublish(publishTargetId.value)
    if (res.code === 200) {
      showToast('发布成功', 'success')
      await fetchData()
      showPublishModal.value = false
      publishTargetId.value = null
    } else {
      showToast(res.message || '发布失败', 'error')
    }
  } catch (e: any) {
    showToast(e.message || '发布失败', 'error')
  } finally {
    publishing.value = false
  }
}

const copyContent = (content: Content) => {
  const title = content.titles?.[0] || ''
  const text = `${title}\n\n${content.body}\n\n${content.tags?.map(t => '#' + t).join(' ') || ''}`
  navigator.clipboard.writeText(text).then(() => {
    showToast('内容已复制', 'success')
  })
}

const handleAccountRefresh = (data: any) => {
  console.log('[handleAccountRefresh] 收到数据:', data)
  if (!data) {
    showToast('刷新失败，请重试', 'error')
    return
  }
  
  // 检查是否是默认数据（昵称是 "小红书账号" 表示没有真实数据）
  const isDefaultData = data.nickname === '小红书账号' && !data.avatar
  
  // 只更新有效数据，避免覆盖为 null
  xhsStats.value = {
    ...xhsStats.value,
    ...data,
    nickname: data.nickname || xhsStats.value.nickname,
    avatar: data.avatar || xhsStats.value.avatar,
  }
  
  // 保存到 localStorage
  try {
    localStorage.setItem('xhs_stats_cache', JSON.stringify(xhsStats.value))
  } catch (e) {
    console.log('[handleAccountRefresh] 无法缓存数据')
  }
  
  console.log('[handleAccountRefresh] 更新后 xhsStats:', xhsStats.value)
  
  if (isDefaultData) {
    showToast('无法获取实时数据，已显示缓存数据', 'info')
  } else {
    showToast('账号数据已刷新', 'success')
  }
}

// 账号数据 computed
const accountData = computed(() => {
  const data = {
    nickname: xhsStats.value.nickname,
    avatar: xhsStats.value.avatar,
    followers: xhsStats.value.followers,
    total_notes: xhsStats.value.total_notes,
    total_likes: xhsStats.value.total_likes
  }
  console.log('[accountData] 计算:', data)
  return data
})

// 初始化
fetchData()

// 轮询：有创作中内容时更频繁刷新
let pollInterval: number | null = null
let normalInterval: number | null = null

// 高频轮询（创作中时）
const startHighFreqPoll = () => {
  if (pollInterval) clearInterval(pollInterval)
  pollInterval = window.setInterval(() => {
    console.log('[Dashboard] 高频轮询刷新...')
    fetchData()
  }, 3000) // 3秒刷新一次，更实时
}

const stopHighFreqPoll = () => {
  if (pollInterval) {
    clearInterval(pollInterval)
    pollInterval = null
  }
}

watch(hasCreatingContent, (hasCreating) => {
  if (hasCreating) {
    console.log('[Dashboard] 检测到创作中内容，开启高频轮询')
    startHighFreqPoll()
  } else {
    console.log('[Dashboard] 无创作中内容，停止高频轮询')
    stopHighFreqPoll()
  }
}, { immediate: true })

// 普通轮询（10秒，比之前30秒更频繁）
normalInterval = window.setInterval(() => {
  console.log('[Dashboard] 普通轮询刷新...')
  fetchData()
}, 10000)

// 组件卸载时清理
onUnmounted(() => {
  stopHighFreqPoll()
  if (normalInterval) clearInterval(normalInterval)
})
</script>
