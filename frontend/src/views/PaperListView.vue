<template>
  <!-- 列表页：编目行列表——筛选板 + 排序 + 分页 + 对比勾选 -->
  <div class="paper-list-view">
    <header class="page-header" v-reveal>
      <div class="page-heading">
        <span class="eyebrow">Catalog</span>
        <h1 class="page-title">论文库</h1>
        <p class="page-intro">
          3DGS 水印与 IP 保护方向 · 共 <span class="intro-count">{{ store.total }}</span> 篇
        </p>
      </div>
      <div class="page-actions">
        <el-button
          :disabled="store.selectedForCompare.length < 2"
          @click="router.push('/compare')"
        >
          对比{{ store.selectedForCompare.length ? ` (${store.selectedForCompare.length})` : '' }}
        </el-button>
        <el-button type="primary" @click="createVisible = true">+ 新增论文</el-button>
      </div>
    </header>

    <!-- AI 检索面板——触发 arXiv 抓取 + LLM 抽取 -->
    <PipelinePanel @updated="store.fetchList()" />

    <!-- 筛选板 -->
    <div class="plate filter-plate" v-reveal>
      <el-form :model="store.filters" label-width="auto" class="filter-form">
        <el-form-item class="filter-search">
          <el-input
            v-model="store.filters.q"
            placeholder="搜索标题/摘要/方法/批注"
            clearable
            @keyup.enter="handleSearch"
            @clear="handleSearch"
          />
        </el-form-item>

        <el-form-item label="任务">
          <el-select v-model="store.filters.task_type" placeholder="全部" clearable @change="handleSearch">
            <el-option v-for="opt in taskTypeOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
          </el-select>
        </el-form-item>

        <el-form-item label="属性">
          <el-select v-model="store.filters.attribute_selection" placeholder="全部" clearable @change="handleSearch">
            <el-option v-for="opt in attributeOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
          </el-select>
        </el-form-item>

        <el-form-item label="分布">
          <el-select v-model="store.filters.distribution_strategy" placeholder="全部" clearable @change="handleSearch">
            <el-option v-for="opt in distributionOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
          </el-select>
        </el-form-item>

        <el-form-item label="注入">
          <el-select v-model="store.filters.injection_pipeline" placeholder="全部" clearable @change="handleSearch">
            <el-option v-for="opt in injectionOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
          </el-select>
        </el-form-item>

        <el-form-item label="阅读">
          <el-select v-model="store.filters.read_status" placeholder="全部" clearable @change="handleSearch">
            <el-option label="未读" value="unread" />
            <el-option label="在读" value="reading" />
            <el-option label="已读" value="read" />
          </el-select>
        </el-form-item>

        <el-form-item label="质量">
          <el-select v-model="store.filters.curation_status" placeholder="全部" clearable @change="handleSearch">
            <el-option label="AI 未核实" value="auto" />
            <el-option label="已复核" value="reviewed" />
            <el-option label="已验证" value="verified" />
          </el-select>
        </el-form-item>

        <el-form-item label="排序" class="filter-sort">
          <el-select v-model="store.filters.sort_by" @change="handleSearch">
            <el-option label="入库时间" value="added_at" />
            <el-option label="发表日期" value="pub_date" />
            <el-option label="PSNR" value="psnr" />
          </el-select>
        </el-form-item>

        <el-form-item class="filter-reset">
          <el-button text @click="store.resetFilters()">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 编目列表：<640px 用卡片视图，否则用原 grid 表格 -->
    <div v-if="isCardView" class="paper-cards" v-loading="store.loading">
      <article
        v-for="paper in store.items"
        :key="paper.id"
        class="paper-card"
        tabindex="0"
        @click="router.push(`/papers/${paper.id}`)"
        @keydown.enter="router.push(`/papers/${paper.id}`)"
      >
        <header class="card-head">
          <StatusSeal :status="paper.curation_status" />
          <span class="card-year">{{ yearOf(paper.pub_date) }}</span>
          <span class="row-read" :class="paper.read_status">{{ readStatusLabel(paper.read_status) }}</span>
        </header>
        <h3 class="card-title">{{ paper.title }}</h3>
        <p class="card-authors">{{ paper.authors.slice(0, 3).join(', ') }}{{ paper.authors.length > 3 ? ' et al.' : '' }}</p>
        <div v-if="paper.task_type && paper.task_type.length" class="card-tags">
          <span v-for="t in paper.task_type" :key="t" class="mini-tag">{{ taskTypeLabel(t) }}</span>
        </div>
        <footer class="card-foot">
          <span
            class="row-check"
            :class="{
              checked: isSelected(paper.id),
              disabled: !isSelected(paper.id) && store.selectedForCompare.length >= 4,
            }"
            :title="isSelected(paper.id) ? '移出对比' : '加入对比（最多 4 篇）'"
            @click.stop="toggleCompare(paper)"
          >
            <span class="checkmark">✓</span>
          </span>
          <el-link type="primary" :underline="false" @click.stop="router.push(`/papers/${paper.id}`)">
            详情 →
          </el-link>
        </footer>
      </article>
      <div v-if="!store.loading && !store.items.length" class="empty-state">
        没有匹配的论文——放宽筛选条件，或触发一次 AI 检索。
      </div>
    </div>

    <div v-else class="catalog" v-loading="store.loading">
      <!-- 表头：档号行。年份可点击排序 -->
      <div class="catalog-head">
        <span class="ch-check"></span>
        <button
          class="ch-year sortable"
          :class="{ active: store.filters.sort_by === 'pub_date' }"
          @click="toggleSortYear"
          title="按发表日期排序"
        >
          年份<span class="sort-arrow">{{ store.filters.sort_by === 'pub_date' ? (store.filters.order === 'desc' ? '↓' : '↑') : '↕' }}</span>
        </button>
        <span class="ch-main">标题 / 作者</span>
        <span class="ch-tags">任务</span>
        <span class="ch-read">阅读</span>
        <span class="ch-seal">状态</span>
      </div>

      <!-- 数据行 -->
      <div
        v-for="paper in store.items"
        :key="paper.id"
        class="catalog-row"
        tabindex="0"
        @click="router.push(`/papers/${paper.id}`)"
        @keydown.enter="router.push(`/papers/${paper.id}`)"
      >
        <!-- 对比勾选框：点击不触发行跳转 -->
        <span
          class="row-check"
          :class="{
            checked: isSelected(paper.id),
            disabled: !isSelected(paper.id) && store.selectedForCompare.length >= 4,
          }"
          :title="isSelected(paper.id) ? '移出对比' : '加入对比（最多 4 篇）'"
          @click.stop="toggleCompare(paper)"
        >
          <span class="checkmark">✓</span>
        </span>
        <span class="row-year">{{ yearOf(paper.pub_date) }}</span>
        <div class="row-main">
          <div class="row-title">{{ paper.title }}</div>
          <div class="row-authors">{{ paper.authors.join(', ') }}</div>
        </div>
        <div class="row-tags">
          <span v-for="t in paper.task_type" :key="t" class="mini-tag">{{ taskTypeLabel(t) }}</span>
        </div>
        <span class="row-read" :class="paper.read_status">{{ readStatusLabel(paper.read_status) }}</span>
        <span class="row-seal"><StatusSeal :status="paper.curation_status" /></span>
      </div>

      <!-- 空状态 -->
      <div v-if="!store.loading && !store.items.length" class="empty-state">
        没有匹配的论文——放宽筛选条件，或触发一次 AI 检索。
      </div>
    </div>

    <!-- 分页 -->
    <div class="list-footer">
      <span class="total-note">
        共 {{ store.total }} 篇 · 已选 {{ store.selectedForCompare.length }}/4 用于对比
      </span>
      <el-pagination
        :total="store.total"
        :page-size="store.limit"
        :current-page="currentPage"
        layout="prev, pager, next"
        @current-change="handlePageChange"
      />
    </div>

    <!-- 新增论文弹窗 -->
    <PaperCreateDialog
      v-model:visible="createVisible"
      @created="handleCreated"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { usePapersStore } from '../stores/papers'
import { useTheme } from '../composables/useTheme'
import { useMediaQuery } from '../composables/useMediaQuery'
import PaperCreateDialog from '../components/PaperCreateDialog.vue'
import PipelinePanel from '../components/PipelinePanel.vue'
import StatusSeal from '../components/StatusSeal.vue'

// 列表页用浅色主题
useTheme('light')

const router = useRouter()
const store = usePapersStore()
const createVisible = ref(false)
// <640px 切换为卡片视图
const isCardView = useMediaQuery('(max-width: 639px)')

onMounted(() => {
  store.fetchList()
})

// ---- 对比勾选 ----
function isSelected(id) {
  return store.selectedForCompare.includes(id)
}

/**
 * 勾选/取消勾选一篇论文加入对比。
 * 最多 4 篇；超限时提示而不是静默失败。
 */
function toggleCompare(paper) {
  const list = store.selectedForCompare
  const idx = list.indexOf(paper.id)
  if (idx >= 0) {
    list.splice(idx, 1)
    return
  }
  if (list.length >= 4) {
    ElMessage.warning('最多同时对比 4 篇，先取消一篇')
    return
  }
  list.push(paper.id)
}

// ---- 下拉选项 ----
const taskTypeOptions = [
  { label: '水印', value: 'watermarking' },
  { label: '隐写', value: 'steganography' },
  { label: '篡改定位', value: 'tamper_localization' },
  { label: '编辑防护', value: 'editing_protection' },
  { label: '其他', value: 'other' },
]

const attributeOptions = [
  { label: '仅SH', value: 'sh_only' },
  { label: '混合', value: 'mixed' },
  { label: '辅助属性', value: 'auxiliary' },
  { label: '其他', value: 'other' },
]

const distributionOptions = [
  { label: '全局', value: 'global' },
  { label: '局部·频率', value: 'local_frequency' },
  { label: '局部·不确定性', value: 'local_uncertainty' },
  { label: '其他', value: 'other' },
]

const injectionOptions = [
  { label: '逐资产微调', value: 'per_asset_finetune' },
  { label: '可泛化映射', value: 'generalizable_mapping' },
  { label: '生成内嵌入', value: 'generation_embedded' },
  { label: '其他', value: 'other' },
]

// 当前页码（从 offset 换算）
const currentPage = computed(() => Math.floor(store.offset / store.limit) + 1)

// ---- 事件 ----

// 筛选条件变化：回到第一页重新加载
function handleSearch() {
  store.offset = 0
  store.fetchList()
}

// 点"年份"表头：按发表日期排序；已按此排序时切换升降序
function toggleSortYear() {
  if (store.filters.sort_by === 'pub_date') {
    store.filters.order = store.filters.order === 'desc' ? 'asc' : 'desc'
  } else {
    store.filters.sort_by = 'pub_date'
    store.filters.order = 'desc'
  }
  handleSearch()
}

// 翻页
function handlePageChange(page) {
  store.changePage((page - 1) * store.limit)
}

// 新增成功后刷新
function handleCreated() {
  createVisible.value = false
  store.fetchList()
}

// ---- 显示工具 ----
function taskTypeLabel(value) {
  const map = { watermarking: '水印', steganography: '隐写', tamper_localization: '篡改定位', editing_protection: '编辑防护', other: '其他' }
  return map[value] || value
}

function readStatusLabel(status) {
  const map = { unread: '未读', reading: '在读', read: '已读' }
  return map[status] || status
}

function yearOf(dateStr) {
  return dateStr ? String(dateStr).slice(0, 4) : '—'
}
</script>

<style scoped>
.paper-list-view {
  max-width: 1200px;
  margin: 0 auto;
  padding: var(--space-xl) var(--space-lg);
}
@media (max-width: 639px) {
  .paper-list-view { padding: var(--space-lg) var(--space-md); }
  .page-header { flex-direction: column; align-items: stretch; }
  .page-actions { width: 100%; }
  .page-actions .el-button { flex: 1; }
}

/* ===== 页头 ===== */
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
  font-size: clamp(1.5rem, 5vw, 32px);
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: 0.01em;
}
.page-intro {
  font-size: 13px;
  color: var(--text-secondary);
}
.intro-count {
  font-family: var(--font-mono);
  color: var(--accent);
}
.page-actions {
  display: flex;
  gap: var(--space-sm);
  flex: none;
}

/* ===== 筛选板 ===== */
.filter-plate {
  padding: 14px 18px 6px;
  margin-bottom: var(--space-lg);
}
/* 默认（移动端）：单列 grid，控件填满单元 */
.filter-plate :deep(.filter-form) {
  display: grid;
  grid-template-columns: 1fr;
  gap: 8px;
}
/* 搜索框置顶，跨整行 */
.filter-plate :deep(.filter-search) {
  grid-column: 1 / -1;
  margin: 0;
}
.filter-plate :deep(.filter-reset) {
  margin: 0;
}
.filter-plate :deep(.el-form-item) {
  margin: 0;
}
.filter-plate :deep(.el-form-item__label) {
  font-size: 12px;
  color: var(--text-tertiary);
}
.filter-plate :deep(.el-input),
.filter-plate :deep(.el-select) {
  width: 100%;
}

/* ≥640px：2 列 grid */
@media (min-width: 640px) {
  .filter-plate :deep(.filter-form) {
    grid-template-columns: 1fr 1fr;
    gap: 10px 12px;
  }
  .filter-plate :deep(.filter-search) { grid-column: 1 / -1; }
  .filter-plate :deep(.filter-reset) { grid-column: 1 / -1; }
}

/* ≥1024px：恢复 inline 横向流 */
@media (min-width: 1024px) {
  .filter-plate :deep(.filter-form) {
    display: flex;
    flex-wrap: wrap;
    gap: 0;
  }
  .filter-plate :deep(.filter-search) { grid-column: auto; flex: 1 1 240px; }
  .filter-plate :deep(.filter-reset) { grid-column: auto; }
  .filter-plate :deep(.el-form-item) { margin-right: 14px; margin-bottom: 10px; }
  .filter-plate :deep(.el-input),
  .filter-plate :deep(.el-select) { width: auto; }
  .filter-plate :deep(.filter-form .filter-search .el-input) { width: 240px; }
  .filter-plate :deep(.filter-form .el-form-item:not(.filter-search):not(.filter-reset) .el-select) { min-width: 110px; max-width: 160px; }
}

/* ===== 编目列表 ===== */
.catalog {
  border-top: 0.5px solid var(--border-strong);
}

/* 档号表头 */
.catalog-head {
  display: grid;
  grid-template-columns: 36px 56px minmax(0, 1fr) 130px 80px 52px;
  gap: 16px;
  align-items: center;
  padding: 10px 8px;
  border-bottom: 0.5px solid var(--border-subtle);
  font-family: var(--font-mono);
  font-size: 11px;
  letter-spacing: 0.08em;
  color: var(--text-tertiary);
}
.sortable {
  background: none;
  border: none;
  padding: 0;
  font: inherit;
  color: inherit;
  letter-spacing: inherit;
  cursor: pointer;
  text-align: left;
  transition: color var(--transition);
}
.sortable:hover,
.sortable.active {
  color: var(--accent);
}
.sort-arrow {
  margin-left: 2px;
}

/* 数据行 */
.catalog-row {
  display: grid;
  grid-template-columns: 36px 56px minmax(0, 1fr) 130px 80px 52px;
  gap: 16px;
  align-items: center;
  padding: 15px 8px;
  border-bottom: 0.5px solid var(--border-subtle);
  cursor: pointer;
  transition: background var(--transition);
}
.catalog-row:hover {
  background: var(--bg-surface);
}

/* 对比勾选框：小方印盒 */
.row-check {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  border: 1px solid var(--border-strong);
  border-radius: 2px;
  cursor: pointer;
  transition: background var(--transition), border-color var(--transition);
}
.row-check .checkmark {
  font-size: 11px;
  color: var(--bg-surface);
  opacity: 0;
  transition: opacity var(--transition);
}
.row-check:hover {
  border-color: var(--accent);
}
.row-check.checked {
  background: var(--accent);
  border-color: var(--accent);
}
.row-check.checked .checkmark {
  opacity: 1;
}
.row-check.disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

.row-year {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--accent);
}

.row-main {
  min-width: 0;
}
.row-title {
  font-family: var(--font-serif);
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.5;
  transition: color var(--transition);
}
.catalog-row:hover .row-title {
  color: var(--accent);
}
.row-authors {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.row-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

/* 阅读状态：色点 + 文字 */
.row-read {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-secondary);
}
.row-read::before {
  content: '';
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--text-tertiary);
}
.row-read.reading::before { background: var(--warning); }
.row-read.read::before { background: var(--success); }

.row-seal {
  display: flex;
  justify-content: flex-end;
}

/* 空状态 */
.empty-state {
  padding: var(--space-2xl);
  text-align: center;
  color: var(--text-secondary);
  font-size: 13px;
}

/* ===== 分页 ===== */
.list-footer {
  margin-top: var(--space-lg);
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-md);
  flex-wrap: wrap;
}
.total-note {
  color: var(--text-tertiary);
  font-size: 12px;
  font-family: var(--font-mono);
}

/* 窄屏：收起任务/阅读/状态列，保证标题可读 */
@media (max-width: 900px) {
  .catalog-head .ch-tags,
  .catalog-head .ch-read,
  .catalog-head .ch-seal,
  .catalog-row .row-tags,
  .catalog-row .row-read,
  .catalog-row .row-seal {
    display: none;
  }
  .catalog-head,
  .catalog-row {
    grid-template-columns: 36px 56px minmax(0, 1fr);
  }
  .row-authors {
    display: none;
  }
}

/* ===== 卡片视图（<640px） ===== */
.paper-cards {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}
.paper-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 16px;
  background: var(--bg-surface);
  border: 0.5px solid var(--border-subtle);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
  cursor: pointer;
  transition: box-shadow var(--transition), transform var(--transition);
  min-height: 44px;
}
.paper-card:hover {
  box-shadow: var(--shadow-md);
}
.paper-card:active {
  transform: scale(0.99);
}
.card-head {
  display: flex;
  align-items: center;
  gap: 10px;
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-tertiary);
  letter-spacing: 0.06em;
}
.card-year {
  color: var(--accent);
}
.card-title {
  font-family: var(--font-serif);
  font-size: 16px;
  font-weight: 600;
  line-height: 1.5;
  color: var(--text-primary);
  margin: 0;
}
.card-authors {
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.5;
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.card-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}
.card-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 8px;
  border-top: 0.5px solid var(--border-subtle);
  margin-top: 4px;
  min-height: 36px;
}
</style>
