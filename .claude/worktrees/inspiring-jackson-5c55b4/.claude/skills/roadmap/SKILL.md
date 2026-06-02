---
name: roadmap
description: Trạng thái phase hiện tại và roadmap dài hạn của dự án. Dùng để biết task nào đang ưu tiên, và cảnh báo khi user đề xuất nhảy phase.
---

# Roadmap — AI Trend Agent

## Trạng thái hiện tại (2026-05-08)

**Branch active**: `feature-phase4-ai`

### Đã hoàn thành

| Phase | Nội dung | Trạng thái |
|-------|----------|-----------|
| 1 | Foundation: requests, JSON/RSS parsing | ✅ |
| 2 | Pythonic: Set dedupe, list comprehension, regex tagging | ✅ |
| 3 | OOP + SOLID: BaseAgent, Factory pattern, async refactor | ✅ |
| 4 | Gemini AI: summary + sentiment, decorators, context managers | ✅ |

### Đang thực thi

Hiện tại dự án ở trạng thái **stable Phase 4**. Trọng tâm tiếp theo:

1. Ổn định AIAnalyzerAgent (rate limit, retry, fallback khi Gemini fail).
2. Test coverage — chưa có pytest suite.
3. Chuẩn bị migrate CSV → SQLite (Phase 5).

### Sắp tới

| Phase | Nội dung | Điều kiện tiên quyết |
|-------|----------|---------------------|
| 5 | DB storage (SQLite → PostgreSQL) | Phase 4 stable + có test |
| 6 | Multi-channel publisher (Telegram/Discord) | Phase 5 done |
| 7+ | RAG chatbot, full-text extraction, Celery, Redis cache | Phase 6 done |

## Chỉ thị cho AI Agent

- Khi user yêu cầu code mới: **ưu tiên** task trong "Đang thực thi".
- Nếu user đòi Docker/Cloud deploy ngay → **cảnh báo** rằng cần hoàn thành test + DB migration trước.
- Nếu user đòi nhảy thẳng tới Phase 7 (RAG) → cảnh báo rằng cần Phase 5 (DB) làm nền.
- Mọi đề xuất nhảy phase phải kèm ADR trong `knowledge/decisions/`.

## Advanced upgrades (Senior Level — chưa lên lịch)

- **RAG Evolution**: CSV → Vector DB (Pinecone/Chroma).
- **Full-text extraction**: Scrape body bài viết, không chỉ title.
- **Task queue**: Celery/RabbitMQ chống crash khi network/API fail.
- **Redis cache**: O(1) dedupe persistent cross-restart.
