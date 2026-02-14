import { defineStore } from 'pinia'
import { ref } from 'vue'
import { contentApi } from '../api/content'

export const useContentStore = defineStore('content', () => {
  // State
  const contents = ref([])
  const loading = ref(false)
  const currentContent = ref(null)

  // Actions
  const fetchContents = async (params = {}) => {
    loading.value = true
    try {
      const res = await contentApi.getList(params)
      contents.value = res.data.items || []
      return res.data
    } finally {
      loading.value = false
    }
  }

  const createContent = async (data) => {
    const res = await contentApi.create(data)
    contents.value.unshift(res.data)
    return res.data
  }

  const approveContent = async (id) => {
    const res = await contentApi.approve(id)
    const index = contents.value.findIndex(c => c.id === id)
    if (index > -1) {
      contents.value[index] = { ...contents.value[index], ...res.data }
    }
    return res.data
  }

  const rejectContent = async (id) => {
    const res = await contentApi.reject(id)
    const index = contents.value.findIndex(c => c.id === id)
    if (index > -1) {
      contents.value[index] = { ...contents.value[index], ...res.data }
    }
    return res.data
  }

  const publishContent = async (id) => {
    const res = await contentApi.publish(id)
    const index = contents.value.findIndex(c => c.id === id)
    if (index > -1) {
      contents.value[index] = { ...contents.value[index], ...res.data }
    }
    return res.data
  }

  return {
    contents,
    loading,
    currentContent,
    fetchContents,
    createContent,
    approveContent,
    rejectContent,
    publishContent
  }
})
