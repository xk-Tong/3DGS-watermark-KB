<template>
  <!-- 列表页——Phase 1：筛选条 + 搜索 + 排序 + 分页 -->
  <div class="paper-list-view">
    <div class="header">
      <h1>3DGS 水印论文库</h1>
      <span class="subtitle">3D Gaussian Splatting IP Protection Knowledge Base</span>
      <el-button type="primary" class="add-btn" @click="createVisible = true">+ 新增论文</el-button>
    </div>

    <!-- AI 检索面板——触发 arXiv 抓取 + LLM 抽取 -->
    <PipelinePanel @updated="store.fetchList()" />

    <!-- 筛选条容器 -->
    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" :model="store.filters" label-width="auto">
        <!-- 关键词搜索：输入框 + 搜索按钮 -->
        <el-form-item>
          <el-input
            v-model="store.filters.q"
            placeholder="搜索标题/摘要/方法/批注"
            clearable
            style="width: 260px"
            @keyup.enter="handleSearch"
            @clear="handleSearch"
          />
          <!-- @keyup.enter：按下回车触发搜索；@clear：点清空按钮也触发搜索 -->
          <el-button type="primary" @click="handleSearch" style="margin-left: 8px">搜索</el-button>
        </el-form-item>

        <!-- task_type 多选筛选（这里是单选下拉，因为后端按单个值 LIKE 筛选） -->
        <el-form-item label="任务">
          <el-select v-model="store.filters.task_type" placeholder="全部" clearable style="width: 140px" @change="handleSearch">
            <!-- el-option：下拉选项。v-for 循环渲染选项列表 -->
            <el-option v-for="opt in taskTypeOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
          </el-select>
        </el-form-item>

        <!-- 机制三维度筛选 -->
        <el-form-item label="属性选择">
          <el-select v-model="store.filters.attribute_selection" placeholder="全部" clearable style="width: 130px" @change="handleSearch">
            <el-option v-for="opt in attributeOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
          </el-select>
        </el-form-item>

        <el-form-item label="分布策略">
          <el-select v-model="store.filters.distribution_strategy" placeholder="全部" clearable style="width: 140px" @change="handleSearch">
            <el-option v-for="opt in distributionOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
          </el-select>
        </el-form-item>

        <el-form-item label="注入管道">
          <el-select v-model="store.filters.injection_pipeline" placeholder="全部" clearable style="width: 140px" @change="handleSearch">
            <el-option v-for="opt in injectionOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
          </el-select>
        </el-form-item>

        <!-- 阅读状态筛选 -->
        <el-form-item label="阅读">
          <el-select v-model="store.filters.read_status" placeholder="全部" clearable style="width: 100px" @change="handleSearch">
            <el-option label="未读" value="unread" />
            <el-option label="在读" value="reading" />
            <el-option label="已读" value="read" />
          </el-select>
        </el-form-item>

        <!-- 数据质量状态筛选 -->
        <el-form-item label="质量">
          <el-select v-model="store.filters.curation_status" placeholder="全部" clearable style="width: 120px" @change="handleSearch">
            <el-option label="⚠️ AI 未核实" value="auto" />
            <el-option label="已复核" value="reviewed" />
            <el-option label="已验证" value="verified" />
          </el-select>
        </el-form-item>

        <!-- 排序选择 -->
        <el-form-item label="排序">
          <el-select v-model="store.filters.sort_by" style="width: 120px" @change="handleSearch">
            <el-option label="入库时间" value="added_at" />
            <el-option label="发表日期" value="pub_date" />
            <el-option label="PSNR" value="psnr" />
          </el-select>
          <el-button @click="toggleOrder" style="margin-left: 4px">
            <!-- 动态图标：降序显示↓，升序显示↑ -->
            {{ store.filters.order === 'desc' ? '↓' : '↑' }}
          </el-button>
        </el-form-item>

        <!-- 重置按钮 -->
        <el-form-item>
          <el-button @click="store.resetFilters()">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 论文表格 -->
    <el-table :data="store.items" v-loading="store.loading" border stripe style="width: 100%" @row-click="handleRowClick">
      <!-- 行点击跳转详情：@row-click 绑定，点击整行跳转 -->
      <el-table-column prop="title" label="标题" min-width="280" />
      <el-table-column label="作者" min-width="160">
        <template #default="{ row }">
          {{ row.authors.join(', ') }}
        </template>
      </el-table-column>
      <el-table-column label="任务类型" min-width="140">
        <template #default="{ row }">
          <el-tag v-for="t in row.task_type" :key="t" size="small" type="primary" style="margin-right: 4px">
            {{ taskTypeLabel(t) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="pub_date" label="发表日期" width="120" />
      <el-table-column label="阅读" width="80">
        <template #default="{ row }">
          <el-tag :type="readStatusType(row.read_status)" size="small">
            {{ readStatusLabel(row.read_status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="数据状态" width="130">
        <template #default="{ row }">
          <el-tag :type="statusTagType(row.curation_status)" size="small">
            {{ statusLabel(row.curation_status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="80" fixed="right">
        <template #default="{ row }">
          <router-link :to="`/papers/${row.id}`">
            <el-button link type="primary" size="small">详情</el-button>
          </router-link>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div class="footer">
      <span class="total">共 {{ store.total }} 篇</span>
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
import { usePapersStore } from '../stores/papers'
import PaperCreateDialog from '../components/PaperCreateDialog.vue'
import PipelinePanel from '../components/PipelinePanel.vue'

// useRouter：Vue Router 的编程式导航 hook，拿到 router 实例用于跳转。
const router = useRouter()
const store = usePapersStore()
const createVisible = ref(false)   // 新增弹窗显示状态

onMounted(() => {
  store.fetchList()
})

// ---- 下拉选项数据 ----
// 把后端枚举值映射成中文标签，让用户看懂。
// 这些选项和后端枚举的 value 严格对应。
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

// ---- 计算属性 ----
// currentPage：当前页码（从 offset 计算，offset=0 是第 1 页）。
// computed：计算属性，依赖的 ref 变化时自动重算。模板里用 store.currentPage 即可。
const currentPage = computed(() => Math.floor(store.offset / store.limit) + 1)

// ---- 事件处理函数 ----

/**
 * 作用：筛选条件变化时触发搜索——重置到第一页并重新加载。
 * 使用场景：所有筛选下拉的 @change、搜索按钮点击、回车、清空。
 */
function handleSearch() {
  store.offset = 0  // 筛选条件变了，回到第一页
  store.fetchList()
}

/**
 * 作用：切换排序方向（升序/降序）。
 */
function toggleOrder() {
  store.filters.order = store.filters.order === 'desc' ? 'asc' : 'desc'
  handleSearch()
}

/**
 * 作用：翻页。
 * @param {number} page - 新页码（Element Plus 传过来的，从 1 开始）
 */
function handlePageChange(page) {
  // 页码转 offset：第 1 页 offset=0，第 2 页 offset=20（每页 20 条）
  store.changePage((page - 1) * store.limit)
}

/**
 * 作用：新增论文成功后的回调——关闭弹窗 + 重新加载列表。
 */
function handleCreated() {
  createVisible.value = false
  store.fetchList()
}

/**
 * 作用：点击表格行跳转到该论文详情页。
 * @param {Object} row - 被点击行的数据对象
 * 使用场景：el-table 的 @row-click 事件，点击任意位置跳转，不限于"详情"按钮。
 */
function handleRowClick(row) {
  router.push(`/papers/${row.id}`)
}

// ---- 显示工具函数 ----
// 把后端枚举值转成中文标签，用于表格展示。
function taskTypeLabel(value) {
  const map = { watermarking: '水印', steganography: '隐写', tamper_localization: '篡改定位', editing_protection: '编辑防护', other: '其他' }
  return map[value] || value
}

function readStatusType(status) {
  const map = { unread: 'info', reading: 'warning', read: 'success' }
  return map[status] || 'info'
}

function readStatusLabel(status) {
  const map = { unread: '未读', reading: '在读', read: '已读' }
  return map[status] || status
}

function statusTagType(status) {
  const map = { auto: 'warning', reviewed: 'info', verified: 'success' }
  return map[status] || 'info'
}

function statusLabel(status) {
  const map = { auto: '⚠️ 未核实', reviewed: '已复核', verified: '已验证' }
  return map[status] || status
}
</script>

<style scoped>
/* scoped：样式只作用于当前组件，不泄漏到其他组件 */
.paper-list-view {
  max-width: 1400px;
  margin: 0 auto;
  padding: 24px;
}

.header {
  margin-bottom: 20px;
}

.header h1 {
  font-size: 22px;
  color: #303133;
  margin-bottom: 4px;
}

.subtitle {
  font-size: 13px;
  color: #909399;
}

.add-btn {
  float: right;
}

/* 筛选条卡片：浅色背景，无阴影，紧凑 */
.filter-card {
  margin-bottom: 16px;
}

.filter-card :deep(.el-form--inline .el-form-item) {
  margin-right: 12px;
  margin-bottom: 8px;
}
/* :deep()：穿透 scoped 限制，修改子组件（Element Plus）内部样式。
   因为 scoped 默认只能改当前组件的元素，改不了 Element Plus 组件内部的 class。 */

.footer {
  margin-top: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.total {
  color: #909399;
  font-size: 14px;
}
</style>
