<template>
  <!-- AI 检索面板——触发 arXiv 抓取 + LLM 抽取流水线 -->
  <el-card class="pipeline-panel" shadow="never">
    <div class="pipeline-header">
      <span class="title">🔍 AI 自动检索</span>
      <el-button
        type="primary"
        size="small"
        :loading="status.running"
        :disabled="status.running"
        @click="handleRun"
      >
        {{ status.running ? '检索中...' : '检索新论文' }}
      </el-button>
    </div>

    <!-- 上次运行结果 -->
    <div v-if="status.last_result" class="result-summary">
      <div class="stats">
        <el-tag type="info" size="small">抓取 {{ status.last_result.fetched || 0 }}</el-tag>
        <el-tag type="info" size="small">已存在 {{ status.last_result.duplicated || 0 }}</el-tag>
        <el-tag type="danger" size="small">过滤 {{ status.last_result.filtered_out || 0 }}</el-tag>
        <el-tag type="success" size="small">入库 {{ status.last_result.saved || 0 }}</el-tag>
        <el-tag type="warning" size="small" v-if="status.last_result.errors">错误 {{ status.last_result.errors }}</el-tag>
      </div>

      <!-- 详细记录（可折叠） -->
      <el-collapse v-if="status.last_result.details && status.last_result.details.length">
        <el-collapse-item title="详细记录" name="details">
          <div
            v-for="(d, i) in status.last_result.details"
            :key="i"
            class="detail-item"
          >
            <!-- 状态图标：根据 d.status 前缀判断 -->
            <span class="detail-status" :class="detailClass(d.status)">
              {{ detailIcon(d.status) }}
            </span>
            <span class="detail-title">{{ d.title }}</span>
            <span class="detail-id" v-if="d.arxiv_id">{{ d.arxiv_id }}</span>
          </div>
        </el-collapse-item>
      </el-collapse>
    </div>

    <!-- 错误信息 -->
    <el-alert
      v-if="status.last_error"
      type="error"
      :title="status.last_error"
      :closable="false"
      style="margin-top: 8px"
    />

    <!-- 上次运行时间 -->
    <div v-if="status.last_finished_at" class="last-run">
      上次完成：{{ formatTime(status.last_finished_at) }}
    </div>
  </el-card>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { pipelineApi } from '../api/pipeline'

// 流水线状态——直接绑定后端 /status 返回的数据结构。
const status = ref({
  running: false,
  last_run_at: null,
  last_finished_at: null,
  last_result: null,
  last_error: null,
})

// 轮询定时器引用——onUnmounted 时要清掉，避免组件销毁后还在轮询。
let pollTimer = null

onMounted(async () => {
  // 组件挂载时拉一次当前状态（显示上次运行结果）
  await fetchStatus()
})

onUnmounted(() => {
  // 组件销毁时清理定时器，防止内存泄漏。
  // 内存泄漏：如果不清，定时器会继续跑，但组件已经不在了，回调里访问 ref 会报错或无效。
  if (pollTimer) clearInterval(pollTimer)
})

/**
 * 作用：从后端拉取流水线当前状态。
 */
async function fetchStatus() {
  try {
    status.value = await pipelineApi.getStatus()
  } catch (e) {
    // 静默失败，不打扰用户（状态查询失败不弹错误）
    console.error('查状态失败:', e)
  }
}

/**
 * 作用：触发检索流水线。
 * 使用场景：用户点击"检索新论文"按钮。
 */
async function handleRun() {
  try {
    const res = await pipelineApi.run({ max_results: 50 })
    if (!res.started) {
      ElMessage.warning(res.message)
      return
    }
    ElMessage.success('检索已启动，后台运行中...')
    status.value.running = true
    // 开始轮询——每 5 秒查一次状态。
    startPolling()
  } catch (e) {
    const msg = e.response?.data?.detail || e.message
    ElMessage.error('启动失败：' + msg)
  }
}

/**
 * 作用：开始轮询状态，流水线跑完后停止轮询并刷新列表。
 */
function startPolling() {
  // 清掉旧的定时器（防止重复轮询）
  if (pollTimer) clearInterval(pollTimer)

  // setInterval：每隔指定毫秒执行一次回调。
  // 这里每 5 秒查一次状态。
  pollTimer = setInterval(async () => {
    await fetchStatus()

    // 流水线跑完了（running 变 false），停止轮询。
    if (!status.value.running) {
      clearInterval(pollTimer)
      pollTimer = null

      // 如果有入库的论文，提示用户刷新列表。
      const saved = status.value.last_result?.saved || 0
      if (saved > 0) {
        ElMessage.success(`检索完成，新增 ${saved} 篇论文`)
        // 通知父组件刷新列表——通过 emit 事件。
        emit('updated')
      } else {
        ElMessage.info('检索完成，无新论文')
      }
    }
  }, 5000)
}

// emit：向父组件发事件，流水线跑完后通知列表页刷新数据。
const emit = defineEmits(['updated'])

// ---- 工具函数 ----

/**
 * 作用：根据 detail.status 前缀返回 CSS 类名（控制颜色）。
 * @param {string} status - 如 "saved" / "duplicated" / "filtered_out:..." / "error:..."
 */
function detailClass(status) {
  if (!status) return ''
  if (status.startsWith('saved')) return 'text-success'
  if (status.startsWith('duplicated')) return 'text-info'
  if (status.startsWith('filtered_out')) return 'text-warning'
  if (status.startsWith('error')) return 'text-danger'
  return ''
}

/**
 * 作用：根据 detail.status 返回状态图标。
 */
function detailIcon(status) {
  if (!status) return '•'
  if (status.startsWith('saved')) return '✅'
  if (status.startsWith('duplicated')) return '⏭️'
  if (status.startsWith('filtered_out')) return '🚫'
  if (status.startsWith('error')) return '❌'
  return '•'
}

/**
 * 作用：ISO 时间格式化成本地可读格式。
 */
function formatTime(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleString('zh-CN', {
    month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit',
  })
}
</script>

<style scoped>
.pipeline-panel {
  margin-bottom: 16px;
}

.pipeline-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.pipeline-header .title {
  font-weight: 600;
  font-size: 14px;
  color: #303133;
}

.result-summary {
  margin-top: 12px;
}

.stats {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.detail-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 0;
  font-size: 13px;
}

.detail-status {
  width: 20px;
  text-align: center;
}

.detail-title {
  flex: 1;
  color: #303133;
  /* 超长标题省略号 */
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.detail-id {
  color: #909399;
  font-size: 12px;
  font-family: monospace;
}

.last-run {
  margin-top: 8px;
  font-size: 12px;
  color: #909399;
}

/* 状态颜色 */
.text-success { color: #67c23a; }
.text-info { color: #909399; }
.text-warning { color: #e6a23c; }
.text-danger { color: #f56c6c; }
</style>
