# ADR 0007 — Chuyển publisher Telegram → Discord (webhook)

- **Ngày**: 2026-06-30
- **Trạng thái**: Accepted
- **Phase**: 6 (Publisher)

## Bối cảnh

Telegram trên máy người dùng gặp sự cố, không dùng được nữa. Cần một kênh
phát thông báo thay thế. `TelegramAgent` đã hoàn chỉnh (digest gộp + chia
chunk) nên muốn giữ pattern, chỉ đổi kênh.

## Quyết định

Thêm `DiscordAgent` (`@AgentFactory.register("discord")`) dùng **Incoming
Webhook** (không cần bot/OAuth/gateway — chỉ một URL từ Channel → Settings
→ Integrations). Mirror cấu trúc `TelegramAgent`:

- Digest gộp, tự chia chunk theo `DISCORD_MAX_MESSAGE_LENGTH = 1900`
  (Discord cap cứng 2000), không cắt giữa một bài.
- Định dạng **Markdown** (thay HTML của Telegram); escape ký tự markdown,
  giữ nguyên URL trong `[title](url)`.
- `allowed_mentions.parse = []` để chặn mention ngoài ý muốn.

`main.py` pipeline thay `create("telegram")` → `create("discord")`.
`TelegramAgent` **giữ lại** trong factory (không xóa code, OCP) nhưng không
nằm trong pipeline → có thể bật lại bằng 1 dòng.

`.env.example`: thêm `DISCORD_WEBHOOK_URL`, đánh dấu khối Telegram là legacy.

## Hệ quả

- **Tích cực**: setup đơn giản hơn Telegram (không cần BotFather/chat_id);
  thiếu `DISCORD_WEBHOOK_URL` → agent bỏ qua êm (đúng L07, enrichment).
- **Tiêu cực**: trùng lặp logic digest giữa Telegram & Discord agent. Nếu
  sau này có ≥3 publisher, nên trích `DigestFormatter` chung (nợ kỹ thuật).
- **Tương thích ngược**: Telegram vẫn đăng ký, dữ liệu/model không đổi.

## Phương án đã loại

- *Discord Bot (gateway)*: cần token + intents, phức tạp hơn webhook cho
  nhu cầu một chiều (chỉ đẩy tin).
- *Xóa TelegramAgent*: mất tùy chọn quay lại; vi phạm tinh thần OCP.
