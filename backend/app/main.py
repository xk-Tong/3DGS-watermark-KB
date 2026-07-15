"""
FastAPI 应用入口——创建 app 实例、配置中间件、挂载路由、启动建表。

启动命令：
    cd backend
    /Users/kang/.workbuddy/binaries/python/envs/default/bin/python -m uvicorn app.main:app --reload --port 8000

    app.main:app 的含义：app/main.py 文件里的 app 变量。
    --reload：代码改动后自动重启，开发期用。生产部署去掉。
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import create_db_and_tables
from .api import papers
from .config import settings


# lifespan（生命周期钩子）：替代已废弃的 @app.on_event("startup")。
# 用 @asynccontextmanager 装饰一个生成器函数：
#   - yield 之前的代码在"应用启动时"执行一次
#   - yield 之后的代码在"应用关闭时"执行一次
# 这里在启动时建表。FastAPI 0.93+ 推荐这种写法。
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时：建数据库表（幂等，表已存在则跳过）
    create_db_and_tables()
    yield
    # 关闭时的清理逻辑放这里（Phase 0 没有需要清理的）


app = FastAPI(
    title="3DGS_KB API",
    version="0.1.0",
    lifespan=lifespan,
)

# ---- CORS 配置（前后端分离必须）----
# CORS（Cross-Origin Resource Sharing，跨域资源共享）：
#   前端跑在 localhost:5173，后端跑在 localhost:8000，端口不同属于"不同源"。
#   浏览器安全策略默认阻止跨域请求，后端必须显式声明"允许哪些来源访问"。
#
# 开发期其实有双保险：vite.config.js 的 devServer.proxy 把 /api 代理到 8000，
#   浏览器看到的请求是同源 localhost:5173/api/*，理论上不触发 CORS。
#   但这里仍配置 CORS 兜底，防止调试时直接请求后端。
#
# 注意：allow_origins 不能用 ["*"] 同时 allow_credentials=True，
#   浏览器规范禁止这个组合（会拒绝带 Cookie 的跨域请求）。
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],     # 允许所有 HTTP 方法（GET/POST/PUT/DELETE）
    allow_headers=["*"],     # 允许所有请求头
)

# include_router：把 papers 路由挂到 app 上，统一加 /api 前缀。
# 最终端点：GET /api/papers、GET /api/papers/{id}、POST /api/papers
app.include_router(papers.router, prefix="/api")


@app.get("/api/health")
def health():
    """健康检查端点——联调用，验证后端是否活着。"""
    return {"status": "ok"}
