// Pinia store——论文列表的状态管理。
//
// Pinia 是 Vue 3 官方推荐的状态管理库（Vuex 的继任者）。
// 作用：把"论文列表数据"和"加载状态"提到组件外，多个组件可以共享同一份数据。
//
// 这里用 setup 风格（组合式）定义 store，对新手更直观：
//   ref() 对应 state（响应式数据）
//   function 对应 action（修改 state 的方法）

import { defineStore } from 'pinia'
import { ref } from 'vue'
import { papersApi } from '../api/papers'

// defineStore('papers', () => {...})：
//   第一个参数是 store 的唯一 id（调试用）
//   第二个参数是 setup 函数，返回 state 和 action
export const usePapersStore = defineStore('papers', () => {
  // ---- state（状态）----
  // ref() 创建响应式数据：数据变化时，用到它的模板会自动更新。
  // .value 才能拿到/修改真正的值（在模板里 Vue 自动解包，不用写 .value）。
  const items = ref([])      // 论文列表数组
  const total = ref(0)       // 总数（分页用）
  const loading = ref(false) // 加载中标志，控制表格 loading 动画

  // ---- action（动作）----
  /**
   * 拉取论文列表。
   * @param {Object} params - { q?, limit?, offset? }
   * 使用场景：列表页组件 onMounted 时调用。
   */
  async function fetchList(params = {}) {
    loading.value = true
    try {
      const data = await papersApi.list(params)
      items.value = data.items
      total.value = data.total
    } finally {
      // finally：无论成功失败都执行，确保 loading 关闭。
      loading.value = false
    }
  }

  // 返回 state 和 action，模板/store 外部能访问到。
  return { items, total, loading, fetchList }
})
