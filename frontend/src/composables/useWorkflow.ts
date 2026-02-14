// composables/useWorkflow.ts
import { ref } from 'vue'
import { contentApi } from '../services/content'
import type { Content } from '../types'

export function useWorkflow(onComplete: () => void) {
  const isCreating = ref(false)
  
  const start = async () => {
    if (isCreating.value) return
    
    isCreating.value = true
    
    try {
      const res = await contentApi.startWorkflow()
      
      if (res.code === 200) {
        onComplete()
        const contentId = res.data?.content?.id
        if (contentId) {
          pollStatus(contentId, onComplete)
        }
        return { success: true, contentId }
      }
      
      // 非200状态码，重置状态并返回错误
      isCreating.value = false
      return { success: false, error: res.message || '服务暂时不可用' }
    } catch (e: any) {
      isCreating.value = false
      return { success: false, error: e.message || '网络错误' }
    }
  }
  
  const pollStatus = (contentId: string, onDone: () => void) => {
    let attempts = 0
    const maxAttempts = 30
    
    const check = async () => {
      attempts++
      
      try {
        const res = await contentApi.getById(contentId)
        
        if (res.code === 200 && res.data.status !== 'CREATING') {
          onDone()
          isCreating.value = false
          return
        }
        
        if (attempts < maxAttempts) {
          setTimeout(check, 2000)
        } else {
          isCreating.value = false
        }
      } catch (e) {
        isCreating.value = false
      }
    }
    
    setTimeout(check, 2000)
  }
  
  return { isCreating, start }
}
