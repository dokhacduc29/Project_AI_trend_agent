---
name: roadmap
description: Trạng thái phase hiện tại và roadmap dài hạn của dự án. Dùng để biết task nào đang ưu tiên, và cảnh báo khi user đề xuất nhảy phase.
---

# Roadmap — AI Trend Agent

## Trạng thái hiện tại (2026-05-22)

**Branch active**: `main`

### Đã hoàn thành

| Phase | Nội dung | Trạng thái |
|-------|----------|-----------|
| 1 | Foundation: httpx, JSON/RSS parsing | ✅ |
| 2 | Pythonic: Set dedupe, comprehensions, regex tagging, Multi-layer refactor | ✅ |
| 3 | OOP + SOLID: BaseAgent, Factory pattern, async refactor | ✅ |
| 4 | Gemini AI: summary + sentiment, decorators, context managers | ✅ |
| 5 | Cloud DB: Supabase PostgreSQL (`DatabaseStorageAgent`) | ✅ |
| Deploy | Docker multi-stage build + Kubernetes (minikube) | ✅ |

### Đang thực thi

1. Mở rộng test coverage — đã có `test_agents.py`, cần thêm case.
2. Profiling pipeline (đo tốc độ từng agent).
3. Hoàn thiện `DiscordAgent` — hiện chỉ là stub, chưa gọi API Discord thật.

### Sắp tới

| Phase | Nội dung | Điều kiện tiên quyết |
|-------|----------|---------------------|
| 6 | Multi-channel publisher (Telegram/Discord) | DiscordAgent stub → hoàn thiện |
| CI/CD | GitHub Actions: build → test → scan → deploy | Test suite ổn định |
| 7+ | FastAPI Web API, RAG chatbot, full-text extraction | Phase 6 done |

## Chỉ thị cho AI Agent

- Khi user yêu cầu code mới: **ưu tiên** task trong "Đang thực thi".
- Nếu user đòi nhảy thẳng tới Phase 7 (RAG/FastAPI) → cảnh báo rằng cần hoàn thiện Phase 6 trước.
- Mọi đề xuất nhảy phase phải kèm ADR trong `knowledge/decisions/`.

## Tính năng chưa phát triển (để rỗng — chưa làm)

- **DiscordAgent**: file tồn tại nhưng `execute()` chỉ là stub, chưa `httpx.post` tới Discord API.
- **CI/CD**: chưa có GitHub Actions workflow.
- **FastAPI**: chưa khởi tạo Web API.
- **SQLAlchemy ORM**: dự án dùng Supabase client trực tiếp.
- **RAG / Vector DB**: chưa lên kế hoạch chi tiết.
