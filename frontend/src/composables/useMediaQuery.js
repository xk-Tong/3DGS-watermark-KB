// 响应式断点监听 composable。
// 用法：const isMobile = useMediaQuery('(max-width: 1023px)')
// 返回 ref<boolean>，随窗口尺寸变化自动更新。
// SSR 安全：默认 false，onMounted 后才同步当前状态。

import { ref, onMounted, onBeforeUnmount } from 'vue'

export function useMediaQuery(query) {
  const matches = ref(false)
  let mql = null

  const sync = (e) => {
    matches.value = e ? e.matches : (mql ? mql.matches : false)
  }

  onMounted(() => {
    if (typeof window === 'undefined' || !window.matchMedia) return
    mql = window.matchMedia(query)
    sync()
    if (mql.addEventListener) mql.addEventListener('change', sync)
    else mql.addListener(sync) // Safari < 14
  })

  onBeforeUnmount(() => {
    if (!mql) return
    if (mql.removeEventListener) mql.removeEventListener('change', sync)
    else mql.removeListener(sync)
  })

  return matches
}
