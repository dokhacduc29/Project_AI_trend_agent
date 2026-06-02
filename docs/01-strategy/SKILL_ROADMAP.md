# Trạng thái Dự án & Lộ trình (Project Roadmap)

> Cập nhật: 22/05/2026. Đối chiếu trực tiếp với `Roadmap .v2.csv`.

## Đã hoàn thành

### Giai đoạn 1 — AI Data Foundation (Day 1-10)
- Nền tảng Python: type hints, control flow, hàm, cấu trúc dữ liệu (List/Tuple/Set/Dict).
- Làm việc với File (.txt, .csv), thư viện chuẩn (os, sys, datetime).
- Debugging, traceback.

### Giai đoạn 2 — Pythonic & Data Scaling (Day 11-20)
- Comprehensions, lambda, map/filter/reduce.
- `collections` (defaultdict cho analytics).
- Xử lý JSON & API, Regex nâng cao (gắn tag thực thể).
- Tái cấu trúc Module/Package → phân lớp Multi-layer Backend (Domain/Application/Infrastructure/WebApi).

### Giai đoạn 3 — OOP & SOLID (Day 21-30)
- Class, kế thừa, đa hình, đóng gói.
- Dunder methods, `@classmethod`/`@staticmethod`/`@property`.
- Abstract classes (`BaseAgent` ABC).
- Dataclasses (`Article`, `PipelineContext`).
- Design Patterns: Singleton, Factory (`AgentFactory` tự đăng ký — thỏa OCP).

### Giai đoạn 4 — Advanced Python (Day 31-40, một phần)
- Iterators & Iterables.
- Decorators (`@timer`, `@logger`).
- Context Managers (quản lý I/O file & HTTPX).
- Enums (`Sentiment`), advanced type hinting.
- `itertools` / `functools` (`functools.wraps`).
- Tích hợp Gemini AI: sinh tóm tắt + sentiment cho bài báo.

### Giai đoạn 5 — Tối ưu hóa & Triển khai (một phần)
- Asyncio: `async/await` với `httpx`, cào 3 nguồn đồng thời qua `asyncio.gather`.
- **Database:** Tích hợp Supabase PostgreSQL cloud (`SupabaseStorageAgent`).
- **Đóng gói:** Dockerfile multi-stage build, non-root user.
- **Triển khai:** Kubernetes manifests, deploy thành công lên minikube local cluster.

## Đang thực thi (Current Focus)

- **Generators & yield** (Day 32) — chuẩn bị tối ưu luồng dữ liệu lớn.
- **Profiling** (Day 47) — đo tốc độ từng dòng code.
- **Unit Testing với pytest** (Day 49) — đã có `test_agents.py`, cần mở rộng coverage.
- Hoàn thiện `TelegramAgent` (hiện là stub) — Phase 6.

## Tính năng chưa phát triển

- **TelegramAgent / Discord publisher:** mới là stub, chưa gọi API Telegram thật.
- **CI/CD:** GitHub Actions pipeline (build → test → scan → deploy) — chưa thiết lập.
- **FastAPI Web API:** chưa khởi tạo (Day 53-55).
- **SQLAlchemy ORM:** dự án dùng Supabase client trực tiếp, chưa qua ORM.
- **Multiprocessing / Threading nâng cao:** chưa áp dụng vào pipeline.

## Chỉ thị cốt lõi cho AI Agent

- Khi được yêu cầu viết code, ưu tiên các task trong phần **"Đang thực thi"**.
- Nếu user đòi nhảy thẳng tới tính năng chưa có nền tảng (VD: FastAPI khi chưa có DB layer ổn định) → **cảnh báo** và đề xuất hoàn thành tiền đề trước.
- Mọi thay đổi kiến trúc lớn → ghi ADR trong `knowledge/decisions/`.
