# ADR 0006 — Eval suite cho parser & robustness output AI

- **Ngày**: 2026-06-30
- **Trạng thái**: Accepted
- **Phase**: Hardening
- **Nguồn chuẩn mực**: DenisSergeevitch/agents-best-practices (`evals.md`) — *"Implement validators for injection, missing tool results, timeouts, budget exhaustion. Trace-level grading preferred over pass/fail"*; tirth8205/code-review-graph — *"test gaps… untested hotspots"*.

## Bối cảnh

Phần parse JSON từ Gemini (`_parse_batch_response`, bóc markdown + map
sentiment; tương tự ở `cleaner`/`trend`) là vùng **dễ vỡ nhất** mà **không
có test nào**. Đổi prompt/model có thể âm thầm phá parser mà không ai biết.

## Quyết định

Thêm `ai_trend_agent.Tests/test_evals.py` + golden set
`evals/golden_sentiment.json`. Eval chạy **offline, deterministic** (không
gọi mạng):

1. **ACCURACY** — feed response RAW đã biết (clean, markdown-wrapped, nhãn
   tiếng Việt/chữ hoa) → assert sentiment parse đúng, chốt ngưỡng
   `MIN_SENTIMENT_ACCURACY = 0.95`.
2. **ROBUSTNESS** — JSON hỏng/rỗng → KHÔNG crash, về mặc định NEUTRAL,
   không sửa bài.
3. **BUDGET** — vượt trần → trả fallback + tăng `blocked` (validator cho
   ADR 0005).

## Hệ quả

- **Tích cực**: khóa hành vi parser; đổi prompt/model mà làm hỏng parse sẽ
  fail CI ngay. Golden set mở rộng dần khi gặp ca lỗi mới (regression).
- **Tiêu cực**: eval này chấm **parser**, chưa chấm **chất lượng ngữ nghĩa**
  của model (cần golden có nhãn người + gọi model thật) — ghi nhận là bước
  tiếp theo.
- **Tương thích ngược**: chỉ thêm test, không đụng code chạy.

## Phương án đã loại

- *Gọi Gemini thật trong test*: phi-deterministic, tốn quota, không chạy
  được trong CI offline. Để dành cho một "live eval" tùy chọn sau này.
