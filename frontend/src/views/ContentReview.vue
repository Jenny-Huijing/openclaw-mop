<template>
  <div class="content-review">
    <el-page-header title="内容审核" @back="$router.push('/contents')" />
    
    <el-card v-if="currentContent" class="review-card">
      <template #header>
        <div class="card-header">
          <span>{{ currentContent.title }}</span>
          <el-tag :type="getStatusType(currentContent.status)">{{ statusText(currentContent.status) }}</el-tag>
        </div>
      </template>
      
      <div class="content-body">
        <pre>{{ currentContent.body }}</pre>
      </div>
      
      <div class="content-tags">
        <el-tag v-for="tag in currentContent.tags" :key="tag" class="tag">{{ tag }}</el-tag>
      </div>
      
      <div class="actions">
        <el-button v-if="currentContent.status === 'review'" type="success" size="large" @click="approve">✅ 审核通过</el-button>
        <el-button v-if="currentContent.status === 'review'" type="danger" size="large" @click="reject">❌ 拒绝</el-button>
        <el-button v-if="currentContent.status === 'ready'" type="primary" size="large" @click="publish">🚀 立即发布</el-button>
      </div>
    </el-card>
    
    <el-empty v-else description="加载中..." />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useContentStore } from '../stores'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const contentStore = useContentStore()

const currentContent = ref(null)

const fetchContent = async () => {
  const id = route.params.id as string
  // 这里应该调用API获取详情，暂时用列表数据
  await contentStore.fetchContents()
  currentContent.value = contentStore.contents.find(c => c.id === id)
}

const getStatusType = (status: string) => {
  const map: Record<string, string> = {
    draft: 'info',
    review: 'warning',
    ready: 'success',
    published: 'success',
    rejected: 'danger'
  }
  return map[status] || 'info'
}

const statusText = (status: string) => {
  const map: Record<string, string> = {
    draft: '草稿',
    review: '待审核',
    ready: '待发布',
    published: '已发布',
    rejected: '已拒绝'
  }
  return map[status] || status
}

const approve = async () => {
  try {
    await contentStore.approveContent(currentContent.value!.id)
    ElMessage.success('审核通过')
    fetchContent()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const reject = async () => {
  try {
    await contentStore.rejectContent(currentContent.value!.id)
    ElMessage.success('已拒绝')
    fetchContent()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const publish = async () => {
  try {
    await contentStore.publishContent(currentContent.value!.id)
    ElMessage.success('发布成功')
    fetchContent()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

onMounted(fetchContent)
</script>

<style scoped>
.content-review {
  padding: 20px;
}
.review-card {
  margin-top: 20px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.content-body {
  background: #f5f7fa;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
}
.content-body pre {
  white-space: pre-wrap;
  font-family: inherit;
  line-height: 1.8;
}
.content-tags {
  margin-bottom: 20px;
}
.content-tags .tag {
  margin-right: 10px;
}
.actions {
  display: flex;
  gap: 15px;
  justify-content: center;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
}
</style>
