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

// 定义Store('papers', () => {...})：
//   第一个参数是 store 的唯一 id（调试用）
//   第二个参数是 setup 函数，返回 state 和 action
export const usePapersStore = defineStore('papers', () => {
  // ---- state（状态）----
  // ref() 创建响应式数据：数据变化时，用到它的模板会自动更新。
  // .value 才能拿到/修改真正的值（在模板里 Vue 自动解包，不用写 .value）。
  const items = ref([])      // 论文列表数组
  const total = ref(0)       // 总数（分页用）
  const loading = ref(false) // 加载中标志，控制表格 loading 动画

  // filters：当前筛选条件，用 reactive 对象统一管理。
  // 所有字段都给默认值（null 或空字符串表示"不筛选"）。
  // 列表页的筛选条控件双向绑定到这个对象，改了就触发 fetchList。
  const filters = ref({
    q: '',                              // 关键词搜索
    task_type: null,                    // 任务类型（多选值域里的一个，null=不筛选）
    attribute_selection: null,          // 机制维度一
    distribution_strategy: null,        // 机制维度二
    injection_pipeline: null,           // 机制维度三
    year: null,                         // 年份
    read_status: null,                  // 阅读状态
    curation_status: null,             // 数据质量状态
    sort_by: 'added_at',              // 排序字段
    order: 'desc',                     // 排序方向
  })

  // 分页状态
  const limit = ref(20)      // 每页数量
  const offset = ref(0)       // 当前页起始位置（0=第一页）

  // 对比功能：选中的论文 id 列表。
  // 用 Set 存储去重，但 ref 需要 Array 才能响应式追踪，所以用数组 + includes 判断。
  // 限制 2-4 篇（决策文档定义）。
  const selectedForCompare = ref([])

  // ---- action（动作）----
  /**
   * 拉取论文列表。
   * @param {Object} extraParams - 额外覆盖参数（比如手动指定 offset 翻页）
   * 使用场景：列表页 onMounted 时调用，筛选条件变化时调用。
   */
  async function fetchList(extraParams = {}) {
    loading.value = true
    try {
      // 构造请求参数：把 filters 和分页参数合并。
      // 用展开运算符 ... 把 filters 的所有字段摊平到新对象。
      // extraParams 在最后，会覆盖前面同名字段（比如 extraParams.offset 覆盖分页）。
      const params = {
        ...filters.value,
        limit: limit.value,
        offset: offset.value,
        ...extraParams,
      }

      // 清理参数：null / 空字符串的字段不传给后端（避免后端把空字符串当筛选条件）。
      // Object.fromEntries + filter：遍历 params，只保留有值的字段。
      // Object.entries(obj) 把对象转成 [key, value] 数组，filter 过滤，fromEntries 转回对象。
      const cleanParams = Object.fromEntries(
        Object.entries(params).filter(([, v]) => v !== null && v !== '' && v !== undefined)
      )

      const data = await papersApi.list(cleanParams)
      items.value = data.items
      total.value = data.total
    } finally {
      // finally：无论成功失败都执行，确保 loading 关闭。
      loading.value = false
    }
  }

  /**
   * 重置筛选条件到默认值并重新加载。
   * 使用场景：用户点"重置筛选"按钮。
   */
  function resetFilters() {
    filters.value = {
      q: '',
      task_type: null,
      attribute_selection: null,
      distribution_strategy: null,
      injection_pipeline: null,
      year: null,
      read_status: null,
      curation_status: null,
      sort_by: 'added_at',
      order: 'desc',
    }
    offset.value = 0
    fetchList()
  }

  /**
   * 翻页——更新 offset 并重新加载。
   * @param {number} newOffset - 新的起始位置
   */
  function changePage(newOffset) {
    offset.value = newOffset
    fetchList()
  }

  /**
   * 作用：切换某篇论文的选中状态（勾选/取消勾选对比）。
   * @param {number} id - 论文 id
   * @param {boolean} selected - true=选中，false=取消
   * 限制最多 4 篇（决策文档定义 2-4 篇对比）。
   */
  function toggleCompare(id, selected) {
    if (selected) {
      // 勾选：如果已满 4 篇，不让加（返回 false 让 UI 提示）
      if (selectedForCompare.value.length >= 4) return false
      if (!selectedForCompare.value.includes(id)) {
        selectedForCompare.value.push(id)
      }
    } else {
      // 取消勾选：filter 返回不含该 id 的新数组
      selectedForCompare.value = selectedForCompare.value.filter((x) => x !== id)
    }
    return true
  }

  /**
   * 作用：清空对比选择。
   */
  function clearCompare() {
    selectedForCompare.value = []
  }

  // 返回 state 和 action，模板/store 外部能访问到。
  return {
    items, total, loading, filters, limit, offset, selectedForCompare,
    fetchList, resetFilters, changePage, toggleCompare, clearCompare,
  }
})
