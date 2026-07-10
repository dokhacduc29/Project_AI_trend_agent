# Nhật Ký Quyết Định & Bộ Nhớ (Memory Log)

Ghi nhận trạng thái hệ thống và **trỏ tới** các quyết định kiến trúc chi tiết.
Nguồn sự thật của mọi quyết định là `knowledge/decisions/` (ADR) — file này chỉ
tóm tắt và liên kết, không kể lại (tuân thủ rule *single source*).

## Index ADR (nguồn chuẩn: `knowledge/decisions/`)

| ADR | Quyết định | Ngày |
|---|---|---|
| [0001](../../knowledge/decisions/0001-trend-synthesis-agent.md) | Thêm `TrendSynthesisAgent` & mở rộng `PipelineContext` | — |
| [0002](../../knowledge/decisions/0002-hybrid-ai-cleaner.md) | Hybrid AI Cleaner & mở rộng `Article` model | — |
| [0003](../../knowledge/decisions/0003-pipeline-resilience.md) | Pipeline resilience: phân biệt agent *critical* vs *enrichment* | 2026-06-30 |
| [0004](../../knowledge/decisions/0004-externalize-prompts.md) | Tách prompt ra file (`prompt_loader.py`, `prompts/`) | 2026-06-30 |
| [0005](../../knowledge/decisions/0005-gemini-budget.md) | Budget enforcement cho lời gọi Gemini | 2026-06-30 |
| [0006](../../knowledge/decisions/0006-eval-suite.md) | Eval suite cho parser & robustness output AI | 2026-06-30 |
| [0007](../../knowledge/decisions/0007-discord-pivot.md) | Chuyển publisher Telegram → Discord (webhook) | 2026-06-30 |
| [0008](../../knowledge/decisions/0008-container-runtime-correctness.md) | Container runtime correctness: một nguồn sự thật cho deps | 2026-07-10 |
| [0009](../../knowledge/decisions/0009-secret-hygiene.md) | Secret hygiene: không trong URL, không trong log, không trong git | 2026-07-10 |
| [0010](../../knowledge/decisions/0010-supabase-rls-secret-key.md) | Khoá bảng Supabase: secret key + RLS; storage thành critical | 2026-07-10 |

## [2026-07-10] Hardening Tier A — container boot được lần đầu

Lộ trình đầy đủ + nợ kỹ thuật còn treo: [`docs/03-engineering/hardening-plan.md`](../03-engineering/hardening-plan.md).

Tóm tắt — chi tiết xem ADR:
- **Container (0008)**: `Dockerfile` cài SDK sai (`google-generativeai`) trong khi
  code dùng `google-genai` → image **chưa từng boot được**. Tách
  `requirements-runtime.txt`, pin `google-genai==2.7.0` (version đã chạy thật).
- **Secret hygiene (0009)**: NewsAPI key rời khỏi query string sang header
  `X-Api-Key`; `SecretRedactingFilter` che token webhook trong log mà vẫn giữ
  dòng chẩn đoán.
- **Supabase (0010)**: bảng `articles` từng mở toang (anon key + RLS tắt) →
  `sb_secret_` + bật RLS không policy. `SupabaseStorageAgent.is_critical = True`,
  gỡ `except` nuốt lỗi: lưu hỏng thì đừng đăng.

Kiểm chứng bằng một chu kỳ production thật trong container: 49 giây, 12 bài thô →
11 bài sạch, 5/12 lời gọi Gemini, ghi 3 dòng Supabase, gửi 4 tin nhắn Discord.

**Còn treo, ưu tiên cao**: xoay webhook Discord (đã lộ trong log trước ADR 0009);
`main.py` thoát exit code 0 khi thiếu key — phải sửa trước khi viết CronJob.

## [2026-06-30] Hardening + Pivot Publisher (Phase 6)

Tóm tắt — chi tiết xem ADR tương ứng ở bảng trên:
- **Resilience (0003)**: pipeline chia agent thành *critical* (lỗi → dừng) và
  *enrichment* (lỗi → degrade, vẫn tiếp tục). Mọi tool call trả observation, không null.
- **Prompt-as-artifact (0004)**: prompt Gemini tách khỏi code vào `prompts/`, nạp
  qua `prompt_loader.py` — sửa prompt không đụng logic.
- **Gemini budget (0005)**: giới hạn số lời gọi/chi phí Gemini mỗi lần chạy.
- **Eval suite (0006)**: `test_evals.py` + `evals/` kiểm thử độ bền parser và
  output AI (ngoài unit test thuần).
- **Discord pivot (0007)**: Telegram trên máy người dùng hỏng → thay bằng
  `DiscordAgent` qua Incoming Webhook, mirror pattern `TelegramAgent`.

## [2026-05-14] Chuẩn hóa Kiến trúc Đa lớp & Rà soát Luật Thép

### 1. Trạng thái Hệ thống
- **Cấu trúc**: Hoàn tất chuyển đổi mã nguồn Core ETL về mô hình phân lớp chuẩn (`Backend` chứa `Domain`, `Application`, `Infrastructure`, `WebApi`).
- **Orchestrator**: Điểm dẫn nhập chính thức chuyển sang `Backend/ai_trend_agent.WebApi/main.py`.

### 2. Xử lý Ánh xạ IDE (Static Analysis)
- Cấu hình file `settings.json` và `pyrightconfig.json` sử dụng đường dẫn tuyệt đối chuẩn gạch chéo xuôi (`/`) để Pylance/Pyright giải quyết hoàn hảo các câu lệnh import phẳng (flat import) mà không cần can thiệp mã nguồn.
- Tạo file `.env` toàn cục cấp gốc định nghĩa biến `PYTHONPATH` hỗ trợ VS Code Python Extension đồng bộ môi trường phân tích ngầm định.

### 3. Kết quả Rà soát Code theo 10 Luật Thép (xem `agent-guide.md`)
- **L01 (No Hardcode Secrets)**: Tuân thủ 100%. Mọi API Key (`NEWS_API_KEY`, `GEMINI_API_KEY`) đều nạp động qua `PipelineContext` từ file `.env` không được commit.
- **L02 (Logging)**: Ghi nhận giới hạn ở đo lường hiệu suất (Timer), số lượng bản ghi và tracing cơ bản; không log dữ liệu nhạy cảm.
- **L03 (Asyncio)**: Tận dụng hoàn toàn I/O bất đồng bộ qua `httpx.AsyncClient` và `asyncio.gather()`, không có tác vụ chờ đồng bộ gây nghẽn luồng.
- **L09 (No Magic Numbers)**: Các thông số vòng đời, kích thước trang, định mức truy vấn đều quản lý tập trung tại `config.py`.
- **Phân lớp (kiến trúc)**: `Domain` chỉ chứa hằng số/dataclasses thuần; `Application` định nghĩa interface/decorator; `Infrastructure` triển khai I/O ngoài.

### 4. Đồng bộ Lộ trình Chiến lược (Roadmap .v2)
- Cập nhật ánh xạ thực tế các kỹ năng Python Backend đã được lập trình hoàn chỉnh vào cột Trạng thái của file `Roadmap .v2.csv` (đánh dấu `✅ Done` cho các ngày thuộc Phase 2, 3, 4, 5 tương ứng với mã nguồn Core ETL hiện hành).

### 5. Hoàn thiện Toàn diện Giai đoạn 5 (Tối ưu Đa nhân & Kiểm thử)
- **Threading xử lý File (Day 42)**: Tích hợp thành công cơ chế `asyncio.to_thread` vào `storage.py` để đẩy các tác vụ I/O ghi đĩa đồng bộ sang luồng nền riêng biệt, loại bỏ rủi ro ách tắc Event Loop.
- **Profiling Hệ thống (Day 47)**: Bổ sung cờ `--profile` vào `main.py` kích hoạt `cProfile` cho phép đo lường và in báo cáo Top 30 hàm tiêu tốn nhiều thời gian nhất.
- **Unit Testing Chuyên nghiệp (Day 49)**: Khởi tạo bộ kiểm thử tự động `Backend/ai_trend_agent.Tests/test_agents.py` sử dụng khung `pytest` và `pytest-asyncio` xác thực độ chính xác của các thuật toán lõi.

### 6. Gộp Nhánh Chính Thức (Merge to Main)
- Gộp toàn bộ thành quả Giai đoạn 4 và Giai đoạn 5 từ nhánh `feature-phase-4-ai` sang nhánh `main` để thiết lập trạng thái chuẩn làm mặc định cho các lượt tải/clone mã nguồn mới.
