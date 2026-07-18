<template>
  <!-- AI 检索面板——触发 arXiv 抓取 + LLM 抽取流水线 -->
  <div class="plate pipeline-panel" v-reveal>
    <div class="pipeline-header">
      <div class="pipeline-heading">
        <span class="eyebrow">arXiv Pipeline</span>
        <span class="pipeline-title">AI 自动检索</span>
      </div>
      <el-button
        type="primary"
        size="small"
        :loading="status.running"
        :disabled="status.running"
        @click="handleRun"
      >
        {{ status.running ? '检索中…' : '检索新论文' }}
      </el-button>
    </div>

    <!-- 上次运行结果 -->
    <div v-if="status.last_result" class="result-summary">
      <div class="stats">
        <span class="stat-chip">抓取 <b>{{ status.last_result.fetched || 0 }}</b></span>
        <span class="stat-chip">已存在 <b>{{ status.last_result.duplicated || 0 }}</b></span>
        <span class="stat-chip danger">过滤 <b>{{ status.last_result.filtered_out || 0 }}</b></span>
        <span class="stat-chip success">入库 <b>{{ status.last_result.saved || 0 }}</b></span>
        <span class="stat-chip warning" v-if="status.last_result.errors">错误 <b>{{ status.last_result.errors }}</b></span>
      </div>

      <!-- 详细记录（可折叠） -->
      <el-collapse v-if="status.last_result.details && status.last_result.details.length">
        <el-collapse-item title="详细记录" name="details">
          <div
            v-for="(d, i) in status.last_result.details"
            :key="i"
            class="detail-item"
          >
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
  </div>
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
  await fetchStatus()
})

onUnmounted(() => {
  // 组件销毁时清理定时器，防止内存泄漏
  if (pollTimer) clearInterval(pollTimer)
})

/**
 * 作用：从后端拉取流水线当前状态。
 */
async function fetchStatus() {
  try {
    status.value = await pipelineApi.getStatus()
  } catch (e) {
    // 静默失败，不打扰用户
    console.error('查状态失败:', e)
  }
}

/**
 * 作用：触发检索流水线。
 */
async function handleRun() {
  try {
    const res = await pipelineApi.run({ max_results: 50 })
    if (!res.started) {
      ElMessage.warning(res.message)
      return
    }
    ElMessage.success('检索已启动，后台运行中…')
    status.value.running = true
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
  if (pollTimer) clearInterval(pollTimer)
  pollTimer = setInterval(async () => {
    await fetchStatus()
    if (!status.value.running) {
      clearInterval(pollTimer)
      pollTimer = null
      const saved = status.value.last_result?.saved || 0
      if (saved > 0) {
        ElMessage.success(`检索完成，新增 ${saved} 篇论文`)
        emit('updated')
      } else {
        ElMessage.info('检索完成，无新论文')
      }
    }
  }, 5000)
}

const emit = defineEmits(['updated'])

// ---- 工具函数 ----
function detailClass(status) {
  if (!status) return ''
  if (status.startsWith('saved')) return 'text-success'
  if (status.startsWith('duplicated')) return 'text-info'
  if (status.startsWith('filtered_out')) return 'text-warning'
  if (status.startsWith('error')) return 'text-danger'
  return ''
}

function detailIcon(status) {
  if (!status) return '·'
  if (status.startsWith('saved')) return '✓'
  if (status.startsWith('duplicated')) return '≡'
  if (status.startsWith('filtered_out')) return '×'
  if (status.startsWith('error')) return '!'
  return '·'
}

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
  padding: 16px 20px;
  margin-bottom: var(--space-lg);
}

.pipeline-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-md);
}

.pipeline-heading {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.pipeline-title {
  font-family: var(--font-serif);
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}

.result-summary {
  margin-top: 12px;
}

/* 统计小芯片：mono 数字 + 状态色 */
.stats {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.stat-chip {
  font-size: 12px;
  color: var(--text-secondary);
  padding: 2px 8px;
  background: var(--bg-hover);
  border-radius: 3px;
}
.stat-chip b {
  font-family: var(--font-mono);
  font-weight: 500;
  color: var(--text-primary);
}
.stat-chip.success b { color: var(--success); }
.stat-chip.danger b { color: var(--warm); }
.stat-chip.warning b { color: var(--warning); }

.detail-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 0;
  font-size: 13px;
}

.detail-status {
  width: 16px;
  text-align: center;
  font-family: var(--font-mono);
}

.detail-title {
  flex: 1;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.detail-id {
  color: var(--text-tertiary);
  font-size: 12px;
  font-family: var(--font-mono);
}

.last-run {
  margin-top: 10px;
  font-size: 12px;
  color: var(--text-tertiary);
  font-family: var(--font-mono);
}

/* 状态颜色（token 化，替代 EP 默认色） */
.text-success { color: var(--success); }
.text-info { color: var(--text-tertiary); }
.text-warning { color: var(--warning); }
.text-danger { color: var(--warm); }
</style>
