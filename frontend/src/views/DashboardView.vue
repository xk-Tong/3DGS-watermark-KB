<template>
  <div class="dashboard-view" v-loading="loading">
    <div class="header">
      <h1>统计仪表盘</h1>
      <span class="subtitle">3DGS IP Protection Knowledge Base Overview</span>
    </div>

    <!-- 统计卡片行 -->
    <div class="stats-cards">
      <el-card class="stat-card" shadow="never">
        <div class="stat-number">{{ stats.total || 0 }}</div>
        <div class="stat-label">总论文数</div>
      </el-card>
      <el-card class="stat-card" shadow="never">
        <div class="stat-number auto">{{ stats.by_curation?.auto || 0 }}</div>
        <div class="stat-label">⚠️ AI 未核实</div>
      </el-card>
      <el-card class="stat-card" shadow="never">
        <div class="stat-number reviewed">{{ (stats.by_curation?.reviewed || 0) + (stats.by_curation?.verified || 0) }}</div>
        <div class="stat-label">已复核/验证</div>
      </el-card>
    </div>

    <!-- 图表网格：两列布局 -->
    <div class="charts-grid">
      <!-- 时间线柱状图 -->
      <el-card class="chart-card" shadow="never">
        <template #header><span class="card-title">论文时间线（按发表年份）</span></template>
        <EChartsBase :option="timelineOption" height="280px" />
      </el-card>

      <!-- 任务类型分布 -->
      <el-card class="chart-card" shadow="never">
        <template #header><span class="card-title">任务类型分布</span></template>
        <EChartsBase :option="taskTypeOption" height="280px" />
      </el-card>

      <!-- 属性选择机制分布 -->
      <el-card class="chart-card" shadow="never">
        <template #header><span class="card-title">属性选择机制分布</span></template>
        <EChartsBase :option="attributeOption" height="280px" />
      </el-card>

      <!-- 注入管道分布 -->
      <el-card class="chart-card" shadow="never">
        <template #header><span class="card-title">注入管道分布</span></template>
        <EChartsBase :option="injectionOption" height="280px" />
      </el-card>
    </div>

    <!-- 属性×注入 交叉热力图（全宽） -->
    <el-card class="chart-card full-width" shadow="never">
      <template #header><span class="card-title">属性选择 × 注入管道 交叉热力图</span></template>
      <EChartsBase :option="heatmapOption" height="320px" />
    </el-card>

    <!-- 攻击覆盖矩阵（全宽） -->
    <el-card class="chart-card full-width" shadow="never">
      <template #header>
        <span class="card-title">攻击覆盖矩阵（论文 × 鲁棒性目标）</span>
      </template>
      <EChartsBase :option="robustnessMatrixOption" height="500px" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { statsApi } from '../api/stats'
import { useTheme } from '../composables/useTheme'
import EChartsBase from '../components/EChartsBase.vue'

// 仪表盘用深色主题——数据可视化在深色背景上更出彩
useTheme('dark')

// 统计数据
const stats = ref({})
// 攻击覆盖矩阵数据
const robustnessData = ref([])
const loading = ref(true)

onMounted(async () => {
  try {
    // 并行加载两个统计接口（Promise.all：等全部完成，比串行快）。
    // 两个请求互不依赖，可以同时发。
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
//  仪表盘深色主题：轴线/文字用浅色，数据用辉光蓝/陶土色
// ============================================================================

// 深色主题 ECharts 通用配置——合并到每个 option 里
const darkTheme = {
  textStyle: { color: '#8B98A8' },
  // 坐标轴文字/轴线颜色
  xAxis: { axisLine: { lineStyle: { color: '#2A3441' } }, axisLabel: { color: '#8B98A8' }, splitLine: { lineStyle: { color: '#1A2330' } } },
  yAxis: { axisLine: { lineStyle: { color: '#2A3441' } }, axisLabel: { color: '#8B98A8' }, splitLine: { lineStyle: { color: '#1A2330' } } },
}

// 中文标签映射（和 options.js 一致，这里重复定义避免循环依赖）
const taskTypeLabels = {
  watermarking: '水印', steganography: '隐写',
  tamper_localization: '篡改定位', editing_protection: '编辑防护', other: '其他',
}
const attrLabels = { sh_only: '仅SH', mixed: '混合', auxiliary: '辅助属性', other: '其他' }
const distLabels = { global: '全局', local_frequency: '局部·频率', local_uncertainty: '局部·不确定性', other: '其他' }
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
    tooltip: { trigger: 'axis', backgroundColor: '#1A2330', borderColor: '#2A3441', textStyle: { color: '#E8EDF2' } },
    xAxis: { ...darkTheme.xAxis, type: 'category', data: years },
    yAxis: { ...darkTheme.yAxis, type: 'value', minInterval: 1 },
    series: [{ data: counts, type: 'bar', itemStyle: { color: '#7C9EFF', borderRadius: [3, 3, 0, 0] } }],
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
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)', backgroundColor: '#1A2330', borderColor: '#2A3441', textStyle: { color: '#E8EDF2' } },
    legend: { bottom: 0, type: 'scroll', textStyle: { color: '#8B98A8' } },
    series: [{
      type: 'pie',
      radius: ['35%', '65%'],
      center: ['50%', '45%'],
      data,
      label: { formatter: '{b}\n{c}篇', color: '#E8EDF2' },
      // 饼图配色：辉光蓝系 + 陶土色点缀
      color: ['#7C9EFF', '#E5A893', '#6BB85A', '#D4A537', '#5A6573'],
    }],
  }
})

// ---- 属性选择机制分布柱状图 ----
const attributeOption = computed(() => {
  const byAttr = stats.value.by_attribute || {}
  const keys = ['sh_only', 'mixed', 'auxiliary', 'other']
  const data = keys.map((k) => byAttr[k] || 0)
  return {
    tooltip: { trigger: 'axis', backgroundColor: '#1A2330', borderColor: '#2A3441', textStyle: { color: '#E8EDF2' } },
    xAxis: { ...darkTheme.xAxis, type: 'category', data: keys.map((k) => attrLabels[k]) },
    yAxis: { ...darkTheme.yAxis, type: 'value', minInterval: 1 },
    series: [{ data, type: 'bar', itemStyle: { color: '#6BB85A', borderRadius: [3, 3, 0, 0] } }],
    grid: { left: '8%', right: '5%', bottom: '10%', top: '8%' },
  }
})

// ---- 注入管道分布柱状图 ----
const injectionOption = computed(() => {
  const byInj = stats.value.by_injection || {}
  const keys = ['per_asset_finetune', 'generalizable_mapping', 'generation_embedded', 'other']
  const data = keys.map((k) => byInj[k] || 0)
  return {
    tooltip: { trigger: 'axis', backgroundColor: '#1A2330', borderColor: '#2A3441', textStyle: { color: '#E8EDF2' } },
    xAxis: { ...darkTheme.xAxis, type: 'category', data: keys.map((k) => injLabels[k]), axisLabel: { ...darkTheme.xAxis.axisLabel, interval: 0, rotate: 15 } },
    yAxis: { ...darkTheme.yAxis, type: 'value', minInterval: 1 },
    series: [{ data, type: 'bar', itemStyle: { color: '#E5A893', borderRadius: [3, 3, 0, 0] } }],
    grid: { left: '8%', right: '5%', bottom: '15%', top: '8%' },
  }
})

// ---- 属性×注入 交叉热力图 ----
const heatmapOption = computed(() => {
  const byAttr = stats.value.by_attribute || {}
  const byInj = stats.value.by_injection || {}
  // 需要原始论文数据来交叉统计——但 overview 没返回原始数据。
  // 这里用一个简化版：基于 by_attribute 和 by_injection 的边际分布做"预期交叉"。
  // 真正的交叉统计需要后端加端点，Phase 3 先用简化版（后续优化）。
  // 简化：直接用 robustnessData（不含分类字段），改用空数据占位。
  // TODO: 后端加 /stats/cross-attr-injection 端点返回真实交叉数据。
  const attrKeys = ['sh_only', 'mixed', 'auxiliary', 'other']
  const injKeys = ['per_asset_finetune', 'generalizable_mapping', 'generation_embedded', 'other']
  // 占位数据：全 0（后续后端补充真实交叉统计）
  const heatData = []
  for (let i = 0; i < attrKeys.length; i++) {
    for (let j = 0; j < injKeys.length; j++) {
      heatData.push([j, i, 0])
    }
  }
  return {
    tooltip: { position: 'top' },
    grid: { left: '15%', right: '5%', bottom: '15%', top: '5%' },
    xAxis: { type: 'category', data: injKeys.map((k) => injLabels[k]), splitArea: { show: true } },
    yAxis: { type: 'category', data: attrKeys.map((k) => attrLabels[k]), splitArea: { show: true } },
    visualMap: {
      min: 0, max: 10, calculable: true,
      orient: 'horizontal', left: 'center', bottom: '2%',
      inRange: { color: ['#f5f7fa', '#409eff'] },
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

  // 攻击类型列表（固定顺序，2D 在前 3D 在后）
  const attackTypes = [
    'geometric_transform', 'photometric', 'signal_degradation',
    'pruning', 'cloning', 'spatial_transform', 'noise_injection', 'quantization', 'parameter_merging',
  ]

  // 矩阵数据：[x(攻击列), y(论文行), value(0或1)]
  // ECharts 热力图要 [[x, y, value], ...] 格式。
  // 论文标题太长，截断显示。
  const paperLabels = papers.map((p) => {
    const t = p.title.length > 30 ? p.title.slice(0, 30) + '...' : p.title
    return t
  })

  const heatData = []
  papers.forEach((paper, y) => {
    attackTypes.forEach((attack, x) => {
      // paper.robustness_targets 是数组，includes 检查是否包含该攻击。
      const covered = paper.robustness_targets.includes(attack) ? 1 : 0
      heatData.push([x, y, covered])
    })
  })

  return {
    tooltip: {
      backgroundColor: '#1A2330',
      borderColor: '#2A3441',
      textStyle: { color: '#E8EDF2' },
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
      splitArea: { show: true, areaStyle: { color: ['#0F1419', '#1A2330'] } },
      axisLabel: { interval: 0, rotate: 30, color: '#8B98A8' },
      axisLine: { lineStyle: { color: '#2A3441' } },
    },
    yAxis: {
      type: 'category',
      data: paperLabels,
      splitArea: { show: true, areaStyle: { color: ['#0F1419', '#1A2330'] } },
      axisLabel: { fontSize: 11, color: '#8B98A8' },
      axisLine: { lineStyle: { color: '#2A3441' } },
    },
    visualMap: {
      min: 0, max: 1,
      calculable: false,
      show: false,
      inRange: { color: ['#1A2330', '#7C9EFF'] },
    },
    series: [{
      type: 'heatmap',
      data: heatData,
      label: { show: true, formatter: (p) => p.value[2] ? '✓' : '', color: '#E8EDF2' },
    }],
  }
})
</script>

<style scoped>
/* 仪表盘深色主题——固定深色色值，不依赖 CSS 变量（因为 data-theme=dark 已设） */
.dashboard-view {
  max-width: 1400px;
  margin: 0 auto;
  padding: var(--space-xl) var(--space-lg);
}

.header { margin-bottom: var(--space-lg); }
.header h1 {
  font-family: var(--font-display);
  font-size: 24px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
}
.subtitle { font-size: 13px; color: var(--text-secondary); }

/* 统计卡片行 */
.stats-cards {
  display: flex;
  gap: var(--space-md);
  margin-bottom: var(--space-lg);
}
.stat-card {
  flex: 1;
  text-align: center;
  background: var(--bg-surface);
  border: 0.5px solid var(--border-subtle);
  border-radius: var(--radius-md);
}
.stat-number {
  font-family: var(--font-display);
  font-size: 36px;
  font-weight: 600;
  color: var(--accent);
  line-height: 1;
}
.stat-number.auto { color: var(--warm); }
.stat-number.reviewed { color: var(--success); }
.stat-label { font-size: 12px; color: var(--text-tertiary); margin-top: 6px; }

/* 图表网格 */
.charts-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-md);
  margin-bottom: var(--space-md);
}
@media (max-width: 900px) {
  .charts-grid { grid-template-columns: 1fr; }
}

/* 图表卡片用深色 surface */
.chart-card {
  background: var(--bg-surface);
  border: 0.5px solid var(--border-subtle);
  border-radius: var(--radius-md);
}
.chart-card.full-width { grid-column: 1 / -1; }
.card-title {
  font-weight: 500;
  font-size: 13px;
  color: var(--text-primary);
}
</style>
