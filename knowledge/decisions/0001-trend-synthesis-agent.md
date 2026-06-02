# ADR 0001 — Thêm TrendSynthesisAgent & mở rộng PipelineContext

- **Ngày**: 2026-06-02
- **Trạng thái**: Accepted
- **Phase**: A (AI Enhancement)

## Bối cảnh

Project tên "AI Trend Agent" nhưng AI chỉ xuất hiện ở 1/5 agent
(`SummarizationAgent` — tóm tắt từng bài + sentiment). Phần "Trend"
(phân tích xu hướng vĩ mô) mà tên project hứa hẹn hoàn toàn chưa có.
Các bước còn lại (scraper, cleaner, storage, telegram) không dùng AI.

## Quyết định

1. Thêm agent mới `TrendSynthesisAgent` (`@AgentFactory.register("trend")`)
   chạy SAU `analyzer` và TRƯỚC `storage` trong pipeline. Nó đọc toàn bộ
   `ctx.articles` (đã có summary + sentiment) và gọi Gemini MỘT lần để rút
   ra 3-5 xu hướng nổi + tâm lý chung + nhận định tổng quan.

2. Mở rộng `PipelineContext` thêm field `trend_report: TrendReport`
   (dataclass mới trong `models.py`). Đây là thay đổi cấu trúc cốt lõi
   nên ghi ADR theo CLAUDE.md §6.

3. `TelegramAgent` đặt phần xu hướng lên ĐẦU digest gửi về điện thoại.

## Hệ quả

- **Tích cực**: Bổ sung đúng lời hứa "Trend"; tăng lượng AI có ý nghĩa;
  tận dụng dữ liệu đã có nên chi phí thấp (1 call/chu kỳ).
- **Tiêu cực**: `PipelineContext` to hơn; mọi agent nhận thêm field
  (nhưng không bắt buộc dùng → không phá vỡ LSP).
- **Tương thích ngược**: `trend_report` có default rỗng
  (`generated=False`) nên pipeline cũ vẫn chạy nếu thiếu GEMINI_API_KEY.

## Phương án đã cân nhắc

- *Gộp vào SummarizationAgent*: bị loại — vi phạm SRP (1 agent làm 2 việc
  khác cấp độ: micro tóm tắt vs macro xu hướng).
- *Lưu trend dưới dạng str đơn giản trong ctx*: bị loại — dataclass
  `TrendReport` có cấu trúc giúp Telegram format đẹp & dễ lưu DB sau này.
