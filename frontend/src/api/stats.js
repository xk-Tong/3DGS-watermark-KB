// 统计数据 API 封装。

import client from './client'

export const statsApi = {
  /**
   * 获取仪表盘总览统计。
   * @returns {Promise<Object>} { total, by_curation, by_task_type, by_attribute, by_distribution, by_injection, by_year }
   * 使用场景：仪表盘页面 onMounted 时加载。
   */
  getOverview: () => client.get('/stats/overview').then((r) => r.data),

  /**
   * 获取攻击覆盖矩阵数据。
   * @returns {Promise<Array>} [{ paper_id, title, arxiv_id, robustness_targets }]
   * 使用场景：攻击覆盖矩阵热力图渲染。
   */
  getRobustness: () => client.get('/stats/robustness').then((r) => r.data),
}
