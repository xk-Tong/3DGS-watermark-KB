"""
DeepSeek LLM 客户端——相关性过滤 + 结构化抽取。

DeepSeek 兼容 OpenAI API 格式，所以直接用 openai 官方 SDK 调用，
只需把 base_url 换成 DeepSeek 的端点。

环境变量：
    DEEPSEEK_API_KEY：DeepSeek API 密钥，从 https://platform.deepseek.com/ 获取。
    没配会抛 RuntimeError 提示。

模型：
    deepseek-chat：DeepSeek 的通用对话模型，性价比高，抽取质量够用。
"""
import json
import os
from typing import Optional

from openai import OpenAI

from .prompts import build_relevance_prompt, build_extraction_prompt


# DeepSeek 配置
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-v4-pro"

# 模块级单例：OpenAI client 实例。
# 用单例而非每次新建，因为 client 内部有连接池复用，重复创建浪费资源。
# _client 初始为 None，首次调用时懒加载（lazy init）。
_client: Optional[OpenAI] = None


def get_client() -> OpenAI:
    """
    作用：获取 DeepSeek LLM 客户端单例（懒加载）。

    返回：OpenAI 客户端实例（配置成指向 DeepSeek）。

    异常：没配 DEEPSEEK_API_KEY 环境变量时抛 RuntimeError。

    使用场景：check_relevance 和 extract_paper_fields 内部调用。
    """
    global _client
    if _client is not None:
        return _client

    # os.environ：进程的环境变量字典。
    # 从环境变量读 API key——不要把 key 硬编码在代码里（安全风险 + 换 key 要改代码）。
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError(
            "未配置 DEEPSEEK_API_KEY 环境变量。"
            "请到 https://platform.deepseek.com/ 获取 API key，然后运行："
            "export DEEPSEEK_API_KEY='你的key'"
        )

    # OpenAI(base_url=..., api_key=...)：创建指向 DeepSeek 的客户端。
    # openai SDK 会把请求发到 base_url 而不是 OpenAI 官方端点。
    # DeepSeek 的 API 和 OpenAI 完全兼容，所以 SDK 不用改。
    _client = OpenAI(base_url=DEEPSEEK_BASE_URL, api_key=api_key)
    return _client


def check_relevance(title: str, abstract: str) -> dict:
    """
    作用：判断论文是否属于 3DGS IP 保护领域（相关性过滤）。

    参数：
        title：论文标题。
        abstract：论文摘要。

    返回：dict，格式 {"relevant": bool, "reason": str}。

    使用场景：流水线 runner 对 arXiv 搜到的每篇论文调用，过滤掉不相关的（如纯渲染优化）。
    """
    client = get_client()
    messages = build_relevance_prompt(title, abstract)

    # client.chat.completions.create()：OpenAI chat API 的核心调用。
    # model：用哪个模型。messages：对话消息列表。
    # response_format={"type": "json_object"}：强制模型返回合法 JSON（JSON mode）。
    #   不加这个，模型可能返回带 markdown 代码块的文本，需要手动 strip。
    #   加了之后，模型保证返回的是可 parse 的 JSON 字符串。
    # temperature=0：随机性设为 0，让输出尽量确定（分类任务要一致性，不要创意）。
    response = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=messages,
        response_format={"type": "json_object"},
        temperature=0,
    )

    # response.choices[0].message.content：模型返回的文本（JSON 字符串）。
    # choices 是候选回复列表，默认只返回 1 个（n=1），取 [0]。
    raw = response.choices[0].message.content
    # json.loads：把 JSON 字符串解析成 Python dict（类似 JS 的 JSON.parse）。
    return json.loads(raw)


def extract_paper_fields(title: str, abstract: str) -> dict:
    """
    作用：从论文标题+摘要抽取结构化分类字段（按 taxonomy）。

    参数：
        title：论文标题。
        abstract：论文摘要。

    返回：dict，包含 task_type/attribute_selection/distribution_strategy/injection_pipeline/
        robustness_targets/method_summary/key_contributions/capacity/datasets_used/baselines_compared。

    异常：LLM 返回非法 JSON 时抛 json.JSONDecodeError。

    使用场景：流水线 runner 对通过相关性过滤的论文调用，抽取分类字段后入库。
    """
    client = get_client()
    messages = build_extraction_prompt(title, abstract)

    response = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=messages,
        response_format={"type": "json_object"},
        temperature=0,
    )

    raw = response.choices[0].message.content
    result = json.loads(raw)

    # 清洗：确保多选字段是 list（LLM 偶尔会返回单个字符串而非数组）。
    # 如果 LLM 返回 "watermarking" 而非 ["watermarking"]，手动包成 list。
    for field in ("task_type", "robustness_targets", "key_contributions",
                  "datasets_used", "baselines_compared"):
        val = result.get(field)
        if val is None:
            result[field] = []
        elif isinstance(val, str):
            # 单字符串转单元素列表
            result[field] = [val]

    return result
