// useCountUp —— 数字滚动动画。
//
// 监听一个响应式数值，从当前显示值 easeOutCubic 缓动到新值。
// 用于 Hero 统计数字的入场动效：数据异步到达后数字从 0 滚到目标值。
// reduced-motion 时直接取终值，不滚。

import { ref, watch, onUnmounted } from 'vue'

/**
 * @param {Function} source - 返回目标数值的 getter（如 () => stats.value.total）
 * @param {number} duration - 动画时长 ms
 * @returns {Ref<number>} 模板里显示的数字
 */
export function useCountUp(source, duration = 900) {
  const display = ref(0)
  let raf = null

  function animateTo(target) {
    if (raf) cancelAnimationFrame(raf)
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    if (reduced || target <= 0) {
      display.value = Math.max(0, target)
      return
    }
    const from = display.value
    const start = performance.now()
    const tick = (now) => {
      const p = Math.min(1, (now - start) / duration)
      const eased = 1 - Math.pow(1 - p, 3)   // easeOutCubic
      display.value = Math.round(from + (target - from) * eased)
      if (p < 1) raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
  }

  watch(source, (val) => animateTo(Number(val) || 0), { immediate: true })
  onUnmounted(() => { if (raf) cancelAnimationFrame(raf) })

  return display
}
