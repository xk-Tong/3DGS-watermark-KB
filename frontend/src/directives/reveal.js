// v-reveal —— 滚动入场指令。
//
// 用法：
//   <div v-reveal>          进入视口时上浮淡入
//   <div v-reveal="120">    延迟 120ms（用于同组元素 stagger）
//
// 初始态 .reveal（透明 + 下移，样式在 tokens.css），进入视口时加
// .is-revealed 归位。全站共用一个 IntersectionObserver。
// reduced-motion 或浏览器不支持 IO 时直接显示终态，不做动画。

const observer =
  typeof window !== 'undefined' && 'IntersectionObserver' in window
    ? new IntersectionObserver(
        (entries) => {
          for (const entry of entries) {
            if (entry.isIntersecting) {
              entry.target.classList.add('is-revealed')
              observer.unobserve(entry.target)
            }
          }
        },
        // rootMargin 底部内缩 6%：元素刚露头一点就开始动，而不是完全进入才动
        { threshold: 0.1, rootMargin: '0px 0px -6% 0px' }
      )
    : null

export default {
  mounted(el, binding) {
    const delay = Number(binding.value) || 0
    if (delay) el.style.setProperty('--reveal-delay', `${delay}ms`)
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    if (reduced || !observer) {
      el.classList.add('is-revealed')
      return
    }
    el.classList.add('reveal')
    observer.observe(el)
  },
}
