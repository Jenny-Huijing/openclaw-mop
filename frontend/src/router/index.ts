import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('../views/Dashboard.vue')
  },
  {
    path: '/create',
    name: 'Create',
    component: () => import('../views/Create.vue')
  },
  {
    path: '/hotspots',
    name: 'HotspotList',
    component: () => import('../views/HotspotList.vue')
  },
  {
    path: '/workflow',
    name: 'Workflow',
    component: () => import('../views/Workflow.vue')
  },
  {
    path: '/logs',
    name: 'Logs',
    component: () => import('../views/Logs.vue')
  },
  {
    path: '/docs',
    name: 'Documentation',
    component: () => import('../views/Documentation.vue')
  },
  {
    path: '/scheduler',
    name: 'Scheduler',
    component: () => import('../views/Scheduler.vue')
  },
  {
    path: '/analytics',
    name: 'Analytics',
    component: () => import('../views/Dashboard.vue') // 临时使用Dashboard
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('../views/Dashboard.vue') // 临时使用Dashboard
  },
  // 保留旧路由兼容
  {
    path: '/tasks',
    name: 'TaskBoard',
    component: () => import('../views/TaskBoard.vue')
  },
  {
    path: '/contents',
    name: 'ContentList',
    component: () => import('../views/ContentList.vue')
  },
  {
    path: '/contents/:id',
    name: 'ContentReview',
    component: () => import('../views/ContentReview.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
