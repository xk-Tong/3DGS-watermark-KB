<template>
  <!-- 列表页——Phase 0 的里程碑页面 -->
  <div class="paper-list-view">
    <div class="header">
      <h1>3DGS 水印论文库</h1>
      <span class="subtitle">3D Gaussian Splatting IP Protection Knowledge Base</span>
    </div>

    <!-- el-table：Element Plus 的表格组件。
         :data 绑定数据源；v-loading 绑定加载状态（显示转圈动画）；
         border 显示边框；stripe 斑马纹（隔行变色，提升可读性） -->
    <el-table :data="store.items" v-loading="store.loading" border stripe style="width: 100%">
      <!-- el-table-column：每一列。
           prop 对应数据的字段名；label 是表头文字；
           min-width 列最小宽度（会自适应）；width 固定宽度 -->
      <el-table-column prop="title" label="标题" min-width="280" />

      <!-- 自定义列内容：用 #default 插槽。
           { row } 是解构赋值，row 是当前行的数据对象 -->
      <el-table-column label="作者" min-width="160">
        <template #default="{ row }">
          <!-- join：把作者数组用逗号拼成字符串 -->
          {{ row.authors.join(', ') }}
        </template>
      </el-table-column>

      <!-- 任务类型：用 el-tag 标签展示（多选，可能多个） -->
      <el-table-column label="任务类型" min-width="140">
        <template #default="{ row }">
          <!-- v-for：循环渲染每个 tag。
               :key 是循环的 key（帮助 Vue 高效更新，必须唯一） -->
          <el-tag v-for="t in row.task_type" :key="t" size="small" type="primary" style="margin-right: 4px">
            {{ t }}
          </el-tag>
        </template>
      </el-table-column>

      <el-table-column prop="pub_date" label="发表日期" width="120" />

      <!-- curation_status 徽章：不同状态不同颜色 -->
      <el-table-column label="数据状态" width="130">
        <template #default="{ row }">
          <el-tag :type="statusTagType(row.curation_status)" size="small">
            {{ statusLabel(row.curation_status) }}
          </el-tag>
        </template>
      </el-table-column>

      <!-- 操作列：跳转详情（Phase 1 实现编辑/删除） -->
      <el-table-column label="操作" width="80" fixed="right">
        <template #default="{ row }">
          <!-- router-link：Vue Router 的导航组件，渲染成 <a> 标签但不刷新页面 -->
          <router-link :to="`/papers/${row.id}`">
            <el-button link type="primary" size="small">详情</el-button>
          </router-link>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页（Phase 0 简易版，Phase 1 加完整分页交互） -->
    <div class="footer">
      <span class="total">共 {{ store.total }} 篇</span>
    </div>
  </div>
</template>

<script setup>
// <script setup>：Vue 3 组件逻辑，编译后自动暴露给模板使用。
import { onMounted } from 'vue'
import { usePapersStore } from '../stores/papers'

// 获取 store 实例。usePapersStore() 必须在 setup 里调用（组件初始化时）。
const store = usePapersStore()

// onMounted：生命周期钩子，组件挂载到 DOM 后执行。
// 在这里发起请求加载论文列表。
onMounted(() => {
  store.fetchList({ limit: 20 })
})

// curation_status 徽章样式映射：auto 警告色、reviewed/info、verified 成功色
// 返回的是 Element Plus el-tag 的 type 属性值。
function statusTagType(status) {
  const map = {
    auto: 'warning',      // 黄色：⚠️ 未核实
    reviewed: 'info',     // 蓝色：已复核
    verified: 'success',  // 绿色：已验证
  }
  return map[status] || 'info'
}

// curation_status 中文标签
function statusLabel(status) {
  const map = {
    auto: '⚠️ AI 未核实',
    reviewed: '已复核',
    verified: '已验证',
  }
  return map[status] || status
}
</script>

<style scoped>
/* scoped：样式只作用于当前组件，不泄漏到其他组件 */
.paper-list-view {
  max-width: 1200px;
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

.footer {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

.total {
  color: #909399;
  font-size: 14px;
}
</style>
