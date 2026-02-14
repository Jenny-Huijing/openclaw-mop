<template>
  <n-card class="quick-actions-card" :bordered="false" :title="title">
    <n-space vertical class="actions">
      <n-button
        v-for="action in actions"
        :key="action.key"
        :type="action.type || 'default'"
        size="large"
        block
        round
        @click="handleAction(action)"
      >
        <template #icon>
          <component :is="action.icon" />
        </template>
        {{ action.label }}
      </n-button>
    </n-space>

    <n-divider v-if="$slots.tips" />

    <slot name="tips">
      <div v-if="tip" class="tip-card">
        <n-space align="start">
          <bulb-outline class="tip-icon" />
          <div>
            <div class="tip-title">小提示</div>
            <div class="tip-content">{{ tip }}</div>
          </div>
        </n-space>
      </div>
    </slot>
  </n-card>
</template>

<script setup lang="ts">
import { BulbOutline } from '@vicons/ionicons5'
import type { Component } from 'vue'
import { useRouter } from 'vue-router'

interface Action {
  key: string
  label: string
  icon: Component
  type?: 'primary' | 'default'
  route?: string
}

interface Props {
  title?: string
  actions: Action[]
  tip?: string
}

withDefaults(defineProps<Props>(), {
  title: '快捷操作',
  tip: '',
})

const emit = defineEmits(['action'])
const router = useRouter()

const handleAction = (action: Action) => {
  if (action.route) {
    router.push(action.route)
  }
  emit('action', action)
}
</script>

<style scoped>
.quick-actions-card {
  border-radius: 20px;
  min-height: 400px;
}

.actions {
  width: 100%;
}

.actions :deep(.n-button) {
  height: 48px;
  font-size: 15px;
  font-weight: 600;
}

.tip-card {
  background: linear-gradient(135deg, #F3E8FF, #EDE9FE);
  border-radius: 16px;
  padding: 16px;
  margin-top: 8px;
}

.tip-icon {
  font-size: 24px;
  color: #7C3AED;
}

.tip-title {
  font-weight: 600;
  color: #4C1D95;
  margin-bottom: 4px;
}

.tip-content {
  font-size: 13px;
  color: #6B21A8;
  line-height: 1.5;
}
</style>
