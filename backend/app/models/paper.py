"""
Paper 数据模型 + 全部枚举定义。

这是整个后端的核心：用 SQLModel 定义一张 papers 表。
SQLModel 的特点——一个类同时承担三个角色：
  1. 数据库表的 schema 定义（table=True 让它映射成一张表）
  2. 数据库行的 Python 对象映射（ORM：存进去是对象，读出来也是对象）
  3. （可选）API 的请求/响应数据校验（继承自 Pydantic BaseModel）

本文件只负责 1 和 2（表结构 + ORM）。API 边界的校验放在 schemas/paper.py 里，
和 model 分离是 FastAPI 最佳实践——存储结构和接口契约解耦，可以独立演进。

枚举设计：全部继承 (str, enum.Enum)。
  - 继承 str：让枚举成员的 value 直接是字符串（如 "watermarking"），
    JSON 序列化时直接是字符串，前端拿到无需额外映射表。
  - 继承 enum.Enum：标准库枚举，保证值域受限、不可随意传入非法值。
"""
import enum
from datetime import date, datetime
from typing import Optional, List

from sqlmodel import SQLModel, Field
import sqlalchemy as sa


# ============================================================================
#  枚举定义区
#  分类体系来源于 3dgs水印综述总结.md 的三层框架（扰动机制 / 保护范式 / 鲁棒性威胁）
#  每个枚举对应综述里的一个分类维度，值域和综述完全对齐
# ============================================================================

class SourceType(str, enum.Enum):
    """论文入库来源（记录这篇论文是怎么进库的）。"""
    arxiv_auto = "arxiv_auto"   # AI 流水线自动从 arXiv 抓取入库
    manual = "manual"           # Web UI 手动录入
    imported = "imported"      # 批量导入（如冷启动从综述 .bib 灌入）


class TaskType(str, enum.Enum):
    """任务类型（综述第二层·四类 IP 保护任务，多选）。

    一篇论文可能同时做多个任务，比如某水印方法也做篡改定位。
    所以这个字段在 Paper 里存成 list（JSON 列），而非单选。
    """
    watermarking = "watermarking"                       # 3DGS 水印
    steganography = "steganography"                     # 3DGS 隐写术
    tamper_localization = "tamper_localization"         # 3DGS 篡改定位
    editing_protection = "editing_protection"           # 3DGS 编辑防护
    other = "other"                                     # 兜底


class AttributeSelection(str, enum.Enum):
    """机制维度一：属性选择机制（综述第一层·单选）。

    选哪个高斯参数来嵌入扰动。一篇论文只用一种策略，所以是单选。
    """
    sh_only = "sh_only"       # 仅扰动球谐系数（控制颜色/外观，不动几何）
    mixed = "mixed"           # 混合扰动（SH + 几何类参数 μ/Σ/α）
    auxiliary = "auxiliary"   # 辅助属性（不碰原始参数，额外附加新属性）
    other = "other"


class DistributionStrategy(str, enum.Enum):
    """机制维度二：分布策略（综述第一层·单选）。

    扰动施加在哪些高斯基元上。
    注意：成员名 global_ 加了下划线，因为 global 是 Python 关键字不能直接用做标识符；
    但 .value 仍是字符串 "global"，数据库里存的就是 "global"，和综述术语一致。
    """
    global_ = "global"                     # 全局策略：对所有基元均匀施加
    local_frequency = "local_frequency"    # 局部·傅里叶频率引导（低频鲁棒/高频细节）
    local_uncertainty = "local_uncertainty"  # 局部·不确定性引导（边界处基元影响小）
    other = "other"


class InjectionPipeline(str, enum.Enum):
    """机制维度三：扰动注入管道（综述第一层·单选）。

    怎么把扰动注入进去——是每个资产单独优化，还是预训练通用映射。
    """
    per_asset_finetune = "per_asset_finetune"         # 逐资产微调（每个资产跑一次优化）
    generalizable_mapping = "generalizable_mapping"  # 可泛化映射（预训练编码器，一次前向）
    generation_embedded = "generation_embedded"      # 生成内嵌入（扰动集成进生成模型）
    other = "other"


class RobustnessTarget(str, enum.Enum):
    """鲁棒性目标（综述第三层·多选）。

    这篇论文评估了抵御哪些攻击。分 2D（作用于渲染图像）和 3D（直接作用于高斯参数）。
    一篇论文通常测多种攻击，所以存成 list。
    """
    # --- 2D 失真（作用于渲染出来的图像）---
    geometric_transform = "geometric_transform"   # 几何变换（旋转、裁剪）
    photometric = "photometric"                     # 光度变换（亮度/对比度）
    signal_degradation = "signal_degradation"      # 信号退化（模糊、噪声、JPEG 压缩）
    # --- 3D 失真（直接作用于高斯参数空间）---
    pruning = "pruning"                # 剪枝（删掉部分高斯基元）
    cloning = "cloning"                # 克隆（复制基元稀释扰动）
    spatial_transform = "spatial_transform"  # 空间变换（旋转/缩放/平移基元）
    noise_injection = "noise_injection"      # 高斯噪声注入
    quantization = "quantization"            # 模型量化
    parameter_merging = "parameter_merging"  # 参数合并


class ReadStatus(str, enum.Enum):
    """个人阅读状态。"""
    unread = "unread"   # 未读（默认）
    reading = "reading"  # 在读
    read = "read"        # 已读完


class CurationStatus(str, enum.Enum):
    """数据质量状态——区分 AI 抽取 vs 人工核实。

    这是质量门的核心字段：
      - auto：AI 流水线自动抽取入库，未经人工核实，UI 上显示"⚠️ 未核实"徽章，不进统计图表
      - reviewed：你看过并修正过 AI 抽错的字段
      - verified：你深度读过并确认全部字段准确（最高信任）
    """
    auto = "auto"
    reviewed = "reviewed"
    verified = "verified"


# ============================================================================
#  Paper 表模型
# ============================================================================

class Paper(SQLModel, table=True):
    """
    论文实体——整个知识库的核心表。

    table=True 是 SQLModel 的开关：让这个类不仅是个 Pydantic 数据模型，
    还会映射成数据库里的一张表（表名由 __tablename__ 指定）。
    每个实例 = 表里一行，每个类属性 = 表里一列。

    字段分四组：身份 / 内容 / 分类 / 技术 / 个人，注释见各字段。
    """

    __tablename__ = "papers"

    # ---------------- 身份字段 ----------------
    id: Optional[int] = Field(default=None, primary_key=True)
    # primary_key=True：主键，数据库自动自增。default=None 表示新建时不传，让 DB 生成。

    arxiv_id: Optional[str] = Field(default=None, index=True, unique=True)
    # index=True：建索引，加速按 arxiv_id 查询。
    # unique=True：唯一约束，防止同一篇论文重复入库。

    doi: Optional[str] = Field(default=None)

    title: str = Field(index=True)
    # 标题建索引：列表页排序、搜索常按 title，索引让查询快。

    # authors 存作者列表，如 ["张三", "李四"]。
    # 这是"多值字段"——一篇论文有多个作者。
    # 用 JSON 列存储：SQLite 把 list 序列化成 JSON 字符串存进 TEXT 列，
    # 读取时自动反序列化回 Python list，对代码完全透明。
    #
    # 写法要点（易错点）：必须同时给 default=[] 和 sa_column=Column(sa.JSON)
    #   - default=[] ：Python 端新建实例时的默认值（空列表）
    #   - sa_column=sa.Column(sa.JSON) ：告诉 SQLAlchemy 这列用 JSON 类型
    # 两个都给，否则 SQLModel 会把可变的 list 默认值当成"共享引用"报错。
    authors: List[str] = Field(default=[], sa_column=sa.Column(sa.JSON))

    venue: Optional[str] = Field(default=None)
    # 发表会议/期刊，如 "AAAI'26"；arXiv preprint 没正式发表时为 None。

    pub_date: Optional[date] = Field(default=None)
    # 发表日期。非 arXiv 论文（只有会议接收没上线）可能为空。

    source: SourceType = Field(default=SourceType.manual)
    # 入库来源，默认 manual（手动录入）。AI 流水线会设成 arxiv_auto。

    added_at: datetime = Field(default_factory=datetime.utcnow)
    # 入库时间戳。
    # 用 default_factory=datetime.utcnow 而非 default=datetime.utcnow()：
    #   - default=datetime.utcnow() 在"类定义时"就求值一次，所有实例共享同一时间（bug！）
    #   - default_factory=datetime.utcnow 在"每次新建实例时"才调用函数，拿到当时的时间
    #   这是 Python 可变默认参数陷阱的同类问题，务必用 factory 形式。

    # ---------------- 内容字段 ----------------
    abstract: str

    pdf_url: Optional[str] = Field(default=None)
    method_summary: Optional[str] = Field(default=None)
    # AI 抽取的方法概述。Phase 0 为空，Phase 2 由 DeepSeek 填充。

    key_contributions: Optional[List[str]] = Field(default=None, sa_column=sa.Column(sa.JSON))
    # AI 抽取的关键贡献点列表。

    # ---------------- 分类字段（核心）----------------
    # task_type：多选枚举，存成 list[str]，元素是 TaskType 枚举的 value。
    # 比如 ["watermarking"] 或 ["watermarking", "tamper_localization"]。
    # 注意这里用 List[str] 而非 List[TaskType]：SQLModel 的 JSON 列不原生支持枚举校验，
    # 值的合法性在 schemas/paper.py 的 Pydantic schema 层校验。
    task_type: List[str] = Field(default=[], sa_column=sa.Column(sa.JSON))

    # 机制三维度——单选，直接用枚举类型，数据库存字符串值。
    attribute_selection: Optional[AttributeSelection] = Field(default=None)
    distribution_strategy: Optional[DistributionStrategy] = Field(default=None)
    injection_pipeline: Optional[InjectionPipeline] = Field(default=None)

    robustness_targets: List[str] = Field(default=[], sa_column=sa.Column(sa.JSON))
    # 多选枚举，存成 list[str]，如 ["pruning", "noise_injection"]。

    tags: List[str] = Field(default=[], sa_column=sa.Column(sa.JSON))
    # 完全自由标签，承接枚举覆盖不到的细粒度（如 "frequency-domain"、具体数据集名）。

    # ---------------- 技术字段 ----------------
    capacity: Optional[str] = Field(default=None)
    # 嵌入容量，用字符串而非数字，因为各单位不一（"256 bits/model" / "0.5 bpp"）。

    datasets_used: Optional[List[str]] = Field(default=None, sa_column=sa.Column(sa.JSON))
    baselines_compared: Optional[List[str]] = Field(default=None, sa_column=sa.Column(sa.JSON))

    # 三个 headline 固定列——最常被比较的指标，提成独立列方便排序查询。
    psnr: Optional[float] = Field(default=None)
    ssim: Optional[float] = Field(default=None)
    bit_accuracy: Optional[float] = Field(default=None)

    extra_metrics: Optional[dict] = Field(default=None, sa_column=sa.Column(sa.JSON))
    # 异构指标兜底：其余不统一的指标（LPIPS、capacity_bpp、不同攻击下的准确率等）塞进这个 JSON。
    # 设计取舍：固定列 vs JSON 的平衡——固定列保证"按 PSNR 排序"能直接查，JSON 保证不被新指标逼着改表。

    code_url: Optional[str] = Field(default=None)

    # ---------------- 个人字段 ----------------
    read_status: ReadStatus = Field(default=ReadStatus.unread)
    personal_notes: Optional[str] = Field(default=None)
    # 个人批注——个人 KB 的核心价值，区别于"通用论文数据库"。

    curation_status: CurationStatus = Field(default=CurationStatus.auto)
    # 数据质量状态，默认 auto（AI 抽取未核实）。

    last_reviewed_at: Optional[datetime] = Field(default=None)
    # 最后人工复核时间，未复核时为 None。
