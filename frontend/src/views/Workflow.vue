<template>
  <div class="py-8">
    <div class="max-w-6xl mx-auto px-6">
      <!-- 页面标题 -->
      <div class="mb-8">
        <h1 class="text-2xl font-bold text-slate-900">工作流可视化</h1>
        <p class="text-slate-500 mt-1">LangGraph Agent 工作流编排与监控</p>
      </div>

      <!-- 工作流架构图 Tab -->
      <div class="bg-white rounded-xl border border-slate-200 shadow-sm p-6 mb-6">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-semibold text-slate-900">工作流架构</h2>
          <div class="flex items-center gap-2">
            <!-- Tab 切换按钮 -->
            <div class="flex bg-slate-100 rounded-lg p-1">
              <button
                @click="activeGraphTab = 'custom'"
                :class="[
                  'px-3 py-1.5 rounded-md text-sm font-medium transition-all',
                  activeGraphTab === 'custom'
                    ? 'bg-white text-slate-900 shadow-sm'
                    : 'text-slate-500 hover:text-slate-700'
                ]"
              >
                架构图
              </button>
              <button
                @click="activeGraphTab = 'mermaid'"
                :class="[
                  'px-3 py-1.5 rounded-md text-sm font-medium transition-all',
                  activeGraphTab === 'mermaid'
                    ? 'bg-white text-slate-900 shadow-sm'
                    : 'text-slate-500 hover:text-slate-700'
                ]"
              >
                LangGraph
              </button>
            </div>
            <span class="px-3 py-1 bg-emerald-100 text-emerald-700 rounded-full text-sm font-medium">
              运行中
            </span>
          </div>
        </div>
        
        <!-- 自定义架构图 -->
        <div v-if="activeGraphTab === 'custom'" class="relative bg-slate-50 rounded-lg p-8 overflow-x-auto">
          <div class="min-w-[800px]">
            <!-- 节点和连线 -->
            <div class="flex items-center justify-between">
              <WorkflowNode
                v-for="(node, index) in workflowNodes"
                :key="node.id"
                :node="node"
                :is-last="index === workflowNodes.length - 1"
                @click="selectedNode = node"
              />
            </div>
          </div>
        </div>
        
        <!-- LangGraph Mermaid 图 -->
        <div v-else class="relative bg-slate-50 rounded-lg p-4 overflow-x-auto">
          <div ref="mermaidContainer" class="mermaid flex justify-center">
            {{ mermaidCode || '加载中...' }}
          </div>
        </div>
      </div>

      <!-- 节点详情 -->
      <div v-if="selectedNode" class="bg-white rounded-xl border border-slate-200 shadow-sm p-6 mb-6">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-semibold text-slate-900">{{ selectedNode.name }}</h2>
          <button 
            @click="selectedNode = null"
            class="text-slate-400 hover:text-slate-600"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>
        
        <div class="grid grid-cols-2 gap-6">
          <div>
            <h3 class="text-sm font-medium text-slate-500 mb-2">职责</h3>
            <ul class="space-y-1">
              <li 
                v-for="duty in selectedNode.duties" 
                :key="duty"
                class="text-sm text-slate-700 flex items-center gap-2"
              >
                <span class="w-1.5 h-1.5 bg-blue-500 rounded-full"></span>
                {{ duty }}
              </li>
            </ul>
          </div>
          <div>
            <h3 class="text-sm font-medium text-slate-500 mb-2">技术栈</h3>
            <div class="flex flex-wrap gap-2">
              <span 
                v-for="tech in selectedNode.techs" 
                :key="tech"
                class="px-2 py-1 bg-slate-100 text-slate-600 rounded text-xs"
              >
                {{ tech }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- 运行中的工作流 -->
      <div class="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-semibold text-slate-900">最近工作流执行记录</h2>
          <button 
            @click="fetchWorkflowLogs"
            class="text-blue-600 hover:text-blue-700 text-sm font-medium"
          >
            刷新
          </button>
        </div>
        
        <div class="space-y-3">
          <div 
            v-for="log in workflowLogs" 
            :key="log.id"
            class="flex items-center gap-4 p-4 bg-slate-50 rounded-lg hover:bg-slate-100 transition-colors"
          >
            <div :class="[
              'w-10 h-10 rounded-lg flex items-center justify-center',
              statusColors[log.status]
            ]">
              <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path v-if="log.status === 'completed'" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                <path v-else-if="log.status === 'running'" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
              </svg>
            </div>
            <div class="flex-1">
              <div class="flex items-center gap-2">
                <span class="font-medium text-slate-900">{{ log.workflow_id }}</span>
                <span :class="[
                  'px-2 py-0.5 rounded text-xs',
                  statusBgColors[log.status]
                ]">
                  {{ statusLabels[log.status] }}
                </span>
              </div>
              <div class="text-sm text-slate-500 mt-0.5">
                {{ log.agent_name }} · {{ log.action }} · {{ formatTime(log.created_at) }}
              </div>
            </div>
            <div class="text-right">
              <div class="text-sm font-medium text-slate-700">{{ log.duration_ms }}ms</div>
            </div>
          </div>
          
          <EmptyState v-if="workflowLogs.length === 0" message="暂无工作流记录" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import EmptyState from '../components/EmptyState.vue'
import WorkflowNode from '../components/WorkflowNode.vue'
import { workflowApi } from '../services/workflow'

const selectedNode = ref(null)
const workflowLogs = ref([])
const mermaidCode = ref('')
const mermaidContainer = ref<HTMLElement | null>(null)
const activeGraphTab = ref('custom') // 'custom' | 'mermaid'

// 动态加载 mermaid
const loadMermaid = () => {
  return new Promise<void>((resolve, reject) => {
    if ((window as any).mermaid) {
      resolve()
      return
    }
    const script = document.createElement('script')
    script.src = 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js'
    script.onload = () => {
      ;(window as any).mermaid.initialize({ 
        startOnLoad: false,
        theme: 'default',
        flowchart: {
          useMaxWidth: true,
          htmlLabels: true,
          curve: 'basis'
        }
      })
      resolve()
    }
    script.onerror = reject
    document.head.appendChild(script)
  })
}

const renderMermaid = async () => {
  await loadMermaid()
  const mermaid = (window as any).mermaid
  
  if (mermaidContainer.value && mermaidCode.value) {
    try {
      // 清除之前的内容
      mermaidContainer.value.innerHTML = mermaidCode.value
      // 渲染
      await mermaid.run({
        nodes: [mermaidContainer.value]
      })
    } catch (e) {
      console.error('Mermaid 渲染失败:', e)
    }
  }
}

const fetchMermaidGraph = async () => {
  try {
    const res = await workflowApi.getGraph()
    if (res.code === 200 && res.data?.mermaid) {
      mermaidCode.value = res.data.mermaid
      await nextTick()
      await renderMermaid()
    }
  } catch (e) {
    console.error('获取 Mermaid 图失败:', e)
  }
}

const workflowNodes = ref([
  {
    id: 'research',
    name: 'Research Agent',
    icon: '🔍',
    color: 'blue',
    description: '热点发现、实时搜索、分类整理',
    duties: ['热点发现', '实时搜索', '分类整理'],
    techs: ['Brave Search API', '多源聚合', '智能去重']
  },
  {
    id: 'creator',
    name: 'Creator Agent',
    icon: '✨',
    color: 'purple',
    bgColor: 'bg-purple-100',
    description: '文案生成、配图创作、标签推荐',
    duties: ['文案生成', '配图创作', '标签推荐'],
    techs: ['方舟大模型', '即梦图像', '提示词工程']
  },
  {
    id: 'compliance',
    name: 'Compliance Agent',
    icon: '🛡️',
    color: 'amber',
    bgColor: 'bg-amber-100',
    description: '合规检查、敏感词检测、风险评级',
    duties: ['合规检查', '敏感词检测', '风险评级'],
    techs: ['关键词过滤', 'LLM 审核', '修改建议']
  },
  {
    id: 'review',
    name: 'Human Review',
    icon: '👤',
    color: 'emerald',
    description: '人工审核、决策判断、修改意见',
    duties: ['人工审核', '决策判断', '修改意见'],
    techs: ['Web UI', '飞书 Bot', '实时通知']
  },
  {
    id: 'publisher',
    name: 'Publisher Agent',
    icon: '📤',
    color: 'rose',
    description: '生成发布包、数据记录、状态更新',
    duties: ['生成发布包', '数据记录', '状态更新'],
    techs: ['MCP 协议', '小红书 API', '定时发布']
  }
])

const statusColors = {
  completed: 'bg-emerald-500',
  running: 'bg-blue-500',
  failed: 'bg-red-500',
  pending: 'bg-slate-400'
}

const statusBgColors = {
  completed: 'bg-emerald-100 text-emerald-700',
  running: 'bg-blue-100 text-blue-700',
  failed: 'bg-red-100 text-red-700',
  pending: 'bg-slate-100 text-slate-600'
}

const statusLabels = {
  completed: '已完成',
  running: '运行中',
  failed: '失败',
  pending: '等待中'
}

const formatTime = (time: string) => {
  if (!time) return '--:--'
  try {
    // 手动解析无时区时间戳
    const cleanTs = time.split('.')[0]
    if (cleanTs.includes('T')) {
      const [datePart, timePart] = cleanTs.split('T')
      const [year, month, day] = datePart.split('-').map(Number)
      const [hour, minute, second = 0] = timePart.split(':').map(Number)
      const date = new Date(year, month - 1, day, hour, minute, second)
      if (isNaN(date.getTime())) return '--:--'
      return date.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
    }
    return new Date(time).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
  } catch (e) {
    return '--:--'
  }
}

// 监听 Tab 切换，切换到 mermaid 时重新渲染
watch(activeGraphTab, async (newTab) => {
  if (newTab === 'mermaid' && mermaidCode.value) {
    await nextTick()
    await renderMermaid()
  }
})

const fetchWorkflowLogs = async () => {
  try {
    const res = await workflowApi.getLogs()
    if (res.code === 200) {
      workflowLogs.value = res.data.items || []
    }
  } catch (e) {
    console.error('获取工作流日志失败:', e)
  }
}

// 自动刷新
let refreshInterval: number | null = null

const startAutoRefresh = () => {
  refreshInterval = window.setInterval(() => {
    fetchWorkflowLogs()
  }, 5000) // 每5秒刷新
}

const stopAutoRefresh = () => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
    refreshInterval = null
  }
}

onMounted(() => {
  fetchWorkflowLogs()
  fetchMermaidGraph()
  startAutoRefresh()
})

onUnmounted(() => {
  stopAutoRefresh()
})
</script>
