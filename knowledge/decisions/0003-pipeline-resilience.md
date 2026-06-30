# ADR 0003 — Pipeline resilience: critical vs enrichment agent

- **Ngày**: 2026-06-30
- **Trạng thái**: Accepted
- **Phase**: Hardening (hệ thống thực tiễn)
- **Nguồn chuẩn mực**: DenisSergeevitch/agents-best-practices — *"Result universality: every tool call must return an observation… no null"*, *"Deterministic stopping: explicit termination reasons"*; tirth8205/code-review-graph — phân tích *blast radius* (lỗi 1 node lan xuống caller/dependent).

## Bối cảnh

`run_pipeline` cũ: **bất kỳ** agent ném exception → `return`, dừng cả chu
kỳ. Hệ quả thực tế: `analyzer` (Gemini) lỗi/hết quota → `storage` và
`discord` **không bao giờ chạy** → mất sạch dữ liệu đã cào & làm sạch ở
các bước trước. Đây là một silent abort của toàn pipeline.

## Quyết định

Thêm thuộc tính `BaseAgent.is_critical: bool = False` (thay đổi BaseAgent
→ ghi ADR theo CLAUDE.md §6) phân loại agent:

- **critical** (`scraper`): không có dữ liệu thô → các bước sau vô nghĩa
  → lỗi thì DỪNG chu kỳ.
- **enrichment** (mặc định: `cleaner`, `analyzer`, `trend`, `storage`,
  `discord`): lỗi → LOG rõ lý do rồi `continue`, pipeline đi tiếp.

`run_pipeline` đọc `getattr(agent, "is_critical", False)` để quyết định
abort hay tiếp tục.

## Hệ quả

- **Tích cực**: một bước enrichment hỏng không còn làm mất dữ liệu đã có;
  storage luôn có cơ hội chạy. Lỗi được phân loại rõ trong log
  (`[CRITICAL]` vs `[ENRICHMENT]`).
- **Tiêu cực**: chu kỳ có thể "thành công một phần" (ví dụ lưu được nhưng
  không gửi Discord) — chấp nhận được, hơn là mất tất cả.
- **Tương thích ngược**: agent không khai báo `is_critical` mặc định
  enrichment → an toàn.

## Phương án đã loại

- *Giữ nguyên abort-all*: rủi ro mất dữ liệu cao.
- *Bọc try/except trong từng agent*: rải rác, vi phạm DRY, mỗi agent phải
  tự nhớ — đặt quyết định ở orchestrator gọn và nhất quán hơn.
