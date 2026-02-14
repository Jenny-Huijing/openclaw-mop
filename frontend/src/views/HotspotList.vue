<template>
  <div class="min-h-screen bg-slate-50">
    <!-- 页面头部 -->
    <div class="max-w-7xl mx-auto px-6 py-6">
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-2xl font-bold text-slate-900">热点发现</h1>
          <p class="text-slate-500 text-sm mt-1">AI实时追踪全网热点，智能推荐创作方向</p>
        </div>
        <div class="flex items-center gap-3">
          <span class="text-sm text-slate-500">最后更新: {{ lastUpdate }}</span>
          <button 
            @click="fetchHotspots"
            :disabled="loading"
            class="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            <ArrowPathIcon :class="['w-4 h-4', loading ? 'animate-spin' : '']" />
            刷新热点
          </button>
        </div>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="max-w-7xl mx-auto px-6 py-6">
      <div class="grid grid-cols-4 md:grid-cols-7 gap-3">
        <div 
          v-for="stat in categoryStats" 
          :key="stat.key"
          @click="currentCategory = stat.key"
          :class="[
            'p-3 rounded-xl border-2 cursor-pointer transition-all',
            currentCategory === stat.key 
              ? 'border-blue-500 bg-blue-50' 
              : 'border-transparent bg-white hover:border-slate-200'
          ]"
        >
          <div class="flex items-center gap-2">
            <div :class="['w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0', stat.bgColor]">
              <component :is="stat.icon" class="w-4 h-4" :class="stat.iconColor" />
            </div>
            <div class="min-w-0">
              <p class="text-lg font-bold text-slate-900">{{ stat.count }}</p>
              <p class="text-xs text-slate-500 truncate">{{ stat.name }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 热点列表 -->
    <div class="max-w-7xl mx-auto px-6 pb-12">
      <!-- 筛选和排序 -->
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center gap-2">
          <button
            v-for="filter in filters"
            :key="filter.key"
            @click="currentFilter = filter.key"
            :class="[
              'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
              currentFilter === filter.key
                ? 'bg-slate-900 text-white'
                : 'bg-white text-slate-600 hover:bg-slate-100'
            ]"
          >
            {{ filter.label }}
          </button>
        </div>
        <div class="flex items-center gap-2 text-sm text-slate-500">
          <span>排序:</span>
          <select v-model="sortBy" class="px-3 py-1.5 bg-white border border-slate-200 rounded-lg">
            <option value="heat">按热度</option>
            <option value="time">按时间</option>
          </select>
        </div>
      </div>

      <!-- 列表内容 -->
      <div v-if="filteredHotspots.length > 0" class="space-y-4">
        <div 
          v-for="hotspot in filteredHotspots" 
          :key="hotspot.id"
          class="bg-white rounded-xl border border-slate-200 p-6 hover:shadow-lg transition-shadow cursor-pointer"
          @click="openDetail(hotspot)"
        >
          <div class="flex items-start gap-6">
            <!-- 左侧热度 -->
            <div class="flex-shrink-0 text-center">
              <div class="w-16 h-16 rounded-full bg-gradient-to-br from-rose-500 to-orange-500 flex items-center justify-center">
                <span class="text-white font-bold text-lg">{{ hotspot.heat_score }}</span>
              </div>
              <p class="text-xs text-slate-500 mt-2">热度分</p>
            </div>

            <!-- 中间内容 -->
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-3 mb-2">
                <span :class="['px-2 py-1 rounded-full text-xs font-medium', getCategoryStyle(hotspot.category)]">
                  {{ getCategoryName(hotspot.category) }}
                </span>
                <span class="text-xs text-slate-400">{{ formatTime(hotspot.discovered_at) }}</span>
                <span v-if="hotspot.trend === 'rising'" class="flex items-center gap-1 text-xs text-rose-600">
                  <ArrowTrendingUpIcon class="w-3 h-3" />
                  热度上升
                </span>
              </div>
              
              <h3 class="text-lg font-semibold text-slate-900 mb-2 line-clamp-1">{{ hotspot.title }}</h3>
              <p class="text-slate-600 text-sm line-clamp-2 mb-4">{{ hotspot.summary || '暂无摘要' }}</p>

              <!-- 关键词 -->
              <div class="flex items-center gap-2">
                <span 
                  v-for="keyword in (hotspot.keywords || []).slice(0, 5)" 
                  :key="keyword"
                  class="px-2 py-1 bg-slate-100 text-slate-600 text-xs rounded"
                >
                  {{ keyword }}
                </span>
              </div>
            </div>

            <!-- 右侧操作 -->
            <div class="flex-shrink-0 flex flex-col gap-2">
              <button 
                @click.stop="adoptHotspot(hotspot)"
                class="flex items-center gap-1 px-4 py-2 bg-rose-600 text-white text-sm rounded-lg hover:bg-rose-700 transition-colors"
              >
                <PlusIcon class="w-4 h-4" />
                采纳创作
              </button>
              <button 
                @click.stop="openDetail(hotspot)"
                class="px-4 py-2 text-slate-600 text-sm border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors"
              >
                查看详情
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-else class="py-16 text-center bg-white rounded-xl border border-slate-200">
        <div class="w-20 h-20 mx-auto mb-4 rounded-full bg-slate-100 flex items-center justify-center">
          <InboxIcon class="w-10 h-10 text-slate-300" />
        </div>
        <p class="text-slate-500 mb-2">暂无热点数据</p>
        <p class="text-slate-400 text-sm mb-4">点击刷新获取最新热点</p>
        <button 
          @click="fetchHotspots"
          class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          立即获取
        </button>
      </div>
    </div>

    <!-- 详情弹窗 -->
    <TransitionRoot appear :show="showDetailModal" as="template">
      <Dialog as="div" @close="closeDetail" class="relative z-50">
        <TransitionChild
          enter="ease-out duration-300"
          enter-from="opacity-0"
          enter-to="opacity-100"
          leave="ease-in duration-200"
          leave-from="opacity-100"
          leave-to="opacity-0"
        >
          <div class="fixed inset-0 bg-black/30 backdrop-blur-sm" />
        </TransitionChild>

        <div class="fixed inset-0 overflow-y-auto">
          <div class="flex min-h-full items-center justify-center p-4">
            <TransitionChild
              enter="ease-out duration-300"
              enter-from="opacity-0 scale-95"
              enter-to="opacity-100 scale-100"
              leave="ease-in duration-200"
              leave-from="opacity-100 scale-100"
              leave-to="opacity-0 scale-95"
            >
              <DialogPanel v-if="selectedHotspot" class="w-full max-w-2xl bg-white rounded-2xl shadow-xl">
                <!-- 弹窗头部 -->
                <div class="p-6 border-b border-slate-100">
                  <div class="flex items-start justify-between">
                    <div>
                      <div class="flex items-center gap-2 mb-3">
                        <span :class="['px-2 py-1 rounded-full text-xs font-medium', getCategoryStyle(selectedHotspot.category)]">
                          {{ getCategoryName(selectedHotspot.category) }}
                        </span>
                        <span class="flex items-center gap-1 text-sm text-rose-600">
                          <FireIcon class="w-4 h-4" />
                          热度 {{ selectedHotspot.heat_score }}分
                        </span>
                      </div>
                      <DialogTitle class="text-xl font-bold text-slate-900">
                        {{ selectedHotspot.title }}
                      </DialogTitle>
                    </div>
                    <button @click="closeDetail" class="p-2 text-slate-400 hover:text-slate-600">
                      <XMarkIcon class="w-5 h-5" />
                    </button>
                  </div>
                </div>

                <!-- 弹窗内容 -->
                <div class="p-6">
                  <!-- 热度趋势图 -->
                  <div class="mb-6">
                    <h4 class="text-sm font-medium text-slate-700 mb-3">热度趋势</h4>
                    <div class="h-32 bg-slate-50 rounded-lg flex items-end gap-1 p-4">
                      <div 
                        v-for="(trend, idx) in trendData" 
                        :key="idx"
                        class="flex-1 bg-rose-500 rounded-t transition-all"
                        :style="{ height: trend + '%' }"
                      />
                    </div>
                  </div>

                  <!-- 摘要 -->
                  <div class="mb-6">
                    <h4 class="text-sm font-medium text-slate-700 mb-3">热点摘要</h4>
                    <p class="text-slate-600 leading-relaxed">{{ selectedHotspot.summary || '暂无摘要' }}</p>
                  </div>

                  <!-- 创作角度 -->
                  <div class="mb-6 p-4 bg-blue-50 rounded-xl">
                    <h4 class="text-sm font-medium text-blue-900 mb-2 flex items-center gap-2">
                      <LightBulbIcon class="w-4 h-4" />
                      AI推荐的创作角度
                    </h4>
                    <ul class="space-y-2">
                      <li 
                        v-for="(angle, idx) in angles" 
                        :key="idx"
                        class="text-blue-700 text-sm flex items-start gap-2"
                      >
                        <span class="w-5 h-5 rounded-full bg-blue-200 text-blue-700 text-xs flex items-center justify-center flex-shrink-0">{{ idx + 1 }}</span>
                        {{ angle }}
                      </li>
                    </ul>
                  </div>

                  <!-- 关键词 -->
                  <div>
                    <h4 class="text-sm font-medium text-slate-700 mb-3">相关关键词</h4>
                    <div class="flex flex-wrap gap-2">
                      <span 
                        v-for="keyword in (selectedHotspot.keywords || [])" 
                        :key="keyword"
                        class="px-3 py-1.5 bg-slate-100 text-slate-600 text-sm rounded-lg"
                      >
                        {{ keyword }}
                      </span>
                    </div>
                  </div>
                </div>

                <!-- 弹窗底部 -->
                <div class="p-6 border-t border-slate-100 flex items-center justify-between">
                  <a 
                    v-if="selectedHotspot.source_url"
                    :href="selectedHotspot.source_url"
                    target="_blank"
                    class="text-blue-600 hover:text-blue-700 text-sm flex items-center gap-1"
                  >
                    查看原文
                    <ArrowTopRightOnSquareIcon class="w-4 h-4" />
                  </a>
                  <div v-else />
                  <button 
                    @click="adoptHotspot(selectedHotspot); closeDetail()"
                    class="flex items-center gap-2 px-6 py-2.5 bg-rose-600 text-white rounded-lg hover:bg-rose-700 transition-colors"
                  >
                    <PlusIcon class="w-5 h-5" />
                    采纳此热点创作
                  </button>
                </div>
              </DialogPanel>
            </TransitionChild>
          </div>
        </div>
      </Dialog>
    </TransitionRoot>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { 
  ArrowPathIcon, 
  PlusIcon, 
  InboxIcon, 
  FireIcon,
  ArrowTrendingUpIcon,
  XMarkIcon,
  ArrowTopRightOnSquareIcon,
  LightBulbIcon,
  NewspaperIcon,
  ChartBarIcon,
  SparklesIcon,
  HeartIcon,
  MusicalNoteIcon,
  TagIcon
} from '@heroicons/vue/24/outline'
import { Dialog, DialogPanel, DialogTitle, TransitionChild, TransitionRoot } from '@headlessui/vue'
import { ElMessage } from 'element-plus'
import { hotspotApi } from '../services/hotspot'
import { contentApi } from '../services/content'

// 状态
const hotspots = ref([])
const loading = ref(false)
const currentCategory = ref('all')
const currentFilter = ref('all')
const sortBy = ref('heat')
const showDetailModal = ref(false)
const selectedHotspot = ref(null)
const lastUpdate = ref('刚刚')

// 分类统计
const categoryStats = computed(() => [
  { key: 'all', name: '全部热点', count: hotspots.value.length, icon: NewspaperIcon, bgColor: 'bg-slate-100', iconColor: 'text-slate-600' },
  { key: 'finance', name: '财经', count: hotspots.value.filter(h => h.category === 'finance').length, icon: ChartBarIcon, bgColor: 'bg-emerald-100', iconColor: 'text-emerald-600' },
  { key: 'tech', name: '科技', count: hotspots.value.filter(h => h.category === 'tech').length, icon: SparklesIcon, bgColor: 'bg-blue-100', iconColor: 'text-blue-600' },
  { key: 'lifestyle', name: '生活', count: hotspots.value.filter(h => h.category === 'lifestyle').length, icon: HeartIcon, bgColor: 'bg-rose-100', iconColor: 'text-rose-600' },
  { key: 'social', name: '社会', count: hotspots.value.filter(h => h.category === 'social').length, icon: FireIcon, bgColor: 'bg-orange-100', iconColor: 'text-orange-600' },
  { key: 'entertainment', name: '娱乐', count: hotspots.value.filter(h => h.category === 'entertainment').length, icon: MusicalNoteIcon, bgColor: 'bg-purple-100', iconColor: 'text-purple-600' },
  { key: 'other', name: '其他', count: hotspots.value.filter(h => h.category === 'other').length, icon: TagIcon, bgColor: 'bg-gray-100', iconColor: 'text-gray-600' },
])

// 筛选选项
const filters = [
  { key: 'all', label: '全部' },
  { key: 'rising', label: '热度上升' },
  { key: 'high', label: '高热度(>80)' },
]

// 筛选后的热点
const filteredHotspots = computed(() => {
  let result = hotspots.value
  
  // 分类筛选
  if (currentCategory.value !== 'all') {
    result = result.filter(h => h.category === currentCategory.value)
  }
  
  // 其他筛选
  if (currentFilter.value === 'rising') {
    result = result.filter(h => h.trend === 'rising')
  } else if (currentFilter.value === 'high') {
    result = result.filter(h => h.heat_score > 80)
  }
  
  // 排序
  if (sortBy.value === 'heat') {
    result = [...result].sort((a, b) => (b.heat_score || 0) - (a.heat_score || 0))
  } else {
    result = [...result].sort((a, b) => new Date(b.discovered_at) - new Date(a.discovered_at))
  }
  
  return result
})

// 热度趋势模拟数据
const trendData = computed(() => {
  if (!selectedHotspot.value) return []
  const base = selectedHotspot.value.heat_score || 50
  return Array.from({ length: 12 }, () => Math.max(20, Math.min(100, base + (Math.random() - 0.5) * 30)))
})

// 创作角度
const angles = computed(() => {
  const categoryAngles = {
    finance: [
      '从理财角度分析这对普通人的影响',
      '解读政策背后的投资机会',
      '分享3个应对策略，帮你守住钱袋子',
    ],
    tech: [
      '这项技术如何改变我们的生活',
      '普通人如何抓住这次技术红利',
      '深度解析：这背后的商业逻辑',
    ],
    lifestyle: [
      '亲测分享：我的真实体验',
      '避坑指南：这些细节要注意',
      '教你3招，轻松上手',
    ],
    social: [
      '从民生角度解读这个热点',
      '这可能是你关心的话题',
      '政策解读：对我们有什么影响',
    ],
  }
  return categoryAngles[selectedHotspot.value?.category] || [
    '这个热点值得关注',
    '分析背后的深层原因',
    '分享你的观点和看法',
  ]
})

// 获取热点列表
const fetchHotspots = async () => {
  loading.value = true
  try {
    const res = await hotspotApi.getList(50)
    if (res.code === 200) {
      hotspots.value = res.data.items || []
      const now = new Date()
lastUpdate.value = now.toLocaleString('zh-CN', { hour: '2-digit', minute: '2-digit' })
    }
  } catch (error) {
    console.error('获取热点失败:', error)
  } finally {
    loading.value = false
  }
}

// 采纳热点创作
const adoptHotspot = async (hotspot: any) => {
  try {
    const res = await contentApi.startWorkflow()
    if (res.code === 200) {
      ElMessage.success('已基于此热点创建创作任务')
    }
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

// 打开详情
const openDetail = (hotspot: any) => {
  selectedHotspot.value = hotspot
  showDetailModal.value = true
}

// 关闭详情
const closeDetail = () => {
  showDetailModal.value = false
  selectedHotspot.value = null
}

// 获取分类名称
const getCategoryName = (category: string) => {
  const names: Record<string, string> = {
    finance: '财经',
    tech: '科技',
    lifestyle: '生活',
    social: '社会',
    entertainment: '娱乐',
    other: '其他',
  }
  return names[category] || '其他'
}

// 获取分类样式
const getCategoryStyle = (category: string) => {
  const styles: Record<string, string> = {
    finance: 'bg-emerald-100 text-emerald-700',
    tech: 'bg-blue-100 text-blue-700',
    lifestyle: 'bg-rose-100 text-rose-700',
    social: 'bg-orange-100 text-orange-700',
    entertainment: 'bg-purple-100 text-purple-700',
    other: 'bg-slate-100 text-slate-600',
  }
  return styles[category] || 'bg-slate-100 text-slate-600'
}

// 格式化时间
import { parseLocalTime } from '../utils/date'

const formatTime = (time: string) => {
  if (!time) return ''
  const date = parseLocalTime(time)
  const now = new Date()
  const diff = (now.getTime() - date.getTime()) / 1000
  
  if (diff < 60) return '刚刚'
  if (diff < 3600) return `${Math.floor(diff / 60)}分钟前`
  if (diff < 86400) return `${Math.floor(diff / 3600)}小时前`
  return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

onMounted(() => {
  fetchHotspots()
})
</script>
