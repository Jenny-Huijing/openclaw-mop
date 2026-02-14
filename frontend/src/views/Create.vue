<template>
  <div class="create-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <n-button quaternary @click="$router.back()">
        ← 返回
      </n-button>
      <span class="page-title">内容创作</span>
      <n-button type="primary" round @click="publish">
        发布
      </n-button>
    </div>

    <!-- 内容为空状态 -->
    <div class="empty-create">
      <div class="empty-icon">✨</div>
      <div class="empty-title">AI 智能创作</div>
      <div class="empty-desc">
        选择热点话题，AI 将为你生成完整的小红书内容
      </div>
      <n-space>
        <n-button type="primary" round @click="$router.push('/hotspots')">
          🔥 从热点创作
        </n-button>
        <n-button round @click="createBlank">
          📝 空白创作
        </n-button>
      </n-space>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

const createBlank = () => {
  // 创建空白内容
}

const publish = () => {
  // 发布内容
}
</script>

<style scoped>
.create-page {
  max-width: 900px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 32px;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  color: #FFFFFF;
}

.empty-create {
  background: #1A1A1A;
  border: 1px solid #333333;
  border-radius: 16px;
  padding: 80px 40px;
  text-align: center;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 24px;
}

.empty-title {
  font-size: 24px;
  font-weight: 600;
  color: #FFFFFF;
  margin-bottom: 12px;
}

.empty-desc {
  font-size: 15px;
  color: #A0A0A0;
  margin-bottom: 32px;
}
</style>
