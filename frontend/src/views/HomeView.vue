<template>
  <div class="home-view">
    <!-- ===== Hero（深色 + 高斯泼溅场）===== -->
    <section class="hero">
      <GaussParticles />

      <div class="hero-content">
        <div class="hero-eyebrow hero-in" :style="{ '--d': 0 }">3D Gaussian Splatting · Watermarking Archive</div>
        <h1 class="hero-title hero-in" :style="{ '--d': 1 }">水印与 IP 保护<br/>论文知识库</h1>
        <p class="hero-subtitle hero-in" :style="{ '--d': 2 }">
          追踪 3DGS 资产知识产权保护方向的研究进展——水印、隐写、篡改定位、编辑防护
        </p>

        <!-- 底栏：左统计、右入口，像档案卡的落款行 -->
        <div class="hero-bottom hero-in" :style="{ '--d': 3 }">
          <div class="hero-stats" v-if="stats.total">
            <div class="hero-stat">
              <span class="hero-stat-number">{{ totalDisplay }}</span>
              <span class="hero-stat-label">收录论文</span>
            </div>
            <div class="hero-stat">
              <span class="hero-stat-number">{{ recentDisplay }}</span>
              <span class="hero-stat-label">近 30 天</span>
            </div>
            <div class="hero-stat">
              <span class="hero-stat-number warn">{{ autoDisplay }}</span>
              <span class="hero-stat-label">待复核</span>
            </div>
          </div>
          <div class="hero-actions">
            <router-link to="/papers" class="hero-cta">浏览论文库 →</router-link>
            <router-link to="/dashboard" class="hero-link">统计仪表盘</router-link>
          </div>
        </div>
      </div>

      <!-- 右侧竖排题字：典藏室的边款 -->
      <span class="hero-side-note" aria-hidden="true">三维高斯泼溅 · 数字水印典藏</span>
    </section>

    <!-- ===== 追踪范围（分类法索引条）===== -->
    <section class="scope-strip" v-reveal>
      <div class="scope-inner">
        <div class="scope-heading">
          <span class="eyebrow">Scope</span>
          <span class="scope-title">追踪范围</span>
        </div>
        <div class="scope-items">
          <router-link
            v-for="item in scopeItems"
            :key="item.value"
            to="/papers"
            class="scope-item"
          >
            <span class="scope-cn">{{ item.label }}</span>
            <span class="scope-count">{{ scopeCount(item.value) }}</span>
            <span class="scope-en">{{ item.en }}</span>
          </router-link>
        </div>
      </div>
    </section>

    <!-- ===== 最新收录（编目行）===== -->
    <section class="recent-section">
      <div class="section-inner">
        <div class="section-header" v-reveal>
          <div class="section-heading">
            <span class="eyebrow">Recent</span>
            <h2 class="section-title">最新收录</h2>
          </div>
          <router-link to="/papers" class="section-link">全部 →</router-link>
        </div>

        <div class="recent-list" v-loading="loading">
          <router-link
            v-for="(paper, i) in recentPapers"
            :key="paper.id"
            v-reveal="i * 60"
            :to="`/papers/${paper.id}`"
            class="recent-row"
          >
            <span class="recent-year">{{ formatYear(paper.pub_date) }}</span>
            <div class="recent-main">
              <h3 class="recent-title">{{ paper.title }}</h3>
              <p class="recent-meta">
                {{ paper.authors.slice(0, 3).join(', ') }}{{ paper.authors.length > 3 ? ' et al.' : '' }}
                — {{ truncate(paper.abstract, 80) }}
              </p>
            </div>
            <div class="recent-side">
              <span v-for="t in paper.task_type" :key="t" class="mini-tag">{{ taskLabel(t) }}</span>
              <StatusSeal :status="paper.curation_status" />
            </div>
            <span class="recent-arrow">→</span>
          </router-link>
        </div>

        <!-- 空状态 -->
        <div v-if="!loading && !recentPapers.length" class="empty-state">
          还没有论文。去 <router-link to="/papers">论文列表</router-link> 手动添加或触发 AI 检索。
        </div>
      </div>
    </section>

    <!-- ===== 知识库概览（档案板图表）===== -->
    <section class="overview-section" v-if="stats.total">
      <div class="section-inner">
        <div class="section-header" v-reveal>
          <div class="section-heading">
            <span class="eyebrow">Overview</span>
            <h2 class="section-title">知识库概览</h2>
          </div>
          <router-link to="/dashboard" class="section-link">完整仪表盘 →</router-link>
        </div>

        <div class="overview-grid">
          <!-- 时间线 mini 图 -->
          <div class="plate" v-reveal>
            <div class="plate-header">
              <span class="plate-title">收录年份</span>
              <span class="plate-note">By year</span>
            </div>
            <div class="plate-body">
              <div class="year-bars">
                <div
                  v-for="year in sortedYears"
                  :key="year"
                  class="year-bar-item"
                >
                  <div class="year-bar-track">
                    <div
                      class="year-bar-fill"
                      :style="{ height: barHeight(year) + '%' }"
                    ></div>
                  </div>
                  <span class="year-bar-label">{{ year }}</span>
                  <span class="year-bar-value">{{ stats.by_year[year] }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 任务类型分布 -->
          <div class="plate" v-reveal="100">
            <div class="plate-header">
              <span class="plate-title">任务分布</span>
              <span class="plate-note">By task</span>
            </div>
            <div class="plate-body">
              <div class="task-rows">
                <div v-for="(count, type) in sortedTasks" :key="type" class="task-row">
                  <span class="task-name">{{ taskLabel(type) }}</span>
                  <div class="task-bar">
                    <div class="task-fill" :style="{ width: tagWidth(count) + '%' }"></div>
                  </div>
                  <span class="task-count">{{ count }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { statsApi } from '../api/stats'
import { papersApi } from '../api/papers'
import { useTheme } from '../composables/useTheme'
import { useCountUp } from '../composables/useCountUp'
import GaussParticles from '../components/GaussParticles.vue'
import StatusSeal from '../components/StatusSeal.vue'

// 首页与全站统一浅色主题；Hero 的水墨高斯场配色取自 token（墨蓝/朱砂）。
useTheme('light')

const stats = ref({})
const recentPapers = ref([])
const loading = ref(true)

onMounted(async () => {
  try {
    const [overview, papers] = await Promise.all([
      statsApi.getOverview(),
      // 拉最新 6 篇（按入库时间倒序）
      papersApi.list({ limit: 6, sort_by: 'added_at', order: 'desc' }),
    ])
    stats.value = overview
    recentPapers.value = papers.items
  } catch (e) {
    console.error('加载首页数据失败:', e)
  } finally {
    loading.value = false
  }
})

// 近 30 天新增数：后端没返回精确数字，用最近论文数近似展示
const recentCount = computed(() => recentPapers.value.length)

// Hero 数字滚动：数据异步到达后从 0 缓动到目标值
const totalDisplay = useCountUp(() => stats.value.total)
const recentDisplay = useCountUp(() => recentCount.value)
const autoDisplay = useCountUp(() => stats.value.by_curation?.auto)

// ---- 追踪范围索引条 ----
// 分类法的四个主任务类型 + 计数，点击进论文库
const scopeItems = [
  { value: 'watermarking', label: '水印', en: 'Watermarking' },
  { value: 'steganography', label: '隐写', en: 'Steganography' },
  { value: 'tamper_localization', label: '篡改定位', en: 'Tamper Localization' },
  { value: 'editing_protection', label: '编辑防护', en: 'Editing Protection' },
]
function scopeCount(value) {
  const n = stats.value.by_task_type?.[value] || 0
  return String(n).padStart(2, '0')
}

// 年份排序
const sortedYears = computed(() => {
  const years = Object.keys(stats.value.by_year || {})
  return years.sort()
})

// 任务类型按数量排序
const sortedTasks = computed(() => {
  const entries = Object.entries(stats.value.by_task_type || {})
  entries.sort((a, b) => b[1] - a[1])
  return Object.fromEntries(entries)
})

// 柱状图高度百分比
function barHeight(year) {
  const max = Math.max(...Object.values(stats.value.by_year || { [year]: 1 }))
  return (stats.value.by_year?.[year] || 0) / max * 100
}

// 标签条宽度百分比
function tagWidth(count) {
  const max = Math.max(...Object.values(stats.value.by_task_type || {}))
  return count / max * 100
}

// ---- 工具函数 ----
const taskLabels = {
  watermarking: '水印', steganography: '隐写',
  tamper_localization: '篡改定位', editing_protection: '编辑防护', other: '其他',
}
function taskLabel(t) { return taskLabels[t] || t }

function formatYear(dateStr) {
  if (!dateStr) return '—'
  return String(dateStr).slice(0, 4)
}

function truncate(text, len) {
  if (!text) return ''
  return text.length > len ? text.slice(0, len) + '…' : text
}
</script>

<style scoped>
.home-view {
  min-height: 100vh;
}

/* ===== Hero（浅色 + 水墨高斯场，全部取自 token）===== */
.hero {
  position: relative;
  background: var(--bg-base);
  min-height: max(560px, 78vh);
  display: flex;
  align-items: center;
  overflow: hidden;
}

.hero-content {
  position: relative;
  z-index: 2;
  max-width: 1200px;
  margin: 0 auto;
  padding: var(--space-2xl) var(--space-lg);
  width: 100%;
}

/* Hero 入场编排：eyebrow → 标题 → 副标题 → 底栏，交错上浮 */
@keyframes hero-rise {
  from { opacity: 0; transform: translateY(22px); }
  to { opacity: 1; transform: translateY(0); }
}
.hero-in {
  opacity: 0;
  animation: hero-rise 0.85s var(--ease-out) forwards;
  animation-delay: calc(80ms + var(--d, 0) * 90ms);
}

.hero-eyebrow {
  display: flex;
  align-items: center;
  gap: 10px;
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--accent);
  letter-spacing: 0.14em;
  text-transform: uppercase;
  margin-bottom: var(--space-lg);
}
.hero-eyebrow::before {
  content: '';
  width: 28px;
  height: 1px;
  background: var(--accent);
  opacity: 0.6;
}

.hero-title {
  font-family: var(--font-serif);
  font-size: clamp(42px, 6vw, 76px);
  font-weight: 700;
  line-height: 1.18;
  color: var(--text-primary);
  margin-bottom: var(--space-lg);
  /* 宋体标题：字距放宽一点更有碑刻感 */
  letter-spacing: 0.02em;
}

.hero-subtitle {
  font-size: 15px;
  line-height: 1.8;
  color: var(--text-secondary);
  max-width: 520px;
}

/* 右侧竖排题字 */
.hero-side-note {
  position: absolute;
  right: 28px;
  top: 50%;
  transform: translateY(-50%);
  z-index: 2;
  writing-mode: vertical-rl;
  font-family: var(--font-serif);
  font-size: 13px;
  letter-spacing: 0.35em;
  color: var(--text-tertiary);
  user-select: none;
}
@media (max-width: 1100px) {
  .hero-side-note { display: none; }
}

/* 底栏：hairline 上的落款行 */
.hero-bottom {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: var(--space-lg);
  flex-wrap: wrap;
  margin-top: var(--space-2xl);
  padding-top: var(--space-lg);
  border-top: 0.5px solid var(--border-default);
}

.hero-stats {
  display: flex;
  gap: var(--space-xl);
}
.hero-stat {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.hero-stat-number {
  font-family: var(--font-display);
  font-size: 32px;
  font-weight: 600;
  color: var(--accent);
  line-height: 1;
}
.hero-stat-number.warn {
  color: var(--warm);
}
.hero-stat-label {
  font-family: var(--font-mono);
  font-size: 11px;
  letter-spacing: 0.08em;
  color: var(--text-tertiary);
}

.hero-actions {
  display: flex;
  gap: var(--space-lg);
  align-items: center;
}
.hero-cta {
  display: inline-block;
  padding: 10px 22px;
  background: var(--accent);
  color: var(--bg-base);
  font-size: 14px;
  font-weight: 500;
  border-radius: var(--radius-sm);
  text-decoration: none;
  transition: background var(--transition), transform var(--transition), box-shadow var(--transition);
}
.hero-cta:hover {
  background: var(--accent-hover);
  color: var(--bg-base);
  transform: translateY(-1px);
  box-shadow: 0 8px 24px -8px rgba(46, 74, 107, 0.4);
}
.hero-link {
  font-size: 14px;
  color: var(--text-secondary);
  text-decoration: none;
  transition: color var(--transition);
}
.hero-link::after {
  content: '→';
  display: inline-block;
  margin-left: 4px;
  transition: transform var(--transition);
}
.hero-link:hover {
  color: var(--text-primary);
}
.hero-link:hover::after {
  transform: translateX(3px);
}

/* ===== 追踪范围索引条 ===== */
.scope-strip {
  background: var(--bg-surface);
  border-bottom: 0.5px solid var(--border-subtle);
}
.scope-inner {
  max-width: 1200px;
  margin: 0 auto;
  padding: var(--space-lg);
  display: flex;
  align-items: center;
  gap: var(--space-2xl);
}
.scope-heading {
  flex: none;
  display: flex;
  flex-direction: column;
  gap: 3px;
}
.scope-title {
  font-family: var(--font-serif);
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}
.scope-items {
  flex: 1;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
}
.scope-item {
  display: grid;
  grid-template-columns: 1fr auto;
  align-items: baseline;
  column-gap: 8px;
  padding: 6px 20px;
  border-left: 0.5px solid var(--border-subtle);
  text-decoration: none;
  transition: background var(--transition);
}
.scope-item:first-child {
  border-left: none;
}
.scope-item:hover {
  background: var(--bg-hover);
}
.scope-cn {
  font-family: var(--font-serif);
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  transition: color var(--transition);
}
.scope-item:hover .scope-cn {
  color: var(--accent);
}
.scope-count {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--text-tertiary);
}
.scope-en {
  grid-column: 1 / -1;
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-tertiary);
  margin-top: 2px;
}
@media (max-width: 860px) {
  .scope-inner { flex-direction: column; align-items: stretch; gap: var(--space-md); }
  .scope-items { grid-template-columns: repeat(2, 1fr); }
  .scope-item:nth-child(3) { border-left: none; }
}

/* ===== 通用 section 容器 ===== */
.section-inner {
  max-width: 1200px;
  margin: 0 auto;
  padding: var(--space-2xl) var(--space-lg) var(--space-xl);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: var(--space-lg);
}
.section-heading {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.section-title {
  font-family: var(--font-serif);
  font-size: 24px;
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: 0.01em;
}
.section-link {
  font-size: 13px;
  color: var(--accent);
  text-decoration: none;
  transition: color var(--transition);
}

/* ===== 最新收录：编目行 ===== */
.recent-list {
  border-top: 0.5px solid var(--border-strong);
}
.recent-row {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 18px 8px;
  border-bottom: 0.5px solid var(--border-subtle);
  text-decoration: none;
  transition: background var(--transition);
}
.recent-row:hover {
  background: var(--bg-surface);
}
.recent-year {
  flex: none;
  width: 44px;
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--accent);
}
.recent-main {
  flex: 1;
  min-width: 0;
}
.recent-title {
  font-family: var(--font-serif);
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.5;
  transition: color var(--transition);
}
.recent-row:hover .recent-title {
  color: var(--accent);
}
.recent-meta {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 3px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.recent-side {
  flex: none;
  display: flex;
  align-items: center;
  gap: 6px;
}
.recent-arrow {
  flex: none;
  color: var(--text-tertiary);
  transition: transform var(--transition), color var(--transition);
}
.recent-row:hover .recent-arrow {
  transform: translateX(4px);
  color: var(--accent);
}
@media (max-width: 760px) {
  .recent-meta { display: none; }
  .recent-side .mini-tag { display: none; }
}

/* ===== 知识库概览 ===== */
.overview-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-md);
}
@media (max-width: 768px) {
  .overview-grid { grid-template-columns: 1fr; }
}

/* mini 柱状图 */
.year-bars {
  display: flex;
  gap: var(--space-md);
  align-items: flex-end;
  height: 120px;
}
.year-bar-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  flex: 1;
}
.year-bar-track {
  width: 100%;
  flex: 1;
  display: flex;
  align-items: flex-end;
  background: var(--bg-hover);
  border-radius: 2px;
  overflow: hidden;
}
.year-bar-fill {
  width: 100%;
  background: var(--accent);
  border-radius: 2px;
  transition: height 0.5s var(--ease-out);
}
.year-bar-label {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-secondary);
}
.year-bar-value {
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 500;
  color: var(--text-primary);
}

/* 任务类型条 */
.task-rows {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.task-row {
  display: flex;
  align-items: center;
  gap: 10px;
}
.task-name {
  font-size: 12px;
  color: var(--text-secondary);
  width: 60px;
  flex-shrink: 0;
}
.task-bar {
  flex: 1;
  height: 6px;
  background: var(--bg-hover);
  border-radius: 3px;
  overflow: hidden;
}
.task-fill {
  height: 100%;
  background: var(--accent);
  border-radius: 3px;
  transition: width 0.5s var(--ease-out);
}
.task-count {
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 500;
  color: var(--text-primary);
  width: 24px;
  text-align: right;
}

/* 空状态 */
.empty-state {
  padding: var(--space-xl);
  text-align: center;
  color: var(--text-secondary);
  font-size: 14px;
}
</style>
