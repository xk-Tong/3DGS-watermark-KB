// axios 实例——封装公共请求配置。
//
// axios.create() 创建一个带默认配置的实例，所有请求复用这些配置。
// 好处：改 baseURL/超时/请求头只改一处，不用每个请求都写一遍。

import axios from 'axios'

// baseURL: '/api' —— 所有请求自动加 /api 前缀。
// 比如 client.get('/papers') 实际请求 /api/papers。
// 开发期 Vite devServer.proxy 把 /api 转发到后端 8000，无需写完整 URL。
const client = axios.create({
  baseURL: '/api',
  timeout: 10000,  // 10 秒超时，超时后请求自动取消并报错
})

export default client
