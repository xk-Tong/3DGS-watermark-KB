<template>
  <div class="dashboard-view" v-loading="loading">
    <header class="page-header" v-reveal>
      <div class="page-heading">
        <span class="eyebrow">Statistics</span>
        <h1 class="page-title">统计仪表盘</h1>
        <p class="page-intro">知识库分布与覆盖情况一览 · 图中每一格/tick 都可数</p>
      </div>
    </header>

    <!-- KPI 数字行 -->
    <div class="stats-row">
      <div class="plate stat-plate" v-reveal>
        <span class="stat-number">{{ totalDisplay }}</span>
        <span class="stat-label">收录论文</span>
      </div>
      <div class="plate stat-plate" v-reveal="60">
        <span class="stat-number warn">{{ autoDisplay }}</span>
        <span class="stat-label">AI 未核实</span>
      </div>
      <div class="plate stat-plate" v-reveal="120">
        <span class="stat-number ok">{{ reviewedDisplay }}</span>
        <span class="stat-label">已复核 / 验证</span>
      </div>
    </div>

    <template v-if="stats.total">
      <!-- ════ L15 · Ballot Tally：任务类型（多选，每项独立 0–100）════ -->
      <div class="plate chart-card wide" v-reveal>
        <h2 class="chart-title">任务归属：{{ taskRows[0]?.name || '—' }} 最多</h2>
        <div class="chart-sub">每个类型一行 · 100 格 = 全部 {{ stats.total }} 篇 · 上墨格 = 属于该类的比例 · 一篇可属多类</div>
        <svg viewBox="0 0 840 268" class="chart" role="img" aria-label="任务类型 tally">
          <template v-for="(n, i) in tallyNodes" :key="i">
            <line v-if="n.t === 'line'" v-bind="n.a" :class="n.anim" :style="{ animationDelay: n.d }" />
            <circle v-else-if="n.t === 'circle'" v-bind="n.a" :class="n.anim" :style="{ animationDelay: n.d }" />
            <text v-else v-bind="n.a" :class="n.anim" :style="{ animationDelay: n.d }">{{ n.s }}<title v-if="n.tip">{{ n.tip }}</title></text>
          </template>
        </svg>
        <div class="chart-src">BALLOT TALLY · ONE TICK = 1% OF PAPERS · INKED = TAGGED · /API/STATS/OVERVIEW</div>
      </div>

      <div class="charts-grid">
        <!-- ════ F1 · Rung Bars：收录年份 ════ -->
        <div class="plate chart-card" v-reveal>
          <h2 class="chart-title">收录按年，一檔一篇</h2>
          <div class="chart-sub">各年份入库篇数 · 柱身一檔 = 一篇 · 灰点标每五檔</div>
          <svg viewBox="0 0 400 300" class="chart" role="img" aria-label="收录年份柱图">
            <template v-for="(n, i) in rungNodes" :key="i">
              <line v-if="n.t === 'line'" v-bind="n.a" :class="n.anim" :style="{ animationDelay: n.d }" />
              <circle v-else-if="n.t === 'circle'" v-bind="n.a" :class="n.anim" :style="{ animationDelay: n.d }" />
              <text v-else v-bind="n.a" :class="n.anim" :style="{ animationDelay: n.d }">{{ n.s }}<title v-if="n.tip">{{ n.tip }}</title></text>
            </template>
          </svg>
          <div class="chart-src">RUNG BARS · ONE RUNG = ONE PAPER · DOT MARKS EVERY FIFTH</div>
        </div>

        <!-- ════ F4 · Tick Donut：属性选择构成 ════ -->
        <div class="plate chart-card" v-reveal="80">
          <h2 class="chart-title">属性载体：{{ attrTop.name }} 占 {{ attrTop.pct }}%</h2>
          <div class="chart-sub">{{ attrSum }} 篇有属性标注 · 表盘一格 = 1% · 十二点起顺时针读</div>
          <svg viewBox="0 0 400 300" class="chart" role="img" aria-label="属性选择环形图">
            <template v-for="(n, i) in donutNodes" :key="i">
              <line v-if="n.t === 'line'" v-bind="n.a" :class="n.anim" :style="{ animationDelay: n.d }" />
              <circle v-else-if="n.t === 'circle'" v-bind="n.a" :class="n.anim" :style="{ animationDelay: n.d }" />
              <text v-else v-bind="n.a" :class="n.anim" :style="{ animationDelay: n.d }">{{ n.s }}<title v-if="n.tip">{{ n.tip }}</title></text>
            </template>
          </svg>
          <div class="chart-src">TICK DONUT · ONE TICK = 1% · SEGMENTS ROUNDED TO FULL PERCENT</div>
        </div>

        <!-- ════ F5 · Tick Rows：注入管道 ════ -->
        <div class="plate chart-card" v-reveal>
          <h2 class="chart-title">注入管道：{{ injRows[0]?.name || '—' }} 居多</h2>
          <div class="chart-sub">横向排名 · 一格 = 一篇 · 灰点标每五格</div>
          <svg viewBox="0 0 400 300" class="chart" role="img" aria-label="注入管道横条图">
            <template v-for="(n, i) in rowNodes" :key="i">
              <line v-if="n.t === 'line'" v-bind="n.a" :class="n.anim" :style="{ animationDelay: n.d }" />
              <circle v-else-if="n.t === 'circle'" v-bind="n.a" :class="n.anim" :style="{ animationDelay: n.d }" />
              <text v-else v-bind="n.a" :class="n.anim" :style="{ animationDelay: n.d }">{{ n.s }}<title v-if="n.tip">{{ n.tip }}</title></text>
            </template>
          </svg>
          <div class="chart-src">TICK ROWS · ONE TICK = ONE PAPER · DOT MARKS EVERY FIFTH</div>
        </div>

        <!-- ════ F10 · Dot Heat：属性 × 注入交叉 ════ -->
        <div class="plate chart-card" v-reveal="80">
          <h2 class="chart-title">最常见搭配：{{ crossPeak.label }}</h2>
          <div class="chart-sub">点面积 ∝ 篇数 · 空格留微点（沉默可见）· 虚线圈 = 峰值</div>
          <svg viewBox="0 0 400 300" class="chart" role="img" aria-label="属性注入交叉热力">
            <template v-for="(n, i) in crossNodes" :key="i">
              <line v-if="n.t === 'line'" v-bind="n.a" :class="n.anim" :style="{ animationDelay: n.d }" />
              <circle v-else-if="n.t === 'circle'" v-bind="n.a" :class="n.anim" :style="{ animationDelay: n.d }"><title v-if="n.tip">{{ n.tip }}</title></circle>
              <text v-else v-bind="n.a" :class="n.anim" :style="{ animationDelay: n.d }">{{ n.s }}<title v-if="n.tip">{{ n.tip }}</title></text>
            </template>
          </svg>
          <div class="chart-src">DOT HEAT · DOT AREA = PAPERS · CROSS-COUNTED FROM FULL LIST</div>
        </div>
      </div>

      <!-- ════ 攻击覆盖矩阵：论文 × 攻击（F10 语法衍生二元矩阵）════ -->
      <div class="plate chart-card wide" v-reveal>
        <h2 class="chart-title">攻击覆盖的全景与缺口</h2>
        <div class="chart-sub">一墨点 = 该论文评估过此攻击 · 行按覆盖数降序 · 底行 = 每种攻击的覆盖篇数</div>
        <div class="matrix-scroll">
          <svg :viewBox="`0 0 840 ${matrixHeight}`" class="chart matrix" role="img" aria-label="攻击覆盖矩阵">
            <template v-for="(n, i) in matrixNodes" :key="i">
              <line v-if="n.t === 'line'" v-bind="n.a" :class="n.anim" :style="{ animationDelay: n.d }" />
              <circle v-else-if="n.t === 'circle'" v-bind="n.a" :class="n.anim" :style="{ animationDelay: n.d }"><title v-if="n.tip">{{ n.tip }}</title></circle>
              <text v-else v-bind="n.a" :class="n.anim" :style="{ animationDelay: n.d }">{{ n.s }}<title v-if="n.tip">{{ n.tip }}</title></text>
            </template>
          </svg>
        </div>
        <div class="chart-src">BINARY MATRIX · INK DOT = ATTACK EVALUATED · BOTTOM ROW = PAPERS COVERING EACH · /API/STATS/ROBUSTNESS</div>
      </div>
    </template>

    <!-- 空状态 -->
    <div v-if="!loading && !stats.total" class="plate empty-plate">
      还没有论文——先去 <router-link to="/papers">论文库</router-link> 收录几篇，仪表盘才有东西可画。
    </div>
  </div>
</template>

<script setup>
// DashboardView —— 手写 SVG 图表（lieflat-charts 语法），弃用 ECharts。
//
// 图型分配（数据形状 → 模板）：
//   任务类型（多选计数）  → L15 Ballot Tally（通栏，1 tick = 1% 论文）
//   收录年份（少类目）    → F1 Rung Bars（1 檔 = 1 篇）
//   属性选择（100% 构成） → F4 Tick Donut（1 tick = 1%）
//   注入管道（横向排名）  → F5 Tick Rows（1 tick = 1 篇）
//   属性×注入（4×4 矩阵） → F10 Dot Heat（点面积 ∝ 篇数，前端从全量论文实算）
//   论文×攻击（二元矩阵） → F10 语法衍生（墨点=已评估，底行计数）
//
// 颜色纪律：全部站内中性灰阶（mono），数据编码零彩色；
// 动画：fade/pop + stagger，滚动进视野（v-reveal 的 .is-revealed）才播。

import { ref, computed, onMounted } from 'vue'
import { statsApi } from '../api/stats'
import { papersApi } from '../api/papers'
import { useTheme } from '../composables/useTheme'
import { useCountUp } from '../composables/useCountUp'

useTheme('light')

const stats = ref({})
const robustnessData = ref([])
const papersAll = ref([])
const loading = ref(true)

onMounted(async () => {
  try {
    const [overview, robustness, papers] = await Promise.all([
      statsApi.getOverview(),
      statsApi.getRobustness(),
      // 交叉矩阵要原始行：后端 limit 上限 100，当前规模一页拿全
      papersApi.list({ limit: 100, sort_by: 'added_at', order: 'desc' }),
    ])
    stats.value = overview
    robustnessData.value = robustness
    papersAll.value = papers.items
  } catch (e) {
    console.error('加载统计数据失败:', e)
  } finally {
    loading.value = false
  }
})

// KPI 数字滚动
const totalDisplay = useCountUp(() => stats.value.total)
const autoDisplay = useCountUp(() => stats.value.by_curation?.auto)
const reviewedDisplay = useCountUp(() => (stats.value.by_curation?.reviewed || 0) + (stats.value.by_curation?.verified || 0))

// ---- mono 语法（取自 mono-tokens.js，映射到站内中性色）----
const INK = '#23272E'                    // 墨：主数据（站内 --text-primary）
const PAPER = '#FCFBF8'                  // 纸：卡面（站内 --bg-surface）
const MUTED = '#5C6470'                  // 次级文字
const FAINT = '#B9BEC5'                  // 来源行/辅助刻度
const GRID = '#E3E1D9'                   // 发丝线（站内 --border-subtle）
const L = ['#23272E', '#565E6C', '#8A919C', '#B9BEC5']   // 灰阶 ladder（按重要性分配）

// 确定性伪随机（mono-tokens）：档长/透明度抖动刷新后长一样
const rnd = (i, k) => Math.abs(((i * 73856093) ^ (k * 19349663)) % 1000) / 1000
const D2R = Math.PI / 180
const pol = (cx, cy, r, deg) => [cx + r * Math.cos(deg * D2R), cy + r * Math.sin(deg * D2R)]

// 中文标签映射
const taskLabels = {
  watermarking: '水印', steganography: '隐写',
  tamper_localization: '篡改定位', editing_protection: '编辑防护', other: '其他',
}
const attrLabels = { sh_only: '仅SH', mixed: '混合', auxiliary: '辅助属性', other: '其他' }
const injLabels = {
  per_asset_finetune: '逐资产微调', generalizable_mapping: '可泛化映射',
  generation_embedded: '生成内嵌入', other: '其他',
}
const ATTACKS = [
  ['geometric_transform', '几何变换'], ['photometric', '光度变换'], ['signal_degradation', '信号退化'],
  ['pruning', '剪枝'], ['cloning', '克隆'], ['spatial_transform', '空间变换'],
  ['noise_injection', '噪声注入'], ['quantization', '量化'], ['parameter_merging', '参数合并'],
]

// ============================================================================
//  L15 · Ballot Tally：任务类型（viewBox 840×268）
// ============================================================================
const taskRows = computed(() => {
  const byTask = stats.value.by_task_type || {}
  return Object.entries(byTask)
    .map(([k, v]) => ({ name: taskLabels[k] || k, v }))
    .sort((a, b) => b.v - a.v)
})

const tallyNodes = computed(() => {
  const total = stats.value.total || 0
  if (!total) return []
  const nodes = []
  taskRows.value.forEach(({ name, v }, i) => {
    const base = 66 + i * 42
    const pct = Math.round(v / total * 100)
    nodes.push({ t: 'text', a: { x: 28, y: base - 26, 'font-size': 9, 'font-weight': 700, fill: MUTED, 'letter-spacing': '.08em' }, s: name, anim: 'a-fade', d: `${i * 0.1}s` })
    nodes.push({ t: 'line', a: { x1: 28, y1: base, x2: 812, y2: base, stroke: GRID, 'stroke-width': 0.6 }, anim: 'a-fade', d: `${i * 0.1}s` })
    for (let k = 0; k < 100; k++) {
      const x = 28 + k * 7.84
      const picked = k < pct
      const h = picked ? 12 + rnd(k + 1, i + 2) * 5 : 4.5 + rnd(k + 1, i + 5) * 2
      nodes.push({
        t: 'line',
        a: { x1: x, y1: base, x2: x, y2: base - h, stroke: picked ? INK : '#CFCEC7', 'stroke-width': picked ? 0.9 : 0.55 },
        anim: 'a-fade', d: `${i * 0.1 + k * 0.006}s`,
      })
      if (k % 10 === 0) nodes.push({ t: 'circle', a: { cx: x, cy: base + 4.5, r: 0.8, fill: '#C6C5BF' }, anim: 'a-fade', d: `${i * 0.1 + k * 0.006}s` })
    }
    // 数值标在上墨边界后，paint-order 描边保证压线可读
    const lx = 28 + Math.max(pct, 1) * 7.84 + 9
    nodes.push({
      t: 'text',
      a: { x: Math.min(lx, 792), y: base - 11, 'font-size': 11, 'font-weight': 800, fill: INK, style: `paint-order:stroke;stroke:${PAPER};stroke-width:3px` },
      s: `${v} 篇 · ${pct}%`, tip: `${name}：${v} / ${total} 篇（一篇可属多类）`, anim: 'a-fade', d: `${0.5 + i * 0.1}s`,
    })
  })
  return nodes
})

// ============================================================================
//  F1 · Rung Bars：收录年份（viewBox 400×300）
// ============================================================================
const rungNodes = computed(() => {
  const byYear = stats.value.by_year || {}
  const years = Object.keys(byYear).sort()
  if (!years.length) return []
  const nodes = []
  const base = 252
  const max = Math.max(...Object.values(byYear))
  const step = Math.min(5.6, 200 / max)          // 檔高自适应，绝不断轴
  const spacing = Math.min(72, 288 / years.length)
  const x0 = (i) => 200 - spacing * (years.length - 1) / 2 + i * spacing
  const HW = 14
  years.forEach((year, i) => {
    const v = byYear[year]
    const x = x0(i)
    for (let k = 0; k < v; k++) {
      const y = base - k * step
      const w = HW - 1.5 + rnd(k + 1, i + 2) * 3
      nodes.push({
        t: 'line',
        a: { x1: x - w, y1: y, x2: x + w, y2: y, stroke: INK, 'stroke-width': 1, opacity: 0.5 + rnd(k + 2, i + 4) * 0.5 },
        anim: 'a-fade', d: `${i * 0.08 + k * 0.012}s`,
      })
      if (k % 5 === 4) nodes.push({ t: 'circle', a: { cx: x + HW + 4.5, cy: y, r: 0.8, fill: '#C6C5BF' }, anim: 'a-fade', d: `${i * 0.08 + k * 0.012}s` })
    }
    nodes.push({
      t: 'text', a: { x, y: base - (v - 1) * step - 10, 'font-size': 11, 'font-weight': 800, fill: INK, 'text-anchor': 'middle' },
      s: v, tip: `${year} 年 — ${v} 篇`, anim: 'a-fade', d: `${0.4 + i * 0.08}s`,
    })
    nodes.push({ t: 'text', a: { x, y: base + 18, 'font-size': 8, 'font-weight': 700, fill: MUTED, 'text-anchor': 'middle', 'letter-spacing': '.08em' }, s: year, anim: 'a-fade', d: `${i * 0.08}s` })
  })
  nodes.push({ t: 'line', a: { x1: 28, y1: base + 4, x2: 372, y2: base + 4, stroke: GRID, 'stroke-width': 0.8 }, anim: 'a-fade', d: '0s' })
  nodes.push({ t: 'text', a: { x: 200, y: 288, 'font-size': 7, 'font-weight': 600, fill: FAINT, 'text-anchor': 'middle', 'letter-spacing': '.12em' }, s: 'ONE RUNG = ONE PAPER · DOT MARKS EVERY FIFTH', anim: 'a-fade', d: '0.9s' })
  return nodes
})

// ============================================================================
//  F4 · Tick Donut：属性选择构成（viewBox 400×300）
// ============================================================================
const attrSegments = computed(() => {
  const byAttr = stats.value.by_attribute || {}
  const segs = Object.entries(byAttr)
    .filter(([, v]) => v > 0)
    .map(([k, v]) => ({ name: attrLabels[k] || k, v }))
    .sort((a, b) => b.v - a.v)
  const sum = segs.reduce((s, x) => s + x.v, 0)
  if (!sum) return { segs: [], sum: 0 }
  // 四舍五入到整格：最大段吃差值，小但有量的段保底 1 格
  let acc = 0
  segs.forEach((s) => { s.pct = Math.max(1, Math.round(s.v / sum * 100)); acc += s.pct })
  segs[0].pct += 100 - acc
  return { segs, sum }
})

const attrSum = computed(() => attrSegments.value.sum)
const attrTop = computed(() => attrSegments.value.segs[0] || { name: '—', pct: 0 })

const donutNodes = computed(() => {
  const { segs, sum } = attrSegments.value
  if (!sum) return []
  const nodes = []
  const cx = 200, cy = 140, R0 = 64
  let k0 = 0
  segs.forEach((seg, si) => {
    const shade = L[si % L.length]
    for (let k = 0; k < seg.pct; k++) {
      const idx = k0 + k
      const a = idx * 3.6 - 90
      const len = 10 + rnd(idx + 1, si + 2) * 6
      const [x1, y1] = pol(cx, cy, R0, a)
      const [x2, y2] = pol(cx, cy, R0 + len, a)
      nodes.push({ t: 'line', a: { x1, y1, x2, y2, stroke: shade, 'stroke-width': 1 }, anim: 'a-fade', d: `${idx * 0.012}s` })
      if (idx % 10 === 0) {
        const [dx, dy] = pol(cx, cy, R0 - 5, a)
        nodes.push({ t: 'circle', a: { cx: dx, cy: dy, r: 0.8, fill: '#C6C5BF' }, anim: 'a-fade', d: `${idx * 0.012}s` })
      }
    }
    // 段标签：中角 + 虚线牵引
    const mid = (k0 + seg.pct / 2) * 3.6 - 90
    const [lx, ly] = pol(cx, cy, R0 + 38, mid)
    const [gx, gy] = pol(cx, cy, R0 + 20, mid)
    nodes.push({ t: 'line', a: { x1: gx, y1: gy, x2: lx, y2: ly, stroke: '#C6C5BF', 'stroke-width': 0.7, 'stroke-dasharray': '1 3' }, anim: 'a-fade', d: `${0.6 + si * 0.1}s` })
    const anchor = Math.cos(mid * D2R) > 0.3 ? 'start' : Math.cos(mid * D2R) < -0.3 ? 'end' : 'middle'
    nodes.push({
      t: 'text',
      a: { x: lx, y: ly + 3, 'font-size': 8, 'font-weight': 800, fill: shade, 'text-anchor': anchor, 'letter-spacing': '.06em', style: `paint-order:stroke;stroke:${PAPER};stroke-width:3px` },
      s: `${seg.name} ${seg.pct}%`, tip: `${seg.name} — ${seg.v} / ${sum} 篇`, anim: 'a-fade', d: `${0.65 + si * 0.1}s`,
    })
    k0 += seg.pct
  })
  nodes.push({ t: 'text', a: { x: cx, y: cy - 2, 'font-size': 22, 'font-weight': 800, fill: INK, 'text-anchor': 'middle' }, s: sum, anim: 'a-fade', d: '0.9s' })
  nodes.push({ t: 'text', a: { x: cx, y: cy + 14, 'font-size': 7, 'font-weight': 600, fill: MUTED, 'text-anchor': 'middle', 'letter-spacing': '.1em' }, s: '篇已标注属性', anim: 'a-fade', d: '0.9s' })
  nodes.push({ t: 'text', a: { x: 200, y: 288, 'font-size': 7, 'font-weight': 600, fill: FAINT, 'text-anchor': 'middle', 'letter-spacing': '.12em' }, s: "TWELVE O'CLOCK IS ZERO · READS CLOCKWISE", anim: 'a-fade', d: '1.1s' })
  return nodes
})

// ============================================================================
//  F5 · Tick Rows：注入管道（viewBox 400×300）
// ============================================================================
const injRows = computed(() => {
  const byInj = stats.value.by_injection || {}
  return Object.entries(byInj)
    .map(([k, v]) => ({ name: injLabels[k] || k, v }))
    .sort((a, b) => b.v - a.v)
})

const rowNodes = computed(() => {
  const rows = injRows.value
  if (!rows.length) return []
  const nodes = []
  const max = Math.max(...rows.map((r) => r.v))
  const X0 = 108
  const PX = Math.min(6.9, 250 / max)
  rows.forEach(({ name, v }, i) => {
    const y = 56 + i * 52
    nodes.push({ t: 'text', a: { x: 98, y: y + 3, 'font-size': 8, 'font-weight': 700, fill: MUTED, 'text-anchor': 'end', 'letter-spacing': '.08em' }, s: name, anim: 'a-fade', d: `${i * 0.08}s` })
    nodes.push({ t: 'line', a: { x1: X0, y1: y + 9, x2: X0 + max * PX, y2: y + 9, stroke: GRID, 'stroke-width': 0.6 }, anim: 'a-fade', d: `${i * 0.08}s` })
    for (let k = 0; k < v; k++) {
      const x = X0 + k * PX + PX / 2
      const h = 9 + rnd(k + 1, i + 2) * 6
      nodes.push({
        t: 'line',
        a: { x1: x, y1: y + 9, x2: x, y2: y + 9 - h, stroke: INK, 'stroke-width': 0.9, opacity: 0.55 + rnd(k + 3, i + 5) * 0.45 },
        anim: 'a-fade', d: `${i * 0.08 + k * 0.012}s`,
      })
      if (k % 5 === 4) nodes.push({ t: 'circle', a: { cx: x, cy: y + 13, r: 0.8, fill: '#C6C5BF' }, anim: 'a-fade', d: `${i * 0.08 + k * 0.012}s` })
    }
    nodes.push({
      t: 'text', a: { x: X0 + v * PX + 10, y: y + 4, 'font-size': 11, 'font-weight': 800, fill: INK },
      s: v, tip: `${name} — ${v} 篇`, anim: 'a-fade', d: `${0.4 + i * 0.08}s`,
    })
  })
  nodes.push({ t: 'text', a: { x: 200, y: 288, 'font-size': 7, 'font-weight': 600, fill: FAINT, 'text-anchor': 'middle', 'letter-spacing': '.12em' }, s: 'ONE TICK = ONE PAPER · DOT MARKS EVERY FIFTH', anim: 'a-fade', d: '0.9s' })
  return nodes
})

// ============================================================================
//  F10 · Dot Heat：属性 × 注入交叉（viewBox 400×300，前端实算真数据）
// ============================================================================
const ATTR_KEYS = ['sh_only', 'mixed', 'auxiliary', 'other']
const INJ_KEYS = ['per_asset_finetune', 'generalizable_mapping', 'generation_embedded', 'other']

const crossTab = computed(() => {
  const tab = ATTR_KEYS.map(() => INJ_KEYS.map(() => 0))
  for (const p of papersAll.value) {
    const ai = ATTR_KEYS.indexOf(p.attribute_selection)
    const ji = INJ_KEYS.indexOf(p.injection_pipeline)
    if (ai >= 0 && ji >= 0) tab[ai][ji]++
  }
  return tab
})

const crossMax = computed(() => Math.max(0, ...crossTab.value.flat()))

const crossPeak = computed(() => {
  const max = crossMax.value
  if (!max) return { label: '—' }
  const tab = crossTab.value
  for (let i = 0; i < 4; i++) for (let j = 0; j < 4; j++) {
    if (tab[i][j] === max) return { label: `${attrLabels[ATTR_KEYS[i]]} × ${injLabels[INJ_KEYS[j]]}`, i, j, v: max }
  }
  return { label: '—' }
})

const crossNodes = computed(() => {
  if (!papersAll.value.length) return []
  const nodes = []
  const tab = crossTab.value
  const max = crossMax.value
  const x0 = (j) => 116 + j * 72
  const y0 = (i) => 62 + i * 50
  const peak = crossPeak.value
  ATTR_KEYS.forEach((k, i) => {
    nodes.push({ t: 'text', a: { x: 104, y: y0(i) + 3, 'font-size': 8, 'font-weight': 700, fill: MUTED, 'text-anchor': 'end', 'letter-spacing': '.08em' }, s: attrLabels[k], anim: 'a-fade', d: `${i * 0.05}s` })
  })
  INJ_KEYS.forEach((k, j) => {
    nodes.push({ t: 'text', a: { x: x0(j), y: 252, 'font-size': 7.5, 'font-weight': 600, fill: MUTED, 'text-anchor': 'middle' }, s: injLabels[k], anim: 'a-fade', d: `${j * 0.05}s` })
  })
  tab.forEach((row, i) => row.forEach((v, j) => {
    const x = x0(j), y = y0(i)
    const delay = `${i * 0.05 + j * 0.03}s`
    if (!v) {
      nodes.push({ t: 'circle', a: { cx: x, cy: y, r: 0.8, fill: '#D8D6CE' }, anim: 'a-pop', d: delay })
      return
    }
    const r = 2 + Math.sqrt(v) * 5
    const fill = v > max * 0.66 ? INK : v > max * 0.33 ? '#6E7683' : '#B0AFA9'
    nodes.push({
      t: 'circle', a: { cx: x, cy: y, r, fill }, anim: 'a-pop', d: delay,
      tip: `${attrLabels[ATTR_KEYS[i]]} × ${injLabels[INJ_KEYS[j]]} — ${v} 篇`,
    })
    if (peak.i === i && peak.j === j) {
      nodes.push({ t: 'circle', a: { cx: x, cy: y, r: r + 3.4, fill: 'none', stroke: INK, 'stroke-width': 1, 'stroke-dasharray': '2 3' }, anim: 'a-fade', d: '1s' })
      nodes.push({ t: 'text', a: { x, y: y - r - 7, 'font-size': 8, 'font-weight': 800, fill: INK, 'text-anchor': 'middle' }, s: v, anim: 'a-fade', d: '1s' })
    }
  }))
  nodes.push({ t: 'text', a: { x: 200, y: 288, 'font-size': 7, 'font-weight': 600, fill: FAINT, 'text-anchor': 'middle', 'letter-spacing': '.12em' }, s: 'DOT AREA = PAPERS · DASHED RING = THE PEAK · TINY DOT = EMPTY', anim: 'a-fade', d: '1.1s' })
  return nodes
})

// ============================================================================
//  攻击覆盖矩阵：论文 × 9 攻击（二元，行按覆盖数降序）
// ============================================================================
const matrixRows = computed(() => {
  return [...robustnessData.value]
    .map((p) => ({ ...p, covered: ATTACKS.filter(([k]) => p.robustness_targets.includes(k)).length }))
    .sort((a, b) => b.covered - a.covered)
})

const attackCounts = computed(() => {
  return ATTACKS.map(([k]) => robustnessData.value.filter((p) => p.robustness_targets.includes(k)).length)
})

const matrixHeight = computed(() => 108 + matrixRows.value.length * 22 + 44)

const matrixNodes = computed(() => {
  const rows = matrixRows.value
  if (!rows.length) return []
  const nodes = []
  const x0 = (j) => 232 + j * 66
  const top = 96
  // 列头：攻击名，-55° 旋转（L4 语法）
  ATTACKS.forEach(([k, label], j) => {
    const x = x0(j)
    nodes.push({
      t: 'text',
      a: { x, y: 66, 'font-size': 8, 'font-weight': 700, fill: MUTED, 'letter-spacing': '.06em', transform: `rotate(-55 ${x} 66)` },
      s: label, anim: 'a-fade', d: `${j * 0.03}s`,
    })
  })
  rows.forEach((p, i) => {
    const y = top + i * 22
    const title = p.title.length > 20 ? p.title.slice(0, 20) + '…' : p.title
    nodes.push({
      t: 'text', a: { x: 222, y: y + 3, 'font-size': 8, 'font-weight': p.covered ? 600 : 400, fill: p.covered ? '#4A5060' : FAINT, 'text-anchor': 'end' },
      s: title, tip: `${p.title}${p.arxiv_id ? ` (${p.arxiv_id})` : ''} — 覆盖 ${p.covered}/9 种攻击`, anim: 'a-fade', d: `${i * 0.03}s`,
    })
    nodes.push({ t: 'line', a: { x1: 228, y1: y, x2: 772, y2: y, stroke: '#EFEEE8', 'stroke-width': 0.5 }, anim: 'a-fade', d: `${i * 0.03}s` })
    ATTACKS.forEach(([k, label], j) => {
      const hit = p.robustness_targets.includes(k)
      nodes.push({
        t: 'circle',
        a: hit ? { cx: x0(j), cy: y, r: 3.2, fill: INK } : { cx: x0(j), cy: y, r: 0.8, fill: '#D8D6CE' },
        anim: 'a-pop', d: `${i * 0.03 + j * 0.012}s`,
        tip: `${title} — ${label}: ${hit ? '✓ 已评估' : '未评估'}`,
      })
    })
  })
  // 底行：每种攻击的覆盖篇数
  const by = top + rows.length * 22 + 20
  nodes.push({ t: 'text', a: { x: 222, y: by + 3, 'font-size': 8, 'font-weight': 700, fill: MUTED, 'text-anchor': 'end', 'letter-spacing': '.06em' }, s: 'Σ 覆盖篇数', anim: 'a-fade', d: '0.6s' })
  attackCounts.value.forEach((c, j) => {
    nodes.push({ t: 'text', a: { x: x0(j), y: by + 3, 'font-size': 9, 'font-weight': 800, fill: INK, 'text-anchor': 'middle' }, s: c, anim: 'a-fade', d: `${0.6 + j * 0.03}s` })
  })
  return nodes
})
</script>

<style scoped>
.dashboard-view {
  max-width: 1200px;
  margin: 0 auto;
  padding: var(--space-xl) var(--space-lg);
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

/* ===== 页头 ===== */
.page-header {
  margin-bottom: var(--space-sm);
}
.page-heading {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.page-title {
  font-family: var(--font-serif);
  font-size: 32px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: 0.01em;
}
.page-intro {
  font-size: 13px;
  color: var(--text-secondary);
}

/* ===== KPI 数字行 ===== */
.stats-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-md);
}
.stat-plate {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 18px 20px;
}
.stat-number {
  font-family: var(--font-display);
  font-size: 40px;
  font-weight: 600;
  color: var(--accent);
  line-height: 1;
}
.stat-number.warn { color: var(--warm); }
.stat-number.ok { color: var(--success); }
.stat-label {
  font-family: var(--font-mono);
  font-size: 11px;
  letter-spacing: 0.08em;
  color: var(--text-tertiary);
}
@media (max-width: 640px) {
  .stats-row { grid-template-columns: 1fr; }
}

/* ===== 图表卡：mono 四件套（结论标题 + 副标题 + 图 + 来源行）=====
   卡片容器沿用站内 plate，视觉骨架按 lieflat-charts 规范 */
.chart-card {
  padding: 24px 26px 16px;
}
.chart-title {
  font-family: var(--font-serif);
  font-size: 17px;
  font-weight: 600;
  letter-spacing: 0.01em;
  color: var(--text-primary);
  margin-bottom: 3px;
}
.chart-sub {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 14px;
}
.chart-src {
  margin-top: 10px;
  font-family: var(--font-mono);
  font-size: 9px;
  font-weight: 500;
  letter-spacing: 0.1em;
  color: var(--text-tertiary);
}
.chart {
  display: block;
  width: 100%;
  height: auto;
}
.chart :deep(text) {
  font-family: 'Inter', sans-serif;
}

.charts-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-md);
}
@media (max-width: 900px) {
  .charts-grid { grid-template-columns: 1fr; }
}

/* 矩阵横向可滚（窄屏不挤压） */
.matrix-scroll {
  overflow-x: auto;
}
.matrix {
  min-width: 720px;
}

/* ===== mono 动画：fade / pop，进视野才播（.is-revealed 由 v-reveal 添加）==== */
@keyframes mono-fade {
  from { opacity: 0; }
  to { opacity: 1; }
}
@keyframes mono-pop {
  from { transform: scale(0); }
  to { transform: none; }
}
.a-fade {
  animation: mono-fade 0.9s ease both;
  animation-play-state: paused;
}
.a-pop {
  transform-box: fill-box;
  transform-origin: center;
  animation: mono-pop 0.5s cubic-bezier(0.2, 0.7, 0.3, 1.3) both;
  animation-play-state: paused;
}
.is-revealed .a-fade,
.is-revealed .a-pop {
  animation-play-state: running;
}
@media (prefers-reduced-motion: reduce) {
  .a-fade, .a-pop { animation: none; }
}

/* 空状态 */
.empty-plate {
  padding: var(--space-2xl);
  text-align: center;
  color: var(--text-secondary);
  font-size: 14px;
}
</style>
