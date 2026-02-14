<template>
  <div class="bg-white rounded-xl p-5 border border-slate-200 shadow-sm">
    <div class="flex items-center gap-2 mb-3">
      <div :class="`w-8 h-8 bg-${color}-100 rounded-lg flex items-center justify-center`">
        <slot name="icon">
          <svg class="w-4 h-4" :class="`text-${color}-600`" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </slot>
      </div>
      <span class="text-sm font-medium text-slate-500">{{ label }}</span>
      <span v-if="badge" class="ml-auto text-xs px-2 py-0.5 bg-amber-100 text-amber-700 rounded">{{ badge }}</span>
    </div>
    <div :class="`text-3xl font-bold text-${color}-600`">{{ value }}</div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  label: string
  value: string | number
  color: 'blue' | 'amber' | 'emerald' | 'violet'
  badge?: string
}>()
</script>
