<template>
  <div class="min-h-screen bg-slate-50">
    <!-- 顶部导航栏 -->
    <nav class="sticky top-0 z-50 bg-white border-b border-slate-200 shadow-sm">
      <div class="max-w-7xl mx-auto px-6">
        <div class="flex items-center justify-between h-16">
          <!-- Logo -->
          <router-link to="/" class="flex items-center gap-3">
            <div class="w-10 h-10 bg-gradient-to-br from-rose-500 to-pink-600 rounded-xl flex items-center justify-center shadow-lg shadow-rose-500/20">
              <SparklesIcon class="h-6 w-6 text-white" />
            </div>
            <span class="font-semibold text-slate-900 text-lg">新媒体智能运营平台</span>
          </router-link>

          <!-- 主导航菜单 -->
          <div class="flex items-center gap-1">
            <router-link 
              v-for="item in mainNavItems" 
              :key="item.path"
              :to="item.path"
              :class="[
                'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors',
                $route.path === item.path
                  ? 'text-rose-600 bg-rose-50' 
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              ]"
            >
              <component :is="item.icon" class="w-4 h-4" />
              {{ item.label }}
            </router-link>
          </div>

          <!-- 右侧用户菜单 -->
          <div class="flex items-center gap-2">
            <div class="w-8 h-8 bg-gradient-to-br from-blue-600 to-blue-500 rounded-full flex items-center justify-center">
              <UserIcon class="h-4 w-4 text-white" />
            </div>
            <span class="text-sm font-medium text-slate-700">女王大人</span>
          </div>
        </div>
      </div>
    </nav>

    <!-- 路由内容 -->
    <main class="py-6">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'
import { computed } from 'vue'
import { 
  SparklesIcon,
  UserIcon,
  HomeIcon,
  FireIcon,
  BeakerIcon,
  DocumentTextIcon,
  BookOpenIcon,
  ClockIcon
} from '@heroicons/vue/24/solid'

const $route = useRoute()

// 主导航菜单
const mainNavItems = [
  { 
    path: '/', 
    label: '工作台', 
    icon: HomeIcon
  },
  { 
    path: '/hotspots', 
    label: '热点发现', 
    icon: FireIcon 
  },
  { 
    path: '/workflow', 
    label: '工作流', 
    icon: BeakerIcon 
  },
  { 
    path: '/scheduler', 
    label: '定时任务', 
    icon: ClockIcon 
  },
  { 
    path: '/logs', 
    label: '系统日志', 
    icon: DocumentTextIcon 
  },
  { 
    path: '/docs', 
    label: '文档', 
    icon: BookOpenIcon 
  },
]
</script>
