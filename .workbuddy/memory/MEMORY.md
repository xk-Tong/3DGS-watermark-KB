# 3DGS_KB 项目长期记忆

## 项目定位
个人知识库/Wiki，追踪 3D Gaussian Splatting (3DGS) 水印及 IP 保护方向论文。
主要自用，偶尔展示给导师/同门。**另一个核心目标：借做这个项目学习全栈 web 开发（前后端、部署上线）**。

## 已锁定决策（grill-me 会话，2026-07-14）

### 技术栈（分支 2）
- 前端：Vue 3 + Vite（用户有少量 Vue/FastAPI 基础）
- 后端：FastAPI（Python 单语言贯穿后端 + AI 流水线）
- Python 环境：**本地 miniconda 环境 `3dgsw_kb`**（Python 3.12.13，/opt/miniconda3/envs/3dgsw_kb/bin/python）。用户明确不用 workbuddy managed venv，用本地 miniconda 专用环境。
- 数据库：SQLite（单人规模足够）
- 部署：国内轻量云服务器 2核2G 3M带宽（~60-99 RMB/年）或海外免费机，动手时再定
- 初期用 IP+端口访问，免备案；后期再考虑域名备案
- AI 流水线触发方式：**手动触发**（Web UI 按钮），不用 cron。检索时按"距上次成功抓取"为日期范围，避免漏论文。
- 质量门：自动入库 + curation_status=auto 徽章 + 统计隔离（auto 不进聚合视图）+ 异步人工复核（auto→reviewed→verified）
- LLM 抽取只负责分类字段和摘要性内容；title/authors/abstract/pub_date/arxiv_id 由 arXiv API 直接给，不进 LLM
- 更新已有论文时只覆盖 curation_status=auto 的字段，reviewed/verified 的人工修正不被覆盖
- Prompt 必须附综述 taxonomy 定义 + few-shot 示例，否则分类会乱
- 冷启动：从综述参考文献列表种子 → 解析 arXiv ID → 批量 API 抓取 → 走同一抽取流水线；非 arXiv 论文走 DOI 查询或手动录入

### 数据模型与分类体系（分支 3）
- 分类范式：**混合（受控枚举 + 自由标签）**，枚举基于 3DGS IP 保护综述的三层框架
- 任务类型（多选）：watermarking / steganography / tamper_localization / editing_protection / other
- 机制三维度（单选，综述第一层，正交）：
  - attribute_selection: sh_only / mixed / auxiliary / other
  - distribution_strategy: global / local_frequency / local_uncertainty / other
  - injection_pipeline: per_asset_finetune / generalizable_mapping / generation_embedded / other
- robustness_targets（多选受控词表，综述第三层）：2D(geometric_transform/photometric/signal_degradation) + 3D(pruning/cloning/spatial_transform/noise_injection/quantization/parameter_merging)
- tags：完全自由
- KB 覆盖范围：综述四类任务全部收录，水印设为默认筛选
- 实验对比建模：PSNR / SSIM / bit_accuracy 三个 headline 固定列 + extra_metrics JSON 兜底
- 关系建模(PaperRelation)第一版不做，等基础流程跑顺再加
- 个人字段：read_status(unread/reading/read) + personal_notes + curation_status(auto/reviewed/verified)

### 参考综述
`3dgs水印综述总结.md` — 2026年2月发表的 3DGS IP 保护首篇系统综述，三层框架（扰动机制 / 保护范式 / 鲁棒性威胁）是分类体系的文献依据。综述 arXiv 可拿 LaTeX 源码 + .bib，作为冷启动种子来源。

### 部署 & 模型耦合（分支 4 收尾）
- **国内轻量机 + DeepSeek**：国内访问快、模型便宜、抽取质量够用、不被墙。
- 海外免费机会导致国内访问 Web 慢，且若用 OpenAI/Claude 与国内部署不匹配。
- LLM API key 存服务器（手动触发，前端不接触 key）。

### 检索浏览 UX & 可视化（分支 5/6）
- 列表页：筛选条（task_type 默认 watermarking、三机制维度、robustness、tags、年份、read_status、curation_status）+ 关键词搜索（title/abstract/method_summary/personal_notes）+ 排序（pub_date/added_at/PSNR）
- 详情页：全字段卡片 + 个人批注编辑区
- 对比视图：勾选 2-4 篇 → 横向对比表（机制维度/指标/鲁棒性并排）
- 可视化：时间线柱状图、机制三维度分布 + 属性×注入交叉热力图、攻击覆盖矩阵（论文×robustness_targets）、统计仪表盘
- 默认视图：水印筛选 + reviewed/verified（auto 不进聚合统计但库内可见带徽章）
- curation_status 徽章：auto 显示"⚠️ AI 抽取未核实"

### grill-me 会话已全部完成（2026-07-14/15）
六个分支全部解决，无遗留 "it depends"。产出 `设计决策与实施路线.md` 作为可参考的决策快照。
