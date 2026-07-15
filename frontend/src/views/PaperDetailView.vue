<template>
  <!-- 详情页占位——Phase 1 实现全字段卡片 + 编辑表单 -->
  <div class="placeholder">
    <el-result icon="info" title="详情页（Phase 1 实现）" sub-title="这里会展示论文全字段卡片 + 个人批注编辑区">
      <template #extra>
        <router-link to="/papers">
          <el-button type="primary">返回列表</el-button>
        </router-link>
      </template>
    </el-result>
  </div>
</template>

<script setup>
// Phase 0 占位，无逻辑
</script>

<style scoped>
.placeholder {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
}
</style>
