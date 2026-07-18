<template>
  <div class="compare-view" v-loading="loading">
    <header class="page-header" v-reveal>
      <div class="page-heading">
        <span class="eyebrow">Compare</span>
        <h1 class="page-title">论文对比</h1>
        <p class="page-intro">勾选 2–4 篇，横向对比机制维度、指标与鲁棒性</p>
      </div>
      <el-button @click="router.back()">← 返回列表</el-button>
    </header>

    <!-- 选中数量提示 -->
    <el-alert
      v-if="papers.length < 2"
      type="info"
      :title="`已选 ${papers.length} 篇，至少选 2 篇才能对比。请返回列表勾选。`"
      :closable="false"
      style="margin-bottom: 16px"
    />

    <!-- 对比矩阵 -->
    <div class="plate compare-plate" v-if="papers.length >= 2" v-reveal>
      <el-table :data="compareRows" style="width: 100%">
        <!-- 第一列：字段名 -->
        <el-table-column prop="label" label="对比项" width="120" fixed />
        <!-- 每篇论文一列 -->
        <el-table-column
          v-for="paper in papers"
          :key="paper.id"
          :label="paper.title.length > 20 ? paper.title.slice(0, 20) + '...' : paper.title"
          min-width="200"
        >
          <template #header>
            <div class="compare-header">
              <router-link :to="`/papers/${paper.id}`" class="paper-link">
                {{ paper.title.length > 25 ? paper.title.slice(0, 25) + '...' : paper.title }}
              </router-link>
              <div class="paper-meta">{{ paper.arxiv_id || '—' }} · {{ paper.pub_date || '—' }}</div>
            </div>
          </template>
          <template #default="{ row }">
            <span v-html="formatValue(row.values[paper.id], row.type)"></span>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 清空选择按钮 -->
    <div v-if="papers.length > 0" class="footer">
      <el-button @click="store.clearCompare(); router.push('/papers')">清空选择并返回</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { usePapersStore } from '../stores/papers'
import { papersApi } from '../api/papers'
import { useTheme } from '../composables/useTheme'

// 对比页用浅色主题
useTheme('light')

const router = useRouter()
const store = usePapersStore()

const papers = ref([])
const loading = ref(true)

// 中文标签映射
const taskLabels = {
  watermarking: '水印', steganography: '隐写',
  tamper_localization: '篡改定位', editing_protection: '编辑防护', other: '其他',
}
const attrLabels = { sh_only: '仅SH', mixed: '混合', auxiliary: '辅助属性', other: '其他' }
const distLabels = { global: '全局', local_frequency: '局部·频率', local_uncertainty: '局部·不确定性', other: '其他' }
const injLabels = {
  per_asset_finetune: '逐资产微调', generalizable_mapping: '可泛化映射',
  generation_embedded: '生成内嵌入', other: '其他',
}
const robustLabels = {
  geometric_transform: '几何变换', photometric: '光度', signal_degradation: '信号退化',
  pruning: '剪枝', cloning: '克隆', spatial_transform: '空间变换',
  noise_injection: '噪声注入', quantization: '量化', parameter_merging: '参数合并',
}

onMounted(async () => {
  // 从 store 的 selectedForCompare 拿选中的 id 列表，逐个拉详情。
  // 用 Promise.all 并行请求，比串行快。
  const ids = store.selectedForCompare
  if (!ids.length) {
    loading.value = false
    return
  }
  try {
    papers.value = await Promise.all(ids.map((id) => papersApi.get(id)))
  } catch (e) {
    console.error('加载对比论文失败:', e)
  } finally {
    loading.value = false
  }
})

// compareRows：把"每篇论文是一个对象"转成"每个对比项是一行"。
// 原始数据结构：[{title, authors, task_type, ...}, ...]（按论文）
// 表格需要：[{label, type, values: {paperId: value}}, ...]（按字段）
// 这是一个"行列转置"操作。
const compareRows = computed(() => {
  const rows = [
    { label: '任务类型', type: 'task_type', values: {} },
    { label: '属性选择', type: 'attribute', values: {} },
    { label: '分布策略', type: 'distribution', values: {} },
    { label: '注入管道', type: 'injection', values: {} },
    { label: '鲁棒性目标', type: 'robustness', values: {} },
    { label: '标签', type: 'tags', values: {} },
    { label: 'PSNR (dB)', type: 'psnr', values: {} },
    { label: 'SSIM', type: 'ssim', values: {} },
    { label: 'Bit Accuracy', type: 'bit_accuracy', values: {} },
    { label: '容量', type: 'capacity', values: {} },
    { label: '数据集', type: 'datasets', values: {} },
    { label: '基线对比', type: 'baselines', values: {} },
    { label: '阅读状态', type: 'read_status', values: {} },
    { label: '数据状态', type: 'curation_status', values: {} },
    { label: '个人批注', type: 'notes', values: {} },
  ]

  // 填充每篇论文的值到对应行
  papers.value.forEach((paper) => {
    // 遍历每一行，根据 type 取对应字段
    rows.forEach((row) => {
      switch (row.type) {
        case 'task_type':
          row.values[paper.id] = paper.task_type.map((t) => taskLabels[t] || t)
          break
        case 'attribute':
          row.values[paper.id] = paper.attribute_selection ? (attrLabels[paper.attribute_selection] || paper.attribute_selection) : '—'
          break
        case 'distribution':
          row.values[paper.id] = paper.distribution_strategy ? (distLabels[paper.distribution_strategy] || paper.distribution_strategy) : '—'
          break
        case 'injection':
          row.values[paper.id] = paper.injection_pipeline ? (injLabels[paper.injection_pipeline] || paper.injection_pipeline) : '—'
          break
        case 'robustness':
          row.values[paper.id] = paper.robustness_targets.map((r) => robustLabels[r] || r)
          break
        case 'tags':
          row.values[paper.id] = paper.tags
          break
        case 'psnr':
          row.values[paper.id] = paper.psnr != null ? paper.psnr.toFixed(2) : '—'
          break
        case 'ssim':
          row.values[paper.id] = paper.ssim != null ? paper.ssim.toFixed(4) : '—'
          break
        case 'bit_accuracy':
          row.values[paper.id] = paper.bit_accuracy != null ? (paper.bit_accuracy * 100).toFixed(1) + '%' : '—'
          break
        case 'capacity':
          row.values[paper.id] = paper.capacity || '—'
          break
        case 'datasets':
          row.values[paper.id] = paper.datasets_used || []
          break
        case 'baselines':
          row.values[paper.id] = paper.baselines_compared || []
          break
        case 'read_status':
          row.values[paper.id] = paper.read_status
          break
        case 'curation_status':
          row.values[paper.id] = paper.curation_status
          break
        case 'notes':
          row.values[paper.id] = paper.personal_notes || ''
          break
      }
    })
  })

  return rows
})

/**
 * 作用：把字段值格式化成 HTML 展示。
 * @param {any} value - 字段值（字符串/数组/数字）
 * @param {string} type - 字段类型，决定格式化方式
 * @returns {string} HTML 字符串
 */
function formatValue(value, type) {
  if (value == null || value === '' || value === '—') return '<span class="empty">—</span>'

  // 数组类型：用标签样式展示每个元素
  if (Array.isArray(value)) {
    if (!value.length) return '<span class="empty">—</span>'
    return value.map((v) => `<span class="tag">${v}</span>`).join(' ')
  }

  // 枚举类型：加颜色
  if (type === 'read_status') {
    const map = {
      unread: '<span class="status info">未读</span>',
      reading: '<span class="status warning">在读</span>',
      read: '<span class="status success">已读</span>',
    }
    return map[value] || value
  }
  if (type === 'curation_status') {
    const map = {
      auto: '<span class="status warning">⚠️ 未核实</span>',
      reviewed: '<span class="status info">已复核</span>',
      verified: '<span class="status success">已验证</span>',
    }
    return map[value] || value
  }

  return String(value)
}
</script>

<style scoped>
.compare-view {
  max-width: 1200px;
  margin: 0 auto;
  padding: var(--space-xl) var(--space-lg);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: var(--space-lg);
  margin-bottom: var(--space-lg);
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

.compare-plate {
  padding: 8px 12px 12px;
}

.compare-header { text-align: left; }
.paper-link {
  color: var(--accent);
  text-decoration: none;
  font-size: 13px;
  font-family: var(--font-serif);
  font-weight: 600;
}
.paper-meta {
  font-size: 11px;
  color: var(--text-tertiary);
  font-family: var(--font-mono);
  margin-top: 2px;
}

.footer { margin-top: var(--space-md); text-align: center; }

/* :deep() 穿透 scoped，给 v-html 渲染的 span 加样式 */
:deep(.tag) {
  display: inline-block;
  padding: 1px 7px;
  margin: 1px 2px;
  background: var(--accent-soft);
  border-radius: 3px;
  font-size: 11px;
  color: var(--accent);
}
:deep(.empty) { color: var(--text-tertiary); }
:deep(.status.info) { color: var(--text-tertiary); }
:deep(.status.warning) { color: var(--warning); }
:deep(.status.success) { color: var(--success); }
</style>
