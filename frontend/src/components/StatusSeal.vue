<template>
  <!-- 印章：数据质量状态的可视化。
       水印是数字时代的藏书印——已验证是朱砂白文印「验」，
       已复核是朱文印「核」，AI 未核实是虚线待办「待」。 -->
  <span class="status-seal" :class="status" :title="label">{{ char }}</span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  // curation_status：auto / reviewed / verified
  status: { type: String, default: 'auto' },
})

const chars = { verified: '验', reviewed: '核', auto: '待' }
const labels = { verified: '已验证', reviewed: '已复核', auto: 'AI 未核实' }

const char = computed(() => chars[props.status] || '?')
const label = computed(() => labels[props.status] || props.status)
</script>

<style scoped>
.status-seal {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  flex: none;
  font-family: var(--font-serif);
  font-size: 11px;
  font-weight: 600;
  line-height: 1;
  border-radius: 2px;
  user-select: none;
}

/* 白文印：朱砂底、白字，微斜像手盖的章 */
.status-seal.verified {
  background: var(--warm);
  color: #FBF5EF;
  box-shadow: inset 0 0 0 1px rgba(251, 245, 239, 0.28);
  transform: rotate(-2.5deg);
}

/* 朱文印：朱砂字、透明底 */
.status-seal.reviewed {
  color: var(--warm);
  border: 1px solid var(--warm);
  transform: rotate(-2.5deg);
}

/* 待办：琥珀虚线，不入印——还没核实 */
.status-seal.auto {
  color: var(--warning);
  border: 1px dashed var(--warning);
}
</style>
