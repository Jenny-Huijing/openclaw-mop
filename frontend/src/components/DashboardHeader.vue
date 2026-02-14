<template>
  <div class="flex items-center justify-between mb-6">
    <div class="flex items-center gap-4">
      <div class="w-12 h-12 bg-gradient-to-br from-rose-500 to-pink-600 rounded-2xl flex items-center justify-center shadow-lg">
        <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.362 5.214A8.252 8.252 0 0112 21 8.25 8.25 0 016.038 7.048 8.287 8.287 0 009 9.6a8.983 8.983 0 013.361-6.867 8.21 8.21 0 003 2.48z" />
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 18a3.75 3.75 0 00.495-7.467 5.99 5.99 0 00-1.925 3.546 5.974 5.974 0 01-2.133-1A3.75 3.75 0 0012 18z" />
        </svg>
      </div>
      <div>
        <h1 class="text-2xl font-bold text-slate-900">工作汇报</h1>
        <p class="text-sm text-slate-500 mt-1">
          {{ today }} · 为你完成了 <span class="font-semibold text-rose-600">{{ total }}</span> 项创作
        </p>
      </div>
    </div>
    
    <!-- 下次创作时间 -->
    <div class="flex items-center gap-2 px-4 py-2 bg-slate-100 rounded-full text-sm text-slate-600">
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <span>下次创作：明天 08:00</span>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  today: string
  total: number
}>()
</script>
