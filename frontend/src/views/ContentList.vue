<template>
  <div class="content-list">
    <el-page-header title="内容管理" @back="$router.push('/')" />
    
    <el-card class="list-card">
      <template #header>
        <div class="card-header">
          <span>内容列表</span>
          <el-button type="primary" @click="fetchContents">刷新</el-button>
        </div>
      </template>
      
      <el-table :data="contents" v-loading="loading">
        <el-table-column prop="title" label="标题" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ statusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
        
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button size="small" @click="viewContent(row)">查看</el-button>
            <el-button v-if="row.status === 'review'" type="success" size="small" @click="approve(row)">通过</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useContentStore } from '../stores'
import { storeToRefs } from 'pinia'
import { ElMessage } from 'element-plus'

const router = useRouter()
const contentStore = useContentStore()
const { contents, loading } = storeToRefs(contentStore)
const { fetchContents, approveContent } = contentStore

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

import { formatLocalTime } from '../utils/date'

const formatTime = (time: string) => {
  return formatLocalTime(time)
}

const viewContent = (row: any) => {
  router.push(`/contents/${row.id}`)
}

const approve = async (row: any) => {
  try {
    await approveContent(row.id)
    ElMessage.success('审核通过')
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

onMounted(fetchContents)
</script>

<style scoped>
.content-list {
  padding: 20px;
}
.list-card {
  margin-top: 20px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
