# Tổng quan Hệ thống AI_Trend_Agent (v3.1 — SOLID Edition)

## Mục tiêu
Thu thập dữ liệu xu hướng AI từ đa nguồn, làm sạch, phân loại tự động, tóm tắt bằng AI (Gemini), và lưu trữ vào cloud database (Supabase PostgreSQL). Hệ thống đóng gói bằng Docker và triển khai trên Kubernetes (minikube).

## Kiến trúc Phân lớp (Multi-layer Backend)

Mã nguồn tổ chức theo 4 lớp tách biệt trách nhiệm:

| Lớp | Thư mục | Trách nhiệm |
|-----|---------|-------------|
| **Domain** | `ai_trend_agent.Domain/` | Dữ liệu thuần & hằng số: `models.py`, `config.py` |
| **Application** | `ai_trend_agent.Application/` | Trừu tượng & nền tảng: `base_agent.py`, `decorators.py` |
| **Infrastructure** | `ai_trend_agent.Infrastructure/` | Agent cụ thể: scraper, cleaner, AI, storage, telegram |
| **WebApi** | `ai_trend_agent.WebApi/` | Điểm vào: `main.py` (orchestrator) |

## Pipeline ETL (Aggregator + Factory)

```
[ScraperAgent] → [CleanerAgent] → [AIAnalyzerAgent] → [SupabaseStorageAgent] → [TelegramAgent]
       │              │                  │                      │                    │
       └──────────────────── PipelineContext (shared dataclass) ─────────────────────┘
```

- **Extract:** 3 nguồn — NewsAPI (JSON), Reddit (JSON), Google News (XML/RSS).
- **Transform:** Lọc trùng (Set), gắn tag thực thể bằng Regex.
- **Enrich:** Gemini sinh tóm tắt + sentiment (gửi theo batch).
- **Load:** Insert vào Supabase PostgreSQL, dedup phía server theo `title`.
- **Notify:** TelegramAgent (đang là stub — Phase 6).
- **Tự động hóa:** Vòng lặp `asyncio.sleep()` (mỗi 4 giờ), KHÔNG dùng `schedule`.

## Các thành phần cốt lõi

### 1. `BaseAgent` (ABC) — `ai_trend_agent.Application/base_agent.py`
- Interface: `async execute(ctx: PipelineContext) → PipelineContext`.
- Helper: `log_info()`, `log_error()`.
- Mọi Agent kế thừa class này.

### 2. `AgentFactory` — `ai_trend_agent.Application/base_agent.py`
- Decorator `@AgentFactory.register("ten")` — Agent **tự đăng ký** khi import.
- Tuân thủ **OCP**: thêm Agent mới KHÔNG cần sửa Factory.
- Tạo instance qua `AgentFactory.create("ten")`.

### 3. `PipelineContext` — `ai_trend_agent.Domain/models.py`
- `@dataclass` chứa: `topic`, `api_key`, `gemini_api_key`, `articles: list[Article]`.
- Chuyển qua tất cả Agent → đảm bảo **LSP** (cùng signature `ctx → ctx`).

### 4. Article schema — `ai_trend_agent.Domain/models.py`
```python
class Sentiment(Enum):
    BULLISH = "Tích cực"
    BEARISH = "Tiêu cực"
    NEUTRAL = "Trung lập"

@dataclass
class Article:
    title: str
    source: str                              # "NewsAPI" | "Reddit" | "Google News RSS"
    date: str                                # ISO 8601 (cắt 10 ký tự)
    url: str
    tags: list[str] = field(default_factory=list)   # ["#OpenAI", "#Funding_Money", ...]
    summary: str = ""                        # AI-generated (Phase 4)
    sentiment: Sentiment = Sentiment.NEUTRAL # Enum (Phase 4)
```
`Article` định nghĩa `__eq__` / `__hash__` theo `title.lower()` → cho phép dedup bằng `set()`.

## Các Agent hiện có

| Agent | Tên đăng ký | Trách nhiệm | Key tech |
|-------|-------------|-------------|----------|
| `ScraperAgent` | `scraper` | Fetch song song 3 nguồn | `httpx.AsyncClient` + `asyncio.gather` |
| `CleanerAgent` | `cleaner` | Dedupe (Set O(1)) + regex tag + sort | `re` + `set()` |
| `AIAnalyzerAgent` | `analyzer` | Summary + sentiment (batch) | `google-generativeai` (Gemini) |
| `StorageAgent` | `storage` | Append CSV + analytics (legacy fallback) | `csv.DictWriter` + `defaultdict` |
| `SupabaseStorageAgent` | `storage` | Insert Supabase + dedup + analytics | `supabase` client + `asyncio.to_thread` |
| `TelegramAgent` | `telegram` | Gửi thông báo *(stub — Phase 6)* | `httpx` *(chưa hoàn thiện)* |

## Lưu trữ (Storage)

- **Chính:** `SupabaseStorageAgent` → Supabase PostgreSQL cloud.
  - Schema bảng `public.articles`: `id, title, source, date, tags, summary, sentiment, url`.
  - Dedup: query `title` đã tồn tại trước khi insert.
  - Supabase client đồng bộ → bọc trong `asyncio.to_thread()` để không block event loop.
- **Fallback:** `StorageAgent` (CSV) vẫn tồn tại nhưng không nằm trong pipeline mặc định.

## Quy tắc khi thêm Agent mới

1. Tạo file `ai_trend_agent.Infrastructure/<ten_agent>.py`.
2. Class kế thừa `BaseAgent`, decorator `@AgentFactory.register("ten")`.
3. Implement `async def execute(self, ctx) -> PipelineContext`.
4. Trong `main.py`: thêm `import <ten_agent>` (side-effect để decorator chạy).
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

## Bảo vệ hệ thống (Fault Tolerance)

- Mọi call API bên ngoài (`httpx.get`, Supabase) bắt buộc có `timeout`.
- `try/except` bao quanh mọi external call — pipeline không bao giờ crash.
- `STARTUP_DELAY_SECONDS` (env var): chờ DNS sẵn sàng khi chạy trong container/K8s.

## Đóng gói & Triển khai

- **Dockerfile:** multi-stage (builder + runtime), chạy non-root `appuser`, `PYTHONPATH` trỏ tới các lớp Backend.
- **Kubernetes:** namespace + Secret + ConfigMap + Deployment + Service. File manifest đánh số `00-`–`04-` để apply đúng thứ tự phụ thuộc.
- Topic đọc từ env var `TOPIC` khi chạy container (không block ở `input()`).

## Anti-patterns đã loại bỏ

- ❌ `time.sleep()` trong loop async → ✅ `asyncio.sleep()`
- ❌ `requests` đồng bộ → ✅ `httpx` async
- ❌ `schedule.every().hours.do(...)` → ✅ `asyncio.sleep(interval)`
- ❌ Magic numbers rải rác → ✅ `config.py`
- ❌ `sys.path.insert()` hack khi chạy container → ✅ `PYTHONPATH` trong Dockerfile

## Khi nào sửa kiến trúc

- Thay đổi `BaseAgent`, `AgentFactory`, hoặc `PipelineContext` → ADR bắt buộc trong `knowledge/decisions/`.
- Thêm publisher mới → tạo Agent sau `SupabaseStorageAgent`.
