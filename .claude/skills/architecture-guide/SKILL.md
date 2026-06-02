---
name: architecture-guide
description: Tham chiếu khi cần hiểu hoặc thay đổi kiến trúc tổng thể của AI Trend Agent (Factory, Pipeline, BaseAgent, PipelineContext, các Agent). Dùng trước khi thêm Agent mới hoặc sửa pipeline.
---

# Architecture Guide — AI Trend Agent

## Tổng quan

AI Trend Agent là một pipeline ETL bất đồng bộ theo mô hình **Aggregator + Factory**:

```
[ScraperAgent] → [CleanerAgent] → [AIAnalyzerAgent] → [StorageAgent]
       │              │                 │                  │
       └──────────── PipelineContext (shared dataclass) ───┘
```

## Các thành phần cốt lõi

### 1. `BaseAgent` (ABC) — `modules/base_agent.py`
- Định nghĩa interface: `async execute(ctx: PipelineContext) → PipelineContext`.
- Cung cấp helper: `log_info()`, `log_error()`.
- Mọi Agent kế thừa class này.

### 2. `AgentFactory` — `modules/base_agent.py`
- Decorator `@AgentFactory.register("ten")` — Agent **tự đăng ký** khi import.
- Tuân thủ **OCP**: thêm Agent mới KHÔNG cần sửa Factory.
- Tạo instance qua `AgentFactory.create("ten")`.

### 3. `PipelineContext` — `modules/models.py`
- `@dataclass` chứa: `topic`, `api_key`, `gemini_api_key`, `articles: list[Article]`.
- Chuyển qua tất cả Agent → đảm bảo **LSP** (cùng signature `ctx → ctx`).

### 4. Article schema (`modules/models.py`)
```python
@dataclass
class Article:
    title: str
    source: str        # "NewsAPI" | "Reddit" | "Google News RSS"
    date: str          # ISO 8601
    url: str
    tags: list[str]    # ["#OpenAI", "#Funding_Money", ...]
    summary: str = ""  # AI-generated (Phase 4)
    sentiment: str = "" # "Positive" | "Negative" | "Neutral"
```

## Các Agent hiện có

| Agent | Trách nhiệm | Key tech |
|-------|-------------|----------|
| `ScraperAgent` | Fetch song song 3 nguồn | `httpx.AsyncClient` + `asyncio.gather` |
| `CleanerAgent` | Dedupe (Set O(1)) + regex tag | `re` + `set()` |
| `AIAnalyzerAgent` | Summary + sentiment | `google-generativeai` (Gemini) |
| `StorageAgent` | Append CSV + analytics | `csv.DictWriter` + `defaultdict` |

## Quy tắc khi thêm Agent mới

1. Tạo file `modules/<ten_agent>.py`.
2. Class kế thừa `BaseAgent`, decorator `@AgentFactory.register("ten")`.
3. Implement `async def execute(self, ctx) -> PipelineContext`.
4. Trong `main.py`: thêm `import modules.<ten_agent>` (side-effect để decorator chạy).
5. Thêm `AgentFactory.create("ten")` vào list `agents`.
6. **KHÔNG sửa** `BaseAgent`, `AgentFactory`, hay `run_pipeline`.

## SOLID compliance

| Nguyên tắc | Cách áp dụng |
|-----------|--------------|
| **S** — SRP | Mỗi Agent đúng 1 trách nhiệm |
| **O** — OCP | Decorator-based registration |
| **L** — LSP | Mọi Agent đều `(ctx) → ctx` |
| **I** — ISP | `BaseAgent` chỉ expose `execute()` + log helpers |
| **D** — DIP | `run_pipeline(agents: list[BaseAgent])` |

## Anti-patterns đã loại bỏ

- ❌ `time.sleep()` trong loop async → ✅ `asyncio.sleep()`
- ❌ `requests` đồng bộ → ✅ `httpx` async
- ❌ `schedule.every().hours.do(...)` → ✅ `asyncio.sleep(interval)`
- ❌ Magic numbers rải rác → ✅ `config.py`
- ❌ `asyncio.run()` lồng trong sync wrapper → ✅ `asyncio.run(main())` ở `__main__`

## Khi nào sửa kiến trúc

- Thay storage backend (CSV → SQLite) → tạo `DatabaseStorageAgent`, swap trong list `agents`.
- Thêm publisher (Telegram/Discord) → tạo Agent mới sau Storage.
- Thay đổi `PipelineContext` → ADR bắt buộc trong `knowledge/decisions/`.
