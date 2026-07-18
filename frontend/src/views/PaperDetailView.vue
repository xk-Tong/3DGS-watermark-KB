<template>
  <div class="paper-detail-view" v-loading="loading">
    <!-- 顶栏：返回 + 编辑 -->
    <div class="detail-topbar">
      <button class="back-link" @click="router.back()">← 返回列表</button>
      <el-button type="primary" plain size="small" @click="openEditDialog">编辑</el-button>
    </div>

    <!-- 论文不存在时的空状态 -->
    <el-empty v-if="!loading && !paper" description="论文不存在" />

    <template v-if="paper">
      <!-- ===== 档案头：元数据 + 宋体题名 ===== -->
      <header class="plate detail-header" v-reveal>
        <div class="detail-meta">
          <a
            v-if="paper.arxiv_id"
            :href="`https://arxiv.org/abs/${paper.arxiv_id}`"
            target="_blank"
            class="meta-chip link"
          >arXiv {{ paper.arxiv_id }}</a>
          <span class="meta-chip">{{ paper.pub_date || '日期未知' }}</span>
          <span class="meta-chip">{{ labelOf(sourceOptions, paper.source) }}</span>
          <span v-if="paper.venue" class="meta-chip">{{ paper.venue }}</span>
          <StatusSeal :status="paper.curation_status" />
        </div>
        <h1 class="detail-title">{{ paper.title }}</h1>
        <p class="detail-authors">{{ paper.authors.join(', ') }}</p>
        <div class="detail-links" v-if="paper.pdf_url || paper.code_url || paper.doi">
          <a v-if="paper.pdf_url" :href="paper.pdf_url" target="_blank" class="ext-link">PDF ↗</a>
          <a v-if="paper.code_url" :href="paper.code_url" target="_blank" class="ext-link">代码仓库 ↗</a>
          <a v-if="paper.doi" :href="`https://doi.org/${paper.doi}`" target="_blank" class="ext-link">DOI ↗</a>
        </div>
      </header>

      <!-- ===== 摘要 ===== -->
      <section class="plate" v-reveal>
        <div class="plate-header">
          <span class="plate-title">摘要</span>
          <span class="plate-note">Abstract</span>
        </div>
        <div class="plate-body abstract-text">{{ paper.abstract || '—' }}</div>
      </section>

      <!-- ===== 方法概述（AI 抽取）===== -->
      <section class="plate" v-reveal>
        <div class="plate-header">
          <span class="plate-title">方法概述</span>
          <span class="plate-note">AI 抽取</span>
        </div>
        <div class="plate-body">
          <div v-if="paper.method_summary" class="abstract-text">{{ paper.method_summary }}</div>
          <div v-else class="empty-note">暂无——AI 流水线尚未抽取</div>
          <div v-if="paper.key_contributions && paper.key_contributions.length" class="contributions">
            <div class="sub-title">关键贡献</div>
            <ol>
              <li v-for="(c, i) in paper.key_contributions" :key="i">{{ c }}</li>
            </ol>
          </div>
        </div>
      </section>

      <!-- ===== 机制分类 + 实验数据（双栏）===== -->
      <div class="detail-grid">
        <section class="plate" v-reveal>
          <div class="plate-header">
            <span class="plate-title">机制分类</span>
            <span class="plate-note">Taxonomy</span>
          </div>
          <div class="plate-body">
            <div class="def-row">
              <span class="def-label">任务类型</span>
              <div class="def-value">
                <span v-for="t in paper.task_type" :key="t" class="mini-tag">{{ labelOf(taskTypeOptions, t) }}</span>
              </div>
            </div>
            <div class="def-row">
              <span class="def-label">属性选择</span>
              <div class="def-value">{{ labelOf(attributeOptions, paper.attribute_selection) || '—' }}</div>
            </div>
            <div class="def-row">
              <span class="def-label">分布策略</span>
              <div class="def-value">{{ labelOf(distributionOptions, paper.distribution_strategy) || '—' }}</div>
            </div>
            <div class="def-row">
              <span class="def-label">注入管道</span>
              <div class="def-value">{{ labelOf(injectionOptions, paper.injection_pipeline) || '—' }}</div>
            </div>
            <div class="def-row">
              <span class="def-label">鲁棒性</span>
              <div class="def-value">
                <template v-if="paper.robustness_targets.length">
                  <span v-for="r in paper.robustness_targets" :key="r" class="mini-tag muted">{{ robustnessLabel(r) }}</span>
                </template>
                <span v-else>—</span>
              </div>
            </div>
            <div class="def-row">
              <span class="def-label">标签</span>
              <div class="def-value">
                <template v-if="paper.tags.length">
                  <span v-for="t in paper.tags" :key="t" class="mini-tag muted">{{ t }}</span>
                </template>
                <span v-else>—</span>
              </div>
            </div>
          </div>
        </section>

        <section class="plate" v-reveal="80">
          <div class="plate-header">
            <span class="plate-title">实验数据</span>
            <span class="plate-note">Metrics</span>
          </div>
          <div class="plate-body">
            <!-- 指标磁贴：大数字是档案页的视觉锚点 -->
            <div class="metric-tiles">
              <div class="metric-tile">
                <span class="metric-value">{{ paper.psnr != null ? paper.psnr.toFixed(2) : '—' }}</span>
                <span class="metric-label">PSNR dB</span>
              </div>
              <div class="metric-tile">
                <span class="metric-value">{{ paper.ssim != null ? paper.ssim.toFixed(4) : '—' }}</span>
                <span class="metric-label">SSIM</span>
              </div>
              <div class="metric-tile">
                <span class="metric-value">{{ paper.bit_accuracy != null ? (paper.bit_accuracy * 100).toFixed(1) + '%' : '—' }}</span>
                <span class="metric-label">Bit Acc</span>
              </div>
            </div>
            <div class="def-row">
              <span class="def-label">容量</span>
              <div class="def-value">{{ paper.capacity || '—' }}</div>
            </div>
            <div class="def-row">
              <span class="def-label">数据集</span>
              <div class="def-value">
                {{ paper.datasets_used && paper.datasets_used.length ? paper.datasets_used.join(', ') : '—' }}
              </div>
            </div>
            <div class="def-row">
              <span class="def-label">基线</span>
              <div class="def-value">
                {{ paper.baselines_compared && paper.baselines_compared.length ? paper.baselines_compared.join(', ') : '—' }}
              </div>
            </div>
            <div v-if="paper.extra_metrics && Object.keys(paper.extra_metrics).length" class="extra-metrics">
              <pre>{{ JSON.stringify(paper.extra_metrics, null, 2) }}</pre>
            </div>
          </div>
        </section>
      </div>

      <!-- ===== 个人使用 ===== -->
      <section class="plate" v-reveal>
        <div class="plate-header">
          <span class="plate-title">个人使用</span>
          <span class="plate-note">Notes</span>
        </div>
        <div class="plate-body">
          <div class="def-row">
            <span class="def-label">阅读状态</span>
            <div class="def-value">
              <span class="read-status" :class="paper.read_status">{{ labelOf(readStatusOptions, paper.read_status) }}</span>
            </div>
          </div>
          <div class="def-row">
            <span class="def-label">数据状态</span>
            <div class="def-value seal-value">
              <StatusSeal :status="paper.curation_status" />
              <span>{{ labelOf(curationStatusOptions, paper.curation_status) }}</span>
            </div>
          </div>
          <div class="def-row">
            <span class="def-label">最后复核</span>
            <div class="def-value">{{ paper.last_reviewed_at ? formatDateTime(paper.last_reviewed_at) : '未复核' }}</div>
          </div>
          <div class="def-row">
            <span class="def-label">入库时间</span>
            <div class="def-value">{{ formatDateTime(paper.added_at) }}</div>
          </div>
          <div class="def-row">
            <span class="def-label">个人批注</span>
            <div class="def-value">
              <div v-if="paper.personal_notes" class="notes-text">{{ paper.personal_notes }}</div>
              <span v-else class="empty-note">点击"编辑"添加批注</span>
            </div>
          </div>
        </div>
      </section>
    </template>

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
import StatusSeal from '../components/StatusSeal.vue'

// 详情页用浅色主题（长文阅读舒适）
useTheme('light')

const route = useRoute()
const router = useRouter()

const paper = ref(null)
const loading = ref(true)
const editVisible = ref(false)

onMounted(async () => {
  await loadPaper()
})

/**
 * 作用：从后端加载当前论文数据。
 */
async function loadPaper() {
  loading.value = true
  try {
    const id = Number(route.params.id)
    paper.value = await papersApi.get(id)
  } catch (e) {
    console.error('加载论文失败:', e)
  } finally {
    loading.value = false
  }
}

function openEditDialog() {
  editVisible.value = true
}

function handleSaved() {
  editVisible.value = false
  loadPaper()
}

// ---- 工具函数 ----
function robustnessLabel(value) {
  const all = [...robustness2DOptions, ...robustness3DOptions]
  return labelOf(all, value)
}

function formatDateTime(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleString('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit',
  })
}
</script>

<style scoped>
.paper-detail-view {
  max-width: 960px;
  margin: 0 auto;
  padding: var(--space-xl) var(--space-lg);
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

/* ===== 顶栏 ===== */
.detail-topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.back-link {
  background: none;
  border: none;
  padding: 0;
  font-size: 13px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: color var(--transition);
}
.back-link:hover {
  color: var(--text-primary);
}

/* ===== 档案头 ===== */
.detail-header {
  padding: var(--space-lg) var(--space-xl);
}
.detail-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: var(--space-md);
}
.meta-chip {
  font-family: var(--font-mono);
  font-size: 11px;
  letter-spacing: 0.04em;
  color: var(--text-secondary);
  padding: 2px 8px;
  border: 0.5px solid var(--border-subtle);
  border-radius: 3px;
  text-decoration: none;
}
.meta-chip.link {
  color: var(--accent);
  transition: border-color var(--transition);
}
.meta-chip.link:hover {
  border-color: var(--accent);
}
.detail-title {
  font-family: var(--font-serif);
  font-size: 28px;
  font-weight: 700;
  line-height: 1.4;
  color: var(--text-primary);
  margin-bottom: var(--space-sm);
}
.detail-authors {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.6;
}
.detail-links {
  display: flex;
  gap: var(--space-lg);
  margin-top: var(--space-md);
}
.ext-link {
  font-size: 13px;
  color: var(--accent);
  text-decoration: none;
  transition: color var(--transition);
}
.ext-link:hover {
  color: var(--accent-hover);
}

/* ===== 正文段落 ===== */
.abstract-text {
  font-size: 14px;
  line-height: 1.9;
  color: var(--text-primary);
  white-space: pre-wrap;
}

.contributions {
  margin-top: var(--space-md);
}
.sub-title {
  font-family: var(--font-serif);
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 8px;
  color: var(--text-primary);
}
.contributions ol {
  padding-left: 20px;
  margin: 0;
}
.contributions li {
  font-size: 13px;
  line-height: 1.9;
  color: var(--text-primary);
}

/* ===== 双栏：分类 + 数据 ===== */
.detail-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-md);
  align-items: start;
}
@media (max-width: 860px) {
  .detail-grid { grid-template-columns: 1fr; }
}

/* mini-tag 的素色变体（鲁棒性/自由标签，不抢任务类型的墨蓝） */
.mini-tag.muted {
  background: var(--bg-hover);
  color: var(--text-secondary);
  margin-right: 4px;
}

/* 指标磁贴 */
.metric-tiles {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-sm);
  margin-bottom: var(--space-md);
}
.metric-tile {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 12px;
  background: var(--bg-base);
  border: 0.5px solid var(--border-subtle);
  border-radius: var(--radius-sm);
}
.metric-value {
  font-family: var(--font-display);
  font-size: 22px;
  font-weight: 600;
  color: var(--accent);
  line-height: 1;
}
.metric-label {
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-tertiary);
}

.extra-metrics pre {
  margin: 12px 0 0;
  background: var(--bg-base);
  border: 0.5px solid var(--border-subtle);
  padding: 12px;
  border-radius: var(--radius-sm);
  font-size: 12px;
  overflow-x: auto;
}

/* 阅读状态：色点 + 文字（与列表页一致） */
.read-status {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
}
.read-status::before {
  content: '';
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--text-tertiary);
}
.read-status.reading::before { background: var(--warning); }
.read-status.read::before { background: var(--success); }

.seal-value {
  display: flex;
  align-items: center;
  gap: 8px;
}

.notes-text {
  white-space: pre-wrap;
  line-height: 1.8;
}
.empty-note {
  color: var(--text-tertiary);
  font-size: 13px;
}
</style>
