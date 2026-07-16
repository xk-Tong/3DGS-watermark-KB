<template>
  <!-- ECharts 图表容器——封装初始化/更新/销毁逻辑，子组件只需传 option prop -->
  <div ref="chartRef" :style="{ width: '100%', height: height }"></div>
</template>

<script setup>
// EChartsBase.vue —— ECharts 图表通用封装。
//
// 为什么需要封装？
//   ECharts 每次 render 都要：init → setOption → resize 监听 → dispose。
//   每个图表都写一遍很啰嗦，封装后子组件只需传 option。
//
// 用法：<EChartsBase :option="myOption" height="300px" />
//   option：ECharts 配置对象（reactive，变化自动更新图表）
//   height：图表高度，默认 300px

import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'

// defineProps：声明接收的属性。
// option 是 Object 类型，必须传（required: true）；height 默认 300px。
const props = defineProps({
  option: { type: Object, required: true },
  height: { type: String, default: '300px' },
})

// ref：模板引用（template ref）。ref(null) 初始为 null，
// 组件挂载后 Vue 自动把 DOM 元素赋值给它（名字和 template 里 ref="chartRef" 对应）。
const chartRef = ref(null)
// chartInstance：ECharts 实例，init 后赋值。
let chartInstance = null

// ResizeObserver：监听容器尺寸变化，自动 resize 图表。
// 比监听 window.resize 更精准（容器被父级 flex 压缩时 window 没变但容器变了）。
let resizeObserver = null

onMounted(() => {
  // echarts.init(dom)：把一个 DOM 元素初始化成 ECharts 实例。
  // 之后所有 setOption 都作用在这个实例上。
  chartInstance = echarts.init(chartRef.value)
  // setOption：设置图表配置，第一次调用会渲染图表。
  chartInstance.setOption(props.option)

  // ResizeObserver：监听容器宽度变化，自动调整图表尺寸。
  resizeObserver = new ResizeObserver(() => {
    chartInstance?.resize()
  })
  resizeObserver.observe(chartRef.value)
})

// watch：监听 option 变化，变化时调用 setOption 更新图表（不重新 init）。
// 这是 ECharts 的标准更新方式——setOption 会做 diff，只更新变化的部分。
watch(
  () => props.option,
  (newOption) => {
    chartInstance?.setOption(newOption, true)
    // 第二个参数 true：notMerge，完全替换而非合并。
    // 数据变了但配置结构没变时用 false（默认）更高效；
    // 配置结构变了（如换图表类型）用 true 更安全。
  },
  { deep: true }  // deep: true 深度监听对象内部变化
)

onUnmounted(() => {
  // 清理：组件销毁时释放 ECharts 实例和 ResizeObserver，防止内存泄漏。
  resizeObserver?.disconnect()
  chartInstance?.dispose()
  chartInstance = null
})
</script>
