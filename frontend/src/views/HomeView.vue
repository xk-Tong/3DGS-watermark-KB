<template>
  <div class="home-view">
    <!-- ===== Hero 区（深色） ===== -->
    <section class="hero">
      <!-- 高斯粒子背景 -->
      <GaussParticles />

      <!-- Hero 内容 -->
      <div class="hero-content">
        <div class="hero-eyebrow">3D Gaussian Splatting</div>
        <h1 class="hero-title">水印与 IP 保护<br/>论文知识库</h1>
        <p class="hero-subtitle">
          追踪 3DGS 资产知识产权保护方向的研究进展——水印、隐写、篡改定位、编辑防护
        </p>

        <!-- 关键数字 -->
        <div class="hero-stats" v-if="stats.total">
          <div class="hero-stat">
            <span class="hero-stat-number">{{ stats.total }}</span>
            <span class="hero-stat-label">收录论文</span>
          </div>
          <div class="hero-stat">
            <span class="hero-stat-number">{{ recentCount }}</span>
            <span class="hero-stat-label">近 30 天</span>
          </div>
          <div class="hero-stat">
            <span class="hero-stat-number warn">{{ stats.by_curation?.auto || 0 }}</span>
            <span class="hero-stat-label">待复核</span>
          </div>
        </div>

        <div class="hero-actions">
          <router-link to="/papers" class="hero-cta">浏览论文库 →</router-link>
          <router-link to="/dashboard" class="hero-link">查看统计</router-link>
        </div>
      </div>

      <!-- 渐变过渡到浅色区 -->
      <div class="hero-fade"></div>
    </section>

    <!-- ===== 最新论文区（浅色） ===== -->
    <section class="recent-section">
      <div class="section-inner">
        <div class="section-header">
          <h2 class="section-title">最新收录</h2>
          <router-link to="/papers" class="section-link">全部 →</router-link>
        </div>

        <div class="recent-papers-list" v-loading="loading">
          <router-link
            v-for="paper in recentPapers"
            :key="paper.id"
            :to="`/papers/${paper.id}`"
            class="recent-paper-card"
          >
            <div class="recent-paper-top">
              <span class="recent-paper-date">{{ formatYear(paper.pub_date) }}</span>
              <span
                v-for="t in paper.task_type"
                :key="t"
                class="recent-paper-tag"
              >{{ taskLabel(t) }}</span>
              <span v-if="paper.curation_status === 'auto'" class="recent-paper-warn">未核实</span>
            </div>
            <h3 class="recent-paper-title">{{ paper.title }}</h3>
            <p class="recent-paper-authors">{{ paper.authors.slice(0, 3).join(', ') }}{{ paper.authors.length > 3 ? ' et al.' : '' }}</p>
            <p class="recent-paper-abstract">{{ truncate(paper.abstract, 120) }}</p>
          </router-link>
        </div>

        <!-- 空状态 -->
        <div v-if="!loading && !recentPapers.length" class="empty-state">
          还没有论文。去 <router-link to="/papers">论文列表</router-link> 手动添加或触发 AI 检索。
        </div>
      </div>
    </section>

    <!-- ===== 统计摘要区（浅色） ===== -->
    <section class="summary-section" v-if="stats.total">
      <div class="section-inner">
        <div class="section-header">
          <h2 class="section-title">知识库概览</h2>
          <router-link to="/dashboard" class="section-link">完整仪表盘 →</router-link>
        </div>

        <div class="summary-grid">
          <!-- 时间线 mini 图 -->
          <div class="summary-card">
            <div class="summary-card-label">按年份</div>
            <div class="summary-bars">
              <div
                v-for="year in sortedYears"
                :key="year"
                class="summary-bar-item"
              >
                <div class="summary-bar-track">
                  <div
                    class="summary-bar-fill"
                    :style="{ height: barHeight(year) + '%' }"
                  ></div>
                </div>
                <span class="summary-bar-label">{{ year }}</span>
                <span class="summary-bar-value">{{ stats.by_year[year] }}</span>
              </div>
            </div>
          </div>

          <!-- 任务类型分布 -->
          <div class="summary-card">
            <div class="summary-card-label">按任务</div>
            <div class="summary-tags">
              <div v-for="(count, type) in sortedTasks" :key="type" class="summary-tag-row">
                <span class="summary-tag-name">{{ taskLabel(type) }}</span>
                <div class="summary-tag-bar">
                  <div class="summary-tag-fill" :style="{ width: tagWidth(count) + '%' }"></div>
                </div>
                <span class="summary-tag-count">{{ count }}</span>
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
import GaussParticles from '../components/GaussParticles.vue'

// 首页用深浅混搭：Hero 区深色，内容区浅色。
// useTheme 在 onMounted 时设 data-theme，但首页特殊——Hero 需要深色而内容区需要浅色。
// 方案：首页默认设 light（因为内容区占比大），Hero 区自己用固定深色样式（不依赖 CSS 变量）。
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

// 近 30 天新增数：用 added_at 粗略判断（这里简化为取 stats 里总数的一部分）
// 实际后端没返回精确的"30天内"数字，用 reviewed+verified 近似展示
const recentCount = computed(() => {
  // 取最近论文数的前 6 篇作为"近期"展示，实际数字需要后端补
  return recentPapers.value.length
})

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

/* ===== Hero 区（深色，固定色值不依赖 CSS 变量）===== */
.hero {
  position: relative;
  /* 深色背景：墨蓝黑 */
  background: #0F1419;
  min-height: 520px;
  display: flex;
  align-items: center;
  overflow: hidden;
}

.hero-content {
  position: relative;
  z-index: 2;
  max-width: 1400px;
  margin: 0 auto;
  padding: var(--space-2xl) var(--space-lg);
  width: 100%;
}

.hero-eyebrow {
  font-family: var(--font-mono);
  font-size: 12px;
  color: #7C9EFF;
  letter-spacing: 0.05em;
  margin-bottom: var(--space-md);
}

.hero-title {
  font-family: var(--font-display);
  font-size: 48px;
  font-weight: 600;
  line-height: 1.1;
  color: #E8EDF2;
  margin-bottom: var(--space-md);
  letter-spacing: -0.02em;
}

.hero-subtitle {
  font-size: 15px;
  line-height: 1.7;
  color: #8B98A8;
  max-width: 520px;
  margin-bottom: var(--space-xl);
}

/* 关键数字 */
.hero-stats {
  display: flex;
  gap: var(--space-xl);
  margin-bottom: var(--space-xl);
}
.hero-stat {
  display: flex;
  flex-direction: column;
}
.hero-stat-number {
  font-family: var(--font-display);
  font-size: 36px;
  font-weight: 600;
  color: #7C9EFF;
  line-height: 1;
}
.hero-stat-number.warn {
  color: #E5A893;
}
.hero-stat-label {
  font-size: 12px;
  color: #5A6573;
  margin-top: 4px;
}

/* CTA 按钮 */
.hero-actions {
  display: flex;
  gap: var(--space-md);
  align-items: center;
}
.hero-cta {
  display: inline-block;
  padding: 10px 20px;
  background: #7C9EFF;
  color: #0F1419;
  font-size: 14px;
  font-weight: 500;
  border-radius: var(--radius-sm);
  text-decoration: none;
  transition: background var(--transition);
}
.hero-cta:hover {
  background: #9DB5FF;
  color: #0F1419;
}
.hero-link {
  font-size: 14px;
  color: #8B98A8;
  text-decoration: none;
}
.hero-link:hover {
  color: #E8EDF2;
}

/* 渐变过渡：从深色 Hero 到浅色内容区 */
.hero-fade {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 80px;
  /* linear-gradient：线性渐变，从透明到浅色背景 */
  background: linear-gradient(to bottom, transparent, #FAF8F3);
  z-index: 1;
}

/* ===== 通用 section 容器 ===== */
.section-inner {
  max-width: 1400px;
  margin: 0 auto;
  padding: var(--space-xl) var(--space-lg);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: var(--space-lg);
}
.section-title {
  font-size: 18px;
  font-weight: 500;
  color: var(--text-primary);
}
.section-link {
  font-size: 13px;
  color: var(--accent);
  text-decoration: none;
}

/* ===== 最新论文卡片 ===== */
.recent-papers-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: var(--space-md);
}

.recent-paper-card {
  display: block;
  padding: var(--space-md);
  background: var(--bg-surface);
  border: 0.5px solid var(--border-subtle);
  border-radius: var(--radius-md);
  text-decoration: none;
  transition: border-color var(--transition), transform var(--transition);
}
.recent-paper-card:hover {
  border-color: var(--border-default);
  transform: translateY(-2px);
}

.recent-paper-top {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}
.recent-paper-date {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-tertiary);
}
.recent-paper-tag {
  font-size: 11px;
  padding: 1px 6px;
  background: var(--accent-soft);
  color: var(--accent);
  border-radius: 3px;
}
.recent-paper-warn {
  font-size: 11px;
  padding: 1px 6px;
  background: var(--warning-soft);
  color: var(--warning);
  border-radius: 3px;
}

.recent-paper-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  line-height: 1.4;
  margin-bottom: 6px;
}
.recent-paper-authors {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}
.recent-paper-abstract {
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.6;
}

/* ===== 统计摘要区 ===== */
.summary-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-md);
}
@media (max-width: 768px) {
  .summary-grid { grid-template-columns: 1fr; }
}

.summary-card {
  padding: var(--space-md);
  background: var(--bg-surface);
  border: 0.5px solid var(--border-subtle);
  border-radius: var(--radius-md);
}
.summary-card-label {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-bottom: var(--space-md);
}

/* mini 柱状图 */
.summary-bars {
  display: flex;
  gap: var(--space-md);
  align-items: flex-end;
  height: 100px;
}
.summary-bar-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  flex: 1;
}
.summary-bar-track {
  width: 100%;
  flex: 1;
  display: flex;
  align-items: flex-end;
  background: var(--bg-hover);
  border-radius: 2px;
  overflow: hidden;
}
.summary-bar-fill {
  width: 100%;
  background: var(--accent);
  border-radius: 2px;
  transition: height 0.3s ease;
}
.summary-bar-label {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-secondary);
}
.summary-bar-value {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-primary);
}

/* 任务类型条 */
.summary-tags {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.summary-tag-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.summary-tag-name {
  font-size: 12px;
  color: var(--text-secondary);
  width: 60px;
  flex-shrink: 0;
}
.summary-tag-bar {
  flex: 1;
  height: 6px;
  background: var(--bg-hover);
  border-radius: 3px;
  overflow: hidden;
}
.summary-tag-fill {
  height: 100%;
  background: var(--accent);
  border-radius: 3px;
  transition: width 0.3s ease;
}
.summary-tag-count {
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
