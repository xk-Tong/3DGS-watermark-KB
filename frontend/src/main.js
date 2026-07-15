// Vue 3 应用入口。
// createApp 创建应用实例，use() 注册插件，mount() 挂载到 DOM。

import { createApp } from 'vue'
import { createPinia } from 'pinia'
// Element Plus 全量引入——Phase 0 求简单，不配按需引入插件。
// 全量引入会让首屏体积大一点（~500KB），Phase 3 优化时换按需引入。
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'  // 引入组件样式（没有这行组件会没样式）
import App from './App.vue'
import router from './router'

const app = createApp(App)

// 注册顺序一般：状态管理 → 路由 → UI 库（UI 库最后，避免它依赖前两者时报错）
app.use(createPinia())   // Pinia：Vue 3 官方推荐的状态管理库（替代 Vuex）
app.use(router)          // Vue Router：前端路由
app.use(ElementPlus)     // Element Plus：全局注册所有组件（el-table、el-tag 等）

app.mount('#app')        // 挂载到 index.html 里的 <div id="app">
