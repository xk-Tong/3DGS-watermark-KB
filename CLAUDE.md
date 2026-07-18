# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

A personal knowledge base tracking 3D Gaussian Splatting (3DGS) watermarking & IP-protection papers. Backend: FastAPI + SQLModel + SQLite. Frontend: Vue 3 + Vite + Element Plus + Pinia + ECharts. A DeepSeek-powered AI pipeline auto-discovers and ingests arXiv papers. The taxonomy (enums in `backend/app/models/paper.py`) is derived from `3dgs水印综述总结.md`; the design rationale lives in `设计决策与实施路线.md`.

## Commands

Backend (run from `backend/`, uses the conda env `/opt/miniconda3/envs/3dgsw_kb/bin/python`):
```bash
# first time: install deps + seed a GuardSplat paper
/opt/miniconda3/envs/3dgsw_kb/bin/pip install -r requirements.txt
/opt/miniconda3/envs/3dgsw_kb/bin/python -m app.core.seed
# dev server (port 8000, --reload)
/opt/miniconda3/envs/3dgsw_kb/bin/python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
# health check
curl localhost:8000/api/health   # -> {"status":"ok"}
```

Frontend (run from `frontend/`, node 24 via nvm `/Users/kang/.nvm/versions/node/v24.18.0/bin/`):
```bash
/Users/kang/.nvm/versions/node/v24.18.0/bin/npm install
/Users/kang/.nvm/versions/node/v24.18.0/bin/npx vite --port 5173
# build: npm run build  (produces frontend/dist)
```

**Start order: backend first, then frontend** (frontend's Vite proxy targets `127.0.0.1:8000`).

There is no test suite and no linter configured. There is no DB migration tool — schema changes require `rm backend/data/kb.db` and restart (tables auto-create via `SQLModel.metadata.create_all` on startup). Do not blow away `kb.db` without flagging it — it holds real ingested data.

DeepSeek API key: copy `backend/.env.example` → `backend/.env` and set `DEEPSEEK_API_KEY` (loaded via `load_dotenv()` in `app/config.py`). Without it the backend starts but the LLM pipeline steps raise at runtime.

## Architecture

### Backend (`backend/app/`)
- `main.py` — FastAPI app; `lifespan` hook calls `create_db_and_tables()` on startup; CORS via `settings.cors_origins`; routers mounted under `/api`.
- `config.py` — `BASE_DIR` resolved from `__file__`; loads `.env`; holds `settings.db_path` (= `backend/data/kb.db`) and `cors_origins` (the Vite dev origin `localhost:5173` is hardcoded here — update for prod).
- `database.py` — single global `engine` (SQLite, `check_same_thread=False`); `get_session()` is the FastAPI dependency. `models.paper.Paper` is imported here purely to register the model with `SQLModel.metadata` — do not remove that import or `create_all` creates no `papers` table.
- `models/paper.py` — **the core schema**. Defines the `Paper` SQLModel table plus all enums (`SourceType`, `TaskType`, `AttributeSelection`, `DistributionStrategy`, `InjectionPipeline`, `RobustnessTarget`, `ReadStatus`, `CurationStatus`). Multi-select fields (`task_type`, `robustness_targets`, `tags`, lists, `extra_metrics`) are stored as `sa.Column(sa.JSON)`. Single-select enums are stored as their string value. Three enums have members whose `.value` differs from their identifier (e.g. `global_ = "global"`) — always compare/store via `.value`. `DistributionStrategy`, `InjectionPipeline`, and the single-select enums are the canonical taxonomy; changing them means re-deriving from the review doc.
- `schemas/paper.py` — Pydantic schemas **separate** from the ORM model (storage shape vs. API contract). `PaperCreate` (no `id`/`added_at`), `PaperRead` (`from_attributes=True` so ORM objects serialize), `PaperUpdate` (all-Optional PATCH semantics). `task_type`/`robustness_targets` are validated against `ALLOWED_*` string sets here because JSON columns can't carry enum validation at the ORM layer.
- `api/papers.py` — list (filter/search/sort/paginate), get, create, PATCH update. JSON-array filtering uses `LIKE '%"value"%'` on the SQLite-serialized string (acceptable at <200-row scale). Total count uses `select(func.count()).select_from(stmt.subquery())` to respect WHERE. PATCH uses `model_dump(exclude_unset=True)` + `setattr` to honor partial updates; mutating `read_status`/`curation_status` sets `last_reviewed_at`. SQLite-specific SQL (e.g. `func.strftime("%Y", ...)`) is used in places — switching DB needs rewriting.
- `api/stats.py` — `GET /api/stats/overview` and `/robustness` for the dashboard. SQLite has no JSON query functions, so multi-select aggregates are computed in Python by loading all rows (fine at current scale).
- `api/pipeline.py` — `POST /api/pipeline/run` (registers `run_pipeline` as a `BackgroundTasks` job and returns immediately) + `GET /api/pipeline/status` (polled by frontend). The long runtime is why this isn't synchronous.
- `pipeline/` — `arxiv_client.py` (Atom XML parsing, 3s rate-limit via `_rate_limit`, `DEFAULT_SEARCH_QUERY`), `llm_client.py` (OpenAI SDK pointed at DeepSeek `base_url`, lazy singleton, uses `response_format={"type":"json_object"}` + `temperature=0`), `prompts.py` (taxonomy definition + few-shot examples fed to the LLM so it emits the exact enum strings, not free-form text), `runner.py` (orchestrates fetch → dedup by `arxiv_id` → relevance filter → extract → ingest with `curation_status=auto`; status held in module-level `PipelineStatus` class, not persisted). `_build_paper` keeps arXiv-sourced fields (title/authors/abstract/pub_date) out of the LLM and only trusts the LLM for classification + summary fields.
- `core/seed.py` — idempotent GuardSplat seed.

### Frontend (`frontend/src/`)
- `main.js` — Pinia + Vue Router + Element Plus (full import) + `assets/tokens.css` imported **after** Element Plus so design-token CSS variables override defaults. Theme system (dark/light) lives in `composables/useTheme.js` and `assets/tokens.css`.
- `router/index.js` — routes: `/` (HomeView hero), `/papers`, `/papers/:id`, `/dashboard`, `/compare`.
- `api/` — `client.js` is an axios instance with `baseURL: '/api'` (relies on Vite proxy in dev → Nginx in prod); per-resource wrappers in `papers.js`, `pipeline.js`, `stats.js`, `options.js`.
- `stores/papers.js` — the Pinia store holds `items`, `total`, `loading`, `filters`, `limit/offset`, and `selectedForCompare` (2–4 paper ids for the compare view). `fetchList` strips null/empty params before sending.
- `views/` + `components/` — `PaperListView` (table + filters + compare checkboxes), `PaperDetailView`, `DashboardView` (ECharts via `components/EChartsBase.vue`), `CompareView`, `HomeView`. `PipelinePanel.vue` is the trigger/poll UI. `GaussParticles.vue` is the decorative 3DGS-themed background.
- `@` alias → `./src` (configured in `vite.config.js`). Vite dev proxies `/api` → `http://127.0.0.1:8000`.

### Invariants worth keeping
- **Model vs schema split**: never add API fields to `models/paper.py` thinking that's enough — add them to the right Pydantic schema (`PaperCreate`/`PaperRead`/`PaperUpdate`) too, or they won't be accepted/returned by the API.
- **Add a new taxonomy value**: update the enum in `models/paper.py`, the `ALLOWED_*` sets in `schemas/paper.py`, the taxonomy text in `pipeline/prompts.py` (so the LLM emits it), and any frontend option enumerations in `api/options.js`.
- **JSON-column mutability**: list/dict defaults on `Paper` use `default=[]`/`None` + `sa_column=sa.Column(sa.JSON)` together — both are required.
- **arXiv rate limit**: keep `time.sleep` gating in `arxiv_client._rate_limit`; arXiv bans IPs that exceed ~1 req / 3s.
- **curation_status**: `auto` entries show an "未核实" badge and stay out of dashboard statistics by design — don't silently include them.