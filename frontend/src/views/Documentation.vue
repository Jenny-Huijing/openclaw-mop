<template>
  <div class="py-8">
    <div class="max-w-5xl mx-auto px-6">
      <!-- 页面标题 -->
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-slate-900">系统文档</h1>
        <p class="text-slate-500 mt-2">新媒体智能运营平台架构设计与技术文档</p>
      </div>

      <!-- 文档导航 -->
      <div class="bg-white rounded-xl border border-slate-200 shadow-sm mb-8">
        <div class="p-6 border-b border-slate-200">
          <h2 class="text-lg font-semibold text-slate-900">目录</h2>
        </div>
        <div class="p-6">
          <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
            <a 
              v-for="section in sections" 
              :key="section.id"
              :href="`#${section.id}`"
              class="flex items-center gap-3 p-3 rounded-lg hover:bg-slate-50 transition-colors"
            >
              <div :class="['w-10 h-10 rounded-lg flex items-center justify-center', section.iconBg]">
                <component :is="section.icon" class="w-5 h-5" :class="section.iconColor" />
              </div>
              <span class="text-sm font-medium text-slate-700">{{ section.title }}</span>
            </a>
          </div>
        </div>
      </div>

      <!-- 系统概述 -->
      <section id="overview" class="bg-white rounded-xl border border-slate-200 shadow-sm mb-8 scroll-mt-24">
        <div class="p-6 border-b border-slate-200">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
              <RocketLaunchIcon class="w-5 h-5 text-blue-600" />
            </div>
            <h2 class="text-xl font-semibold text-slate-900">系统概述</h2>
          </div>
        </div>
        <div class="p-6 prose prose-slate max-w-none">
          <p class="text-slate-600 leading-relaxed">
            新媒体智能运营平台是一个基于 <strong>LangGraph</strong> 和 <strong>AI Agent</strong> 技术的自动化内容创作与发布系统。
            平台整合了热点发现、内容创作、合规审核、人工审核、自动发布等全流程功能，帮助运营团队高效产出优质内容。
          </p>
          
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
            <div class="p-4 bg-slate-50 rounded-lg">
              <div class="text-2xl font-bold text-blue-600">5</div>
              <div class="text-sm text-slate-600">AI Agent 协同工作</div>
            </div>
            <div class="p-4 bg-slate-50 rounded-lg">
              <div class="text-2xl font-bold text-emerald-600">自动化</div>
              <div class="text-sm text-slate-600">从热点到发布</div>
            </div>
            <div class="p-4 bg-slate-50 rounded-lg">
              <div class="text-2xl font-bold text-purple-600">小红书</div>
              <div class="text-sm text-slate-600">MCP 协议对接</div>
            </div>
          </div>
        </div>
      </section>

      <!-- 系统架构 -->
      <section id="architecture" class="bg-white rounded-xl border border-slate-200 shadow-sm mb-8 scroll-mt-24">
        <div class="p-6 border-b border-slate-200">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
              <Squares2X2Icon class="w-5 h-5 text-purple-600" />
            </div>
            <h2 class="text-xl font-semibold text-slate-900">系统架构</h2>
          </div>
        </div>
        <div class="p-6">
          <!-- 架构图 -->
          <div class="bg-slate-50 rounded-lg p-8 mb-6">
            <div class="flex flex-col items-center gap-4">
              <!-- 用户层 -->
              <div class="w-full max-w-md">
                <div class="text-center text-sm font-medium text-slate-500 mb-2">用户层</div>
                <div class="flex justify-center gap-4">
                  <div class="px-4 py-2 bg-white rounded-lg border border-slate-200 text-sm">Web UI</div>
                  <div class="px-4 py-2 bg-white rounded-lg border border-slate-200 text-sm">飞书 Bot</div>
                </div>
              </div>
              
              <!-- 箭头 -->
              <div class="h-8 w-px bg-slate-300"></div>
              
              <!-- API 网关层 -->
              <div class="w-full max-w-md">
                <div class="text-center text-sm font-medium text-slate-500 mb-2">网关层</div>
                <div class="flex justify-center">
                  <div class="px-6 py-2 bg-emerald-50 rounded-lg border border-emerald-200 text-sm font-medium text-emerald-700">Nginx</div>
                </div>
              </div>
              
              <!-- 箭头 -->
              <div class="h-8 w-px bg-slate-300"></div>
              
              <!-- 应用层 -->
              <div class="w-full max-w-2xl">
                <div class="text-center text-sm font-medium text-slate-500 mb-2">应用层 (FastAPI)</div>                
                <div class="grid grid-cols-3 gap-3">
                  <div class="px-3 py-2 bg-blue-50 rounded-lg border border-blue-200 text-center">
                    <div class="text-xs font-medium text-blue-700">API 服务</div>
                  </div>
                  <div class="px-3 py-2 bg-amber-50 rounded-lg border border-amber-200 text-center">
                    <div class="text-xs font-medium text-amber-700">Celery Worker</div>
                  </div>
                  <div class="px-3 py-2 bg-purple-50 rounded-lg border border-purple-200 text-center">
                    <div class="text-xs font-medium text-purple-700">调度器</div>
                  </div>
                </div>
              </div>
              
              <!-- 箭头 -->
              <div class="h-8 w-px bg-slate-300"></div>
              
              <!-- LangGraph Agent -->
              <div class="w-full max-w-3xl">
                <div class="text-center text-sm font-medium text-slate-500 mb-2">LangGraph Agent 工作流</div>                
                <div class="flex justify-center items-center gap-2">
                  <div v-for="(agent, i) in agents" :key="agent.name" class="flex items-center">
                    <div class="px-3 py-2 bg-white rounded-lg border-2 text-center min-w-[80px]"
                         :class="agent.borderColor">
                      <div class="text-lg">{{ agent.icon }}</div>
                      <div class="text-xs font-medium text-slate-700">{{ agent.name }}</div>
                    </div>
                    <div v-if="i < agents.length - 1" class="px-1">
                      <svg class="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
                      </svg>
                    </div>
                  </div>
                </div>
              </div>
              
              <!-- 箭头 -->
              <div class="h-8 w-px bg-slate-300"></div>
              
              <!-- 数据层 -->
              <div class="w-full max-w-2xl">
                <div class="text-center text-sm font-medium text-slate-500 mb-2">数据层</div>                
                <div class="flex justify-center gap-4">
                  <div class="px-4 py-2 bg-white rounded-lg border border-slate-200 text-sm">PostgreSQL</div>
                  <div class="px-4 py-2 bg-white rounded-lg border border-slate-200 text-sm">Redis</div>
                  <div class="px-4 py-2 bg-white rounded-lg border border-slate-200 text-sm">RabbitMQ</div>
                </div>
              </div>
              
              <!-- 箭头 -->
              <div class="h-8 w-px bg-slate-300"></div>
              
              <!-- 外部服务 -->
              <div class="w-full max-w-2xl">
                <div class="text-center text-sm font-medium text-slate-500 mb-2">外部服务</div>                
                <div class="flex justify-center gap-3 flex-wrap">
                  <div class="px-3 py-1.5 bg-rose-50 rounded border border-rose-200 text-xs text-rose-700">小红书 MCP</div>
                  <div class="px-3 py-1.5 bg-blue-50 rounded border border-blue-200 text-xs text-blue-700">方舟大模型</div>
                  <div class="px-3 py-1.5 bg-purple-50 rounded border border-purple-200 text-xs text-purple-700">即梦图像</div>
                  <div class="px-3 py-1.5 bg-orange-50 rounded border border-orange-200 text-xs text-orange-700">Brave Search</div>
                  <div class="px-3 py-1.5 bg-emerald-50 rounded border border-emerald-200 text-xs text-emerald-700">飞书</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Agent 工作流 -->
      <section id="agents" class="bg-white rounded-xl border border-slate-200 shadow-sm mb-8 scroll-mt-24">
        <div class="p-6 border-b border-slate-200">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 bg-amber-100 rounded-lg flex items-center justify-center">
              <BeakerIcon class="w-5 h-5 text-amber-600" />
            </div>
            <h2 class="text-xl font-semibold text-slate-900">Agent 工作流</h2>
          </div>
        </div>
        <div class="p-6">
          <div class="space-y-6">
            <div v-for="agent in agentDetails" :key="agent.name" class="flex gap-4">
              <div class="w-12 h-12 rounded-xl flex items-center justify-center text-2xl shrink-0"
                   :class="agent.bgClass">
                {{ agent.icon }}
              </div>
              <div class="flex-1">
                <div class="flex items-center gap-3 mb-1">
                  <h3 class="font-semibold text-slate-900">{{ agent.name }}</h3>
                  <span class="px-2 py-0.5 rounded text-xs font-medium"
                        :class="agent.tagClass">{{ agent.tag }}</span>
                </div>                
                <p class="text-sm text-slate-600 mb-2">{{ agent.description }}</p>
                
                <div class="flex flex-wrap gap-2">
                  <span v-for="tech in agent.techs" :key="tech" 
                        class="px-2 py-1 bg-slate-100 text-slate-600 rounded text-xs">
                    {{ tech }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- 技术栈 -->
      <section id="tech-stack" class="bg-white rounded-xl border border-slate-200 shadow-sm mb-8 scroll-mt-24">
        <div class="p-6 border-b border-slate-200">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 bg-emerald-100 rounded-lg flex items-center justify-center">
              <CodeBracketIcon class="w-5 h-5 text-emerald-600" />
            </div>
            <h2 class="text-xl font-semibold text-slate-900">技术栈</h2>
          </div>
        </div>
        <div class="p-6">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div v-for="category in techStack" :key="category.name">
              <h3 class="font-medium text-slate-900 mb-3">{{ category.name }}</h3>
              <div class="space-y-2">
                <div v-for="item in category.items" :key="item.name" 
                     class="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                  <span class="text-sm text-slate-700">{{ item.name }}</span>
                  <span class="text-xs text-slate-500">{{ item.version }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- 核心功能 -->
      <section id="features" class="bg-white rounded-xl border border-slate-200 shadow-sm mb-8 scroll-mt-24">
        <div class="p-6 border-b border-slate-200">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 bg-rose-100 rounded-lg flex items-center justify-center">
              <SparklesIcon class="w-5 h-5 text-rose-600" />
            </div>
            <h2 class="text-xl font-semibold text-slate-900">核心功能</h2>
          </div>
        </div>
        <div class="p-6">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div v-for="feature in features" :key="feature.title" class="p-4 border border-slate-200 rounded-lg">
              <div class="flex items-center gap-3 mb-2">
                <component :is="feature.icon" class="w-5 h-5 text-slate-600" />
                <h3 class="font-medium text-slate-900">{{ feature.title }}</h3>
              </div>
              <p class="text-sm text-slate-600">{{ feature.description }}</p>
            </div>
          </div>
        </div>
      </section>

      <!-- 部署说明 -->
      <section id="deployment" class="bg-white rounded-xl border border-slate-200 shadow-sm mb-8 scroll-mt-24">
        <div class="p-6 border-b border-slate-200">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 bg-cyan-100 rounded-lg flex items-center justify-center">
              <ServerIcon class="w-5 h-5 text-cyan-600" />
            </div>
            <h2 class="text-xl font-semibold text-slate-900">部署说明</h2>
          </div>
        </div>
        <div class="p-6">
          <div class="space-y-6">
            <div>
              <h3 class="font-medium text-slate-900 mb-2">Docker Compose 部署</h3>              
              <pre class="bg-slate-900 text-slate-100 p-4 rounded-lg overflow-x-auto text-sm"><code># 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f api

# 重启服务
docker-compose restart api</code></pre>
            </div>
            
            <div>
              <h3 class="font-medium text-slate-900 mb-2">服务清单</h3>              
              <div class="overflow-x-auto">
                <table class="min-w-full text-sm">
                  <thead class="bg-slate-50">
                    <tr>
                      <th class="px-4 py-2 text-left font-medium text-slate-700">服务</th>
                      <th class="px-4 py-2 text-left font-medium text-slate-700">容器名</th>
                      <th class="px-4 py-2 text-left font-medium text-slate-700">端口</th>
                      <th class="px-4 py-2 text-left font-medium text-slate-700">说明</th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-slate-200">
                    <tr v-for="svc in services" :key="svc.name">
                      <td class="px-4 py-2 font-medium text-slate-900">{{ svc.name }}</td>
                      <td class="px-4 py-2 text-slate-600">{{ svc.container }}</td>
                      <td class="px-4 py-2 text-slate-600">{{ svc.port }}</td>
                      <td class="px-4 py-2 text-slate-600">{{ svc.desc }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  RocketLaunchIcon,
  Squares2X2Icon,
  BeakerIcon,
  CodeBracketIcon,
  SparklesIcon,
  ServerIcon,
  FireIcon,
  DocumentTextIcon,
  ShieldCheckIcon,
  UserIcon,
  CloudArrowUpIcon,
  BookOpenIcon
} from '@heroicons/vue/24/outline'

const sections = [
  { id: 'overview', title: '系统概述', icon: RocketLaunchIcon, iconBg: 'bg-blue-100', iconColor: 'text-blue-600' },
  { id: 'architecture', title: '系统架构', icon: Squares2X2Icon, iconBg: 'bg-purple-100', iconColor: 'text-purple-600' },
  { id: 'agents', title: 'Agent 工作流', icon: BeakerIcon, iconBg: 'bg-amber-100', iconColor: 'text-amber-600' },
  { id: 'tech-stack', title: '技术栈', icon: CodeBracketIcon, iconBg: 'bg-emerald-100', iconColor: 'text-emerald-600' },
  { id: 'features', title: '核心功能', icon: SparklesIcon, iconBg: 'bg-rose-100', iconColor: 'text-rose-600' },
  { id: 'deployment', title: '部署说明', icon: ServerIcon, iconBg: 'bg-cyan-100', iconColor: 'text-cyan-600' },
]

const agents = [
  { name: 'Research', icon: '🔍', borderColor: 'border-blue-300' },
  { name: 'Creator', icon: '✨', borderColor: 'border-purple-300' },
  { name: 'Compliance', icon: '🛡️', borderColor: 'border-amber-300' },
  { name: 'Review', icon: '👤', borderColor: 'border-emerald-300' },
  { name: 'Publisher', icon: '📤', borderColor: 'border-rose-300' },
]

const agentDetails = [
  {
    name: 'Research Agent',
    icon: '🔍',
    tag: '热点发现',
    tagClass: 'bg-blue-100 text-blue-700',
    bgClass: 'bg-blue-100',
    description: '通过 Brave Search API 实时搜索热点话题，支持多源聚合和智能去重，为内容创作提供选题灵感。',
    techs: ['Brave Search API', '多源聚合', '智能去重', '实时搜索']
  },
  {
    name: 'Creator Agent',
    icon: '✨',
    tag: '内容创作',
    tagClass: 'bg-purple-100 text-purple-700',
    bgClass: 'bg-purple-100',
    description: '基于方舟大模型生成高质量文案，调用即梦图像服务生成配图，自动推荐标签和话题。',
    techs: ['方舟大模型', '即梦图像', '提示词工程', 'AIGC']
  },
  {
    name: 'Compliance Agent',
    icon: '🛡️',
    tag: '合规检查',
    tagClass: 'bg-amber-100 text-amber-700',
    bgClass: 'bg-amber-100',
    description: '对内容和选题进行合规性检查，包括敏感词检测、风险评级，确保内容符合平台规范。',
    techs: ['关键词过滤', 'LLM 审核', '风险评级', '修改建议']
  },
  {
    name: 'Human Review',
    icon: '👤',
    tag: '人工审核',
    tagClass: 'bg-emerald-100 text-emerald-700',
    bgClass: 'bg-emerald-100',
    description: '人工审核节点，支持 Web UI 和飞书 Bot 两种审核方式，运营人员可对内容进行最终把关。',
    techs: ['Web UI', '飞书 Bot', '实时通知', '决策流转']
  },
  {
    name: 'Publisher Agent',
    icon: '📤',
    tag: '发布管理',
    tagClass: 'bg-rose-100 text-rose-700',
    bgClass: 'bg-rose-100',
    description: '通过 MCP 协议与小红书平台对接，支持自动发布、定时发布和数据记录。',
    techs: ['MCP 协议', '小红书 API', '定时发布', '数据同步']
  }
]

const techStack = [
  {
    name: '后端',
    items: [
      { name: 'FastAPI', version: '0.104+' },
      { name: 'SQLAlchemy', version: '2.0+' },
      { name: 'Celery', version: '5.3+' },
      { name: 'LangGraph', version: '0.0.40+' },
    ]
  },
  {
    name: '前端',
    items: [
      { name: 'Vue 3', version: '3.3+' },
      { name: 'Tailwind CSS', version: '3.4+' },
      { name: 'Arco Design', version: '2.55+' },
      { name: 'Heroicons', version: '2.1+' },
    ]
  },
  {
    name: '数据库',
    items: [
      { name: 'PostgreSQL', version: '15+' },
      { name: 'Redis', version: '7+' },
      { name: 'RabbitMQ', version: '3+' },
    ]
  },
  {
    name: 'AI 服务',
    items: [
      { name: '方舟大模型', version: 'Doubao' },
      { name: '即梦图像', version: 'Seedream' },
      { name: 'OpenAI', version: 'GPT-4' },
      { name: 'Kimi', version: 'Moonshot' },
    ]
  }
]

const features = [
  {
    title: '热点发现',
    icon: FireIcon,
    description: '实时监控全网热点，智能分类和去重，支持财经、科技、生活、社会等多个领域的趋势追踪。'
  },
  {
    title: 'AI 创作',
    icon: SparklesIcon,
    description: '基于大模型的自动文案生成，支持标题、正文、标签、配图全流程自动化创作。'
  },
  {
    title: '合规审核',
    icon: ShieldCheckIcon,
    description: '自动敏感词检测和风险评级，确保内容符合各平台规范，降低违规风险。'
  },
  {
    title: '人工审核',
    icon: UserIcon,
    description: '支持 Web 界面和飞书 Bot 双端审核，一键通过、重新创作或取消。'
  },
  {
    title: '自动发布',
    icon: CloudArrowUpIcon,
    description: '通过 MCP 协议自动发布到小红书，支持图文混排、标签添加、话题关联。'
  },
  {
    title: '工作流编排',
    icon: DocumentTextIcon,
    description: '基于 LangGraph 的可视化工作流，支持节点监控、执行记录、错误追踪。'
  }
]

const services = [
  { name: 'Nginx', container: 'xhs_nginx', port: '80', desc: '网关和静态资源' },
  { name: 'API', container: 'xhs_api', port: '8000', desc: 'FastAPI 主服务' },
  { name: 'Worker', container: 'xhs_worker', port: '-', desc: 'Celery 任务处理' },
  { name: 'Scheduler', container: 'xhs_scheduler', port: '-', desc: '定时任务调度' },
  { name: 'PostgreSQL', container: 'xhs_postgres', port: '5432', desc: '主数据库' },
  { name: 'Redis', container: 'xhs_redis', port: '6379', desc: '缓存和消息队列' },
  { name: 'RabbitMQ', container: 'xhs_rabbitmq', port: '5672', desc: '消息中间件' },
]
</script>

<style scoped>
.scroll-mt-24 {
  scroll-margin-top: 6rem;
}
</style>
