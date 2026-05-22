# 🤖 AI Trend Agent v3.1 — SOLID Edition

> An automated pipeline that scrapes, cleans, tags, AI-summarizes, and stores trending AI news from multiple sources into a cloud database — built with async Python, OOP, SOLID principles, and Gemini AI.

![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python&logoColor=white)
![Architecture](https://img.shields.io/badge/Architecture-Clean%20Architecture%20%2B%20SOLID-green)
![Async](https://img.shields.io/badge/IO-Async%20%2B%20httpx-purple)
![AI](https://img.shields.io/badge/AI-Gemini%202.5%20Flash-orange?logo=google&logoColor=white)
![Database](https://img.shields.io/badge/DB-Supabase%20PostgreSQL-3ECF8E?logo=supabase)
![Container](https://img.shields.io/badge/Deploy-Docker%20%2B%20K8s-2496ED?logo=docker)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 📋 What It Does

AI Trend Agent automatically monitors and collects the latest AI news from **3 sources in parallel**:

| Source | Method | Format |
|--------|--------|--------|
| **NewsAPI** | REST API | JSON |
| **Reddit** (`r/artificial`) | Reddit JSON API | JSON |
| **Google News** | RSS Feed | XML |

The pipeline runs on a schedule (default: every 4 hours): collecting, deduplicating, auto-tagging, AI-summarizing with Gemini, and storing articles into a **Supabase PostgreSQL cloud database**.

---

## 🏗️ Architecture

The project follows **Clean Architecture** with 5 pipeline agents connected via `PipelineContext`:

```
WebApi/main.py (Orchestrator + AgentFactory)
    │
    ├── PipelineContext          ← Shared data object passed between every Agent
    │
    ├── ScraperAgent             →  Extract   (3 sources in parallel via asyncio.gather)
    ├── CleanerAgent             →  Transform (dedupe + regex tagging + sort)
    ├── SummarizationAgent       →  Analyze   (Gemini 2.5 Flash — batch + cache)
    ├── DatabaseStorageAgent     →  Load      (Supabase PostgreSQL — Phase 5)
    └── TelegramAgent            →  Notify    (Telegram Bot — Phase 6, stub)
```

> `StorageAgent` (CSV append-only writer with threading) still exists as a legacy fallback but is not part of the default pipeline.

### SOLID Principles Applied

| Principle | Implementation |
|-----------|---------------|
| **S** — Single Responsibility | Each Agent has exactly one job |
| **O** — Open/Closed | `@AgentFactory.register()` — add agents without modifying Factory or `main.py` |
| **L** — Liskov Substitution | Unified `execute(ctx) → ctx` signature across all agents |
| **I** — Interface Segregation | `BaseAgent` exposes only `execute()`, `log_info()`, `log_error()` |
| **D** — Dependency Inversion | `run_pipeline()` accepts `list[BaseAgent]`, not concrete classes |

---

## 📁 Project Structure

```
Project_AI_trend_agent/
│
├── Dockerfile               # Multi-stage build (builder + runtime, non-root)
├── .dockerignore            # Excludes .env, venv, data, tests
├── .gitignore               # Security: excludes .env, venv, k8s secrets
├── CLAUDE.md                # AI agent project memory
│
├── Backend/
│   ├── requirements.txt
│   ├── .env                            # API keys (not tracked by git)
│   │
│   ├── ai_trend_agent.Domain/          # Entities, models, config
│   │   ├── models.py                   # @dataclass Article, PipelineContext, Sentiment
│   │   └── config.py                   # Centralized constants (L09 — no magic numbers)
│   │
│   ├── ai_trend_agent.Application/      # Business logic abstractions
│   │   ├── base_agent.py               # BaseAgent (ABC) + AgentFactory (decorator)
│   │   └── decorators.py               # @retry, @ai_timer, @ai_logger
│   │
│   ├── ai_trend_agent.Infrastructure/  # Concrete implementations
│   │   ├── scrapers.py                 # ScraperAgent — async multi-source
│   │   ├── cleaner.py                  # CleanerAgent — regex tagging + dedupe
│   │   ├── ai_agent.py                 # SummarizationAgent — Gemini AI
│   │   ├── storage.py                  # StorageAgent — CSV (legacy fallback)
│   │   ├── database_storage.py         # DatabaseStorageAgent — Supabase
│   │   └── telegram_agent.py           # TelegramAgent — Bot notification (stub)
│   │
│   ├── ai_trend_agent.WebApi/
│   │   └── main.py                     # Entry point — pipeline orchestrator
│   │
│   └── ai_trend_agent.Tests/
│       └── test_agents.py              # pytest unit tests
│
├── k8s/                                # Kubernetes manifests (minikube)
│   ├── 00-namespace.yaml
│   ├── 01-secret.yaml.template         # Template — real secrets not committed
│   ├── 02-configmap.yaml
│   ├── 03-deployment.yaml
│   └── 04-service.yaml
│
├── .claude/                            # Claude Code skills & commands
│   ├── commands/                       # Slash commands (bugfix, deploy, tdd...)
│   └── skills/                         # Architecture guide, coding rules, roadmap
│
└── docs/                               # Project documentation
    ├── 01-strategy/                    # Roadmap & planning
    ├── 02-requirements/                # Detailed requirements
    └── 03-engineering/                 # Technical architecture
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.13
- A free [NewsAPI](https://newsapi.org/) key
- A [Google AI Studio](https://aistudio.google.com/) key for Gemini
- A [Supabase](https://supabase.com/) project (URL + anon key)

### Installation

```powershell
# 1. Clone the repository
git clone https://github.com/dokhacduc29/Project_AI_trend_agent.git
cd Project_AI_trend_agent

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# 3. Install dependencies
pip install -r Backend/requirements.txt

# 4. Configure API keys in Backend/.env
#    NEWS_API_KEY=your_newsapi_key
#    GEMINI_API_KEY=your_gemini_key
#    SUPABASE_URL=your_supabase_url
#    SUPABASE_KEY=your_supabase_anon_key
#    TELEGRAM_BOT_TOKEN=your_bot_token   (optional — Phase 6)
#    TELEGRAM_CHAT_ID=your_chat_id       (optional — Phase 6)
```

### Run

```powershell
python Backend/ai_trend_agent.WebApi/main.py
```

Enter a search topic (e.g., `Artificial Intelligence`), or set the `TOPIC` env var for container mode. The pipeline will:

1. **Scrape** all 3 sources **in parallel** via `asyncio.gather()`
2. **Clean** — drop empty titles, normalize text
3. **Tag** — Regex NLP auto-tags entities (`#OpenAI`, `#Google`...)
4. **Deduplicate** — Set lookup O(1), sort by date (Timsort O(N log N))
5. **Analyze** — Gemini 2.5 Flash summarizes + scores sentiment (bullish/bearish/neutral)
6. **Store** — insert new articles into Supabase (server-side dedup by title)
7. **Repeat** every 4 hours — stop gracefully with `Ctrl + C`

---

## 🗄️ Database — Supabase PostgreSQL

`DatabaseStorageAgent` stores articles into **Supabase PostgreSQL cloud** with this schema:

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

**Features:**
- **Dedup query** — checks existing titles before insert to avoid duplicates
- **Async-safe** — uses `asyncio.to_thread()` so the sync Supabase client never blocks the event loop
- **Fault tolerance** — validates `SUPABASE_URL` / `SUPABASE_KEY` from `.env` on init
- **Analytics** — source + tag statistics, same as the CSV agent

---

## 🧠 AI Analysis — Gemini Integration

`SummarizationAgent` uses **3 token-optimization strategies (FinOps)**:

| Strategy | Detail |
|----------|--------|
| **Batch Prompting** | Bundles 5 articles per request — saves ~70% tokens vs. one-by-one calls |
| **Pre-filtering** | Only sends AI articles that already have tags — skips irrelevant ones |
| **MD5 Caching** | Hashes the title → caches results to disk — never re-analyzes a known article |

Per-article output:
- **Summary** — max 15 words
- **Sentiment** — `Tích cực` (bullish) / `Tiêu cực` (bearish) / `Trung lập` (neutral)

---

## 🏷️ Auto-Tagging (Regex NLP)

`CleanerAgent` automatically tags articles based on title content:

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

## 🐳 Docker & Kubernetes

### Docker (multi-stage build)

```powershell
docker build -t ai-trend-agent:latest .
docker run --env-file Backend/.env ai-trend-agent:latest
```

### Kubernetes (minikube)

```bash
# Create the secret from the template (fill in base64-encoded values first)
cp k8s/01-secret.yaml.template k8s/01-secret.yaml

# Load local image into minikube
minikube image load ai-trend-agent:latest

# Apply manifests in dependency order (00- → 04-)
kubectl apply -f k8s/

# Watch logs
kubectl logs -f deployment/ai-trend-agent -n ai-trend-agent
```

> Manifests are numbered `00-`–`04-` so `kubectl apply -f k8s/` applies them in dependency order (namespace first). The `TOPIC` env var is read from the ConfigMap so the container does not block on `input()`.

---

## 🔧 Key Technical Decisions

| Decision | Why |
|----------|-----|
| `httpx` over `requests` | Native async — 3 API calls run in parallel via `asyncio.gather()` |
| `@dataclass` over `namedtuple` | Mutable fields, built-in type hints |
| `PipelineContext` pattern | Unified `execute(ctx) → ctx` signature — fixes LSP violation |
| Decorator-based Factory | Agents self-register via `@AgentFactory.register()` — fixes OCP |
| `asyncio.to_thread()` for blocking I/O | Offloads CSV / Supabase calls off the event loop |
| `asyncio.sleep()` over `schedule` | Removes a sync dependency, no event-loop destruction |
| Supabase over local CSV | Cloud-persistent, server-side dedup, shared across deployments |
| Multi-stage Dockerfile | Build deps separated from runtime — smaller, non-root image |
| `config.py` constants | Zero magic numbers in business logic (Iron Law L09) |
| Gemini 2.5 Flash | Best speed/cost model for summarization |

---

## 📊 Sample Output

```
2026-05-18 15:00:01 - [INFO] - [ScraperAgent] Bắt đầu cào tin về: 'Artificial Intelligence'
2026-05-18 15:00:03 - [INFO] - [ScraperAgent] Thu thập xong: 20 bài thô
2026-05-18 15:00:03 - [INFO] - [CleanerAgent] Lọc xong: 15 bài sạch, độc nhất
2026-05-18 15:00:05 - [INFO] - [SummarizationAgent] Đã phục hồi 3 bài từ Cache.
2026-05-18 15:00:06 - [INFO] - [SummarizationAgent] Đang gửi 12 bài (3 batches) cho Gemini...
2026-05-18 15:00:09 - [INFO] - [SummarizationAgent] Hoàn thành phân tích AI và cập nhật Cache.
2026-05-18 15:00:09 - [INFO] - [DatabaseStorageAgent] Phát hiện 15 articles MỚI.
2026-05-18 15:00:10 - [INFO] - [DatabaseStorageAgent] Đã insert thành công 15 articles vào Supabase.
```

---

## 🛡️ Coding Rules (Iron Laws)

| # | Rule | Description | Status |
|---|------|-------------|--------|
| L01 | No hardcoded secrets | Use `python-dotenv` + `.env` / K8s Secret | ✅ |
| L02 | Logging only | No `print()` in business logic — use `logging` | ✅ |
| L03 | Async-first I/O | `httpx` + `asyncio.gather()` / `to_thread` | ✅ |
| L04 | No SQL injection | Parameterized queries via Supabase client | ✅ |
| L07 | Fault tolerance | Every external call has `timeout` + `try/except` | ✅ |
| L08 | Type hints + docstring | Required on every function | ✅ |
| L09 | No magic numbers | All constants → `config.py` | ✅ |

---

## 🧪 Testing

```powershell
cd Backend
pytest ai_trend_agent.Tests/ -v
```

Current test coverage:
- `Article` dataclass — `__eq__`, `__hash__`, `__len__`
- `CleanerAgent` — regex tagging accuracy
- `AgentFactory` — registration & creation

---

## 🗺️ Roadmap

| Phase | Content | Status |
|-------|---------|--------|
| 1 | Foundation: httpx, JSON/RSS parsing | ✅ Done |
| 2 | Pythonic: Set dedupe, regex tagging, comprehensions | ✅ Done |
| 3 | OOP + SOLID: BaseAgent, Factory pattern, async refactor | ✅ Done |
| 4 | Gemini AI: summarization + sentiment + FinOps | ✅ Done |
| 5 | Database storage: Supabase PostgreSQL cloud | ✅ Done |
| Deploy | Docker multi-stage build + Kubernetes (minikube) | ✅ Done |
| 6 | Multi-channel publisher: Telegram Bot | ⏳ Planned (stub) |
| CI/CD | GitHub Actions: build → test → scan → deploy | ⏳ Planned |
| 7 | RAG chatbot, full-text extraction | ⏳ Planned |

---

## 🤝 Contributing

This is a learning project. Feel free to fork and experiment!

Commit convention: `feat:`, `fix:`, `refactor:`, `docs:`, `chore:`

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.
