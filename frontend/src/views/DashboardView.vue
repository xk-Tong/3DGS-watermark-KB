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
import EChartsBase from '../components/EChartsBase.vue'

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
//  computed：依赖 stats 变化时自动重算，EChartsBase 组件监听 option 变化更新图表。
// ============================================================================

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
  // 按年份排序（Object.keys 返回的顺序不确定，手动排序）。
  // .sort() 默认按字符串排序，年份字符串排序正好是时间顺序。
  const years = Object.keys(byYear).sort()
  const counts = years.map((y) => byYear[y])
  return {
    // tooltip：鼠标悬浮提示。trigger: 'axis' 沿坐标轴显示。
    tooltip: { trigger: 'axis' },
    // xAxis/xAxis：X 轴。type: 'category' 类目轴，data 是标签数组。
    xAxis: { type: 'category', data: years, name: '年份' },
    // yAxis：Y 轴。type: 'value' 数值轴，自动根据数据算刻度。
    yAxis: { type: 'value', name: '论文数', minInterval: 1 },
    // series：数据系列。type: 'bar' 柱状图。
    series: [{ data: counts, type: 'bar', itemStyle: { color: '#409eff' } }],
    // grid：图表在容器内的边距，留出空间给坐标轴标签。
    grid: { left: '8%', right: '5%', bottom: '10%', top: '8%' },
  }
})

// ---- 任务类型分布饼图 ----
const taskTypeOption = computed(() => {
  const byTask = stats.value.by_task_type || {}
  // ECharts 饼图要 [{name, value}] 格式。
  // Object.entries(obj) 把 {a:1,b:2} 转成 [['a',1],['b',2]]，再 map 成 [{name,value}]。
  const data = Object.entries(byTask).map(([key, val]) => ({
    name: taskTypeLabels[key] || key,
    value: val,
  }))
  return {
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    // legend：图例（图表旁边的分类说明）。
    legend: { bottom: 0, type: 'scroll' },
    series: [{
      type: 'pie',
      radius: ['35%', '65%'],  // 内半径35%外半径65% → 环形图
      center: ['50%', '45%'],    // 圆心位置
      data,
      label: { formatter: '{b}\n{c}篇' },
    }],
  }
})

// ---- 属性选择机制分布柱状图 ----
const attributeOption = computed(() => {
  const byAttr = stats.value.by_attribute || {}
  const keys = ['sh_only', 'mixed', 'auxiliary', 'other']
  const data = keys.map((k) => byAttr[k] || 0)
  return {
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: keys.map((k) => attrLabels[k]) },
    yAxis: { type: 'value', minInterval: 1 },
    series: [{ data, type: 'bar', itemStyle: { color: '#67c23a' } }],
    grid: { left: '8%', right: '5%', bottom: '10%', top: '8%' },
  }
})

// ---- 注入管道分布柱状图 ----
const injectionOption = computed(() => {
  const byInj = stats.value.by_injection || {}
  const keys = ['per_asset_finetune', 'generalizable_mapping', 'generation_embedded', 'other']
  const data = keys.map((k) => byInj[k] || 0)
  return {
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: keys.map((k) => injLabels[k]), axisLabel: { interval: 0, rotate: 15 } },
    yAxis: { type: 'value', minInterval: 1 },
    series: [{ data, type: 'bar', itemStyle: { color: '#e6a23c' } }],
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
      splitArea: { show: true },
      axisLabel: { interval: 0, rotate: 30 },
    },
    yAxis: {
      type: 'category',
      data: paperLabels,
      splitArea: { show: true },
      axisLabel: { fontSize: 11 },
    },
    visualMap: {
      min: 0, max: 1,
      calculable: false,
      show: false,  // 不显示图例（只有 0/1 两值，用颜色区分即可）
      inRange: { color: ['#f5f7fa', '#67c23a'] },
    },
    series: [{
      type: 'heatmap',
      data: heatData,
      label: { show: true, formatter: (p) => p.value[2] ? '✓' : '' },
    }],
  }
})
</script>

<style scoped>
.dashboard-view {
  max-width: 1400px;
  margin: 0 auto;
  padding: 24px;
}

.header { margin-bottom: 20px; }
.header h1 { font-size: 22px; color: #303133; margin-bottom: 4px; }
.subtitle { font-size: 13px; color: #909399; }

/* 统计卡片行 */
.stats-cards {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
}
.stat-card { flex: 1; text-align: center; }
.stat-number { font-size: 32px; font-weight: 700; color: #409eff; }
.stat-number.auto { color: #e6a23c; }
.stat-number.reviewed { color: #67c23a; }
.stat-label { font-size: 13px; color: #909399; margin-top: 4px; }

/* 图表网格：两列 */
.charts-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}
/* 响应式：窄屏改单列 */
@media (max-width: 900px) {
  .charts-grid { grid-template-columns: 1fr; }
}

.chart-card { margin-bottom: 0; }
.chart-card.full-width { grid-column: 1 / -1; }
.card-title { font-weight: 600; font-size: 14px; }
</style>
