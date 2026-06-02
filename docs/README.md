# 🤖 AI Trend Agent v3.1 — SOLID Edition

> An automated AI news aggregation pipeline that scrapes, cleans, tags, and stores trending AI articles from multiple sources — built with async Python, OOP, and SOLID principles.
> Following newest claude model 3.7 and mindset of karpathy

![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python&logoColor=white)
![Architecture](https://img.shields.io/badge/Architecture-OOP%20%2B%20SOLID-green)
![Async](https://img.shields.io/badge/IO-Async%20%2B%20httpx-purple)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 📋 What It Does

AI Trend Agent automatically monitors and collects the latest AI news from **3 sources simultaneously**:

| Source | Method | Data Format |
|--------|--------|-------------|
| **NewsAPI** | REST API | JSON |
| **Reddit** | Reddit JSON API | JSON |
| **Google News** | RSS Feed | XML |

The pipeline runs on a configurable schedule (default: every 4 hours), collecting, deduplicating, tagging, and storing articles into CSV files.

---

## 🏗️ Architecture

```
main.py (Orchestrator + Factory)
    │
    ├── PipelineContext (shared data object)
    │
    ├── ScraperAgent.execute(ctx)   →  Extract (3 sources in parallel)
    ├── CleanerAgent.execute(ctx)   →  Transform (dedupe + tag + sort)
    └── StorageAgent.execute(ctx)   →  Load (append-only CSV)
```

### SOLID Principles Applied

| Principle | Implementation |
|-----------|---------------|
| **S** — Single Responsibility | Each Agent has exactly one job |
| **O** — Open/Closed | `@AgentFactory.register()` decorator — add agents without modifying Factory |
| **L** — Liskov Substitution | Unified `execute(ctx) → ctx` signature across all agents |
| **I** — Interface Segregation | `BaseAgent` exposes only `execute()`, `log_info()`, `log_error()` |
| **D** — Dependency Inversion | `run_pipeline()` accepts `list[BaseAgent]`, not concrete classes |

---

## 📁 Project Structure

```
AI_Trend_Agent/
├── main.py                 # Entry point — Pipeline orchestrator + Factory
├── .env                    # API keys (not tracked by git)
├── .gitignore              # Security: excludes .env, venv, data/
├── requirements.txt        # Python dependencies
│
├── modules/
│   ├── __init__.py         # Package initializer
│   ├── base_agent.py       # Abstract Base Class + AgentFactory
│   ├── models.py           # Article dataclass + PipelineContext
│   ├── config.py           # Centralized constants (no magic numbers)
│   ├── scrapers.py         # ScraperAgent — async multi-source fetcher
│   ├── cleaner.py          # CleanerAgent — NLP tagging + deduplication
│   └── storage.py          # StorageAgent — CSV writer with analytics
│
├── .agents/                # AI-native development context
│   ├── SKILL_ARCHITECTURE.md
│   ├── SKILL_CODING_RULES.md
│   └── SKILL_ROADMAP.md
│
└── data/                   # Output directory (auto-created)
    └── *.csv               # Collected articles
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- A free [NewsAPI](https://newsapi.org/) key

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/dokhacduc29/Project_AI_trend_agent.git
cd Project_AI_trend_agent

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure API key
echo NEWS_API_KEY=your_key_here > .env
```

### Run

```bash
python main.py
```

You'll be prompted to enter a search topic (e.g., `Artificial Intelligence`). The agent will:

1. Fetch articles from all 3 sources **in parallel** (async)
2. Clean titles, auto-tag entities (`#OpenAI`, `#Google`, `#Microsoft`...)
3. Deduplicate using `Set` (O(1) lookup)
4. Sort by date (Timsort — O(N log N))
5. Append new articles to `data/<topic>_news.csv`
6. Print source analytics via `defaultdict`
7. Sleep and repeat every 4 hours

Press `Ctrl + C` to stop gracefully.

---

## 🔧 Key Technical Decisions

| Decision | Why |
|----------|-----|
| `httpx` over `requests` | Native async support — 3 API calls run in parallel via `asyncio.gather()` |
| `@dataclass` over `namedtuple` | Mutable fields, built-in type hints, cleaner syntax |
| `PipelineContext` pattern | Unified `execute(ctx) → ctx` signature fixes LSP violation |
| Decorator-based Factory | Agents self-register via `@AgentFactory.register()` — fixes OCP |
| `asyncio.sleep()` over `schedule` | Eliminates sync dependency, no event loop destruction antipattern |
| `config.py` constants | Zero magic numbers in business logic (L09 compliance) |

---

## 🏷️ Auto-Tagging (Regex NLP)

The `CleanerAgent` automatically tags articles based on title content:

| Pattern | Tag |
|---------|-----|
| OpenAI, ChatGPT, GPT-4o | `#OpenAI` |
| Google, Gemini, DeepMind | `#Google` |
| Microsoft, Copilot, Azure | `#Microsoft` |
| Meta, LLaMA, Zuckerberg | `#Meta` |
| Anthropic, Claude | `#Anthropic` |
| Apple | `#Apple` |
| $100M, $2B | `#Funding_Money` |

---

## 📊 Sample Output

```
2026-05-04 15:00:01 - [INFO] - [ScraperAgent] Thu thap xong: 20 bai tho
2026-05-04 15:00:02 - [INFO] - [CleanerAgent] Loc xong: 15 bai sach, doc nhat
2026-05-04 15:00:02 - [INFO] - [StorageAgent] Thong ke nguon tin moi:
2026-05-04 15:00:02 - [INFO] -    [Nguon] NewsAPI: 10 bai
2026-05-04 15:00:02 - [INFO] -    [Nguon] Reddit: 3 bai
2026-05-04 15:00:02 - [INFO] -    [Nguon] Google News RSS: 2 bai
2026-05-04 15:00:02 - [INFO] -    [Tag] #OpenAI: xuat hien 4 lan
2026-05-04 15:00:02 - [INFO] -    [Tag] #Google: xuat hien 3 lan
2026-05-04 15:00:02 - [INFO] - [StorageAgent] Da noi them 15 tin MOI vao: data/ai_news.csv
```

---

## 🛡️ Coding Rules (Iron Laws)

This project enforces strict coding standards defined in `.agents/SKILL_CODING_RULES.md`:

| # | Rule | Status |
|---|------|--------|
| L01 | No hardcoded secrets — use `.env` | ✅ |
| L02 | `logging` only — zero `print()` | ✅ |
| L03 | Async-first with `httpx` | ✅ |
| L04 | Fault tolerance — `try/except` everywhere | ✅ |
| L05 | Type hints on all functions | ✅ |
| L09 | No magic numbers — use `config.py` | ✅ |

---

## 🗺️ Roadmap

- [x] Phase 1: Foundation (Day 1-10)
- [x] Phase 2: Pythonic & Data Scaling (Day 11-20)
- [x] Phase 3: OOP & SOLID (Day 21-30)
- [ ] Phase 4: Telegram Bot integration
- [ ] Phase 5: LLM summarization (Gemini/GPT)
- [ ] Phase 6: Database storage (SQLite/PostgreSQL)

---

## 🤝 Contributing

This is a learning project. Feel free to fork and experiment!

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.
