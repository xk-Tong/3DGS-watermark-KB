// Vue 3 应用入口。
// createApp 创建应用实例，use() 注册插件，mount() 挂载到 DOM。

import { createApp } from 'vue'
import { createPinia } from 'pinia'
// Element Plus 全量引入——保留组件功能，样式通过 tokens.css 覆盖。
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
// 设计令牌：必须在 Element Plus 样式之后引入，才能覆盖默认变量。
import './assets/tokens.css'
import App from './App.vue'
import router from './router'
import reveal from './directives/reveal'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(ElementPlus)
app.directive('reveal', reveal)

app.mount('#app')
