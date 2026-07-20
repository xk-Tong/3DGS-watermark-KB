# 3DGS_KB — 3DGS 水印论文知识库

追踪 3D Gaussian Splatting (3DGS) 水印及 IP 保护方向论文的个人知识库。
后端 FastAPI + SQLModel + SQLite，前端 Vue 3 + Vite + Element Plus。

## 快速启动（本地开发）

### 环境要求

- Python 3.12（建议 conda 独立环境）
- Node 18+（建议 nvm 管理版本）
- DeepSeek API key（可选，仅 LLM 抽取需要）

### 后端（端口 8000）

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 插入种子数据
python -m app.core.seed

# 启动开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

验证：
- `curl localhost:8000/api/health` → `{"status":"ok"}`
- 浏览器开 `localhost:8000/docs` → Swagger UI

### 前端（端口 5173）

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npx vite --port 5173
```

验证：浏览器开 `localhost:5173` → 看到首页。

> 启动顺序：**先启后端，再启前端**（前端依赖后端 API）。

## 配置 DeepSeek API Key

流水线的 LLM 抽取需要 DeepSeek API key（从 https://platform.deepseek.com/ 获取）。

```bash
cd backend
cp .env.example .env
# 编辑 .env，填入你的 key
```

`.env` 文件已被 gitignore，不会提交到仓库。

配好后在前端列表页点"检索新论文"按钮即可触发完整流水线。

## 项目结构

```
backend/   FastAPI 后端
  ├── app/models/    数据模型（Paper 表 + 8 个枚举）
  ├── app/api/       路由（papers CRUD + pipeline + stats）
  ├── app/schemas/   接口校验（Pydantic schema）
  ├── app/pipeline/  AI 流水线（arXiv 抓取 + DeepSeek 抽取）
  ├── app/core/      种子数据
  └── data/kb.db     SQLite 数据库

frontend/  Vue 3 前端
  ├── src/views/     页面（首页/列表/详情/仪表盘/对比）
  ├── src/components/ 组件（粒子Canvas/编辑弹窗/检索面板/ECharts）
  ├── src/api/       接口封装
  ├── src/stores/    Pinia 状态管理
  └── src/assets/    CSS 设计令牌

pipeline/  AI 流水线脚本
```

## 部署架构

```
用户浏览器 → 安全组(:80) → Nginx
                             ├── /api/* → 反代 uvicorn(:8000)
                             └── /*     → 前端静态文件
```

部署方式：单机直装（Nginx + systemd + SQLite）
数据库备份：cron 每日 `cp` 到备份目录

## 当前进度

### Phase 0 — 项目骨架 ✅
Paper 数据模型 + FastAPI CRUD（list/get/create）+ Vue 列表页

### Phase 1 — 核心 CRUD + 列表/详情 ✅
列表筛选条 + 详情页全字段卡片 + PATCH 更新 + 编辑表单 + 新增表单

### Phase 2 — AI 流水线 ✅
arXiv API 封装 + DeepSeek 集成（相关性过滤 + 结构化抽取）+ taxonomy prompt + 流水线编排 + 前端检索面板

### Phase 3 — 可视化 + UI 设计 ✅
- 统计仪表盘（时间线柱状图 / 机制分布 / 攻击覆盖矩阵热力图）
- 论文对比视图（勾选 2-4 篇 → 横向对比表）
- 深浅双主题配色（深色：墨蓝+辉光蓝 / 浅色：羊皮纸+墨水蓝）
- 首页 Hero（高斯粒子 Canvas 动画 + 关键数字 + 最新论文卡片）
- 自定义导航栏 + Google Fonts（Space Grotesk / Inter / JetBrains Mono）

### Phase 4 — 部署上线 ✅
Ubuntu + Miniconda + Nginx 反代 + systemd 守护 + SQLite 备份

## 技术决策

详见 `设计决策与实施路线.md`（grill-me 会话产出的决策快照）。
