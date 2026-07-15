"""
arXiv API 客户端封装。

arXiv 提供免费的公开 API，无需 API key，但有速率限制（建议每 3 秒最多 1 个请求）。
API 文档：https://info.arxiv.org/help/api/index.html

本模块封装两个核心功能：
  1. 关键词搜索：按 search_query 搜索最新论文
  2. 批量按 ID 抓取：给定 arxiv_id 列表，批量拉取元数据（冷启动用）

arXiv API 返回的是 Atom 1.0 格式的 XML（一种类似 RSS 的内容聚合格式），
需要解析 XML 提取每篇论文的 title/abstract/authors 等字段。
"""
import time
import re
import xml.etree.ElementTree as ET
from typing import Optional

import requests

# arXiv API 端点
ARXIV_API_URL = "http://export.arxiv.org/api/query"

# Atom XML 的命名空间（Namespace）。
# XML 命名空间类似 Python 的包名，避免不同 XML 格式的标签名冲突。
# Atom 标准用 "http://www.w3.org/2005/Atom"，arXiv 自己的扩展用 "http://arxiv.org/schemas/atom"。
# 解析时必须带命名空间前缀，否则找不到标签。
NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
}

# 模块级变量：记录上次请求时间，用于限速。
# arXiv 要求请求间隔至少 3 秒，否则可能被封 IP。
_last_request_time: float = 0.0


def _rate_limit():
    """
    作用：确保两次请求间隔至少 3 秒，遵守 arXiv API 速率限制。

    使用场景：每次调 arXiv API 前调用。
    """
    global _last_request_time
    now = time.time()
    elapsed = now - _last_request_time
    if elapsed < 3.0:
        # 还没到 3 秒，sleep 等待剩余时间。
        # time.sleep 是同步阻塞，会暂停当前线程——Phase 2 流水线跑在后台任务里，阻塞没关系。
        time.sleep(3.0 - elapsed)
    _last_request_time = time.time()


def _extract_arxiv_id(id_url: str) -> str:
    """
    作用：从 arXiv 返回的 <id> 字段提取纯 arxiv_id。

    参数：
        id_url：arXiv 返回的 id 字段值，格式如 "http://arxiv.org/abs/2410.03461v1"

    返回：纯 id 如 "2410.03461"（去掉 URL 前缀和版本号 v1）。

    使用场景：解析 Atom XML 时，每个 entry 的 id 是完整 URL，需要提取纯 ID 用于去重和存储。
    """
    # re.sub：正则替换。匹配 "http://arxiv.org/abs/" 前缀，去掉它。
    # [^/]+ 匹配路径部分（2410.03461v1），$ 匹配字符串结尾。
    match = re.search(r"arxiv\.org/abs/(.+)$", id_url)
    if not match:
        return id_url
    raw_id = match.group(1)
    # 去掉版本号：2410.03461v1 → 2410.03461
    # rsplit("v", 1) 从右往左按 "v" 分割一次，取第一部分。
    # 但有些旧 id 格式是 math/0701234 这种，不带 v 版本号，直接返回。
    if "v" in raw_id and raw_id.rsplit("v", 1)[1].isdigit():
        return raw_id.rsplit("v", 1)[0]
    return raw_id


def _parse_entry(entry: ET.Element) -> dict:
    """
    作用：解析单个 Atom <entry> 元素，提取论文元数据。

    参数：
        entry：xml.etree.ElementTree.Element 对象，对应一个 <entry> 标签。

    返回：dict，包含 arxiv_id/title/authors/abstract/published/updated/doi/pdf_url。

    使用场景：_parse_atom 内部对每个 entry 调用。
    """
    # entry.find("atom:title", NS)：在 entry 子元素里找带 atom 命名空间的 title 标签。
    # NS 是前面定义的命名空间字典，"atom:title" 表示 atom 命名空间下的 title。
    title_el = entry.find("atom:title", NS)
    # .text 拿到标签内的文本内容；找不到时 title_el 是 None，用空字符串兜底。
    title = title_el.text.strip() if title_el is not None and title_el.text else ""
    # arXiv 的 title 里常有换行和多余空格，替换成单空格。
    title = re.sub(r"\s+", " ", title)

    summary_el = entry.find("atom:summary", NS)
    abstract = summary_el.text.strip() if summary_el is not None and summary_el.text else ""
    abstract = re.sub(r"\s+", " ", abstract)

    # 作者列表：可能有多个 <author><name>...</name></author>
    authors = []
    for author_el in entry.findall("atom:author", NS):
        name_el = author_el.find("atom:name", NS)
        if name_el is not None and name_el.text:
            authors.append(name_el.text.strip())

    id_el = entry.find("atom:id", NS)
    id_url = id_el.text.strip() if id_el is not None and id_el.text else ""
    arxiv_id = _extract_arxiv_id(id_url)

    published_el = entry.find("atom:published", NS)
    published = published_el.text.strip() if published_el is not None and published_el.text else None

    updated_el = entry.find("atom:updated", NS)
    updated = updated_el.text.strip() if updated_el is not None and updated_el.text else None

    # DOI：arXiv 用自己的命名空间 arxiv:doi
    doi_el = entry.find("arxiv:doi", NS)
    doi = doi_el.text.strip() if doi_el is not None and doi_el.text else None

    # PDF 链接：从 <link> 标签找 rel="related" title="pdf" 的那个
    pdf_url = None
    for link_el in entry.findall("atom:link", NS):
        if link_el.get("title") == "pdf":
            pdf_url = link_el.get("href")
            break

    return {
        "arxiv_id": arxiv_id,
        "title": title,
        "authors": authors,
        "abstract": abstract,
        "published": published,
        "updated": updated,
        "doi": doi,
        "pdf_url": pdf_url,
    }


def _parse_atom(xml_text: str) -> list[dict]:
    """
    作用：解析 arXiv API 返回的 Atom XML，提取所有论文元数据。

    参数：
        xml_text：arXiv API 返回的 XML 字符串。

    返回：list[dict]，每个 dict 是一篇论文的元数据（见 _parse_entry 返回值）。

    异常：XML 格式错误时抛 ET.ParseError。

    使用场景：search_papers 和 fetch_by_ids 内部调用。
    """
    # ET.fromstring：把 XML 字符串解析成 Element 树。
    # 类似 JSON.parse() 解析 JSON，这里是解析 XML。
    root = ET.fromstring(xml_text)

    # root 是 <feed> 根元素，里面每个 <entry> 是一篇论文。
    # findall("atom:entry", NS)：找所有 entry 子元素。
    entries = root.findall("atom:entry", NS)

    # 列表推导式（list comprehension）：[expr for item in iterable]
    # 对每个 entry 调用 _parse_entry，收集结果成列表。
    # 等价于：results = []; for e in entries: results.append(_parse_entry(e)); return results
    return [_parse_entry(e) for e in entries]


def search_papers(
    query: str,
    max_results: int = 50,
    start: int = 0,
    sort_by: str = "submittedDate",
    sort_order: str = "descending",
) -> list[dict]:
    """
    作用：按关键词搜索 arXiv 论文。

    参数：
        query：arXiv search_query 语法字符串。
            例：'all:"Gaussian Splatting" AND (all:watermark OR all:steganography)'
            语法说明：all: 搜全部字段；ti: 标题；abs: 摘要；cat: 分类；AND/OR/ANDNOT 逻辑。
        max_results：最多返回几篇，默认 50。arXiv 单次最多 2000。
        start：跳过前 N 条（分页用），默认 0。
        sort_by：排序字段，默认 "submittedDate"（按提交日期）。
            可选："relevance"（相关度）/"lastUpdatedDate"（最后更新）/"submittedDate"（提交日期）。
        sort_order：排序方向，"descending"（降序，新→旧）或 "ascending"（升序）。

    返回：list[dict]，每个 dict 是一篇论文元数据。

    使用场景：流水线 runner 调用，搜索 3DGS 水印相关新论文。
    """
    _rate_limit()

    # 构造查询参数。
    params = {
        "search_query": query,
        "start": start,
        "max_results": max_results,
        "sortBy": sort_by,
        "sortOrder": sort_order,
    }

    # requests.get：发起 HTTP GET 请求。
    # timeout=30：30 秒超时，防止 arXiv 服务器卡住导致流水线挂死。
    resp = requests.get(ARXIV_API_URL, params=params, timeout=30)
    # raise_for_status()：HTTP 状态码 4xx/5xx 时抛异常，2xx 不抛。
    # 这样调用方能用 try/except 捕获网络错误。
    resp.raise_for_status()

    return _parse_atom(resp.text)


def fetch_by_ids(arxiv_ids: list[str]) -> list[dict]:
    """
    作用：按 arxiv_id 列表批量抓取论文元数据（冷启动用）。

    参数：
        arxiv_ids：arxiv_id 字符串列表，如 ["2410.03461", "2401.12345"]。

    返回：list[dict]，每个 dict 是一篇论文元数据。

    使用场景：冷启动从综述 .bib 提取 arxiv_id 后批量抓取；或补漏检索。
    """
    if not arxiv_ids:
        return []

    _rate_limit()

    # arXiv id_list API：用逗号分隔多个 id，一次请求拉多篇。
    params = {
        "id_list": ",".join(arxiv_ids),
        "max_results": len(arxiv_ids),
    }

    resp = requests.get(ARXIV_API_URL, params=params, timeout=30)
    resp.raise_for_status()

    return _parse_atom(resp.text)


# ---- 预定义的搜索查询 ----
# 决策文档定义的关键词：搜 3DGS IP 保护相关论文。
# all:"Gaussian Splatting" 精确匹配这个词组，AND 后接水印/隐写/篡改/编辑防护等关键词的 OR 组合。
DEFAULT_SEARCH_QUERY = (
    'all:"Gaussian Splatting" AND '
    '(all:watermark OR all:steganography OR all:tamper OR all:"editing protection" OR all:"IP protection")'
)
