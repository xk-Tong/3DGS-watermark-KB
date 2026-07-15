"""
论文 CRUD 路由（Phase 0 仅 list/get/create）。

APIRouter：FastAPI 的路由分组机制。把相关端点组织在一个 router 里，
再在 main.py 用 include_router 挂到 app 上。好处是按模块拆分，main.py 保持干净。
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select, func

from ..database import get_session
from ..models.paper import Paper
from ..schemas.paper import PaperCreate, PaperRead, PaperListResponse

# prefix="/papers"：这个 router 下所有路径都自动加 /papers 前缀。
# 比如 @router.get("") 实际路径是 /papers（加上 main.py 的 /api 前缀就是 /api/papers）。
# tags=["papers"]：在 Swagger UI（/docs）里按 tag 分组的分类标签。
router = APIRouter(prefix="/papers", tags=["papers"])


@router.get("", response_model=PaperListResponse)
def list_papers(
    q: Optional[str] = Query(None, description="关键词，搜 title 和 abstract"),
    limit: int = Query(20, le=100, description="每页数量，最大 100"),
    offset: int = Query(0, ge=0, description="跳过前 N 条，用于分页"),
    session: Session = Depends(get_session),
):
    """
    作用：分页查询论文列表，可选关键词搜索。

    参数：
        q：关键词，在 title 和 abstract 上做 LIKE 模糊匹配。None 表示不搜。
        limit：每页数量，默认 20，上限 100（防止一次拉太多拖慢）。
        offset：跳过前 N 条，配合 limit 实现分页（第 2 页 = offset=20）。
        session：数据库会话，由 Depends(get_session) 自动注入。

    返回：PaperListResponse（{total, items}）。

    使用场景：前端列表页加载时调用 GET /api/papers?limit=20。
    """
    # select(Paper) 构造一个 SELECT 语句（还没执行），类似 SQL 的 SELECT * FROM papers。
    stmt = select(Paper)

    if q:
        # LIKE 模糊匹配。% 匹配任意字符，所以 "%watermark%" 匹配任何含 watermark 的字符串。
        # | 是 SQLModel/SQLAlchemy 的 OR 操作符，组合两个条件为"标题或摘要包含 q"。
        like = f"%{q}%"
        stmt = stmt.where(
            Paper.title.like(like) | Paper.abstract.like(like)
        )

    # 先算总数（分页前），用 func.count() 生成 SELECT COUNT(*)。
    # 注意要 select_from(stmt.subquery())——因为 stmt 可能带 WHERE 条件，
    # 直接 count(Paper) 会忽略条件算出错误的总数。
    total = session.exec(select(func.count()).select_from(stmt.subquery())).one()

    # order_by 排序（按入库时间倒序，最新在前），再加 offset/limit 分页。
    items = session.exec(
        stmt.order_by(Paper.added_at.desc()).offset(offset).limit(limit)
    ).all()

    return PaperListResponse(total=total, items=items)


@router.get("/{paper_id}", response_model=PaperRead)
def get_paper(
    paper_id: int,
    session: Session = Depends(get_session),
):
    """
    作用：按 id 查询单篇论文详情。

    参数：
        paper_id：路径参数，从 URL 的 {paper_id} 部分取（如 /api/papers/3 → paper_id=3）。
        session：数据库会话，依赖注入。

    返回：PaperRead（单篇论文全字段）。

    异常：论文不存在时抛 404。
    """
    # session.get(Paper, paper_id)：按主键查询单条记录，找不到返回 None。
    # 比手动 select().where(Paper.id == paper_id) 更简洁，且利用主键索引更快。
    paper = session.get(Paper, paper_id)
    if not paper:
        # HTTPException：FastAPI 的异常，抛出后自动转成对应 HTTP 状态码的 JSON 错误响应。
        # 404 = Not Found，detail 是返回给前端的错误信息。
        raise HTTPException(status_code=404, detail="Paper not found")
    return paper


@router.post("", response_model=PaperRead, status_code=201)
def create_paper(
    payload: PaperCreate,
    session: Session = Depends(get_session),
):
    """
    作用：创建一条论文记录。

    参数：
        payload：请求体，FastAPI 自动把前端发来的 JSON 按 PaperCreate schema 解析校验。
            校验失败（缺字段、类型错、枚举非法值）自动返回 422，不用手动判断。
        session：数据库会话，依赖注入。

    返回：创建后的 PaperRead（含数据库生成的 id、added_at 等字段）。
    状态码 201（Created），区别于默认 200（OK）——RESTful 约定创建用 201。

    使用场景：前端"新增论文"表单提交，或 Phase 2 的 AI 流水线调用入库。
    """
    # payload.model_dump()：把 Pydantic 模型转成 dict（Pydantic v2 写法，v1 是 .dict()）。
    # 然后用 ** 解包，把 dict 的每个 key-value 作为关键字参数传给 Paper 构造函数。
    # 等价于 Paper(title=payload.title, authors=payload.authors, ...) 但简洁。
    paper = Paper(**payload.model_dump())

    # 三步写库：
    session.add(paper)      # 1. add：把对象加入 session 的"待写入"列表（还没真正写库）
    session.commit()        # 2. commit：真正执行 INSERT，数据落盘
    session.refresh(paper)  # 3. refresh：从数据库重新读一次，把 DB 生成的字段（id、added_at）填回 paper 对象
    # 没有 refresh 的话，return paper 时 paper.id 是 None（commit 只写不回填）。

    return paper
