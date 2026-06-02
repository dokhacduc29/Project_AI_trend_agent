# ADR 0002 — Hybrid AI Cleaner & mở rộng Article model

- **Ngày**: 2026-06-02
- **Trạng thái**: Accepted
- **Phase**: B (AI Enhancement)

## Bối cảnh

`CleanerAgent` cũ chỉ gán tag bằng bảng regex cố định
(`entity_patterns`). Hạn chế: bỏ sót thực thể mới (Mistral, xAI...),
không hiểu ngữ cảnh, không chấm điểm liên quan nên bài lạc đề vẫn lọt
xuống Analyzer/Trend phía sau, làm nhiễu kết quả AI.

## Quyết định

Nâng cấp `CleanerAgent` thành **Hybrid 2 tầng**:

1. **Tầng 1 (Regex)** — giữ nguyên: lọc rác, khử trùng lặp, gán tag thực
   thể rõ ràng. Miễn phí, nhanh, là fallback khi không có AI.
2. **Tầng 2 (AI)** — chỉ chạy khi có `GEMINI_API_KEY`: một batch call
   chấm điểm liên quan 0-10 cho mỗi bài + gán tag cho bài regex bỏ sót.
   Loại bài dưới `CLEANER_RELEVANCE_THRESHOLD`.

Mở rộng `Article` thêm field `relevance_score: int = -1`
(-1 = chưa chấm). Đây là thay đổi model cốt lõi → ghi ADR (CLAUDE.md §6).

## Nguyên tắc Hybrid

- Regex **ưu tiên** cho tag nó biết; AI chỉ **lấp chỗ trống** (bài chưa
  có tag) → tiết kiệm token, tránh AI ghi đè tag chính xác.
- Bài **chưa được AI chấm** (vượt batch size, hoặc lỗi) giữ
  `relevance_score = -1` và **KHÔNG bị loại** (benefit of the doubt).
- Lỗi API/hết quota → fallback toàn bộ về kết quả Tầng 1.

## Hệ quả

- **Tích cực**: dữ liệu sạch & đúng chủ đề hơn → cải thiện Analyzer (P4)
  và Trend Synthesis (Phase A); thêm điểm dùng AI thứ 3 có chiều sâu.
- **Tiêu cực**: thêm ~1 API call/chu kỳ; `Article` to hơn.
- **Tương thích ngược**: thiếu key → hành vi y hệt cleaner regex cũ.

## Phương án đã loại

- *AI hoàn toàn (bỏ regex)*: mất fallback, phụ thuộc 100% Gemini.
- *Gộp vào Analyzer*: vi phạm SRP (lọc vs tóm tắt là 2 trách nhiệm).

## Nợ kỹ thuật ghi nhận

Logic retry Gemini (backoff) hiện lặp ở 3 agent
(`ai_agent`, `trend_agent`, `cleaner`). Nên trích xuất thành helper dùng
chung ở một ADR/cleanup sau.
