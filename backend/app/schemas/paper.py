"""
Pydantic 请求/响应 schema（与 SQLModel model 分离）。

为什么 model 和 schema 要分开？
  - model（models/paper.py）负责数据库存储结构。
  - schema（本文件）负责 API 边界的数据校验和序列化。
  分开后可以独立演进：比如创建接口不接收 id/added_at（这些后端生成），
  但读取接口要返回它们——用不同 schema 控制每个接口接受/返回哪些字段。

继承结构：
  PaperBase（公共字段）
    ├── PaperCreate（创建用，不含 id/added_at 等后端生成字段）
    ├── PaperRead（读取用，含全部字段）
    └── PaperUpdate（部分更新用，所有字段可选，PATCH 语义）
"""
from datetime import date, datetime
from typing import Optional, List

from pydantic import BaseModel, field_validator

from ..models.paper import (
    SourceType, TaskType, AttributeSelection, DistributionStrategy,
    InjectionPipeline, RobustnessTarget, ReadStatus, CurationStatus,
)


# 允许的多选枚举值集合——用于校验 JSON 列里的元素合法性。
# 用集合（set）而非列表，因为集合的 `in` 查询是 O(1)，列表是 O(n)。
# 这些值和枚举类的 .value 一致，手写一遍是为了在校验时用字符串比较（JSON 列存的就是字符串）。
ALLOWED_TASK_TYPES = {t.value for t in TaskType}
ALLOWED_ROBUSTNESS = {r.value for r in RobustnessTarget}


class PaperBase(BaseModel):
    """论文公共字段——创建和读取都需要的字段。

    注意：这里故意不放 id / added_at 等后端生成的字段，
    它们只在 PaperRead 里出现，避免创建接口误传。
    但 read_status / curation_status 放在这里，因为创建时可以指定（不指定走默认值）。
    """
    arxiv_id: Optional[str] = None
    doi: Optional[str] = None
    title: str
    authors: List[str]
    venue: Optional[str] = None
    pub_date: Optional[date] = None
    abstract: str
    pdf_url: Optional[str] = None
    method_summary: Optional[str] = None
    key_contributions: Optional[List[str]] = None

    # 分类字段
    task_type: List[str] = []
    attribute_selection: Optional[AttributeSelection] = None
    distribution_strategy: Optional[DistributionStrategy] = None
    injection_pipeline: Optional[InjectionPipeline] = None
    robustness_targets: List[str] = []
    tags: List[str] = []

    # 技术字段
    capacity: Optional[str] = None
    datasets_used: Optional[List[str]] = None
    baselines_compared: Optional[List[str]] = None
    psnr: Optional[float] = None
    ssim: Optional[float] = None
    bit_accuracy: Optional[float] = None
    extra_metrics: Optional[dict] = None
    code_url: Optional[str] = None

    # 个人字段——放这里让创建和编辑都能改
    read_status: ReadStatus = ReadStatus.unread
    personal_notes: Optional[str] = None
    curation_status: CurationStatus = CurationStatus.auto

    # field_validator：Pydantic v2 的字段校验装饰器。
    # 在数据被接受前先校验，非法值直接报 422 错误给前端。
    # @field_validator("字段名")：校验单个字段；传列表可校验多个。
    # 参数 cls 是类本身（类似 classmethod），v 是待校验的值。
    @field_validator("task_type")
    @classmethod
    def validate_task_type(cls, v: List[str]) -> List[str]:
        """校验 task_type 列表里每个元素都是合法的 TaskType 枚举值。"""
        for item in v:
            if item not in ALLOWED_TASK_TYPES:
                raise ValueError(f"非法 task_type 值: {item}，合法值: {ALLOWED_TASK_TYPES}")
        return v

    @field_validator("robustness_targets")
    @classmethod
    def validate_robustness(cls, v: List[str]) -> List[str]:
        """校验 robustness_targets 每个元素都是合法的 RobustnessTarget 枚举值。"""
        for item in v:
            if item not in ALLOWED_ROBUSTNESS:
                raise ValueError(f"非法 robustness_target 值: {item}，合法值: {ALLOWED_ROBUSTNESS}")
        return v


class PaperCreate(PaperBase):
    """创建论文用的 schema。

    继承 PaperBase 的全部字段，额外加 source（默认 manual）。
    不含 id / added_at / last_reviewed_at——这些后端自动生成。
    """
    source: SourceType = SourceType.manual


class PaperRead(PaperBase):
    """读取论文用的 schema——含后端生成的全部字段。

    用于 API 响应：从数据库读出的 ORM 对象，转成 JSON 返回给前端。
    """
    id: int
    source: SourceType
    added_at: datetime
    last_reviewed_at: Optional[datetime] = None

    # Pydantic v2 配置：from_attributes=True 让 Pydantic 能从"任意对象"按属性名读取字段，
    # 而不只是从 dict 读取。这是让 ORM 对象（SQLModel/SQLAlchemy 实例）能直接被
    # 当成响应返回的关键——FastAPI 的 response_model 会用这个配置把 ORM 对象转成 JSON。
    # （Pydantic v1 里这个配置叫 orm_mode = True，v2 改名了，抄旧教程会踩坑）
    class Config:
        from_attributes = True


class PaperUpdate(BaseModel):
    """
    部分更新论文用的 schema（PATCH 语义）。

    设计取舍——为什么所有字段都 Optional？
        PUT 语义要求传全部字段（没传的会被置空），对"只改一个字段"场景不友好。
        PATCH 语义是"只改传了的字段，没传的保持不变"。
        实现 PATCH 语义的标准做法：所有字段都设成 Optional[...] = None，
        后端只更新"前端显式传了的字段"（非 None 的字段）。

    所有字段都可选，连 title 这种原本必填的也变可选——
    因为编辑时你不一定要改它，不改就不传。
    """
    arxiv_id: Optional[str] = None
    doi: Optional[str] = None
    title: Optional[str] = None
    authors: Optional[List[str]] = None
    venue: Optional[str] = None
    pub_date: Optional[date] = None
    abstract: Optional[str] = None
    pdf_url: Optional[str] = None
    method_summary: Optional[str] = None
    key_contributions: Optional[List[str]] = None

    task_type: Optional[List[str]] = None
    attribute_selection: Optional[AttributeSelection] = None
    distribution_strategy: Optional[DistributionStrategy] = None
    injection_pipeline: Optional[InjectionPipeline] = None
    robustness_targets: Optional[List[str]] = None
    tags: Optional[List[str]] = None

    capacity: Optional[str] = None
    datasets_used: Optional[List[str]] = None
    baselines_compared: Optional[List[str]] = None
    psnr: Optional[float] = None
    ssim: Optional[float] = None
    bit_accuracy: Optional[float] = None
    extra_metrics: Optional[dict] = None
    code_url: Optional[str] = None

    read_status: Optional[ReadStatus] = None
    personal_notes: Optional[str] = None
    curation_status: Optional[CurationStatus] = None

    @field_validator("task_type")
    @classmethod
    def validate_task_type(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """校验 task_type，允许 None（不更新时跳过）。"""
        if v is None:
            return None
        for item in v:
            if item not in ALLOWED_TASK_TYPES:
                raise ValueError(f"非法 task_type 值: {item}，合法值: {ALLOWED_TASK_TYPES}")
        return v

    @field_validator("robustness_targets")
    @classmethod
    def validate_robustness(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """校验 robustness_targets，允许 None。"""
        if v is None:
            return None
        for item in v:
            if item not in ALLOWED_ROBUSTNESS:
                raise ValueError(f"非法 robustness_target 值: {item}，合法值: {ALLOWED_ROBUSTNESS}")
        return v


class PaperListResponse(BaseModel):
    """列表接口的响应——分页结构。

    单纯返回 List[PaperRead] 不够，前端还需要总数 total 来显示分页。
    所以包一层：{ total: 100, items: [...] }
    """
    total: int
    items: List[PaperRead]
