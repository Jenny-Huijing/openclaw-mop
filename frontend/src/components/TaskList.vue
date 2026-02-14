<template>
  <n-card class="task-list-card" :bordered="false" :title="title">
    <template #header-extra>
      <slot name="header-extra">
        <n-button quaternary size="small" @click="emit('refresh')">
          <refresh-outline /> 刷新
        </n-button>
      </slot>
    </template>

    <n-list v-if="tasks.length > 0" hoverable clickable
>
      <n-list-item
        v-for="task in tasks"
        :key="task.id"
        @click="handleClick(task)"
      >
        <n-thing
          :title="task.title"
          :description="formatTime(task.created_at)"
        >
          <template #avatar>
            <n-avatar
              :style="{ background: getStatusColor(task.status) }"
              size="medium"
            >
              {{ task.title?.[0] || '?' }}
            </n-avatar>
          </template>
          <template #header-extra>
            <n-space size="small">
              <n-tag
                :type="getStatusType(task.status)"
                size="small"
                round
              >
                {{ statusText(task.status) }}
              </n-tag>
              <n-tag
                v-if="task.priority"
                :type="getPriorityType(task.priority)"
                size="small"
                round
              >
                {{ task.priority }}
              </n-tag>
            </n-space>
          </template>
        </n-thing>
      </n-list-item>
    </n-list>

    <n-empty
      v-else
      :description="emptyText"
      class="task-list-empty"
    >
      <template #icon>
        <calendar-clear-outline />
      </template>
      <template #extra>
        <slot name="empty-action">
          <n-button type="primary" @click="emit('create')">
            创建任务
          </n-button>
        </slot>
      </template>
    </n-empty>
  </n-card>
</template>

<script setup lang="ts">
import { RefreshOutline, CalendarClearOutline } from '@vicons/ionicons5'
import type { Task } from '../types'

interface Props {
  title?: string
  tasks: Task[]
  emptyText?: string
}

const props = withDefaults(defineProps<Props>(), {
  title: '任务列表',
  emptyText: '暂无任务',
})

const emit = defineEmits(['click', 'refresh', 'create'])

const handleClick = (task: Task) => {
  emit('click', task)
}

const getStatusType = (status?: string) => {
  const map: Record<string, any> = {
    pending: 'warning',
    doing: 'info',
    review: 'primary',
    ready: 'success',
    published: 'default',
  }
  return map[status || ''] || 'default'
}

const getStatusColor = (status?: string) => {
  const map: Record<string, string> = {
    pending: '#F59E0B',
    doing: '#3B82F6',
    review: '#7C3AED',
    ready: '#10B981',
    published: '#6B7280',
  }
  return map[status || ''] || '#6B7280'
}

const getPriorityType = (priority?: string) => {
  const map: Record<string, any> = {
    high: 'error',
    medium: 'warning',
    low: 'default',
  }
  return map[priority || ''] || 'default'
}

const statusText = (status?: string) => {
  const map: Record<string, string> = {
    pending: '待处理',
    doing: '进行中',
    review: '待审核',
    ready: '待发布',
    published: '已发布',
  }
  return map[status || ''] || status || '未知'
}

import { formatLocalTime } from '../utils/date'

const formatTime = (time?: string) => {
  if (!time) return ''
  return formatLocalTime(time)
}
</script>

<style scoped>
.task-list-card {
  border-radius: 20px;
  min-height: 400px;
}

.task-list-empty {
  padding: 60px 0;
}
</style>
