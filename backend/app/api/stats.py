"""
统计聚合端点——给前端仪表盘提供数据。

两个端点：
  GET /api/stats/overview     —— 总览统计（数量/分布）
  GET /api/stats/robustness   —— 攻击覆盖矩阵数据

设计取舍——为什么在后端聚合而非前端聚合？
    前端聚合要拉全部论文数据到浏览器再 count，论文多了会慢。
    后端用 SQL 聚合或 Python 端统计后只返回少量数字，传输量小。
    但 JSON 列无法用 SQL GROUP BY（SQLite 不支持 JSON 查询函数），
    所以 task_type/robustness_targets 等多选字段在 Python 端遍历统计。
"""
from collections import Counter
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import Session, select, func

from ..database import get_session
from ..models.paper import Paper, CurationStatus

router = APIRouter(prefix="/stats", tags=["stats"])


class OverviewStats(BaseModel):
    """总览统计的响应结构。

    每个字段对应仪表盘上的一个图表或卡片。
    """
    total: int
    by_curation: dict        # {auto: 28, reviewed: 0, verified: 0}
    by_task_type: dict       # {watermarking: 17, steganography: 6, ...}
    by_attribute: dict       # {sh_only: 5, mixed: 11, ...}
    by_distribution: dict    # {global: ..., local_frequency: ..., ...}
    by_injection: dict       # {per_asset_finetune: 18, ...}
    by_year: dict            # {"2024": 7, "2025": 12, "2026": 8}
    # 攻击覆盖矩阵：行是论文，列是攻击类型，值是是否覆盖
    # 这里只返回矩阵的汇总（每个攻击类型被多少篇论文评估过）


@router.get("/overview", response_model=OverviewStats)
def get_overview(session: Session = Depends(get_session)):
    """
    作用：返回仪表盘总览统计数据。

    返回：OverviewStats，包含总数、各维度分布、年份分布。

    使用场景：仪表盘页面 onMounted 时加载。
    """
    # 拉全部论文到内存做统计（28 篇规模，毫无压力）。
    # 如果将来论文到几千篇，应该改用 SQL GROUP BY 或缓存。
    papers = session.exec(select(Paper)).all()

    # Counter：collections 标准库的计数器，自动统计每个元素出现次数。
    # 例：Counter(['a','b','a']) → {'a': 2, 'b': 1}
    curation_counter = Counter(p.curation_status.value for p in papers)
    task_type_counter = Counter()
    attr_counter = Counter()
    dist_counter = Counter()
    inj_counter = Counter()
    year_counter = Counter()
    robustness_counter = Counter()

    for p in papers:
        # task_type 是 list，遍历每个元素计数
        for t in p.task_type:
            task_type_counter[t] += 1
        # 单选枚举直接 count
        if p.attribute_selection:
            attr_counter[p.attribute_selection.value] += 1
        if p.distribution_strategy:
            dist_counter[p.distribution_strategy.value] += 1
        if p.injection_pipeline:
            inj_counter[p.injection_pipeline.value] += 1
        # 年份从 pub_date 提取（格式 YYYY-MM-DD，取前 4 位）
        if p.pub_date:
            year_counter[str(p.pub_date)[:4]] += 1
        # 鲁棒性目标也是 list
        for r in p.robustness_targets:
            robustness_counter[r] += 1

    return OverviewStats(
        total=len(papers),
        by_curation=dict(curation_counter),
        by_task_type=dict(task_type_counter),
        by_attribute=dict(attr_counter),
        by_distribution=dict(dist_counter),
        by_injection=dict(inj_counter),
        by_year=dict(year_counter),
    )


class RobustnessMatrixItem(BaseModel):
    """攻击覆盖矩阵的单行——一篇论文覆盖了哪些攻击。"""
    paper_id: int
    title: str
    arxiv_id: Optional[str] = None
    robustness_targets: list[str] = []


@router.get("/robustness", response_model=list[RobustnessMatrixItem])
def get_robustness_matrix(session: Session = Depends(get_session)):
    """
    作用：返回攻击覆盖矩阵数据——每篇论文评估了哪些攻击类型。

    返回：list[RobustnessMatrixItem]，每项是一篇论文及其 robustness_targets。

    使用场景：仪表盘的攻击覆盖矩阵热力图。
    """
    papers = session.exec(select(Paper)).all()
    return [
        RobustnessMatrixItem(
            paper_id=p.id,
            title=p.title,
            arxiv_id=p.arxiv_id,
            robustness_targets=p.robustness_targets,
        )
        for p in papers
    ]
