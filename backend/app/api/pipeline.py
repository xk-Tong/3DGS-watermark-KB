"""
Pipeline API 端点——触发检索 + 查状态。

两个端点：
  POST /api/pipeline/run   —— 触发流水线（后台执行，立即返回）
  GET  /api/pipeline/status —— 查询上次运行状态和结果

设计取舍——为什么用 BackgroundTasks 而非同步执行？
    流水线可能跑 1-5 分钟（arXiv 限速 3s/请求 + 每篇 LLM 调用 2-5 秒）。
    同步执行会让 HTTP 请求超时（浏览器默认 30-60 秒）。
    BackgroundTasks 让请求立即返回"已开始"，流水线在后台跑，
    前端轮询 GET /status 查进度。
"""
from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from typing import Optional

from ..pipeline.runner import run_pipeline, get_status

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


class RunResponse(BaseModel):
    """POST /run 的响应——确认流水线已启动。"""
    message: str
    started: bool


class StatusResponse(BaseModel):
    """GET /status 的响应——流水线当前状态。"""
    running: bool
    last_run_at: Optional[str] = None
    last_finished_at: Optional[str] = None
    last_result: Optional[dict] = None
    last_error: Optional[str] = None


@router.post("/run", response_model=RunResponse)
def trigger_run(
    background_tasks: BackgroundTasks,
    max_results: int = 50,
):
    """
    作用：触发 AI 检索流水线（后台执行）。

    参数：
        background_tasks：FastAPI 内置的 BackgroundTasks，请求返回后在后台执行传入的函数。
        max_results：arXiv 最多拉几篇，默认 50。query 参数传入。

    返回：RunResponse，{message, started}。

    使用场景：前端"检索新论文"按钮点击调用。

    工作原理：
        BackgroundTasks 是 FastAPI 的后台任务机制。
        background_tasks.add_task(func, arg1, arg2) 注册一个函数，
        在 HTTP 响应发送完成后才执行 func(arg1, arg2)。
        这样请求立即返回，流水线在后台慢慢跑。
        前端通过轮询 GET /status 知道进度。
    """
    # 先检查是否已在运行（通过 get_status 读模块变量）。
    status = get_status()
    if status["running"]:
        return RunResponse(message="流水线正在运行中，请等待完成", started=False)

    # 注册后台任务——请求返回后才执行 run_pipeline。
    # 注意：不能直接 await run_pipeline()，因为它是同步函数（不是 async），
    # BackgroundTasks 会在线程池里执行它，不阻塞事件循环。
    background_tasks.add_task(run_pipeline, max_results=max_results)

    return RunResponse(message="流水线已启动，正在后台运行", started=True)


@router.get("/status", response_model=StatusResponse)
def get_pipeline_status():
    """
    作用：查询流水线当前运行状态和上次结果。

    返回：StatusResponse，包含 running/last_run_at/last_result 等。

    使用场景：前端触发 /run 后轮询此端点，显示进度和结果。
    """
    status = get_status()
    return StatusResponse(**status)
