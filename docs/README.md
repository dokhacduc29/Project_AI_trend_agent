# 🤖 AI Trend Agent v4.0 — SOLID Edition

> An automated pipeline that scrapes, AI-cleans (relevance scoring), tags, AI-summarizes, synthesizes macro trends, stores into a cloud database, and pushes a digest to Telegram — built with async Python, OOP, SOLID principles, and Gemini AI.

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
| **Reddit** (`r/ArtificialIntelligence`) | OAuth API (fallback public JSON) | JSON |
| **Google News** | RSS Feed | XML |

The pipeline runs on a schedule (default: every 4 hours): collecting, deduplicating, hybrid AI-cleaning (regex + Gemini relevance scoring), AI-summarizing, synthesizing macro trends, storing into a **Supabase PostgreSQL cloud database**, and sending a formatted **Telegram digest**.

---

## 🏗️ Architecture

The project follows **Clean Architecture** with 6 pipeline agents connected via `PipelineContext`:

```
WebApi/main.py (Orchestrator + AgentFactory)
    │
    ├── PipelineContext          ← Shared data object (articles + trend_report) passed between every Agent
    │
    ├── ScraperAgent             →  Extract   (3 sources in parallel via asyncio.gather)
    ├── CleanerAgent             →  Transform (dedupe + hybrid regex/AI tagging + relevance filter)  [Phase B]
    ├── SummarizationAgent       →  Analyze   (Gemini 2.5 Flash — per-article summary + sentiment, batch + cache)
    ├── TrendSynthesisAgent      →  Synthesize(Gemini — macro trends across all articles)            [Phase A]
    ├── SupabaseStorageAgent     →  Load      (Supabase PostgreSQL — Phase 5)
    └── TelegramAgent            →  Notify    (Telegram digest: trends + articles — Phase 6)
```

> Shared `gemini_client.generate_with_retry()` helper centralizes Gemini calls (exponential backoff for 503/429) used by the Cleaner, Summarization, and Trend agents.
>
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
│   │   ├── scrapers.py                 # ScraperAgent — async multi-source (Reddit OAuth)
│   │   ├── cleaner.py                  # CleanerAgent — hybrid regex + AI relevance [Phase B]
│   │   ├── ai_agent.py                 # SummarizationAgent — Gemini summary + sentiment
│   │   ├── trend_agent.py             # TrendSynthesisAgent — macro trends [Phase A]
│   │   ├── gemini_client.py            # Shared Gemini call helper (retry backoff)
│   │   ├── storage.py                  # StorageAgent — CSV (legacy fallback)
│   │   ├── supabase_storage.py         # SupabaseStorageAgent — Supabase
│   │   └── telegram_agent.py           # TelegramAgent — Bot digest (trends + articles)
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
├── knowledge/                          # Architecture Decision Records (ADR)
│   └── decisions/                      # 0001 Trend Synthesis, 0002 Hybrid Cleaner
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
#    TELEGRAM_BOT_TOKEN=your_bot_token       (optional — Phase 6)
#    TELEGRAM_CHAT_ID=your_chat_id           (optional — Phase 6)
#    REDDIT_CLIENT_ID=your_reddit_client_id  (optional — fixes Reddit 403 via OAuth)
#    REDDIT_CLIENT_SECRET=your_reddit_secret (optional — create a "script" app at reddit.com/prefs/apps)
```

### Run

```powershell
python Backend/ai_trend_agent.WebApi/main.py
```

Enter a search topic (e.g., `Artificial Intelligence`), or set the `TOPIC` env var for container mode. The pipeline will:

1. **Scrape** all 3 sources **in parallel** via `asyncio.gather()`
2. **Clean (hybrid)** — drop empty titles, dedupe (Set O(1) + Timsort), regex tags, then **Gemini relevance scoring (0–10)** drops off-topic articles and fills missing tags [Phase B]
3. **Analyze** — Gemini 2.5 Flash summarizes + scores sentiment (bullish/bearish/neutral) per article
4. **Synthesize trends** — Gemini reads all articles → 3–5 macro trends + overall sentiment + insight [Phase A]
5. **Store** — upsert new articles into Supabase (`on_conflict=url`)
6. **Notify** — send a Telegram digest (trends on top + article list, auto-chunked ≤4096 chars)
7. **Repeat** every 4 hours — stop gracefully with `Ctrl + C`

---

## 🗄️ Database — Supabase PostgreSQL

`SupabaseStorageAgent` stores articles into **Supabase PostgreSQL cloud** with this schema:

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
- **Upsert dedup** — `upsert(on_conflict="url", ignore_duplicates=True)` lets the DB's `url` UNIQUE constraint skip duplicates atomically (no pre-query needed)
- **Async-safe** — uses `asyncio.to_thread()` so the sync Supabase client never blocks the event loop
- **Fault tolerance** — reads `SUPABASE_URL` / `SUPABASE_KEY` from `.env` (lazy client init); errors are logged, pipeline continues

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

## 🏷️ Hybrid Cleaner — Regex + AI (Phase B)

`CleanerAgent` runs **two tiers** so the free regex pass handles the easy cases and Gemini only fills the gaps:

**Tier 1 — Regex (free, fast):** dedupe + tag clear entities.

| Pattern | Tag |
|---------|-----|
| OpenAI, ChatGPT, GPT-4o | `#OpenAI` |
| Google, Gemini, DeepMind, Alphabet | `#Google` |
| Microsoft, Copilot, Azure | `#Microsoft` |
| Meta, LLaMA, Zuckerberg | `#Meta` |
| Anthropic, Claude | `#Anthropic` |
| Apple | `#Apple` |
| `$100M`, `$2B`... | `#Funding_Money` |

**Tier 2 — AI (Gemini, only when `GEMINI_API_KEY` is set):**
- Scores **relevance 0–10** for every article → drops off-topic ones below the threshold (fixes regex false positives like a "best apple pie recipe" → `#Apple`)
- Tags articles that regex couldn't recognize (new entities like Mistral, xAI)
- **Graceful fallback** — if quota runs out or the call fails, the regex result is used (pipeline never breaks)

---

## 🔮 Trend Synthesis (Phase A)

While `SummarizationAgent` summarizes **each** article (micro view), `TrendSynthesisAgent` reads **all** articles in one Gemini call to produce the macro picture:

- **3–5 emerging trends** (each with related-article count)
- **Overall market sentiment** (bullish / bearish / neutral)
- **One-line insight**

The result (`PipelineContext.trend_report`) is placed at the **top of the Telegram digest** so the big picture comes first.

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
2026-06-02 16:24:46 - [INFO] - [ScraperAgent] Thu thập xong: 11 bài thô
2026-06-02 16:24:47 - [INFO] - [CleanerAgent] Tầng regex: 11 bài sạch, độc nhất.
2026-06-02 16:24:56 - [INFO] - [CleanerAgent] Tầng AI: loại 1 bài lạc đề (điểm < 4).
2026-06-02 16:24:56 - [INFO] - [SummarizationAgent] Đang gửi 10 bài (2 batches) cho Gemini...
2026-06-02 16:25:02 - [INFO] - [SummarizationAgent] Hoàn thành phân tích AI và cập nhật Cache.
2026-06-02 16:25:13 - [INFO] - [TrendSynthesisAgent] Đã rút ra 4 xu hướng nổi bật.
2026-06-02 16:25:15 - [INFO] - [SupabaseStorageAgent] Đã lưu thành công 8 bài mới vào Supabase.
2026-06-02 16:25:17 - [INFO] - [TelegramAgent] Đã gửi thành công 2/2 tin nhắn qua Telegram.
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
| L10 | Decision log | Major changes recorded as ADRs in `knowledge/decisions/` | ✅ |

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
| 6 | Multi-channel publisher: Telegram digest (trends + articles) | ✅ Done |
| **A** | **AI Trend Synthesis** — macro trends across all articles (ADR 0001) | ✅ Done |
| **B** | **Hybrid AI Cleaner** — regex + Gemini relevance scoring (ADR 0002) | ✅ Done |
| Infra | Reddit OAuth fix + shared Gemini retry helper | ✅ Done |
| CI/CD | GitHub Actions: build → test → scan → deploy | ⏳ Planned |
| C | RAG chatbot / Q&A over collected articles | ⏳ Planned |
| D | Agentic loop — LLM self-directed search & tool use | ⏳ Planned |

---

## 🤝 Contributing

This is a learning project. Feel free to fork and experiment!

Commit convention: `feat:`, `fix:`, `refactor:`, `docs:`, `chore:`

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.
