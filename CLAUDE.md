# CLAUDE.md — AI Trend Agent

> File memory chính cho Claude Code khi làm việc trong repo này.
> Mục tiêu: cung cấp context kiến trúc, Iron Laws, và workflow để AI agent hành xử nhất quán.

> **Trước mỗi phiên, đọc `docs/ai-context/context-index.md`** — entry point nạp
> đầy đủ ngữ cảnh (tổng quan, Luật Thép, nhật ký quyết định/ADR).

---

## 1. Project Snapshot

- **Tên**: AI Trend Agent v4.0 — SOLID Edition
- **Ngôn ngữ**: Python 3.13 (async)
- **Mục đích**: Pipeline ETL tự động thu thập tin AI từ 3 nguồn (NewsAPI, Reddit JSON, Google News RSS), làm sạch (regex + Hybrid AI cleaner), phân tích bằng Gemini (summary/sentiment/trend synthesis), lưu **Supabase PostgreSQL** (CSV là fallback legacy), và phát hành qua **Discord webhook**.
- **Pattern chính**: Factory + Strategy + Pipeline (ETL) qua các `BaseAgent`; pipeline phân biệt agent *critical* (lỗi → dừng) vs *enrichment* (lỗi → degrade).

## 2. Cấu trúc thư mục

```
AI_Trend_Agent/
├── pyproject.toml           # Khai báo package (src-layout) — ADR 0014
├── Dockerfile               # Multi-stage build (builder + runtime, non-root)
├── .dockerignore
├── k8s/                     # K8s manifests (00-namespace → 04-service)
├── Backend/
│   ├── requirements.txt         # Superset: runtime + dev (pytest)
│   ├── requirements-runtime.txt # Deps của image — nguồn sự thật cho runtime
│   ├── .env                     # NEWS_API_KEY, GEMINI_API_KEY, SUPABASE_* (KHÔNG commit)
│   ├── src/ai_trend_agent/      # PACKAGE THẬT — import tuyệt đối, không hack sys.path
│   │   ├── domain/
│   │   │   ├── models.py        # @dataclass Article + PipelineContext + Sentiment enum
│   │   │   └── config.py        # Hằng số tập trung — Luật L09
│   │   ├── application/
│   │   │   ├── base_agent.py    # BaseAgent (ABC) + AgentFactory (decorator-based)
│   │   │   ├── decorators.py    # @retry, @timer, context managers
│   │   │   ├── log_redaction.py # Che secret trong log (ADR 0009)
│   │   │   └── prompt_loader.py # Nạp prompt từ prompts/ (ADR 0004)
│   │   ├── infrastructure/
│   │   │   ├── scrapers.py          # ScraperAgent — async multi-source
│   │   │   ├── cleaner.py           # CleanerAgent — regex tag + dedupe + Hybrid AI (ADR 0002)
│   │   │   ├── ai_agent.py          # SummarizationAgent — Gemini summary + sentiment
│   │   │   ├── trend_agent.py       # TrendSynthesisAgent — tổng hợp xu hướng (ADR 0001)
│   │   │   ├── gemini_client.py     # Client Gemini + budget enforcement (ADR 0005)
│   │   │   ├── storage.py           # StorageAgent — CSV append (legacy fallback)
│   │   │   ├── supabase_storage.py  # SupabaseStorageAgent — Supabase PostgreSQL (chính)
│   │   │   ├── discord_agent.py     # DiscordAgent — publisher webhook (ADR 0007)
│   │   │   └── telegram_agent.py    # TelegramAgent — deprecated (thay bằng Discord)
│   │   ├── prompts/             # Prompt-as-artifact (ADR 0004) — PACKAGE DATA, đi kèm khi cài
│   │   └── worker/
│   │       └── main.py          # Orchestrator one-shot: cli() → run_pipeline
│   └── tests/
│       ├── test_agents.py       # pytest unit tests
│       ├── test_evals.py        # Eval suite — parser & robustness output AI (ADR 0006)
│       └── evals/               # Golden datasets (vd: golden_sentiment.json)
├── .claude/skills/          # Skills định nghĩa hành vi AI agent
└── docs/                    # Tài liệu, roadmap, kiến trúc (gồm docs/ai-context/)
```

## 3. 10 Iron Laws (rút gọn)

| # | Luật | Áp dụng |
|---|------|---------|
| L01 | No hardcoded secrets | Dùng `python-dotenv` + `.env` |
| L02 | Logging only | Cấm `print()`, dùng module `logging` |
| L03 | Async-first I/O | `httpx` + `asyncio.gather()` cho mọi API call |
| L04 | No SQL injection | ORM hoặc parameterized query |
| L05 | FastAPI-only nếu làm API | Có pagination + rate limit |
| L06 | Soft delete | `is_deleted=True`, không `DELETE` cứng |
| L07 | Fault tolerance | Mọi external call có `timeout` + `try/except` |
| L08 | Type hints + docstring | Bắt buộc |
| L09 | No magic numbers | Mọi hằng số → `config.py` |
| L10 | Decision log | Thay đổi lớn ghi vào `knowledge/decisions/` |

Chi tiết đầy đủ: xem `.claude/skills/coding-rules/SKILL.md`.

## 4. Naming Convention

- Docs (`.md`): `lowercase-with-hyphens.md`
- Python files: `snake_case.py`
- Class: `PascalCase`
- Function/var: `snake_case`
- Tag commit: `feat:`, `fix:`, `refactor:`, `docs:`, `chore:`

## 5. Workflow khi nhận task

1. **Plan**: Tóm tắt 3-5 bước, list file ảnh hưởng.
2. **Confirm**: Chờ user `OK` / `proceed` (trừ bugfix khẩn).
3. **Ambiguity**: Gắn tag `[VERIFY]` khi yêu cầu mơ hồ — KHÔNG bịa.
4. **Output**: Markdown chuyên nghiệp, không dùng H1 trong báo cáo nhỏ.

## 6. Quy tắc thay đổi kiến trúc

- Mọi thay đổi `BaseAgent`, `PipelineContext`, hoặc Factory → ghi ADR vào `knowledge/decisions/`.
- Thêm Agent mới → chỉ cần `@AgentFactory.register("ten_agent")`, không sửa `main.py` hay Factory (luật OCP).
- Thay đổi schema CSV → cập nhật `config.CSV_FIELDNAMES` và migration note.

## 7. Run & Debug

```powershell
# Cài đặt — LUÔN cài editable, package phải nằm trong môi trường thì import
# tuyệt đối (ai_trend_agent.domain.models) mới hoạt động.
python -m venv venv
venv\Scripts\activate
pip install -e .
pip install -r Backend/requirements.txt   # thêm dev deps (pytest)

# Chạy — console script sinh bởi pyproject.toml
ai-trend-worker
# hoặc: python -m ai_trend_agent.worker.main

# Chạy test (từ gốc repo, không cần cd Backend)
pytest Backend/tests -v

# Dừng an toàn: Ctrl + C
```

## 8. Roadmap nhanh

- [x] Phase 1-2: Foundation + Pythonic
- [x] Phase 3: OOP + SOLID
- [x] Phase 4: Gemini AI integration (summary/sentiment + TrendSynthesis + Hybrid cleaner)
- [x] Phase 5: Supabase PostgreSQL cloud database (thay CSV)
- [x] Deploy: Docker multi-stage build + Kubernetes (minikube)
- [x] Hardening: pipeline resilience (ADR 0003), externalize prompts (ADR 0004), Gemini budget (ADR 0005), eval suite (ADR 0006)
- [x] Phase 6: Discord publisher qua webhook (ADR 0007 — pivot từ Telegram)
- [x] CI/CD: GitHub Actions pipeline (ADR 0013 — test→build→smoke→Trivy→push GHCR)

Chi tiết: `.claude/skills/roadmap/SKILL.md`.

## 9. Liên kết

- Architecture: `knowledge/architecture/overview.md`
- Decisions log: `knowledge/decisions/`
- API references: `knowledge/apis/`
- Prompt templates: `knowledge/prompts/`
- Glossary: `knowledge/glossary.md`
