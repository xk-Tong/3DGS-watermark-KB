"""
LLM 抽取用的 prompt 模板——包含综述 taxonomy 定义和 few-shot 示例。

为什么 prompt 要附 taxonomy 定义？
    LLM 不知道我们自定义的枚举值（如 sh_only/local_frequency）是什么意思。
    如果不解释，它会把属性选择瞎猜成任意字符串，导致 schema 校验失败。
    把综述里每个枚举值的定义和代表方法写进 prompt，LLM 才能按定义分类。

few-shot 示例的作用：
    给 LLM 看几个"输入摘要 → 输出 JSON"的完整例子，让它学会期望的输出格式。
    比"纯指令"更有效，因为模型能模仿示例的结构。
"""
import json


# ============================================================================
#  taxonomy 定义（喂给 LLM 的分类体系说明）
# ============================================================================

TAXONOMY_DEFINITION = """你正在为"3DGS 水印与 IP 保护"论文知识库做分类。请按以下分类体系抽取字段。

## 任务类型 task_type（多选，从以下选 0-N 个）
- watermarking：3DGS 水印（嵌入所有权信息，事后验证）
- steganography：3DGS 隐写术（大容量秘密信息隐蔽嵌入）
- tamper_localization：3DGS 篡改定位（检测并定位恶意修改区域）
- editing_protection：3DGS 编辑防护（让资产抵抗未经授权的编辑）
- other：不属于以上任一类别

## 属性选择机制 attribute_selection（单选）
- sh_only：仅扰动球谐系数(SH)，控制颜色/外观，不影响几何形状
- mixed：混合扰动，同时修改SH和几何参数(位置μ/协方差Σ/不透明度α)
- auxiliary：辅助属性，不修改原始参数，额外附加新属性
- other：不属于以上

## 分布策略 distribution_strategy（单选）
- global：全局策略，对所有高斯基元均匀施加扰动
- local_frequency：局部·频率引导，按傅里叶频率选择子集（高频/低频）
- local_uncertainty：局部·不确定性引导，选高不确定性基元（通常在物体边界）
- other：不属于以上

## 注入管道 injection_pipeline（单选）
- per_asset_finetune：逐资产微调，每个3DGS资产单独优化
- generalizable_mapping：可泛化映射，预训练编码器推理时一次前向
- generation_embedded：生成内嵌入，扰动集成进3DGS生成模型
- other：不属于以上

## 鲁棒性目标 robustness_targets（多选，选论文评估了哪些攻击）
2D失真：geometric_transform / photometric / signal_degradation
3D失真：pruning / cloning / spatial_transform / noise_injection / quantization / parameter_merging
（如果论文没明确评估攻击，返回空数组 []）
"""


# ============================================================================
#  Few-shot 示例（让 LLM 学会期望的输出格式）
# ============================================================================

# 示例 1：GuardSplat（水印论文，SH-only，全局，逐资产微调）
FEWSHOT_EXAMPLE_1 = {
    "input_title": "GuardSplat: A Robust and Secure Watermarking for 3D Gaussian Splatting",
    "input_abstract": (
        "GuardSplat 提出一种面向 3D Gaussian Splatting 资产的鲁棒水印框架。"
        "通过在球谐系数（SH）上嵌入不可见扰动实现所有权保护，"
        "并引入噪声增强训练与对抗学习以抵御剪枝、噪声注入等 3D 攻击。"
    ),
    "output": {
        "task_type": ["watermarking"],
        "attribute_selection": "sh_only",
        "distribution_strategy": "global",
        "injection_pipeline": "per_asset_finetune",
        "robustness_targets": ["pruning", "noise_injection", "quantization"],
        "method_summary": "在球谐系数上嵌入水印，结合噪声增强训练和对抗学习提升对剪枝、噪声等3D攻击的鲁棒性。",
        "key_contributions": [
            "在SH系数上嵌入水印实现所有权保护",
            "引入噪声增强训练提升鲁棒性",
            "对抗学习抵御3D攻击",
        ],
        "capacity": None,
        "datasets_used": [],
        "baselines_compared": [],
    },
}

# 示例 2：GS-Hider（隐写，辅助属性，全局，逐资产微调）
FEWSHOT_EXAMPLE_2 = {
    "input_title": "GS-Hider: Hiding Information in 3D Gaussian Splatting",
    "input_abstract": (
        "GS-Hider 通过给每个高斯基元附加额外的辅助属性通道来隐藏信息，"
        "不修改原始的位置、协方差、不透明度等参数，保证渲染质量无损。"
    ),
    "output": {
        "task_type": ["steganography"],
        "attribute_selection": "auxiliary",
        "distribution_strategy": "global",
        "injection_pipeline": "per_asset_finetune",
        "robustness_targets": [],
        "method_summary": "给高斯基元附加辅助属性通道隐藏信息，不修改原始参数，保证渲染质量。",
        "key_contributions": [
            "辅助属性通道实现高容量信息隐藏",
            "不修改原始参数保证渲染无损",
        ],
        "capacity": None,
        "datasets_used": [],
        "baselines_compared": [],
    },
}


def build_relevance_prompt(title: str, abstract: str) -> list[dict]:
    """
    作用：构造"相关性过滤"的对话消息列表。

    参数：
        title：论文标题。
        abstract：论文摘要。

    返回：list[dict]，OpenAI chat messages 格式。
        每个 dict 有 role（system/user/assistant）和 content 字段。

    使用场景：llm_client.check_relevance 调用，判断论文是否属于 3DGS IP 保护领域。
    """
    # system message：设定 LLM 的角色和行为规则。
    system_msg = (
        "你是一个论文分类助手。判断给定论文是否属于'3D Gaussian Splatting (3DGS) 资产 IP 保护'领域。"
        "IP 保护包括：水印(watermarking)、隐写术(steganography)、篡改定位(tamper localization)、编辑防护(editing protection)。"
        "注意排除：3DGS 渲染优化、去伪影、场景重建等与 IP 保护无关的工作，即使它们提到了 Gaussian Splatting。"
        "只返回 JSON，格式：{\"relevant\": true/false, \"reason\": \"一句话理由\"}"
    )
    # user message：把标题和摘要喂给 LLM。
    user_msg = f"标题：{title}\n摘要：{abstract}"

    # OpenAI chat API 要求 messages 是 [{role, content}, ...] 格式。
    # system 设定全局指令，user 是用户输入。
    return [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg},
    ]


def build_extraction_prompt(title: str, abstract: str) -> list[dict]:
    """
    作用：构造"结构化抽取"的对话消息列表——附 taxonomy 定义 + few-shot 示例。

    参数：
        title：论文标题。
        abstract：论文摘要。

    返回：list[dict]，OpenAI chat messages 格式，包含 system（taxonomy+示例）和 user（待抽取论文）。

    使用场景：llm_client.extract_paper_fields 调用，抽取分类字段和方法摘要。
    """
    # system message 里塞三样东西：taxonomy 定义 + 两个 few-shot 示例 + 输出格式要求。
    system_msg = (
        TAXONOMY_DEFINITION
        + "\n\n## 输出格式\n"
        + "返回一个 JSON 对象，包含以下字段（无法判断的填 null，多选字段填数组）：\n"
        + json.dumps({
            "task_type": ["枚举值数组"],
            "attribute_selection": "枚举值或null",
            "distribution_strategy": "枚举值或null",
            "injection_pipeline": "枚举值或null",
            "robustness_targets": ["枚举值数组"],
            "method_summary": "一句话方法概述",
            "key_contributions": ["贡献点数组"],
            "capacity": "容量字符串或null",
            "datasets_used": ["数据集名数组"],
            "baselines_compared": ["基线方法名数组"],
        }, ensure_ascii=False, indent=2)
        + "\n\n## 示例 1\n"
        + f"输入：{FEWSHOT_EXAMPLE_1['input_title']}\n{FEWSHOT_EXAMPLE_1['input_abstract']}\n"
        + "输出：" + json.dumps(FEWSHOT_EXAMPLE_1['output'], ensure_ascii=False)
        + "\n\n## 示例 2\n"
        + f"输入：{FEWSHOT_EXAMPLE_2['input_title']}\n{FEWSHOT_EXAMPLE_2['input_abstract']}\n"
        + "输出：" + json.dumps(FEWSHOT_EXAMPLE_2['output'], ensure_ascii=False)
        + "\n\n只返回 JSON，不要额外解释。"
    )

    user_msg = f"标题：{title}\n摘要：{abstract}"

    return [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg},
    ]
