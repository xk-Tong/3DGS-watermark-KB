<template>
  <!-- Canvas 容器：绝对定位铺满父元素，粒子在背后渲染 -->
  <canvas ref="canvasRef" class="gauss-particles"></canvas>
</template>

<script setup>
// GaussParticles.vue —— 水墨高斯场，网站的签名元素（浅色版）。
//
// 3DGS 的高斯泼溅 × 水墨晕染：墨蓝色水彩斑块在纸面上
// "落墨 → 晕开 → 淡去 → 换处重生"，偶有朱砂一点（呼应印章 motif）。
// 配色取自设计 token（--accent 墨蓝 / --warm 朱砂），与浅色典藏室主题一体。
//
// 设计要点：
//   - 生命周期编舞：每个斑块 bloom（化开）→ sustain → dissolve（淡去）→ 重生，
//     整个场永远在呼吸，而不是屏保式的匀速直线漂移
//   - 构图：泼溅位置用真正的高斯分布（Box-Muller）聚集在少数"墨团"周围，
//     偏向右侧——给左侧标题留白带（标题左对齐）
//   - 斑块质感：预渲染为 offscreen sprite（三瓣晕染 + 边缘水痕环），
//     运行时只 drawImage——比每帧建渐变快一个量级，边缘也不像喷枪圆斑
//   - multiply 混合：斑块重叠处像墨一样加深，而不是越叠越灰
//   - 细小墨点缓慢漂移，是 splat 渲染前的"点云"
//   - 性能：sprite 复用池 + DPR≤2 + 视口外/后台跳帧；reduced-motion 静态一帧

import { ref, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  // 大斑块数 / 小墨点数（移动端自动减到 60%）
  splatCount: { type: Number, default: 22 },
  dotCount: { type: Number, default: 26 },
  // 墨蓝（RGB 分量字符串）——与 --accent 同值
  inkColor: { type: String, default: '46, 74, 107' },      // #2E4A6B
  // 朱砂——与 --warm 同值，呼应印章
  sealColor: { type: String, default: '184, 57, 43' },     // #B8392B
  // 朱砂斑块比例（0-1），宜少不宜多
  sealRatio: { type: Number, default: 0.12 },
})

const canvasRef = ref(null)
let ctx = null
let animationId = null
let width = 0
let height = 0
let frame = 0
let isVisible = true
let observer = null

let inkSprites = []
let sealSprites = []
let splats = []
let dots = []
let clusters = []

// onUnmounted 必须在 setup 顶层注册（写进 onMounted 回调会静默注册失败）
let cleanup = () => {}

// ---- 工具 ----

// smoothstep 缓动：bloom/dissolve 的起落都走这条曲线
function smooth(t) {
  return t * t * (3 - 2 * t)
}

// Box-Muller：真正的高斯分布——泼溅点围绕墨团聚集，点题 3D Gaussian
function gauss2(cx, cy, spread) {
  const u = Math.random() || 1e-6
  const v = Math.random()
  const r = Math.sqrt(-2 * Math.log(u)) * spread
  const a = 2 * Math.PI * v
  return [cx + r * Math.cos(a), cy + r * Math.sin(a)]
}

// ---- 斑块 sprite 预渲染 ----
// 三瓣晕染 + 边缘水痕环：水彩落纸后中心深、边缘有一圈沉淀线的形态。
// sprite 内部用 multiply 让瓣与瓣之间自然加深。
function makeSplatSprite(rgb) {
  const r = 70 + Math.random() * 80          // 基础半径 70–150（逻辑像素）
  const SS = 2                                // 超采样倍数，Retina 下不糊
  const side = Math.ceil(r * 2)
  const cv = document.createElement('canvas')
  cv.width = side * SS
  cv.height = side * SS
  const c = cv.getContext('2d')
  c.scale(SS, SS)
  c.globalCompositeOperation = 'multiply'

  const lobes = [
    { dx: 0, dy: 0, lr: r * 0.66, a: 0.5 },
    { dx: (Math.random() - 0.5) * r * 0.5, dy: (Math.random() - 0.5) * r * 0.5, lr: r * 0.45, a: 0.4 },
    { dx: (Math.random() - 0.5) * r * 0.5, dy: (Math.random() - 0.5) * r * 0.5, lr: r * 0.38, a: 0.34 },
  ]
  for (const L of lobes) {
    const g = c.createRadialGradient(r + L.dx, r + L.dy, 0, r + L.dx, r + L.dy, L.lr)
    g.addColorStop(0, `rgba(${rgb}, ${L.a})`)
    g.addColorStop(0.55, `rgba(${rgb}, ${L.a * 0.45})`)
    g.addColorStop(0.82, `rgba(${rgb}, ${L.a * 0.12})`)
    g.addColorStop(1, `rgba(${rgb}, 0)`)
    c.fillStyle = g
    c.beginPath()
    c.arc(r + L.dx, r + L.dy, L.lr, 0, Math.PI * 2)
    c.fill()
  }

  // 边缘水痕环：水彩干燥时颜料沉淀在边缘形成的细线
  const ring = c.createRadialGradient(r, r, r * 0.5, r, r, r * 0.97)
  ring.addColorStop(0, `rgba(${rgb}, 0)`)
  ring.addColorStop(0.82, `rgba(${rgb}, 0)`)
  ring.addColorStop(0.9, `rgba(${rgb}, 0.1)`)
  ring.addColorStop(1, `rgba(${rgb}, 0)`)
  c.fillStyle = ring
  c.beginPath()
  c.arc(r, r, r, 0, Math.PI * 2)
  c.fill()

  return { canvas: cv, radius: r }
}

// ---- 斑块：有生命周期的泼墨 ----
class Splat {
  constructor(initial) {
    this.respawn(initial)
  }

  respawn(initial = false) {
    // 80% 落在墨团周围（高斯聚集），20% 随机散落
    const useCluster = Math.random() < 0.8 && clusters.length
    if (useCluster) {
      const c = clusters[Math.floor(Math.random() * clusters.length)]
      const [gx, gy] = gauss2(c.x, c.y, c.spread)
      this.x = gx
      this.y = gy
    } else {
      this.x = Math.random() * width
      this.y = Math.random() * height
    }
    // 选 sprite：少数朱砂，多数墨蓝
    const useSeal = Math.random() < props.sealRatio
    const pool = useSeal ? sealSprites : inkSprites
    this.sprite = pool[Math.floor(Math.random() * pool.length)]
    this.scale = 0.7 + Math.random() * 0.9
    // 大斑块更淡（面积大则浓度低，像真实晕开）
    this.peak = (0.1 + Math.random() * 0.16) * (1.15 - (this.scale - 0.7) * 0.3) * (useSeal ? 0.75 : 1)
    this.life = 600 + Math.random() * 800      // 10–23 秒一个轮回
    // 初始化时年龄随机铺开，让第一帧就是"正在进行"的场
    this.age = initial ? Math.random() * this.life : 0
    this.vx = (Math.random() - 0.5) * 0.12
    this.vy = (Math.random() - 0.5) * 0.08 - 0.01
  }

  update() {
    this.age++
    if (this.age >= this.life) this.respawn()
    this.x += this.vx
    this.y += this.vy
  }

  // 透明度包络：快速淡入 → 持续 → 长尾淡去
  alpha() {
    const t = this.age / this.life
    if (t >= 1) return 0
    const aIn = smooth(Math.min(1, t / 0.2))
    const aOut = t > 0.65 ? smooth(Math.max(0, 1 - (t - 0.65) / 0.35)) : 1
    return this.peak * aIn * aOut
  }

  // 半径生长：落墨后前 50% 生命周期从 55% 晕开到 100%
  growth() {
    const t = Math.min(1, this.age / (this.life * 0.5))
    return 0.55 + 0.45 * (1 - Math.pow(1 - t, 3))
  }
}

// ---- 墨点：splat 渲染前的"点云"，缓慢漂移 ----
class Dot {
  constructor() {
    this.x = Math.random() * width
    this.y = Math.random() * height
    this.r = 0.8 + Math.random() * 1.4
    this.vx = (Math.random() - 0.5) * 0.15
    this.vy = (Math.random() - 0.5) * 0.15
    this.baseAlpha = 0.16 + Math.random() * 0.22
    this.pulseFreq = 0.003 + Math.random() * 0.005
    this.phase = Math.random() * Math.PI * 2
  }

  update() {
    this.x += this.vx
    this.y += this.vy
    if (this.x < -4) this.x = width + 4
    else if (this.x > width + 4) this.x = -4
    if (this.y < -4) this.y = height + 4
    else if (this.y > height + 4) this.y = -4
    this.alpha = this.baseAlpha * (0.7 + 0.3 * Math.sin(frame * this.pulseFreq + this.phase))
  }

  draw(c) {
    c.fillStyle = `rgba(${props.inkColor}, ${this.alpha})`
    c.beginPath()
    c.arc(this.x, this.y, this.r, 0, Math.PI * 2)
    c.fill()
  }
}

// ---- 墨团位置：偏右侧构图，给左侧标题留白带 ----
function makeClusters() {
  return [
    { x: 0.74 * width, y: 0.3 * height, spread: 0.13 * width },
    { x: 0.55 * width, y: 0.74 * height, spread: 0.11 * width },
    { x: 0.9 * width, y: 0.66 * height, spread: 0.09 * width },
  ]
}

// ---- 绘制一帧（动画循环与 reduced-motion 静态帧共用） ----
function drawField() {
  ctx.clearRect(0, 0, width, height)
  // 斑块：multiply 让重叠处像墨一样加深
  ctx.globalCompositeOperation = 'multiply'
  for (const s of splats) {
    const r = s.sprite.radius * s.scale * s.growth()
    ctx.globalAlpha = s.alpha()
    ctx.drawImage(s.sprite.canvas, s.x - r, s.y - r, r * 2, r * 2)
  }
  ctx.globalAlpha = 1
  // 墨点：保持 crisp，盖在晕染之上
  ctx.globalCompositeOperation = 'source-over'
  for (const d of dots) d.draw(ctx)
}

onMounted(() => {
  const canvas = canvasRef.value
  ctx = canvas.getContext('2d')

  function init() {
    resize()
    // sprite 复用池：10 墨蓝 + 4 朱砂，斑块共享，避免每帧建渐变
    inkSprites = Array.from({ length: 10 }, () => makeSplatSprite(props.inkColor))
    sealSprites = Array.from({ length: 4 }, () => makeSplatSprite(props.sealColor))
    clusters = makeClusters()
    // 移动端减量
    const small = width < 720
    const nS = small ? Math.round(props.splatCount * 0.6) : props.splatCount
    const nD = small ? Math.round(props.dotCount * 0.6) : props.dotCount
    splats = Array.from({ length: nS }, () => new Splat(true))
    dots = Array.from({ length: nD }, () => new Dot())
  }

  function resize() {
    const rect = canvas.parentElement.getBoundingClientRect()
    // 重新赋值 canvas.width 会重置变换矩阵，之后重新 scale 是安全的
    const dpr = Math.min(window.devicePixelRatio || 1, 2)
    width = rect.width
    height = rect.height
    canvas.width = width * dpr
    canvas.height = height * dpr
    canvas.style.width = width + 'px'
    canvas.style.height = height + 'px'
    ctx.scale(dpr, dpr)
  }

  function animate() {
    animationId = requestAnimationFrame(animate)
    // 滚出视口或切后台时跳帧
    if (!isVisible || document.hidden) return
    frame++
    for (const s of splats) s.update()
    for (const d of dots) d.update()
    drawField()
  }

  const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches

  init()
  if (!prefersReduced) {
    animate()
  } else {
    // reduced-motion：静态一帧（年龄已随机铺开，是"进行中"的场）
    drawField()
  }

  // 只在 Hero 进入视口时绘制
  observer = new IntersectionObserver(([entry]) => {
    isVisible = entry.isIntersecting
  }, { threshold: 0 })
  observer.observe(canvas)

  function handleResize() {
    init()
    // 静态模式下 resize 后补一帧
    if (prefersReduced) drawField()
  }
  window.addEventListener('resize', handleResize)

  cleanup = () => {
    if (animationId) cancelAnimationFrame(animationId)
    if (observer) observer.disconnect()
    window.removeEventListener('resize', handleResize)
  }
})

onUnmounted(() => cleanup())
</script>

<style scoped>
.gauss-particles {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;  /* 不拦截鼠标事件 */
}
</style>
