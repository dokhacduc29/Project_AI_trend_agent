# CLAUDE.md — AI Trend Agent

> File memory chính cho Claude Code khi làm việc trong repo này.
> Mục tiêu: cung cấp context kiến trúc, Iron Laws, và workflow để AI agent hành xử nhất quán.

---

## 1. Project Snapshot

- **Tên**: AI Trend Agent v3.1 — SOLID Edition
- **Ngôn ngữ**: Python 3.13 (async)
- **Mục đích**: Pipeline tự động thu thập tin AI từ 3 nguồn (NewsAPI, Reddit JSON, Google News RSS), làm sạch, phân loại bằng regex/Gemini, và lưu CSV.
- **Pattern chính**: Factory + Strategy + Pipeline (ETL) qua các `BaseAgent`.

## 2. Cấu trúc thư mục

```
AI_Trend_Agent/
├── main.py                  # Orchestrator: asyncio.run(main()) → run_pipeline(agents, ctx)
├── modules/
│   ├── base_agent.py        # BaseAgent (ABC) + AgentFactory (decorator-based)
│   ├── models.py            # @dataclass Article + PipelineContext
│   ├── config.py            # Hằng số tập trung — Luật L09
│   ├── scrapers.py          # ScraperAgent — async multi-source
│   ├── cleaner.py           # CleanerAgent — regex tag + dedupe
│   ├── ai_agent.py          # AIAnalyzerAgent — Gemini summary + sentiment
│   ├── storage.py           # StorageAgent — CSV append
│   └── decorators.py        # @retry, @timer, context managers
├── data/                    # Output CSV (auto-tạo, gitignore)
├── .claude/skills/          # Skills định nghĩa hành vi AI agent
├── knowledge/               # LLM Wiki — kiến thức dự án
└── .env                     # NEWS_API_KEY, GEMINI_API_KEY (KHÔNG commit)
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
# Cài đặt
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Chạy
python main.py

# Dừng an toàn: Ctrl + C
```

## 8. Roadmap nhanh

- [x] Phase 1-2: Foundation + Pythonic
- [x] Phase 3: OOP + SOLID
- [x] Phase 4: Gemini AI integration
- [ ] Phase 5: SQLite/PostgreSQL thay CSV
- [ ] Phase 6: Telegram/Discord publisher

Chi tiết: `.claude/skills/roadmap/SKILL.md`.

## 9. Liên kết

- Architecture: `knowledge/architecture/overview.md`
- Decisions log: `knowledge/decisions/`
- API references: `knowledge/apis/`
- Prompt templates: `knowledge/prompts/`
- Glossary: `knowledge/glossary.md`
