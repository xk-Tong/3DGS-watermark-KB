"""
种子数据脚本——插入一条 GuardSplat 论文用于联调验证。

GuardSplat 是综述里提到的代表性水印方法（扰动球谐系数 SH）。
用真实论文做种子，让 Phase 0 的列表页看起来有意义，不是 "test/test" 占位数据。

运行方式（在 backend/ 目录下）：
    /Users/kang/.workbuddy/binaries/python/envs/default/bin/python -m app.core.seed

    python -m app.core.seed 的含义：把 app.core.seed 当模块执行。
    用 -m 而非直接 app/core/seed.py，是为了让相对导入（from ..database import ...）能正常工作。
"""
from sqlmodel import Session, select

from ..database import engine, create_db_and_tables
from ..models.paper import (
    Paper, SourceType, AttributeSelection, DistributionStrategy,
    InjectionPipeline, CurationStatus,
)


def seed():
    """
    作用：插入 GuardSplat 种子论文（如已存在则跳过，保证幂等可重复运行）。

    幂等性设计：先按 arxiv_id 查是否已存在，存在就跳过。
    这样反复运行 seed 不会产生重复数据。
    """
    # 先建表（万一还没启动过后端）
    create_db_and_tables()

    with Session(engine) as s:
        # select(Paper).where(...) 构造查询，s.exec(...).first() 执行并取第一条。
        # 检查这个 arxiv_id 是否已存在，避免重复插入。
        existing = s.exec(
            select(Paper).where(Paper.arxiv_id == "2410.03461")
        ).first()

        if existing:
            print(f"种子已存在（id={existing.id}），跳过。")
            return

        # 构造 GuardSplat 论文——数据按综述笔记填，字段含义见 models/paper.py 注释。
        paper = Paper(
            arxiv_id="2410.03461",
            title="GuardSplat: A Robust and Secure Watermarking for 3D Gaussian Splatting",
            authors=["Zhiyu Zhu", "Jiangqun Wu", "Yan Liu", "et al."],
            venue="arXiv preprint",
            pub_date=None,   # arXiv 预印本，正式发表日期待定
            source=SourceType.manual,
            abstract=(
                "GuardSplat 提出一种面向 3D Gaussian Splatting 资产的鲁棒水印框架。"
                "通过在球谐系数（SH）上嵌入不可见扰动实现所有权保护，"
                "并引入噪声增强训练与对抗学习以抵御剪枝、噪声注入等 3D 攻击。"
                "实验表明在保持高渲染质量的同时，水印对多种失真具有鲁棒性。"
            ),
            # 分类字段——综述里 GuardSplat 的定位
            task_type=["watermarking"],
            attribute_selection=AttributeSelection.sh_only,        # 仅扰动球谐系数
            distribution_strategy=DistributionStrategy.global_,   # 全局分布策略
            injection_pipeline=InjectionPipeline.per_asset_finetune,  # 逐资产微调
            robustness_targets=["pruning", "noise_injection", "quantization"],
            tags=["frequency-domain", "adversarial-training"],
            # 技术字段——Phase 0 暂留空，Phase 2 由 AI 抽取或人工补充
            capacity=None,
            psnr=None,
            ssim=None,
            bit_accuracy=None,
            # 个人字段
            curation_status=CurationStatus.reviewed,   # 种子数据标记为已复核，进统计
        )

        s.add(paper)
        s.commit()
        s.refresh(paper)   # 回填 id
        print(f"种子插入成功：id={paper.id}, title={paper.title}")


if __name__ == "__main__":
    seed()
