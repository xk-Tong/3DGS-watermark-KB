// Vue Router 配置——定义 URL 路径和页面组件的映射关系。

import { createRouter, createWebHistory } from 'vue-router'

// routes 数组：每个对象是一条路由规则。
const routes = [
  // 首页：HomeView（深色 Hero + 最新论文 + 统计摘要）
  { path: '/', name: 'home', component: () => import('../views/HomeView.vue') },
  { path: '/papers', name: 'paper-list', component: () => import('../views/PaperListView.vue') },
  { path: '/papers/:id', name: 'paper-detail', component: () => import('../views/PaperDetailView.vue') },
  { path: '/dashboard', name: 'dashboard', component: () => import('../views/DashboardView.vue') },
  { path: '/compare', name: 'compare', component: () => import('../views/CompareView.vue') },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
