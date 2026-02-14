import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { taskApi } from '../api/task'

export const useTaskStore = defineStore('task', () => {
  // State
  const tasks = ref([])
  const loading = ref(false)
  const currentTask = ref(null)

  // Getters
  const pendingTasks = computed(() => tasks.value.filter(t => t.status === 'pending'))
  const doingTasks = computed(() => tasks.value.filter(t => t.status === 'doing'))
  const reviewTasks = computed(() => tasks.value.filter(t => t.status === 'review'))
  const readyTasks = computed(() => tasks.value.filter(t => t.status === 'ready'))
  const publishedTasks = computed(() => tasks.value.filter(t => t.status === 'published'))

  // Actions
  const fetchTasks = async (params = {}) => {
    loading.value = true
    try {
      const res = await taskApi.getList(params)
      tasks.value = res.data.items || []
      return res.data
    } finally {
      loading.value = false
    }
  }

  const createTask = async (data) => {
    const res = await taskApi.create(data)
    tasks.value.unshift(res.data)
    return res.data
  }

  const updateTask = async (id, data) => {
    const res = await taskApi.update(id, data)
    const index = tasks.value.findIndex(t => t.id === id)
    if (index > -1) {
      tasks.value[index] = { ...tasks.value[index], ...res.data }
    }
    return res.data
  }

  const deleteTask = async (id) => {
    await taskApi.delete(id)
    tasks.value = tasks.value.filter(t => t.id !== id)
  }

  return {
    tasks,
    loading,
    currentTask,
    pendingTasks,
    doingTasks,
    reviewTasks,
    readyTasks,
    publishedTasks,
    fetchTasks,
    createTask,
    updateTask,
    deleteTask
  }
})
