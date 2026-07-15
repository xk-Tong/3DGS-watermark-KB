# pipeline/ — AI 检索-抽取-入库流水线

Phase 2 实现，Phase 0 仅占位。

## 规划内容（Phase 2）

- arXiv API 抓取（关键词搜索 + id_list 批量）
- DeepSeek 集成：相关性过滤 + 结构化抽取（带综述 taxonomy prompt）
- schema 校验 + 错误队列
- 手动触发（Web UI 按钮调 FastAPI 后端）
- curation_status 流转

详见 `设计决策与实施路线.md` 第四节。
