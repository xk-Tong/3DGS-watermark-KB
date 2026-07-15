// 论文相关 API 调用封装。
//
// 把后端接口调用集中到一个文件，好处：
//   1. 后端路径变了只改这里，不用每个组件里找
//   2. 组件代码只调用 papersApi.list()，不关心 URL 细节

import client from './client'

// 导出一个对象，每个方法是后端一个接口的封装。
export const papersApi = {
  /**
   * 获取论文列表（分页）。
   * @param {Object} params - 查询参数：{ q?, limit?, offset? }
   * @returns {Promise<Object>} { total, items }
   * 使用场景：列表页 onMounted 时调用加载。
   */
  list: (params = {}) => client.get('/papers', { params }).then((r) => r.data),
  // .then(r => r.data)：axios 响应数据在 r.data 里，直接解包返回业务数据。

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
}
