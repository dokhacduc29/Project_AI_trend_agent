# ADR 0005 — Budget enforcement cho lời gọi Gemini

- **Ngày**: 2026-06-30
- **Trạng thái**: Accepted
- **Phase**: Hardening
- **Nguồn chuẩn mực**: DenisSergeevitch/agents-best-practices — *"Budget enforcement: step, time, token, and cost budgets as mandatory features — not optional"* + *"Deterministic stopping rather than allowing loops to exhaust budgets silently"*.

## Bối cảnh

Không có trần nào cho số lời gọi Gemini trong một chu kỳ. Một bug (vòng
lặp, batch sai, dữ liệu phình) có thể tạo ra hàng loạt request → cháy quota
free tier hoặc phát sinh chi phí ngoài kiểm soát, không có cảnh báo.

## Quyết định

Thêm budget cấp module trong `gemini_client`:

- `GEMINI_MAX_CALLS_PER_CYCLE` (config): trần số request/chu kỳ.
- `reset_budget()` gọi ở đầu `run_pipeline` mỗi chu kỳ.
- `generate_with_retry`: nếu `calls >= max` → KHÔNG gọi mạng, trả `fallback`
  kèm log lý do `[BUDGET]` (deterministic stopping); ngược lại tăng bộ đếm
  `calls` + cộng dồn `in_chars` để ước lượng token.
- `budget_report()` → `run_pipeline` log tổng kết cuối chu kỳ
  (`calls/max`, `~input_tokens`, `blocked`) phục vụ observability.

## Hệ quả

- **Tích cực**: chặn runaway cost/quota; có số liệu chi phí mỗi chu kỳ.
  Vượt trần thoái lui mềm (fallback) thay vì crash.
- **Tiêu cực**: trạng thái cấp module → không an toàn nếu chạy nhiều
  pipeline song song trong cùng process (hiện tại single-pipeline → chấp
  nhận). Ghi nhận là nợ kỹ thuật nếu sau này đa luồng.
- **Tương thích ngược**: trần đặt đủ rộng (12) cho khối lượng hiện tại →
  không ảnh hưởng vận hành bình thường.

## Phương án đã loại

- *Không có budget*: rủi ro chi phí.
- *Budget theo token thật từ response*: cần usage metadata mỗi call, phức
  tạp hơn; đếm theo số call đủ dùng cho free tier (giới hạn RPM/RPD).
