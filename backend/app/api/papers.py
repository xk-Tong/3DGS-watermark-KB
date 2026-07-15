"""
论文 CRUD 路由（Phase 1：list 筛选/排序 + get + create + update）。

APIRouter：FastAPI 的路由分组机制。把相关端点组织在一个 router 里，
再在 main.py 用 include_router 挂到 app 上。好处是按模块拆分，main.py 保持干净。
"""
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select, func, or_

from ..database import get_session
from ..models.paper import (
    Paper, TaskType, AttributeSelection, DistributionStrategy,
    InjectionPipeline, ReadStatus, CurationStatus,
)
from ..schemas.paper import PaperCreate, PaperRead, PaperUpdate, PaperListResponse

# prefix="/papers"：这个 router 下所有路径都自动加 /papers 前缀。
# 比如 @router.get("") 实际路径是 /papers（加上 main.py 的 /api 前缀就是 /api/papers）。
# tags=["papers"]：在 Swagger UI（/docs）里按 tag 分组的分类标签。
router = APIRouter(prefix="/papers", tags=["papers"])


@router.get("", response_model=PaperListResponse)
def list_papers(
    q: Optional[str] = Query(None, description="关键词，搜 title/abstract/method_summary/personal_notes"),
    task_type: Optional[str] = Query(None, description="筛选任务类型，传枚举值如 watermarking"),
    attribute_selection: Optional[AttributeSelection] = Query(None),
    distribution_strategy: Optional[DistributionStrategy] = Query(None),
    injection_pipeline: Optional[InjectionPipeline] = Query(None),
    year: Optional[int] = Query(None, description="按 pub_date 年份筛选"),
    read_status: Optional[ReadStatus] = Query(None),
    curation_status: Optional[CurationStatus] = Query(None),
    sort_by: str = Query("added_at", description="排序字段：added_at/pub_date/psnr"),
    order: str = Query("desc", description="排序方向：desc 降序 / asc 升序"),
    limit: int = Query(20, le=100, description="每页数量，最大 100"),
    offset: int = Query(0, ge=0, description="跳过前 N 条，用于分页"),
    session: Session = Depends(get_session),
):
    """
    作用：分页查询论文列表，支持多维筛选、关键词搜索、排序。

    参数：
        q：关键词，在 title/abstract/method_summary/personal_notes 上做 LIKE 模糊匹配。
        task_type：按任务类型筛选。因为是 JSON 数组存储，用 LIKE '%"watermarking"%' 匹配。
            （值域小且数组长度短，LIKE 性能完全够用，无需关联表）
        attribute_selection/distribution_strategy/injection_pipeline：机制三维度单选筛选。
        year：按 pub_date 年份筛选（如 2025）。
        read_status：按阅读状态筛选（unread/reading/read）。
        curation_status：按数据质量状态筛选（auto/reviewed/verified）。
        sort_by：排序字段，支持 added_at（默认）/ pub_date / psnr。
        order：desc 降序（新→旧）或 asc 升序（旧→新）。
        limit/offset：分页。
        session：数据库会话，由 Depends(get_session) 自动注入。

    返回：PaperListResponse（{total, items}）。

    使用场景：前端列表页加载、筛选条件变化、翻页时调用。
    """
    # select(Paper) 构造一个 SELECT 语句（还没执行），类似 SQL 的 SELECT * FROM papers。
    stmt = select(Paper)

    # ---- 关键词搜索 ----
    if q:
        # or_：SQLModel/SQLAlchemy 的 OR 操作符，组合多个条件为"任一匹配"。
        # 搜索范围扩展到 4 个字段：title/abstract/method_summary/personal_notes。
        # 注意 personal_notes 可能是 None（NULL），LIKE 对 NULL 的结果是 NULL（视为 false），
        # 不会报错，只是匹配不到，符合预期（没批注的论文不在搜索范围）。
        like = f"%{q}%"
        stmt = stmt.where(
            or_(
                Paper.title.like(like),
                Paper.abstract.like(like),
                Paper.method_summary.like(like),
                Paper.personal_notes.like(like),
            )
        )

    # ---- 多维筛选 ----
    if task_type:
        # JSON 列的筛选技巧：task_type 存成 JSON 数组（如 ["watermarking","steganography"]），
        # SQLite 把它序列化成字符串 '["watermarking","steganography"]'。
        # 用 LIKE '%"watermarking"%' 能匹配到包含该元素的数组。
        # 这是个 hack 但对小规模（<200 篇）+ 小值域（5 个枚举值）完全够用，
        # 正经做法是关联表 + JOIN，但那是 Phase 2+ 的优化。
        stmt = stmt.where(Paper.task_type.like(f'%"{task_type}"%'))

    if attribute_selection:
        # 单选枚举是普通字符串列，直接 == 比较，走索引（如果有）。
        stmt = stmt.where(Paper.attribute_selection == attribute_selection)
    if distribution_strategy:
        stmt = stmt.where(Paper.distribution_strategy == distribution_strategy)
    if injection_pipeline:
        stmt = stmt.where(Paper.injection_pipeline == injection_pipeline)

    if year:
        # strftime 是 SQLite 的日期函数，'%Y' 提取年份。
        # pub_date 是 date 类型，strftime 把它格式化成字符串再比较。
        # 注意：不同数据库日期函数不同（PostgreSQL 用 EXTRACT(YEAR FROM ...)），
        # 这里写的是 SQLite 专用语法，迁移到别的数据库要改。
        stmt = stmt.where(func.strftime("%Y", Paper.pub_date) == str(year))

    if read_status:
        stmt = stmt.where(Paper.read_status == read_status)
    if curation_status:
        stmt = stmt.where(Paper.curation_status == curation_status)

    # ---- 总数 ----
    # 先算总数（分页前），用 func.count() 生成 SELECT COUNT(*)。
    # 注意要 select_from(stmt.subquery())——因为 stmt 可能带 WHERE 条件，
    # 直接 count(Paper) 会忽略条件算出错误的总数。
    total = session.exec(select(func.count()).select_from(stmt.subquery())).one()

    # ---- 排序 ----
    # getattr(Paper, sort_by)：动态获取模型属性。
    # 比如 sort_by="added_at" 等价于 Paper.added_at，sort_by="psnr" 等价于 Paper.psnr。
    # 这是 Python 反射机制，用字符串名访问对象属性。
    sort_column = getattr(Paper, sort_by, Paper.added_at)
    # .asc()/.desc()：升序/降序。三元表达式：order=="desc" 用降序，否则升序。
    if order == "desc":
        stmt = stmt.order_by(sort_column.desc())
    else:
        stmt = stmt.order_by(sort_column.asc())

    # ---- 分页 ----
    items = session.exec(stmt.offset(offset).limit(limit)).all()

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


@router.patch("/{paper_id}", response_model=PaperRead)
def update_paper(
    paper_id: int,
    payload: PaperUpdate,
    session: Session = Depends(get_session),
):
    """
    作用：部分更新一篇论文（PATCH 语义——只改传了的字段，没传的保持不变）。

    参数：
        paper_id：要更新的论文 id。
        payload：PaperUpdate schema，所有字段都是 Optional。
            前端只传要改的字段，没传的字段为 None，后端跳过不更新。
        session：数据库会话，依赖注入。

    返回：更新后的 PaperRead。

    异常：论文不存在时抛 404。

    使用场景：详情页编辑表单提交——改分类字段、补技术指标、改阅读状态等。

    设计取舍——用 PATCH 还是 PUT？
        PUT 要求传全部字段（没传的会被置空），适合"整体替换"。
        PATCH 只改传了的字段，适合"部分更新"。
        编辑表单通常只改几个字段（比如只改 read_status），用 PATCH 更合理，
        避免前端要先把全字段拉一遍再传回。
    """
    paper = session.get(Paper, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    # payload.model_dump(exclude_unset=True)：Pydantic v2 的关键参数。
    # exclude_unset=True：只返回"前端显式传了的字段"，没传的字段不包含在 dict 里。
    # 区别于 model_dump()（返回全部字段，没传的为 None）：
    #   - 不加 exclude_unset：前端没传 title，dict 里 title=None，会把数据库里的 title 覆盖成 None（bug！）
    #   - 加了 exclude_unset：dict 里没有 title 这个 key，下面的 setattr 跳过它，保持原值
    update_data = payload.model_dump(exclude_unset=True)

    # 遍历要更新的字段，逐个 setattr 到 ORM 对象上。
    # setattr(obj, name, value)：Python 内置函数，等价于 obj.name = value。
    # 用 setattr 而非直接 paper.title = ... 是因为字段名是动态的（从 dict key 来）。
    for field, value in update_data.items():
        setattr(paper, field, value)

    # 如果改了 read_status 或 curation_status，更新最后复核时间。
    # Python 的 `in` 对 dict 检查 key 是否存在。
    if "read_status" in update_data or "curation_status" in update_data:
        from datetime import datetime
        paper.last_reviewed_at = datetime.utcnow()

    session.add(paper)      # add：标记 paper 为"待更新"（已存在的对象再 add 就是 update）
    session.commit()        # commit：真正执行 UPDATE
    session.refresh(paper)  # refresh：回填（虽然主键不变，但养成习惯）
    return paper
