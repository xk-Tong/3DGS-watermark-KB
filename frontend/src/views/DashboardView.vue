<template>
  <div class="dashboard-view" v-loading="loading">
    <header class="page-header" v-reveal>
      <div class="page-heading">
        <span class="eyebrow">Statistics</span>
        <h1 class="page-title">统计仪表盘</h1>
        <p class="page-intro">知识库分布与覆盖情况一览</p>
      </div>
    </header>

    <!-- 统计数字行 -->
    <div class="stats-row">
      <div class="plate stat-plate" v-reveal>
        <span class="stat-number">{{ stats.total || 0 }}</span>
        <span class="stat-label">收录论文</span>
      </div>
      <div class="plate stat-plate" v-reveal="60">
        <span class="stat-number warn">{{ stats.by_curation?.auto || 0 }}</span>
        <span class="stat-label">AI 未核实</span>
      </div>
      <div class="plate stat-plate" v-reveal="120">
        <span class="stat-number ok">{{ (stats.by_curation?.reviewed || 0) + (stats.by_curation?.verified || 0) }}</span>
        <span class="stat-label">已复核 / 验证</span>
      </div>
    </div>

    <!-- 图表网格：两列 -->
    <div class="charts-grid">
      <div class="plate" v-reveal>
        <div class="plate-header">
          <span class="plate-title">论文时间线</span>
          <span class="plate-note">By year</span>
        </div>
        <div class="plate-body">
          <EChartsBase :option="timelineOption" height="280px" />
        </div>
      </div>

      <div class="plate" v-reveal="60">
        <div class="plate-header">
          <span class="plate-title">任务类型分布</span>
          <span class="plate-note">By task</span>
        </div>
        <div class="plate-body">
          <EChartsBase :option="taskTypeOption" height="280px" />
        </div>
      </div>

      <div class="plate" v-reveal="120">
        <div class="plate-header">
          <span class="plate-title">属性选择机制</span>
          <span class="plate-note">Attribute</span>
        </div>
        <div class="plate-body">
          <EChartsBase :option="attributeOption" height="280px" />
        </div>
      </div>

      <div class="plate" v-reveal="180">
        <div class="plate-header">
          <span class="plate-title">注入管道分布</span>
          <span class="plate-note">Injection</span>
        </div>
        <div class="plate-body">
          <EChartsBase :option="injectionOption" height="280px" />
        </div>
      </div>
    </div>

    <!-- 属性×注入 交叉热力图（全宽） -->
    <div class="plate full-width" v-reveal>
      <div class="plate-header">
        <span class="plate-title">属性选择 × 注入管道</span>
        <span class="plate-note">Cross</span>
      </div>
      <div class="plate-body">
        <EChartsBase :option="heatmapOption" height="320px" />
      </div>
    </div>

    <!-- 攻击覆盖矩阵（全宽） -->
    <div class="plate full-width" v-reveal>
      <div class="plate-header">
        <span class="plate-title">攻击覆盖矩阵</span>
        <span class="plate-note">Paper × Attack</span>
      </div>
      <div class="plate-body">
        <EChartsBase :option="robustnessMatrixOption" height="500px" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { statsApi } from '../api/stats'
import { useTheme } from '../composables/useTheme'
import EChartsBase from '../components/EChartsBase.vue'

// 仪表盘用浅色主题——与整体设计一致（原为深色，经反馈改用浅色）
useTheme('light')

// 统计数据
const stats = ref({})
// 攻击覆盖矩阵数据
const robustnessData = ref([])
const loading = ref(true)

onMounted(async () => {
  try {
    const [overview, robustness] = await Promise.all([
      statsApi.getOverview(),
      statsApi.getRobustness(),
    ])
    stats.value = overview
    robustnessData.value = robustness
  } catch (e) {
    console.error('加载统计数据失败:', e)
  } finally {
    loading.value = false
  }
})

// ============================================================================
//  ECharts option 计算属性
//  浅色主题：轴线/文字用次级灰，数据色取自设计 token（墨蓝/朱砂/古金/深绿）
// ============================================================================

const C = {
  text: '#5C6470',
  line: '#E3E1D9',
  split: '#E9E7E0',
  ink: '#23272E',
  accent: '#2E4A6B',
  warm: '#B8392B',
  green: '#4A7C3A',
  gold: '#A98B45',
  grey: '#9AA1AB',
  bgA: '#F4F3EF',
  bgB: '#EDECE7',
  surface: '#FCFBF8',
}

const lightTheme = {
  textStyle: { color: C.text },
  xAxis: {
    axisLine: { lineStyle: { color: C.line } },
    axisLabel: { color: C.text },
    splitLine: { lineStyle: { color: C.split } },
  },
  yAxis: {
    axisLine: { lineStyle: { color: C.line } },
    axisLabel: { color: C.text },
    splitLine: { lineStyle: { color: C.split } },
  },
}

const tooltipBase = {
  backgroundColor: '#FFFFFF',
  borderColor: C.line,
  textStyle: { color: C.ink },
}

// 中文标签映射（和 options.js 一致，这里重复定义避免循环依赖）
const taskTypeLabels = {
  watermarking: '水印', steganography: '隐写',
  tamper_localization: '篡改定位', editing_protection: '编辑防护', other: '其他',
}
const attrLabels = { sh_only: '仅SH', mixed: '混合', auxiliary: '辅助属性', other: '其他' }
const injLabels = {
  per_asset_finetune: '逐资产微调', generalizable_mapping: '可泛化映射',
  generation_embedded: '生成内嵌入', other: '其他',
}
const robustnessLabels = {
  geometric_transform: '几何变换', photometric: '光度变换', signal_degradation: '信号退化',
  pruning: '剪枝', cloning: '克隆', spatial_transform: '空间变换',
  noise_injection: '噪声注入', quantization: '量化', parameter_merging: '参数合并',
}

// ---- 时间线柱状图 ----
const timelineOption = computed(() => {
  const byYear = stats.value.by_year || {}
  const years = Object.keys(byYear).sort()
  const counts = years.map((y) => byYear[y])
  return {
    tooltip: { trigger: 'axis', ...tooltipBase },
    xAxis: { ...lightTheme.xAxis, type: 'category', data: years },
    yAxis: { ...lightTheme.yAxis, type: 'value', minInterval: 1 },
    series: [{ data: counts, type: 'bar', itemStyle: { color: C.accent, borderRadius: [3, 3, 0, 0] } }],
    grid: { left: '8%', right: '5%', bottom: '10%', top: '8%' },
  }
})

// ---- 任务类型分布饼图 ----
const taskTypeOption = computed(() => {
  const byTask = stats.value.by_task_type || {}
  const data = Object.entries(byTask).map(([key, val]) => ({
    name: taskTypeLabels[key] || key,
    value: val,
  }))
  return {
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)', ...tooltipBase },
    legend: { bottom: 0, type: 'scroll', textStyle: { color: C.text } },
    series: [{
      type: 'pie',
      radius: ['35%', '65%'],
      center: ['50%', '45%'],
      data,
      label: { formatter: '{b}\n{c}篇', color: C.ink },
      // 饼图配色：墨蓝 + 朱砂 + 深绿 + 古金 + 灰
      color: [C.accent, C.warm, C.green, C.gold, C.grey],
    }],
  }
})

// ---- 属性选择机制分布柱状图 ----
const attributeOption = computed(() => {
  const byAttr = stats.value.by_attribute || {}
  const keys = ['sh_only', 'mixed', 'auxiliary', 'other']
  const data = keys.map((k) => byAttr[k] || 0)
  return {
    tooltip: { trigger: 'axis', ...tooltipBase },
    xAxis: { ...lightTheme.xAxis, type: 'category', data: keys.map((k) => attrLabels[k]) },
    yAxis: { ...lightTheme.yAxis, type: 'value', minInterval: 1 },
    series: [{ data, type: 'bar', itemStyle: { color: C.green, borderRadius: [3, 3, 0, 0] } }],
    grid: { left: '8%', right: '5%', bottom: '10%', top: '8%' },
  }
})

// ---- 注入管道分布柱状图 ----
const injectionOption = computed(() => {
  const byInj = stats.value.by_injection || {}
  const keys = ['per_asset_finetune', 'generalizable_mapping', 'generation_embedded', 'other']
  const data = keys.map((k) => byInj[k] || 0)
  return {
    tooltip: { trigger: 'axis', ...tooltipBase },
    xAxis: { ...lightTheme.xAxis, type: 'category', data: keys.map((k) => injLabels[k]), axisLabel: { ...lightTheme.xAxis.axisLabel, interval: 0, rotate: 15 } },
    yAxis: { ...lightTheme.yAxis, type: 'value', minInterval: 1 },
    series: [{ data, type: 'bar', itemStyle: { color: C.warm, borderRadius: [3, 3, 0, 0] } }],
    grid: { left: '8%', right: '5%', bottom: '15%', top: '8%' },
  }
})

// ---- 属性×注入 交叉热力图 ----
const heatmapOption = computed(() => {
  // TODO: 后端加 /stats/cross-attr-injection 端点返回真实交叉数据，当前为占位
  const attrKeys = ['sh_only', 'mixed', 'auxiliary', 'other']
  const injKeys = ['per_asset_finetune', 'generalizable_mapping', 'generation_embedded', 'other']
  const heatData = []
  for (let i = 0; i < attrKeys.length; i++) {
    for (let j = 0; j < injKeys.length; j++) {
      heatData.push([j, i, 0])
    }
  }
  return {
    tooltip: { position: 'top' },
    grid: { left: '15%', right: '5%', bottom: '15%', top: '5%' },
    xAxis: { type: 'category', data: injKeys.map((k) => injLabels[k]), splitArea: { show: true }, axisLine: { lineStyle: { color: C.line } }, axisLabel: { color: C.text } },
    yAxis: { type: 'category', data: attrKeys.map((k) => attrLabels[k]), splitArea: { show: true }, axisLine: { lineStyle: { color: C.line } }, axisLabel: { color: C.text } },
    visualMap: {
      min: 0, max: 10, calculable: true,
      orient: 'horizontal', left: 'center', bottom: '2%',
      inRange: { color: [C.bgB, C.accent] },
    },
    series: [{
      type: 'heatmap', data: heatData,
      label: { show: true },
      emphasis: { itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0, 0, 0, 0.5)' } },
    }],
  }
})

// ---- 攻击覆盖矩阵热力图 ----
const robustnessMatrixOption = computed(() => {
  const papers = robustnessData.value
  if (!papers.length) return {}

  const attackTypes = [
    'geometric_transform', 'photometric', 'signal_degradation',
    'pruning', 'cloning', 'spatial_transform', 'noise_injection', 'quantization', 'parameter_merging',
  ]

  const paperLabels = papers.map((p) => {
    const t = p.title.length > 30 ? p.title.slice(0, 30) + '...' : p.title
    return t
  })

  const heatData = []
  papers.forEach((paper, y) => {
    attackTypes.forEach((attack, x) => {
      const covered = paper.robustness_targets.includes(attack) ? 1 : 0
      heatData.push([x, y, covered])
    })
  })

  return {
    tooltip: {
      ...tooltipBase,
      formatter: (params) => {
        const paper = papers[params.value[1]]
        const attack = attackTypes[params.value[0]]
        const covered = params.value[2] ? '✓ 已评估' : '— 未评估'
        return `${paper.title}<br/>${robustnessLabels[attack]}: ${covered}`
      },
    },
    grid: { left: '35%', right: '5%', bottom: '15%', top: '5%' },
    xAxis: {
      type: 'category',
      data: attackTypes.map((a) => robustnessLabels[a]),
      splitArea: { show: true, areaStyle: { color: [C.bgA, C.bgB] } },
      axisLabel: { interval: 0, rotate: 30, color: C.text },
      axisLine: { lineStyle: { color: C.line } },
    },
    yAxis: {
      type: 'category',
      data: paperLabels,
      splitArea: { show: true, areaStyle: { color: [C.bgA, C.bgB] } },
      axisLabel: { fontSize: 11, color: C.text },
      axisLine: { lineStyle: { color: C.line } },
    },
    visualMap: {
      min: 0, max: 1,
      calculable: false,
      show: false,
      inRange: { color: [C.split, C.accent] },
    },
    series: [{
      type: 'heatmap',
      data: heatData,
      label: { show: true, formatter: (p) => p.value[2] ? '✓' : '', color: C.ink },
    }],
  }
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

/* 统计数字行 */
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

/* 图表网格 */
.charts-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-md);
}
@media (max-width: 900px) {
  .charts-grid { grid-template-columns: 1fr; }
}
</style>
