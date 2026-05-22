# 🤖 AI Trend Agent v3.1 — SOLID Edition

> Pipeline tự động thu thập, làm sạch, phân tích và lưu trữ tin tức AI từ nhiều nguồn — xây dựng bằng async Python, OOP, SOLID principles và Gemini AI.

![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python&logoColor=white)
![Architecture](https://img.shields.io/badge/Architecture-Clean%20Architecture%20%2B%20SOLID-green)
![Async](https://img.shields.io/badge/IO-Async%20%2B%20httpx-purple)
![AI](https://img.shields.io/badge/AI-Gemini%202.5%20Flash-orange?logo=google&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 📋 What It Does

AI Trend Agent tự động giám sát và thu thập tin tức AI mới nhất từ **3 nguồn song song**:

| Nguồn | Phương thức | Định dạng |
|-------|-------------|-----------|
| **NewsAPI** | REST API | JSON |
| **Reddit** (`r/artificial`) | Reddit JSON API | JSON |
| **Google News** | RSS Feed | XML |

Pipeline chạy theo lịch (mặc định: mỗi 4 giờ), tự động thu thập, loại trùng, gán nhãn, phân tích bằng Gemini AI và lưu vào CSV / Supabase PostgreSQL.

---

## 🏗️ Architecture

Dự án theo **Clean Architecture** với 5 pipeline agent được kết nối qua `PipelineContext`:

```
WebApi/main.py (Orchestrator + AgentFactory)
    │
    ├── PipelineContext          ← Đối tượng dữ liệu dùng chung giữa mọi Agent
    │
    ├── ScraperAgent             →  Extract   (3 nguồn song song qua asyncio.gather)
    ├── CleanerAgent             →  Transform (Dedupe + Regex tagging + Sort)
    ├── SummarizationAgent       →  Analyze   (Gemini 2.5 Flash — batch + cache)
    ├── StorageAgent             →  Load CSV  (append-only + threading)
    ├── DatabaseStorageAgent     →  Load DB   (Supabase PostgreSQL — Phase 5)
    └── TelegramAgent            →  Publish   (Telegram Bot — Phase 6)
```

### SOLID Principles Applied

| Nguyên tắc | Cách áp dụng |
|------------|-------------|
| **S** — Single Responsibility | Mỗi Agent chỉ có đúng một nhiệm vụ |
| **O** — Open/Closed | `@AgentFactory.register()` — thêm Agent mới mà không sửa Factory hay `main.py` |
| **L** — Liskov Substitution | Chữ ký thống nhất `execute(ctx) → ctx` cho mọi Agent |
| **I** — Interface Segregation | `BaseAgent` chỉ expose `execute()`, `log_info()`, `log_error()` |
| **D** — Dependency Inversion | `run_pipeline()` nhận `list[BaseAgent]`, không nhận class cụ thể |

---

## 📁 Project Structure

```
Project_AI_trend_agent/
│
├── Backend/
│   ├── ai_trend_agent.Domain/          # Entities, models, config
│   │   ├── models.py                   # @dataclass Article, PipelineContext, Sentiment
│   │   └── config.py                   # Hằng số tập trung (L09 — no magic numbers)
│   │
│   ├── ai_trend_agent.Application/     # Business logic abstractions
│   │   ├── base_agent.py               # BaseAgent (ABC) + AgentFactory (decorator)
│   │   └── decorators.py               # @retry, @ai_timer, @ai_logger
│   │
│   ├── ai_trend_agent.Infrastructure/  # Triển khai cụ thể
│   │   ├── scrapers.py                 # ScraperAgent — async multi-source
│   │   ├── cleaner.py                  # CleanerAgent — regex tagging + dedupe
│   │   ├── ai_agent.py                 # SummarizationAgent — Gemini AI
│   │   ├── storage.py                  # StorageAgent — CSV (threading)
│   │   ├── database_storage.py         # DatabaseStorageAgent — Supabase
│   │   └── telegram_agent.py           # TelegramAgent — Bot notification
│   │
│   ├── ai_trend_agent.WebApi/
│   │   └── main.py                     # Entry point — Pipeline orchestrator
│   │
│   ├── ai_trend_agent.Tests/
│   │   └── test_agents.py              # Pytest unit tests
│   │
│   └── requirements.txt
│
├── .claude/                            # Claude Code skills & commands
│   ├── commands/                       # Slash commands (bugfix, deploy, tdd...)
│   └── skills/                         # Architecture guide, coding rules, roadmap
│
├── docs/                               # Tài liệu dự án
│   ├── 01-strategy/                    # Roadmap & kế hoạch
│   ├── 02-requirements/                # Yêu cầu chi tiết
│   └── 03-engineering/                 # Kiến trúc kỹ thuật
│
├── Dockerfile
└── .env                                # API keys (không commit)
```

---

## 🚀 Quick Start

### Yêu cầu

- Python 3.11+
- Tài khoản [NewsAPI](https://newsapi.org/) (free tier)
- Tài khoản [Google AI Studio](https://aistudio.google.com/) để lấy Gemini API key

### Cài đặt

```bash
# 1. Clone repository
git clone https://github.com/dokhacduc29/Project_AI_trend_agent.git
cd Project_AI_trend_agent/Backend

# 2. Tạo virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# 3. Cài dependencies
pip install -r requirements.txt

# 4. Cấu hình API keys
cp .env.example .env
# Sửa file .env và điền vào:
# NEWS_API_KEY=your_newsapi_key
# GEMINI_API_KEY=your_gemini_key
# SUPABASE_URL=your_supabase_url      (tùy chọn — Phase 5)
# SUPABASE_KEY=your_supabase_key      (tùy chọn — Phase 5)
# TELEGRAM_BOT_TOKEN=your_bot_token   (tùy chọn — Phase 6)
# TELEGRAM_CHAT_ID=your_chat_id       (tùy chọn — Phase 6)
```

### Chạy

```bash
cd ai_trend_agent.WebApi
python main.py
```

Nhập từ khóa tìm kiếm (ví dụ: `Artificial Intelligence`). Pipeline sẽ:

1. **Cào tin** từ 3 nguồn **song song** qua `asyncio.gather()`
2. **Làm sạch** — loại bỏ tiêu đề trống, chuẩn hóa
3. **Gán nhãn** — Regex NLP tự động tag thực thể (`#OpenAI`, `#Google`...)
4. **Loại trùng** — Set lookup O(1), sort theo ngày (Timsort O(N log N))
5. **Phân tích AI** — Gemini 2.5 Flash tóm tắt + đánh giá sentiment (bullish/bearish/neutral)
6. **Lưu trữ** — ghi nối tiếp vào `data/<topic>_news.csv` qua Threading
7. **Lặp lại** mỗi 4 giờ — dừng gracefully bằng `Ctrl + C`

---

## 🗄️ Database — Supabase PostgreSQL

`DatabaseStorageAgent` lưu trữ articles vào **Supabase PostgreSQL cloud** với schema:

```sql
public.articles (
  id          int8        PRIMARY KEY,
  title       text,
  source      text,
  date        text,
  tags        text,
  summary     text,
  sentiment   text,
  url         text,
  created_at  timestamptz DEFAULT now(),
  topic       text
)
```

**Tính năng:**
- **Dedup query** — kiểm tra title đã tồn tại trước khi insert, tránh trùng lặp
- **Async-safe** — dùng `asyncio.to_thread()` để gọi Supabase client không block Event Loop
- **Fault tolerance** — validate `SUPABASE_URL` / `SUPABASE_KEY` từ `.env` khi khởi tạo
- **Analytics** — thống kê nguồn tin + tag tương tự CSV agent

Production database hiện tại đã chạy ổn định với hàng chục records được nạp tự động qua pipeline.

---

## 🧠 AI Analysis — Gemini Integration

`SummarizationAgent` dùng **3 chiến lược tối ưu token (FinOps)**:

| Chiến lược | Chi tiết |
|-----------|---------|
| **Batch Prompting** | Gộp 5 bài/request — tiết kiệm ~70% token so với gọi từng bài |
| **Pre-filtering** | Chỉ gửi AI những bài đã có tag — bỏ qua bài không liên quan |
| **MD5 Caching** | Hash tiêu đề → cache kết quả xuống disk — không gọi lại bài đã phân tích |

Kết quả phân tích cho mỗi bài:
- **Summary**: Tóm tắt tối đa 15 từ
- **Sentiment**: `Tích cực` / `Tiêu cực` / `Trung lập`

---

## 🏷️ Auto-Tagging (Regex NLP)

`CleanerAgent` tự động gán nhãn dựa trên tiêu đề bài viết:

| Pattern | Tag |
|---------|-----|
| OpenAI, ChatGPT, GPT-4o | `#OpenAI` |
| Google, Gemini, DeepMind, Alphabet | `#Google` |
| Microsoft, Copilot, Azure | `#Microsoft` |
| Meta, LLaMA, Zuckerberg | `#Meta` |
| Anthropic, Claude | `#Anthropic` |
| Apple | `#Apple` |
| `$100M`, `$2B`... | `#Funding_Money` |

---

## 🔧 Key Technical Decisions

| Quyết định | Lý do |
|-----------|-------|
| `httpx` thay `requests` | Hỗ trợ async native — 3 API call song song qua `asyncio.gather()` |
| `@dataclass` thay `namedtuple` | Mutable fields, type hints tích hợp sẵn |
| `PipelineContext` pattern | Thống nhất chữ ký `execute(ctx) → ctx` — fix LSP violation |
| Decorator-based Factory | Agent tự đăng ký qua `@AgentFactory.register()` — đúng OCP |
| `asyncio.to_thread()` cho I/O file | Offload CSV read/write sang thread riêng, không block Event Loop |
| `asyncio.sleep()` thay `schedule` | Loại bỏ dependency đồng bộ, không phá Event Loop |
| `config.py` cho mọi hằng số | Zero magic numbers trong business logic (Iron Law L09) |
| Gemini 2.5 Flash | Mô hình tối ưu tốc độ/chi phí cho summarization |

---

## 📊 Sample Output

```
2026-05-18 15:00:01 - [INFO] - [ScraperAgent] Bắt đầu cào tin về: 'Artificial Intelligence'
2026-05-18 15:00:03 - [INFO] - [ScraperAgent] Thu thập xong: 20 bài thô
2026-05-18 15:00:03 - [INFO] - [CleanerAgent] Lọc xong: 15 bài sạch, độc nhất
2026-05-18 15:00:05 - [INFO] - [SummarizationAgent] Đã phục hồi 3 bài từ Cache.
2026-05-18 15:00:06 - [INFO] - [SummarizationAgent] Đang gửi 12 bài (3 batches) cho Gemini...
2026-05-18 15:00:09 - [INFO] - [SummarizationAgent] Hoàn thành phân tích AI và cập nhật Cache.
2026-05-18 15:00:09 - [INFO] - [StorageAgent] Thống kê nguồn tin mới:
2026-05-18 15:00:09 - [INFO] -    [Nguồn] NewsAPI: 10 bài
2026-05-18 15:00:09 - [INFO] -    [Nguồn] Reddit: 3 bài
2026-05-18 15:00:09 - [INFO] -    [Nguồn] Google News RSS: 2 bài
2026-05-18 15:00:09 - [INFO] -    [Tag] #OpenAI: xuất hiện 4 lần
2026-05-18 15:00:09 - [INFO] -    [Tag] #Google: xuất hiện 3 lần
2026-05-18 15:00:09 - [INFO] - [StorageAgent] Đã nối thêm 15 tin MỚI vào: data/artificial_intelligence_news.csv (qua Threading)
```

---

## 🛡️ Coding Rules (Iron Laws)

| # | Luật | Mô tả | Status |
|---|------|-------|--------|
| L01 | No hardcoded secrets | Dùng `python-dotenv` + `.env` | ✅ |
| L02 | Logging only | Cấm `print()`, dùng module `logging` | ✅ |
| L03 | Async-first I/O | `httpx` + `asyncio.gather()` cho mọi API call | ✅ |
| L04 | No SQL injection | ORM / parameterized query | ✅ |
| L06 | Soft delete | `is_deleted=True`, không DELETE cứng | ✅ |
| L07 | Fault tolerance | Mọi external call có `timeout` + `try/except` | ✅ |
| L08 | Type hints + docstring | Bắt buộc trên mọi function | ✅ |
| L09 | No magic numbers | Mọi hằng số → `config.py` | ✅ |

---

## 🧪 Testing

```bash
cd Backend
pytest ai_trend_agent.Tests/ -v
```

Test coverage hiện tại:
- `Article` dataclass — `__eq__`, `__hash__`, `__len__`
- `CleanerAgent.extract_entities()` — Regex tagging accuracy
- `AgentFactory` — Registration & creation

---

## 🗺️ Roadmap

| Phase | Nội dung | Trạng thái |
|-------|----------|-----------|
| 1 | Foundation: requests, JSON/RSS parsing | ✅ Done |
| 2 | Pythonic: Set dedupe, regex tagging, list comprehension | ✅ Done |
| 3 | OOP + SOLID: BaseAgent, Factory pattern, async refactor | ✅ Done |
| 4 | Gemini AI: summarization + sentiment + FinOps | ✅ Done |
| 5 | Database storage: Supabase PostgreSQL cloud | ✅ Done |
| 6 | Multi-channel publisher: Telegram Bot | ⏳ Planned |
| 7 | RAG chatbot, full-text extraction | ⏳ Planned |
| 8 | Task queue: Celery + Redis cache | ⏳ Planned |

---

## 🤝 Contributing

Đây là learning project. Fork và thử nghiệm thoải mái!

Commit convention: `feat:`, `fix:`, `refactor:`, `docs:`, `chore:`

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

Hướng dẫn chạy toàn bộ dự án
1. Chạy unit test:


venv\Scripts\activate
cd Backend
pytest ai_trend_agent.Tests/ -v
2. Chạy app local:


python Backend/ai_trend_agent.WebApi/main.py
3. Chạy bằng Docker:


docker run --env-file Backend/.env ai-trend-agent:v4
4. Chạy trên K8s (minikube) — production-like:


kubectl apply -f k8s/00-namespace.yaml
kubectl apply -f k8s/01-secret.yaml
kubectl apply -f k8s/02-configmap.yaml
kubectl apply -f k8s/03-deployment.yaml
kubectl apply -f k8s/04-service.yaml

kubectl logs -f deployment/ai-trend-agent -n ai-trend-agent
Lưu ý: requirements.txt đang nằm ở Backend/requirements.txt, không phải root. Nếu CLAUDE.md ghi pip install -r requirements.txt thì cần sửa đường dẫn cho khớp.
