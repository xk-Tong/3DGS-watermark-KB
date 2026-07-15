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

# 启动开发服务器（依赖已装在 workspace，通过 node_modules 软链接解析）
PATH=/Users/kang/.workbuddy/binaries/node/versions/22.22.2/bin:$PATH \
  /Users/kang/.workbuddy/binaries/node/versions/22.22.2/bin/npx vite --port 5173
```

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

## 当前进度（Phase 0）

- ✅ 项目骨架 + git
- ✅ Paper 数据模型（SQLModel + 全部枚举 + JSON 列）
- ✅ FastAPI CRUD（list / get / create）
- ✅ Vue 列表页（Element Plus 表格 + Pinia + Router）
- ✅ 前后端联调跑通

下一步（Phase 1）：列表筛选条、详情页全字段卡片、update 端点 + 编辑表单。

## 技术决策

详见 `设计决策与实施路线.md`（grill-me 会话产出的决策快照）。
