// 论文相关 API 调用封装。
//
// 把后端接口调用集中到一个文件，好处：
//   1. 后端路径变了只改这里，不用每个组件里找
//   2. 组件代码只调用 papersApi.list()，不关心 URL 细节

import client from './client'

// 导出一个对象，每个方法是后端一个接口的封装。
export const papersApi = {
  /**
   * 获取论文列表（分页 + 筛选 + 排序）。
   * @param {Object} params - 查询参数，全部可选：
   *   { q?, task_type?, attribute_selection?, distribution_strategy?,
   *     injection_pipeline?, year?, read_status?, curation_status?,
   *     sort_by?, order?, limit?, offset? }
   *   不传的字段后端不会筛选，传了的字段作为筛选条件。
   * @returns {Promise<Object>} { total, items }
   * 使用场景：列表页组件 onMounted 时调用，筛选条件变化时调用。
   */
  list: (params = {}) => client.get('/papers', { params }).then((r) => r.data),
  // client.get(url, { params })：axios 把 params 对象拼成 query string。
  // 比如 { task_type: 'watermarking', limit: 20 } → /papers?task_type=watermarking&limit=20
  // 只传有的字段，undefined 的字段不会出现在 URL 里（axios 自动过滤）。

  /**
   * 获取单篇论文详情。
   * @param {number} id - 论文 id
   * @returns {Promise<Object>} 论文全字段
   */
  get: (id) => client.get(`/papers/${id}`).then((r) => r.data),

  /**
   * 创建论文。
   * @param {Object} data - 论文数据（符合 PaperCreate schema）
   * @returns {Promise<Object>} 创建后的论文（含 id）
   */
  create: (data) => client.post('/papers', data).then((r) => r.data),

  /**
   * 部分更新论文（PATCH 语义——只改传了的字段）。
   * @param {number} id - 要更新的论文 id
   * @param {Object} data - 只包含要改的字段，没传的字段保持不变
   *   例：{ read_status: 'reading' } 只改阅读状态，其他字段不动
   * @returns {Promise<Object>} 更新后的论文全字段
   * 使用场景：详情页编辑表单提交，改分类/指标/阅读状态等。
   */
  update: (id, data) => client.patch(`/papers/${id}`, data).then((r) => r.data),
  // HTTP PATCH 方法：部分更新，区别于 PUT（整体替换）。
  // 后端用 exclude_unset=True 只处理传了的字段。
}
