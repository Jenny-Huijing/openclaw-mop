<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="visible" class="fixed inset-0 z-50 flex items-center justify-center p-4" @click.self="onCancel">
        <!-- 遮罩 -->
        <div class="absolute inset-0 bg-black/50 backdrop-blur-sm"></div>
        
        <!-- 弹窗 -->
        <div class="relative bg-white rounded-xl shadow-xl w-full max-w-sm p-6">
          <!-- 标题 -->
          <h3 class="text-lg font-semibold text-slate-900 mb-2">{{ title }}</h3>
          
          <!-- 内容 -->
          <p class="text-slate-600 mb-6">{{ content }}</p>
          
          <!-- 按钮 -->
          <div class="flex gap-3 justify-end">
            <button 
              @click="onCancel"
              class="px-4 py-2 text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
            >
              {{ cancelText }}
            </button>
            <button 
              @click="onConfirm"
              :class="[
                'px-4 py-2 rounded-lg transition-colors',
                type === 'danger' 
                  ? 'bg-red-600 text-white hover:bg-red-700' 
                  : 'bg-blue-600 text-white hover:bg-blue-700'
              ]"
            >
              {{ okText }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
interface Props {
  visible: boolean
  title?: string
  content?: string
  okText?: string
  cancelText?: string
  type?: 'default' | 'danger'
}

withDefaults(defineProps<Props>(), {
  title: '确认',
  content: '',
  okText: '确定',
  cancelText: '取消',
  type: 'default'
})

const emit = defineEmits<{
  confirm: []
  cancel: []
}>()

const onConfirm = () => emit('confirm')
const onCancel = () => emit('cancel')
</script>

<style scoped>
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
</style>
