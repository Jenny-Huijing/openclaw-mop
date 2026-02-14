// composables/useContents.ts
import { ref, computed, onMounted, watch } from 'vue'
import { contentApi } from '../services/content'
import { xhsApi } from '../services/xhs'
import type { Content, FilterType } from '../types'

export function useContents() {
  const contents = ref<Content[]>([])
  const loading = ref(false)
  const currentFilter = ref<FilterType>('all')
  // 尝试从 localStorage 恢复缓存数据
  const getCachedStats = () => {
    try {
      const cached = localStorage.getItem('xhs_stats_cache')
      if (cached) {
        const data = JSON.parse(cached)
        console.log('[useContents] 从 localStorage 恢复缓存:', data.nickname)
        return data
      }
    } catch (e) {
      console.log('[useContents] 无法读取缓存')
    }
    return {
      followers: 0,
      total_notes: 0,
      total_likes: 0,
      nickname: '',
      avatar: ''
    }
  }
  
  const xhsStats = ref(getCachedStats())

  const stats = computed(() => ({
    total: contents.value.length,
    creating: contents.value.filter(c => c.status === 'CREATING').length,
    reviewing: contents.value.filter(c => c.status === 'reviewing').length,
    approved: contents.value.filter(c => c.status === 'approved').length,
    published: contents.value.filter(c => c.status === 'published').length,
    followers: formatFollowers(xhsStats.value.followers),
    nickname: xhsStats.value.nickname,
    avatar: xhsStats.value.avatar,
    total_notes: xhsStats.value.total_notes,
    total_likes: xhsStats.value.total_likes
  }))

  // 格式化粉丝数
  const formatFollowers = (num: number): string => {
    if (num >= 10000) {
      return (num / 10000).toFixed(1) + 'w'
    }
    return num.toString()
  }

  // 账号数据加载状态
  const xhsLoading = ref(false)

  // 获取小红书账号数据
  const fetchXHSStats = async () => {
    if (xhsLoading.value) return // 防止重复请求
    xhsLoading.value = true
    try {
      console.log('[fetchXHSStats] 开始获取...')
      const res = await xhsApi.getStats()
      console.log('[fetchXHSStats] 响应:', res)
      if (res.code === 200 && res.data) {
        // 直接更新数据（后端会处理好缓存和mock）
        console.log('[fetchXHSStats] 更新数据:', res.data)
        const newStats = {
          ...xhsStats.value,
          ...res.data,
          nickname: res.data.nickname || xhsStats.value.nickname,
          avatar: res.data.avatar || xhsStats.value.avatar,
          followers: res.data.followers ?? xhsStats.value.followers,
          total_notes: res.data.total_notes ?? xhsStats.value.total_notes,
          total_likes: res.data.total_likes ?? xhsStats.value.total_likes,
        }
        xhsStats.value = newStats
        // 保存到 localStorage
        try {
          localStorage.setItem('xhs_stats_cache', JSON.stringify(newStats))
          console.log('[fetchXHSStats] 数据已缓存到 localStorage')
        } catch (e) {
          console.log('[fetchXHSStats] 无法缓存数据')
        }
        console.log('[fetchXHSStats] 更新后 xhsStats:', xhsStats.value)
      } else {
        console.log('[fetchXHSStats] 响应数据无效，保持现有数据')
      }
    } catch (e) {
      console.log('[fetchXHSStats] 获取失败:', e)
      // 获取失败时使用缓存
      const cached = getCachedStats()
      if (cached.nickname) {
        xhsStats.value = cached
      }
    } finally {
      xhsLoading.value = false
      console.log('[fetchXHSStats] loading 已重置')
    }
  }
  
  const filteredContents = computed(() => {
    if (currentFilter.value === 'all') return contents.value
    return contents.value.filter(c => c.status === currentFilter.value)
  })
  
  const fetchData = async () => {
    loading.value = true
    try {
      // 先快速获取本地内容数据
      const contentRes = await contentApi.getList()
      if (contentRes.code === 200) {
        console.log('[fetchData] 获取到内容:', contentRes.data.items.length)
        contents.value = contentRes.data.items
      }
      loading.value = false
      
      // 账号数据单独获取（可能很慢，不阻塞内容显示）
      fetchXHSStats()
    } catch (e) {
      console.error(e)
      loading.value = false
    }
  }
  
  // 调试：监听 contents 变化
  watch(contents, (newVal) => {
    console.log('[contents changed]', newVal.length, currentFilter.value, filteredContents.value.length)
  })
  
  // 刷新所有数据（内容 + 账号）
  const refreshAll = async () => {
    loading.value = true
    try {
      await Promise.all([
        fetchData(),
        fetchXHSStats()
      ])
    } catch (e) {
      console.error(e)
    } finally {
      loading.value = false
    }
  }

  // 初始化时获取数据（保留缓存，API失败时显示缓存数据）
  onMounted(() => {
    fetchXHSStats()
  })
  
  const approveContent = async (id: string) => {
    try {
      const res = await contentApi.approve(id)
      await fetchData()
      return { success: true, data: res.data }
    } catch (e: any) {
      return { success: false, error: e.message || '操作失败' }
    }
  }
  
  return {
    contents,
    loading,
    xhsLoading,
    stats,
    xhsStats,
    currentFilter,
    filteredContents,
    fetchData,
    refreshAll,
    approveContent
  }
}
