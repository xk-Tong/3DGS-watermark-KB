// Pipeline API 调用封装——触发检索 + 查状态。

import client from './client'

export const pipelineApi = {
  /**
   * 触发 AI 检索流水线（后台执行，立即返回）。
   * @param {Object} params - { max_results?: number }
   * @returns {Promise<Object>} { message, started }
   * 使用场景：列表页"检索新论文"按钮点击调用。
   *
   * 注意：这个请求本身很快返回（只是启动后台任务），
   * 但后端 BackgroundTasks 会在响应后继续跑流水线。
   * 前端需要轮询 getStatus() 查进度。
   */
  run: (params = {}) => client.post('/pipeline/run', null, { params }).then((r) => r.data),
  // client.post(url, data, config)：第二个参数是请求体（null=不传 body），
  // 第三个参数 config 里放 query 参数（{ params: { max_results: 50 } }）。

  /**
   * 查询流水线当前状态和上次结果。
   * @returns {Promise<Object>} { running, last_run_at, last_finished_at, last_result, last_error }
   * 使用场景：触发 /run 后每隔几秒轮询一次，显示进度和结果。
   */
  getStatus: () => client.get('/pipeline/status').then((r) => r.data),
}
