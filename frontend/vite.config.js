import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

// Vite 配置文件。defineConfig 提供类型提示（即使 JS 也受益于编辑器智能补全）。
export default defineConfig({
  // plugins：Vite 插件列表。@vitejs/plugin-vue 让 Vite 能编译 .vue 单文件组件。
  plugins: [vue()],

  // resolve.alias：模块解析别名。把 '@' 映射到 ./src 目录。
  // 这样 import App from '@/App.vue' 等价于从 src/App.vue 导入，避免写相对路径 ../../。
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
      // import.meta.url：ESM 里当前模块的 URL（此文件的绝对路径）。
      // new URL('./src', import.meta.url)：基于当前文件位置解析 ./src 的绝对路径。
      // fileURLToPath：把 file:// URL 转成文件系统路径字符串。
    },
  },

  // server：开发服务器配置。
  server: {
    port: 5173,
    // proxy：开发期代理。把浏览器请求的 /api/* 转发到后端 8000 端口。
    // 这样前端用相对路径 /api/papers 请求，浏览器认为是同源（5173），
    // 实际由 Vite dev server 转发到 127.0.0.1:8000，避免跨域问题。
    // 生产部署时由 Nginx 做同样的反代。
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
