<template>
  <div class="task-board">
    <a-page-header title="任务看板" subtitle="拖拽管理任务状态" @back="$router.push('/')">
      <template #extra>
        <a-space>
          <a-button type="primary" @click="showCreateModal = true">
            <icon-plus /> 新建任务
          </a-button>
          <a-button @click="fetchTasks">
            <icon-refresh /> 刷新
          </a-button>
        </a-space>
      </template>
    </a-page-header>

    <!-- 看板 -->
    <a-row :gutter="16" class="board">
      <a-col v-for="col in columns" :key="col.status" :span="6">
        <div class="board-column">
          <div class="column-header" :style="{ background: col.color }">
            <div class="column-title">
              <icon-drag-dot-vertical v-if="col.icon" />
              <span>{{ col.title }}</span>
            </div>
            <a-badge :count="col.tasks.length" :offset="[-10, 0]">
              <span class="column-count">{{ col.tasks.length }}</span>
            </a-badge>
          </div>

          <div class="column-body">
            <a-card
              v-for="task in col.tasks"
              :key="task.id"
              class="task-card"
              :bordered="false"
              hoverable
              @click="viewTask(task)"
            >
              <div class="task-header">
                <a-tag :color="getPriorityColor(task.priority)" size="small">{{ task.priority }}</a-tag>
                <span class="task-time">{{ formatTime(task.created_at) }}</span>
              </div>

              <div class="task-title">{{ task.title }}</div>

              <div v-if="task.topic" class="task-topic">
                <a-tag color="gray" size="small">{{ task.topic }}</a-tag>
              </div>

              <div class="task-footer">
                <a-space>
                  <a-button
                    v-if="task.status === 'review'"
                    type="primary"
                    size="mini"
                    @click.stop="approveTask(task)"
                  >
                    通过
                  </a-button>
                  <a-button
                    v-if="task.status === 'review'"
                    size="mini"
                    status="danger"
                    @click.stop="rejectTask(task)"
                  >
                    拒绝
                  </a-button>
                </a-space>
              </div>
            </a-card>
          </div>
        </div>
      </a-col>
    </a-row>

    <!-- 新建任务弹窗 -->
    <a-modal
      v-model:visible="showCreateModal"
      title="新建任务"
      @ok="createTask"
      @cancel="showCreateModal = false"
    >
      <a-form :model="newTask" layout="vertical">
        <a-form-item field="title" label="任务标题" required>
          <a-input v-model="newTask.title" placeholder="请输入任务标题" />
        </a-form-item>
        
        <a-form-item field="topic" label="主题分类">
          <a-select v-model="newTask.topic" placeholder="请选择主题">
            <a-option>银行存款</a-option>
            <a-option>国债逆回购</a-option>
            <a-option>基金定投</a-option>
            <a-option>LPR利率</a-option>
          </a-select>
        </a-form-item>
        
        <a-form-item field="priority" label="优先级">
          <a-radio-group v-model="newTask.priority" type="button">
            <a-radio value="low">低</a-radio>
            <a-radio value="medium">中</a-radio>
            <a-radio value="high">高</a-radio>
          </a-radio-group>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { Message } from '@arco-design/web-vue'
import {
  IconPlus,
  IconRefresh,
  IconDragDotVertical
} from '@arco-design/web-vue/es/icon'

const router = useRouter()
const tasks = ref([])
const loading = ref(false)
const showCreateModal = ref(false)

const newTask = ref({
  title: '',
  topic: '',
  priority: 'medium',
  type: 'content_creation'
})

const columns = computed(() => [
  {
    status: 'pending',
    title: '待处理',
    color: '#ff9a2e',
    icon: true,
    tasks: tasks.value.filter(t => t.status === 'pending')
  },
  {
    status: 'doing',
    title: '进行中',
    color: '#14a9f8',
    icon: true,
    tasks: tasks.value.filter(t => t.status === 'doing')
  },
  {
    status: 'review',
    title: '待审核',
    color: '#165dff',
    icon: true,
    tasks: tasks.value.filter(t => t.status === 'review')
  },
  {
    status: 'ready',
    title: '待发布',
    color: '#00b42a',
    icon: true,
    tasks: tasks.value.filter(t => t.status === 'ready')
  }
])

const fetchTasks = async () => {
  loading.value = true
  try {
    const res = await fetch('/api/v1/tasks?limit=100')
    const data = await res.json()
    if (data.code === 200) {
      tasks.value = data.data.items || []
    }
  } catch (error) {
    console.error('获取任务失败:', error)
  } finally {
    loading.value = false
  }
}

const createTask = async () => {
  try {
    const res = await fetch('/api/v1/tasks', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newTask.value)
    })
    const data = await res.json()
    if (data.code === 200) {
      Message.success('任务创建成功')
      showCreateModal.value = false
      fetchTasks()
    }
  } catch (error) {
    Message.error('创建失败')
  }
}

const viewTask = (task: any) => {
  router.push(`/contents?task_id=${task.id}`)
}

const approveTask = async (task: any) => {
  // 调用审核API
  Message.success('审核通过')
  fetchTasks()
}

const rejectTask = async (task: any) => {
  Message.success('已拒绝')
  fetchTasks()
}

const getPriorityColor = (priority: string) => {
  const map: Record<string, string> = {
    high: 'red',
    medium: 'orange',
    low: 'green'
  }
  return map[priority] || 'blue'
}

import { formatLocalTime } from '../utils/date'

const formatTime = (time: string) => {
  return formatLocalTime(time, { month: '2-digit', day: '2-digit' })
}

onMounted(fetchTasks)
</script>

<style scoped>
.task-board {
  padding-bottom: 24px;
}

.board {
  margin-top: 16px;
}

.board-column {
  background: var(--color-fill-2);
  border-radius: 8px;
  min-height: 500px;
}

.column-header {
  padding: 12px 16px;
  border-radius: 8px 8px 0 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: #fff;
}

.column-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
}

.column-count {
  font-size: 14px;
  opacity: 0.9;
}

.column-body {
  padding: 12px;
}

.task-card {
  margin-bottom: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.task-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.task-time {
  font-size: 12px;
  color: var(--color-text-3);
}

.task-title {
  font-weight: 500;
  margin-bottom: 8px;
  line-height: 1.4;
}

.task-topic {
  margin-bottom: 12px;
}

.task-footer {
  display: flex;
  justify-content: flex-end;
  padding-top: 12px;
  border-top: 1px solid var(--color-border-2);
}
</style>
