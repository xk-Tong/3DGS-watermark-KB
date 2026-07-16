// Vue Router 配置——定义 URL 路径和页面组件的映射关系。

import { createRouter, createWebHistory } from 'vue-router'
import PaperListView from '../views/PaperListView.vue'

// routes 数组：每个对象是一条路由规则。
// path：URL 路径；name：路由名（编程式跳转用）；component：要渲染的组件。
const routes = [
  // 访问根路径 / 时重定向到 /papers（列表页是首页）
  { path: '/', redirect: '/papers' },
  { path: '/papers', name: 'paper-list', component: PaperListView },
  // 下面三个页面用懒加载（动态 import）：只有访问时才加载，减小首屏体积。
  // () => import(...) 返回 Promise，Vue Router 在导航时解析组件。
  { path: '/papers/:id', name: 'paper-detail', component: () => import('../views/PaperDetailView.vue') },
  { path: '/dashboard', name: 'dashboard', component: () => import('../views/DashboardView.vue') },
  { path: '/compare', name: 'compare', component: () => import('../views/CompareView.vue') },
]

// createWebHistory：HTML5 history 模式，URL 是干净的 /papers 不带 # 号。
// （另一种 hash 模式 URL 是 /#/papers，不需要服务器配置但不美观）
// 部署到 Nginx 时需配 try_files（Phase 4 处理），否则刷新会 404。
export default createRouter({
  history: createWebHistory(),
  routes,
})
