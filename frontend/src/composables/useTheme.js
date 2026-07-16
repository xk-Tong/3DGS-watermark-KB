// 主题切换 composable。
// 每个页面通过 useTheme() 设置自己的深浅主题，
// 修改 <html data-theme="dark/light"> 属性触发 CSS 变量切换。

import { onMounted, onUnmounted } from 'vue'

/**
 * 作用：在页面挂载时设置主题，卸载时恢复默认。
 * @param {'dark' | 'light'} theme - 页面主题
 * 使用场景：页面组件 onMounted 里调用 useTheme('dark')。
 */
export function useTheme(theme) {
  onMounted(() => {
    document.documentElement.setAttribute('data-theme', theme)
  })

  // 注意：不在这里 onUnmounted 恢复，因为路由切换时新页面会自己设置主题。
  // 如果新页面没设置，默认走 :root（浅色）。
}
