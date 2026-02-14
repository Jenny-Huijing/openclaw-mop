// composables/useToast.ts
import { ref } from 'vue'
import type { ToastState } from '../types'

const toast = ref<ToastState>({
  show: false,
  message: '',
  type: 'success'
})

let timer: ReturnType<typeof setTimeout> | null = null

export function useToast() {
  const show = (message: string, type: 'success' | 'error' = 'success') => {
    if (timer) clearTimeout(timer)
    toast.value = { show: true, message, type }
    timer = setTimeout(() => {
      toast.value.show = false
    }, 3000)
  }
  
  return { toast, show }
}
