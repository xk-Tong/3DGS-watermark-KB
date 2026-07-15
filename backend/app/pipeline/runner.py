"""
流水线编排——把 arXiv 抓取、相关性过滤、LLM 抽取、入库串成一条完整流水线。

流水线流程（决策文档第四节）：
  ① arXiv 拉取 → ② 相关性过滤 → ③ 去重(按arxiv_id) → ④ LLM 抽取 →
  ⑤ schema 校验 → ⑥ 入库(curation_status=auto) → ⑦ 异步人工复核

触发方式：手动触发（前端"检索"按钮调 POST /api/pipeline/run）。
日期范围：默认"距上次成功抓取"，避免漏论文（即使隔很久才点一次也不漏）。

运行状态：用模块级变量记录（单人用，不需要持久化到数据库）。
"""
import traceback
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Session, select

from ..database import engine
from ..models.paper import Paper, SourceType, CurationStatus
from . import arxiv_client
from . import llm_client


# ============================================================================
#  运行状态（模块级变量）
# ============================================================================

class PipelineStatus:
    """
    流水线运行状态容器。

    用一个类而不是散落的变量，方便统一管理和序列化成 JSON 返回给前端。
    所有字段都是类属性（直接赋值修改），不用实例化。
    """
    # 当前是否正在运行
    running: bool = False
    # 上次运行开始时间（ISO 字符串，给前端展示）
    last_run_at: Optional[str] = None
    # 上次运行结束时间
    last_finished_at: Optional[str] = None
    # 上次运行的详细结果
    last_result: Optional[dict] = None
    # 上次运行的错误信息（运行失败时）
    last_error: Optional[str] = None


def get_status() -> dict:
    """
    作用：获取当前流水线状态，返回给前端。

    返回：dict，包含 running/last_run_at/last_result 等字段。

    使用场景：GET /api/pipeline/status 端点调用，前端轮询查进度。
    """
    return {
        "running": PipelineStatus.running,
        "last_run_at": PipelineStatus.last_run_at,
        "last_finished_at": PipelineStatus.last_finished_at,
        "last_result": PipelineStatus.last_result,
        "last_error": PipelineStatus.last_error,
    }


# ============================================================================
#  流水线核心逻辑
# ============================================================================

def run_pipeline(max_results: int = 50) -> dict:
    """
    作用：执行完整的 AI 检索-抽取-入库流水线。

    参数：
        max_results：arXiv 搜索最多拉几篇，默认 50。

    返回：dict，运行结果摘要（fetched/filtered/duplicated/extracted/saved/errors + details）。

    流程：
        1. arXiv 关键词搜索拉取候选论文
        2. 去重（按 arxiv_id，跳过库里已有的）
        3. 逐篇 LLM 相关性过滤（剔除不相关的）
        4. 对相关的逐篇 LLM 抽取分类字段
        5. schema 校验 + 入库（curation_status=auto）
        6. 返回结果摘要

    使用场景：POST /api/pipeline/run 端点调用（通过 BackgroundTasks 后台执行）。
    """
    # 防止并发运行：如果已经在跑，直接返回"正在运行中"。
    if PipelineStatus.running:
        return {"error": "流水线正在运行中，请等待完成"}

    # 标记开始运行
    PipelineStatus.running = True
    PipelineStatus.last_run_at = datetime.now(timezone.utc).isoformat()
    PipelineStatus.last_error = None

    # 结果统计容器——用 dict 而非一堆变量，方便最后整体返回。
    result = {
        "fetched": 0,        # arXiv 拉取总数
        "duplicated": 0,     # 已在库中跳过的
        "filtered_out": 0,   # 相关性过滤剔除的
        "relevant": 0,       # 通过相关性过滤的
        "saved": 0,          # 成功入库的
        "errors": 0,         # 出错的
        "details": [],       # 每篇论文的处理记录
    }

    try:
        # ---- 步骤 1：arXiv 关键词搜索 ----
        papers = arxiv_client.search_papers(
            arxiv_client.DEFAULT_SEARCH_QUERY,
            max_results=max_results,
        )
        result["fetched"] = len(papers)

        # ---- 步骤 2-5：逐篇处理 ----
        with Session(engine) as session:
            for paper_data in papers:
                arxiv_id = paper_data.get("arxiv_id", "")
                title = paper_data.get("title", "无标题")
                detail = {"arxiv_id": arxiv_id, "title": title, "status": ""}

                try:
                    # 步骤 2：去重——检查库里是否已有这个 arxiv_id
                    existing = session.exec(
                        select(Paper).where(Paper.arxiv_id == arxiv_id)
                    ).first()
                    if existing:
                        result["duplicated"] += 1
                        detail["status"] = "duplicated"
                        result["details"].append(detail)
                        continue

                    # 步骤 3：LLM 相关性过滤
                    relevance = llm_client.check_relevance(title, paper_data.get("abstract", ""))
                    if not relevance.get("relevant", False):
                        result["filtered_out"] += 1
                        detail["status"] = f"filtered_out: {relevance.get('reason', '')}"
                        result["details"].append(detail)
                        continue

                    result["relevant"] += 1

                    # 步骤 4：LLM 结构化抽取
                    extracted = llm_client.extract_paper_fields(title, paper_data.get("abstract", ""))

                    # 步骤 5：构造 Paper 对象并入库
                    paper = _build_paper(paper_data, extracted)
                    session.add(paper)
                    session.commit()
                    session.refresh(paper)

                    result["saved"] += 1
                    detail["status"] = "saved"
                    detail["paper_id"] = paper.id
                    result["details"].append(detail)

                except Exception as e:
                    # 单篇出错不影响其他论文——记下来继续处理下一篇。
                    # traceback.format_exc() 拿完整错误堆栈，调试用。
                    result["errors"] += 1
                    detail["status"] = f"error: {str(e)[:100]}"
                    result["details"].append(detail)

        # 记录完成
        PipelineStatus.last_result = result
        PipelineStatus.last_finished_at = datetime.now(timezone.utc).isoformat()
        return result

    except Exception as e:
        # 整个流水线级别的错误（如 arXiv API 挂了、网络断了）
        PipelineStatus.last_error = f"{type(e).__name__}: {str(e)}"
        PipelineStatus.last_error_traceback = traceback.format_exc()
        return {"error": str(e), "partial_result": result}

    finally:
        # finally：无论成功失败都标记为"不在运行"。
        # 不写在 try/except 里是为了保证一定执行（即使 except 里又抛异常）。
        PipelineStatus.running = False


def _build_paper(arxiv_data: dict, extracted: dict) -> Paper:
    """
    作用：把 arXiv 元数据 + LLM 抽取结果合并成 Paper ORM 对象。

    参数：
        arxiv_data：arXiv API 返回的元数据 dict（arxiv_id/title/authors/abstract/published 等）。
        extracted：LLM 抽取的分类字段 dict（task_type/attribute_selection 等）。

    返回：Paper ORM 实例（未入库，调用方负责 session.add + commit）。

    设计要点：
        - arXiv 直接给的字段（title/authors/abstract/pub_date）用 arxiv_data，
          不进 LLM——决策文档明确"LLM 只负责分类字段和摘要性内容"。
        - LLM 抽取的分类字段用 extracted。
        - pub_date 从 arXiv 的 published 字段解析（格式 2024-10-04T00:00:00Z → date 对象）。
        - curation_status 固定设为 auto（AI 抽取未核实）。
        - source 固定设为 arxiv_auto。
    """
    from datetime import date

    # 解析发表日期：arXiv 返回 ISO 8601 格式如 "2024-10-04T00:00:00Z"。
    # 取前 10 个字符 "2024-10-04"，用 date.fromisoformat 解析成 date 对象。
    pub_date_str = arxiv_data.get("published", "")
    pub_date = None
    if pub_date_str and len(pub_date_str) >= 10:
        try:
            pub_date = date.fromisoformat(pub_date_str[:10])
        except ValueError:
            pub_date = None

    # 构造 Paper 对象。
    # arxiv_data 提供身份和内容字段，extracted 提供分类和技术字段。
    paper = Paper(
        # 身份字段——来自 arXiv
        arxiv_id=arxiv_data.get("arxiv_id"),
        doi=arxiv_data.get("doi"),
        title=arxiv_data.get("title", ""),
        authors=arxiv_data.get("authors", []),
        venue="arXiv preprint",
        pub_date=pub_date,
        source=SourceType.arxiv_auto,
        # added_at 用模型默认值（datetime.utcnow）

        # 内容字段——abstract 来自 arXiv，method_summary/key_contributions 来自 LLM
        abstract=arxiv_data.get("abstract", ""),
        pdf_url=arxiv_data.get("pdf_url"),

        # 分类字段——来自 LLM 抽取
        task_type=extracted.get("task_type", []),
        attribute_selection=extracted.get("attribute_selection"),
        distribution_strategy=extracted.get("distribution_strategy"),
        injection_pipeline=extracted.get("injection_pipeline"),
        robustness_targets=extracted.get("robustness_targets", []),
        tags=extracted.get("tags", []),

        # 方法摘要——来自 LLM
        method_summary=extracted.get("method_summary"),
        key_contributions=extracted.get("key_contributions", []),

        # 技术字段——来自 LLM（可能为空，等人工补充）
        capacity=extracted.get("capacity"),
        datasets_used=extracted.get("datasets_used", []),
        baselines_compared=extracted.get("baselines_compared", []),

        # 个人字段——固定默认值
        curation_status=CurationStatus.auto,  # AI 抽取，未核实
    )
    return paper
