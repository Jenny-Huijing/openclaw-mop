<template>
  <div class="flex items-start">
    <!-- 节点 -->
    <div class="flex flex-col items-center">
      <div 
        @click="$emit('click')"
        :class="[
          'relative flex flex-col items-center p-4 rounded-xl border-2 cursor-pointer transition-all hover:shadow-lg',
          'w-36 bg-white',
          colorClasses[props.node.color]
        ]"
      >
        <!-- 图标 -->
        <div :class="[
          'w-12 h-12 rounded-xl flex items-center justify-center text-2xl mb-2',
          iconBgClasses[props.node.color]
        ]">
          {{ props.node.icon }}
        </div>
        
        <!-- 名称 -->
        <div class="text-sm font-medium text-slate-900 text-center leading-tight">
          {{ props.node.name }}
        </div>
        
        <!-- 状态指示器 -->
        <div :class="[
          'absolute -top-1 -right-1 w-4 h-4 rounded-full border-2 border-white',
          statusIndicatorClass
        ]"></div>
      </div>
      
      <!-- 中文简介 -->
      <p class="mt-2 text-xs text-slate-500 text-center w-36 leading-relaxed h-12 overflow-hidden line-clamp-3">
        {{ props.node.description }}
      </p>
    </div>
    
    <!-- 箭头 -->
    <div v-if="!props.isLast" class="flex items-center px-2 pt-8">
      <svg class="w-6 h-6 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
      </svg>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Node {
  id: string
  name: string
  icon: string
  color: string
  description: string
}

const props = defineProps<{
  node: Node
  isLast?: boolean
}>()

defineEmits(['click'])

const colorClasses: Record<string, string> = {
  blue: 'border-blue-200 hover:border-blue-300',
  amber: 'border-amber-200 hover:border-amber-300',
  purple: 'border-purple-200 hover:border-purple-300',
  emerald: 'border-emerald-200 hover:border-emerald-300',
  rose: 'border-rose-200 hover:border-rose-300'
}

const iconBgClasses: Record<string, string> = {
  blue: 'bg-blue-100',
  amber: 'bg-amber-100',
  purple: 'bg-purple-100',
  emerald: 'bg-emerald-100',
  rose: 'bg-rose-100'
}

// 默认显示运行中状态
const statusIndicatorClass = 'bg-emerald-500'
</script>
