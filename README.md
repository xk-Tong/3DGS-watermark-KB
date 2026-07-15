# 3DGS_KB — 3DGS 水印论文知识库

追踪 3D Gaussian Splatting (3DGS) 水印及 IP 保护方向论文的个人知识库。
后端 FastAPI + SQLModel + SQLite，前端 Vue 3 + Vite + Element Plus。

## 快速启动

### 后端（端口 8000）

```bash
cd backend

# 安装依赖（首次）
/opt/miniconda3/envs/3dgsw_kb/bin/pip install -r requirements.txt

# 插入种子数据（首次）
/opt/miniconda3/envs/3dgsw_kb/bin/python -m app.core.seed

# 启动开发服务器
/opt/miniconda3/envs/3dgsw_kb/bin/python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

验证：
- `curl localhost:8000/api/health` → `{"status":"ok"}`
- 浏览器开 `localhost:8000/docs` → Swagger UI

### 前端（端口 5173）

```bash
cd frontend

# 安装依赖（首次，用本地 nvm 的 npm）
/Users/kang/.nvm/versions/node/v24.18.0/bin/npm install

# 启动开发服务器
/Users/kang/.nvm/versions/node/v24.18.0/bin/npx vite --port 5173
```

> 也可以先 `nvm use 24` 激活环境，再直接 `npm install` / `npx vite --port 5173`。

验证：浏览器开 `localhost:5173/papers` → 看到论文列表表格。

> 启动顺序：**先启后端，再启前端**（前端依赖后端 API）。

## 数据库

- 文件：`backend/data/kb.db`（已 gitignore）
- 改 schema 后重建：`rm backend/data/kb.db` 再重启后端
- 备份：`cp backend/data/kb.db backend/data/kb.db.bak`（建议定期做）

## 项目结构

```
backend/   FastAPI 后端（app/models 数据模型、app/api 路由、app/schemas 接口校验）
frontend/  Vue 3 前端（src/views 页面、src/stores 状态、src/api 接口封装）
pipeline/  AI 流水线（Phase 2 实现：arXiv 抓取 + DeepSeek 抽取）
```

## 当前进度（Phase 2）

- ✅ Phase 0: 项目骨架 + Paper 模型 + list/get/create + 列表页
- ✅ Phase 1: 列表筛选 + 详情页 + 编辑表单 + 新增表单
- ✅ Phase 2: arXiv API 客户端（关键词搜索 + id_list 批量 + Atom XML 解析）
- ✅ Phase 2: DeepSeek LLM 集成（相关性过滤 + 结构化抽取 + taxonomy prompt）
- ✅ Phase 2: 流水线编排（arXiv→去重→过滤→抽取→入库，BackgroundTasks 后台执行）
- ✅ Phase 2: 前端检索面板（触发按钮 + 轮询状态 + 结果展示）
- ⏳ Phase 2 待测: 配置 DEEPSEEK_API_KEY 后测试完整流水线

### 配置 DeepSeek API Key

流水线的 LLM 抽取需要 DeepSeek API key（从 https://platform.deepseek.com/ 获取）：

```bash
export DEEPSEEK_API_KEY='sk-你的key'
# 然后重启后端
cd backend && /opt/miniconda3/envs/3dgsw_kb/bin/python -m uvicorn app.main:app --reload --port 8000
```

配好后在前端列表页点"检索新论文"按钮即可触发完整流水线。

下一步（Phase 3）：可视化（时间线/机制分布热力图/攻击覆盖矩阵/对比视图）。

## 技术决策

详见 `设计决策与实施路线.md`（grill-me 会话产出的决策快照）。
