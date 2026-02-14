<template>
  <div class="flex items-center justify-between mb-6">
    <div class="flex items-center gap-2">
      <svg class="w-5 h-5 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
      </svg>
      <h2 class="font-semibold text-slate-900">内容列表</h2>
    </div>
    
    <div class="flex items-center gap-3">
      <div class="flex gap-1 bg-slate-100 p-1 rounded-lg">
        <button v-for="filter in filters" :key="filter.key"
                @click="$emit('filter', filter.key)"
                :class="current === filter.key ? 'bg-white text-blue-700 shadow-sm' : 'text-slate-600 hover:text-slate-900'"
                class="px-3 py-1.5 text-sm rounded-md transition-all">
          {{ filter.label }}
        </button>
      </div>
      
      <button 
        @click="$emit('create')"
        :disabled="isCreating"
        class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-80 disabled:cursor-not-allowed flex items-center gap-2 transition-colors"
      >
        <svg v-if="isCreating" class="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
        <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        <span>{{ isCreating ? 'AI生成中...' : '开始创作' }}</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { FilterType } from '../types'

defineProps<{
  filters: { key: FilterType; label: string }[]
  current: FilterType
  isCreating: boolean
}>()

defineEmits<{
  filter: [key: FilterType]
  create: []
}>()
</script>
