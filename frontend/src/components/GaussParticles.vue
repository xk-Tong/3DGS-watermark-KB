<template>
  <!-- Canvas 容器：绝对定位铺满父元素，粒子在背后渲染 -->
  <canvas ref="canvasRef" class="gauss-particles"></canvas>
</template>

<script setup>
// GaussParticles.vue —— 高斯粒子 Canvas 组件。
//
// 这是网站的"签名元素"——半透明圆点缓慢漂移、叠加，
// 暗示 3D Gaussian Splatting 的本质：大量高斯粒子泼溅成图像。
//
// 设计要点：
//   - 粒子用径向渐变模拟高斯分布（中心亮边缘暗）
//   - 辉光蓝 #7C9EFF 为主，偶尔有陶土色 #E5A893 点缀（呼应水印隐藏信息）
//   - 粒子有轻微物理运动（漂移 + 边界反弹）
//   - 近距离粒子之间画淡连线（增加"泼溅"质感）
//   - requestAnimationFrame 驱动，prefers-reduced-motion 时停止
//   - 粒子数自适应屏幕宽度（移动端少一些）

import { ref, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  // 粒子数量，不传则按屏幕宽度自适应
  count: { type: Number, default: null },
  // 粒子主色（RGBA 格式，方便控制透明度）
  color: { type: String, default: '124, 158, 255' },     // #7C9EFF
  // 点缀色（少数粒子用）
  accentColor: { type: String, default: '229, 168, 147' },  // #E5A893
  // 点缀色比例（0-1）
  accentRatio: { type: Number, default: 0.15 },
})

const canvasRef = ref(null)
let ctx = null
let animationId = null
let particles = []
let width = 0
let height = 0

// 粒子类：每个粒子有位置、速度、半径、颜色
class Particle {
  constructor(w, h, useAccent) {
    // Math.random() 返回 0-1 的随机数，乘以宽度得到随机 x 位置
    this.x = Math.random() * w
    this.y = Math.random() * h
    // 速度：缓慢漂移，-0.15 到 0.15 px/frame
    this.vx = (Math.random() - 0.5) * 0.3
    this.vy = (Math.random() - 0.5) * 0.3
    // 半径：8-25px，大粒子更像高斯泼溅的"大斑点"
    this.radius = Math.random() * 17 + 8
    // 透明度：0.08-0.25，半透明才能看到叠加效果
    this.opacity = Math.random() * 0.17 + 0.08
    // 是否用点缀色
    this.useAccent = useAccent
  }

  // 更新位置 + 边界反弹
  update(w, h) {
    this.x += this.vx
    this.y += this.vy
    // 边界反弹：碰到边缘速度反转
    if (this.x < -this.radius) this.x = w + this.radius
    if (this.x > w + this.radius) this.x = -this.radius
    if (this.y < -this.radius) this.y = h + this.radius
    if (this.y > h + this.radius) this.y = -this.radius
  }

  // 绘制粒子：径向渐变模拟高斯分布（中心亮边缘暗）
  draw(ctx) {
    const color = this.useAccent ? props.accentColor : props.color
    // createRadialGradient：创建径向渐变。
    // 参数：内圆 x,y,radius + 外圆 x,y,radius
    // 高斯分布的核心：中心不透明，边缘渐变到完全透明
    const gradient = ctx.createRadialGradient(
      this.x, this.y, 0,           // 内圆：中心点，半径 0
      this.x, this.y, this.radius   // 外圆：同中心，半径 = 粒子半径
    )
    gradient.addColorStop(0, `rgba(${color}, ${this.opacity})`)
    gradient.addColorStop(0.5, `rgba(${color}, ${this.opacity * 0.5})`)
    gradient.addColorStop(1, `rgba(${color}, 0)`)

    ctx.fillStyle = gradient
    // beginPath + arc + fill：画一个圆形并填充
    ctx.beginPath()
    ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2)
    ctx.fill()
  }
}

onMounted(() => {
  const canvas = canvasRef.value
  ctx = canvas.getContext('2d')

  // 自适应粒子数量：屏幕宽度 / 12，限制在 30-80 之间
  const count = props.count || Math.min(80, Math.max(30, Math.floor(window.innerWidth / 12)))

  // 初始化粒子
  function init() {
    resize()
    particles = []
    for (let i = 0; i < count; i++) {
      // Math.random() < accentRatio 决定该粒子是否用点缀色
      const useAccent = Math.random() < props.accentRatio
      particles.push(new Particle(width, height, useAccent))
    }
  }

  // 调整 canvas 尺寸匹配父元素
  function resize() {
    const rect = canvas.parentElement.getBoundingClientRect()
    // devicePixelRatio：设备像素比（Retina 屏为 2）。
    // 乘以 dpr 让 canvas 在高 DPI 屏幕上不模糊。
    const dpr = window.devicePixelRatio || 1
    width = rect.width
    height = rect.height
    canvas.width = width * dpr
    canvas.height = height * dpr
    canvas.style.width = width + 'px'
    canvas.style.height = height + 'px'
    // scale：让绘图坐标系匹配 dpr，否则在 Retina 上粒子会变小
    ctx.scale(dpr, dpr)
  }

  // 动画循环
  function animate() {
    // clearRect：清空画布（每帧重绘，否则粒子会拖尾）
    ctx.clearRect(0, 0, width, height)

    // 绘制所有粒子
    for (const p of particles) {
      p.update(width, height)
      p.draw(ctx)
    }

    // 绘制近距离粒子之间的连线（增加"泼溅"质感）
    // 双重循环检查每对粒子距离，O(n²) 但 n≤80 可接受
    ctx.lineWidth = 0.5
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x
        const dy = particles[i].y - particles[j].y
        const dist = Math.sqrt(dx * dx + dy * dy)
        // 距离小于 120px 时画连线，距离越近线越亮
        if (dist < 120) {
          const alpha = (1 - dist / 120) * 0.08
          ctx.strokeStyle = `rgba(${props.color}, ${alpha})`
          ctx.beginPath()
          ctx.moveTo(particles[i].x, particles[i].y)
          ctx.lineTo(particles[j].x, particles[j].y)
          ctx.stroke()
        }
      }
    }

    animationId = requestAnimationFrame(animate)
  }

  // 检查 prefers-reduced-motion：用户设置了减少动效时不启动动画
  const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches

  init()
  if (!prefersReduced) {
    animate()
  } else {
    // reduced-motion：只画一帧静态画面
    ctx.clearRect(0, 0, width, height)
    for (const p of particles) p.draw(ctx)
  }

  // 窗口尺寸变化时重新初始化
  function handleResize() {
    init()
  }
  window.addEventListener('resize', handleResize)

  // 组件卸载时清理
  onUnmounted(() => {
    if (animationId) cancelAnimationFrame(animationId)
    window.removeEventListener('resize', handleResize)
  })
})
</script>

<style scoped>
.gauss-particles {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;  /* 不拦截鼠标事件，让背后元素可点击 */
}
</style>
