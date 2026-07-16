<template>
  <div class="paper-detail-view" v-loading="loading">
    <!-- 返回按钮 -->
    <div class="top-bar">
      <el-button @click="router.back()">← 返回列表</el-button>
      <div class="actions">
        <el-button type="primary" @click="openEditDialog">编辑</el-button>
      </div>
    </div>

    <!-- 论文不存在时的空状态 -->
    <el-empty v-if="!loading && !paper" description="论文不存在" />

    <!-- 全字段卡片展示 -->
    <div v-if="paper" class="cards">
      <!-- 身份信息卡片 -->
      <el-card class="info-card" shadow="never">
        <template #header>
          <span class="card-title">基本信息</span>
        </template>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="标题" :span="2">{{ paper.title }}</el-descriptions-item>
          <el-descriptions-item label="作者" :span="2">{{ paper.authors.join(', ') }}</el-descriptions-item>
          <el-descriptions-item label="arXiv ID">
            <a v-if="paper.arxiv_id" :href="`https://arxiv.org/abs/${paper.arxiv_id}`" target="_blank">
              {{ paper.arxiv_id }}
            </a>
            <span v-else class="empty">—</span>
          </el-descriptions-item>
          <el-descriptions-item label="DOI">
            {{ paper.doi || '—' }}
          </el-descriptions-item>
          <el-descriptions-item label="会议/期刊">{{ paper.venue || '—' }}</el-descriptions-item>
          <el-descriptions-item label="发表日期">{{ paper.pub_date || '—' }}</el-descriptions-item>
          <el-descriptions-item label="入库时间">{{ formatDateTime(paper.added_at) }}</el-descriptions-item>
          <el-descriptions-item label="来源">{{ labelOf(sourceOptions, paper.source) }}</el-descriptions-item>
          <el-descriptions-item label="PDF" :span="2">
            <a v-if="paper.pdf_url" :href="paper.pdf_url" target="_blank">{{ paper.pdf_url }}</a>
            <span v-else class="empty">—</span>
          </el-descriptions-item>
          <el-descriptions-item label="代码仓库" :span="2">
            <a v-if="paper.code_url" :href="paper.code_url" target="_blank">{{ paper.code_url }}</a>
            <span v-else class="empty">—</span>
          </el-descriptions-item>
        </el-descriptions>
      </el-card>

      <!-- 摘要卡片 -->
      <el-card class="info-card" shadow="never">
        <template #header><span class="card-title">摘要</span></template>
        <div class="abstract-text">{{ paper.abstract }}</div>
      </el-card>

      <!-- AI 抽取的方法信息卡片 -->
      <el-card class="info-card" shadow="never">
        <template #header><span class="card-title">方法概述（AI 抽取）</span></template>
        <div v-if="paper.method_summary" class="abstract-text">{{ paper.method_summary }}</div>
        <el-empty v-else description="暂无（AI 流水线 Phase 2 填充）" :image-size="40" />
        <div v-if="paper.key_contributions && paper.key_contributions.length" class="contributions">
          <div class="sub-title">关键贡献：</div>
          <ul>
            <li v-for="(c, i) in paper.key_contributions" :key="i">{{ c }}</li>
          </ul>
        </div>
      </el-card>

      <!-- 分类信息卡片 -->
      <el-card class="info-card" shadow="never">
        <template #header><span class="card-title">分类信息</span></template>
        <el-descriptions :column="1" border>
          <el-descriptions-item label="任务类型">
            <el-tag v-for="t in paper.task_type" :key="t" size="small" type="primary" style="margin-right: 4px">
              {{ labelOf(taskTypeOptions, t) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="属性选择">{{ labelOf(attributeOptions, paper.attribute_selection) || '—' }}</el-descriptions-item>
          <el-descriptions-item label="分布策略">{{ labelOf(distributionOptions, paper.distribution_strategy) || '—' }}</el-descriptions-item>
          <el-descriptions-item label="注入管道">{{ labelOf(injectionOptions, paper.injection_pipeline) || '—' }}</el-descriptions-item>
          <el-descriptions-item label="鲁棒性目标">
            <el-tag v-for="r in paper.robustness_targets" :key="r" size="small" type="info" style="margin-right: 4px">
              {{ robustnessLabel(r) }}
            </el-tag>
            <span v-if="!paper.robustness_targets.length" class="empty">—</span>
          </el-descriptions-item>
          <el-descriptions-item label="标签">
            <el-tag v-for="t in paper.tags" :key="t" size="small" style="margin-right: 4px">{{ t }}</el-tag>
            <span v-if="!paper.tags.length" class="empty">—</span>
          </el-descriptions-item>
        </el-descriptions>
      </el-card>

      <!-- 实验数据卡片 -->
      <el-card class="info-card" shadow="never">
        <template #header><span class="card-title">实验数据</span></template>
        <el-descriptions :column="3" border>
          <el-descriptions-item label="PSNR">{{ paper.psnr != null ? paper.psnr.toFixed(2) + ' dB' : '—' }}</el-descriptions-item>
          <el-descriptions-item label="SSIM">{{ paper.ssim != null ? paper.ssim.toFixed(4) : '—' }}</el-descriptions-item>
          <el-descriptions-item label="Bit Acc">{{ paper.bit_accuracy != null ? (paper.bit_accuracy * 100).toFixed(1) + '%' : '—' }}</el-descriptions-item>
          <el-descriptions-item label="容量">{{ paper.capacity || '—' }}</el-descriptions-item>
          <el-descriptions-item label="数据集" :span="2">
            <span v-if="paper.datasets_used && paper.datasets_used.length">{{ paper.datasets_used.join(', ') }}</span>
            <span v-else class="empty">—</span>
          </el-descriptions-item>
          <el-descriptions-item label="基线对比" :span="3">
            <span v-if="paper.baselines_compared && paper.baselines_compared.length">{{ paper.baselines_compared.join(', ') }}</span>
            <span v-else class="empty">—</span>
          </el-descriptions-item>
        </el-descriptions>
        <div v-if="paper.extra_metrics && Object.keys(paper.extra_metrics).length" class="extra-metrics">
          <div class="sub-title">其他指标：</div>
          <pre>{{ JSON.stringify(paper.extra_metrics, null, 2) }}</pre>
        </div>
      </el-card>

      <!-- 个人使用卡片 -->
      <el-card class="info-card" shadow="never">
        <template #header><span class="card-title">个人使用</span></template>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="阅读状态">
            <el-tag :type="readStatusType(paper.read_status)" size="small">
              {{ labelOf(readStatusOptions, paper.read_status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="数据状态">
            <el-tag :type="curationStatusType(paper.curation_status)" size="small">
              {{ labelOf(curationStatusOptions, paper.curation_status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="最后复核" :span="2">
            {{ paper.last_reviewed_at ? formatDateTime(paper.last_reviewed_at) : '未复核' }}
          </el-descriptions-item>
          <el-descriptions-item label="个人批注" :span="2">
            <div v-if="paper.personal_notes" class="notes-text">{{ paper.personal_notes }}</div>
            <span v-else class="empty">点击"编辑"添加批注</span>
          </el-descriptions-item>
        </el-descriptions>
      </el-card>
    </div>

    <!-- 编辑表单 Dialog -->
    <PaperEditDialog
      v-model:visible="editVisible"
      :paper="paper"
      @saved="handleSaved"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { papersApi } from '../api/papers'
import { useTheme } from '../composables/useTheme'
import {
  taskTypeOptions, attributeOptions, distributionOptions, injectionOptions,
  robustness2DOptions, robustness3DOptions, readStatusOptions,
  curationStatusOptions, sourceOptions, labelOf,
} from '../api/options'
import PaperEditDialog from '../components/PaperEditDialog.vue'

// 详情页用浅色主题（长文阅读舒适）
useTheme('light')

// useRoute：拿到当前路由信息（含 params 路径参数）。
// useRouter：拿到 router 实例用于编程式导航（push/back）。
const route = useRoute()
const router = useRouter()

// 论文数据和加载状态
const paper = ref(null)
const loading = ref(true)
const editVisible = ref(false)   // 编辑弹窗显示状态

onMounted(async () => {
  await loadPaper()
})

/**
 * 作用：从后端加载当前论文数据。
 * 使用场景：组件挂载时调用，编辑保存后重新加载。
 */
async function loadPaper() {
  loading.value = true
  try {
    // route.params.id：从 URL /papers/:id 里取 id 参数。
    // Number() 把字符串转数字（URL 参数都是字符串）。
    const id = Number(route.params.id)
    paper.value = await papersApi.get(id)
  } catch (e) {
    // 请求失败（404 或网络错误），paper 保持 null，显示空状态。
    console.error('加载论文失败:', e)
  } finally {
    loading.value = false
  }
}

/**
 * 作用：打开编辑弹窗。
 */
function openEditDialog() {
  editVisible.value = true
}

/**
 * 作用：编辑保存成功后的回调——重新加载论文数据刷新展示。
 */
function handleSaved() {
  editVisible.value = false
  loadPaper()
}

// ---- 工具函数 ----

/**
 * 鲁棒性目标枚举值 → 中文标签。
 * @param {string} value - 枚举值如 "pruning"
 * @returns {string} 中文标签如 "剪枝"
 */
function robustnessLabel(value) {
  const all = [...robustness2DOptions, ...robustness3DOptions]
  return labelOf(all, value)
}

function readStatusType(status) {
  const map = { unread: 'info', reading: 'warning', read: 'success' }
  return map[status] || 'info'
}

function curationStatusType(status) {
  const map = { auto: 'warning', reviewed: 'info', verified: 'success' }
  return map[status] || 'info'
}

/**
 * 作用：ISO 时间字符串格式化成本地可读格式。
 * @param {string} iso - 如 "2026-07-15T05:48:41"
 * @returns {string} 如 "2026-07-15 05:48"
 */
function formatDateTime(iso) {
  if (!iso) return ''
  // new Date(iso).toLocaleString()：浏览器原生 Date，转成本地时间字符串。
  return new Date(iso).toLocaleString('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit',
  })
}
</script>

<style scoped>
.paper-detail-view {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
}

.top-bar {
  display: flex;
  justify-content: space-between;
  margin-bottom: 16px;
}

.cards {
  display: flex;
  flex-direction: column;
  gap: 16px;   /* 卡片间距，flex gap 比 margin 更简洁 */
}

.info-card .card-title {
  font-weight: 600;
  font-size: 15px;
}

.abstract-text {
  line-height: 1.8;       /* 行高 1.8 倍，长文阅读更舒适 */
  color: #303133;
  white-space: pre-wrap;  /* 保留换行和空格 */
}

.contributions {
  margin-top: 16px;
}

.sub-title {
  font-weight: 600;
  margin-bottom: 8px;
  color: #606266;
}

.contributions ul {
  padding-left: 20px;
}

.contributions li {
  line-height: 1.8;
  color: #303133;
}

.extra-metrics pre {
  background: #f5f7fa;
  padding: 12px;
  border-radius: 4px;
  font-size: 13px;
  overflow-x: auto;
}

.notes-text {
  white-space: pre-wrap;
  line-height: 1.8;
}

.empty {
  color: #c0c4cc;
}
</style>
