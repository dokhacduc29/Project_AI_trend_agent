# ADR 0009 — Secret hygiene: không trong URL, không trong log, không trong git

- **Ngày**: 2026-07-10
- **Trạng thái**: Accepted
- **Phase**: Hardening (Tier A)

## Bối cảnh

Luật Thép L01 nói "no hardcoded secrets", và dự án tuân thủ: `.env` không được
commit, quét toàn bộ lịch sử git không thấy key nào rò.

Nhưng L01 chỉ phủ **nơi secret được khai báo**, không phủ **nơi secret đi qua**.
Một chu kỳ production thật cho thấy hai lỗ hổng mà audit tĩnh không bắt được.

**Secret trong URL.** `scrapers.py` ghép `apiKey` của NewsAPI vào query string
bằng f-string. Query string đi vào access log, proxy, APM, browser history.
Đồng thời `topic` không được URL-encode: từ khóa có khoảng trắng hoặc `&` tạo
request méo.

**Secret trong log.** `httpx` ghi lại **toàn bộ URL** ở mức INFO. Webhook Discord
không có header xác thực — token nằm thẳng trong path. Mỗi chu kỳ in nó ra 4 lần
(4 chunk tin nhắn), vào stdout container, rồi vào bất kỳ hệ thống log tập trung
nào. Ai đọc được log đều đăng bài vào kênh được.

## Quyết định

**Secret không đi qua URL.** NewsAPI key chuyển sang header `X-Api-Key`. `topic`
và mọi tham số đi qua `params=` của httpx để được URL-encode đúng. Google News
RSS sửa cùng cách. URL và locale lên `config.py` (L09).

**Secret không đi vào log.** Thêm `Application/log_redaction.py`:
`SecretRedactingFilter` gắn vào **handler** của root logger, che token webhook
Discord, bot token Telegram, query param `apikey`/`token`/`secret`, và header
`Bearer`/`Basic`. Giữ lại webhook id và HTTP status code để còn chẩn đoán được.

Filter phải gắn ở **handler**, không phải logger: filter đặt trên một logger chỉ
chạy với record log thẳng vào nó, không chạy với record propagate lên từ logger
con như `httpx`.

**Secret không vào git.** Fixture test dùng token giả. Log thì xoay vòng rồi mất;
git history thì vĩnh viễn.

## Hệ quả

- **Tích cực**: log production giữ nguyên giá trị chẩn đoán. Dòng
  `GET .../new.json "403 Blocked"` — thứ đã phát hiện Reddit chết âm thầm — không
  bị đụng tới. Chỉ token bị thay bằng `<REDACTED>`.
- **Tiêu cực**: filter là danh sách pattern, tức là **danh sách chặn**, không phải
  danh sách cho phép. Một secret có hình dạng mới sẽ lọt. Cần bổ sung pattern khi
  thêm dịch vụ mới.
- **Chi phí**: một lượt regex trên mỗi log record. Không đáng kể ở quy mô này.

## Nguyên tắc rút ra

**Bản vá chặn rò tương lai; nó không thu hồi được cái đã lộ.** Webhook Discord
đã xuất hiện trong log trước khi có filter, nên nó phải được xoay — xoá và tạo
lại trong Channel Settings → Integrations → Webhooks. Vá code không thay được
việc đó.

## Phương án đã loại

- *`logging.getLogger("httpx").setLevel(WARNING)`*: một dòng, chặn được rò, nhưng
  giết luôn mọi log chẩn đoán của httpx — `NewsAPI 200`, `Reddit 403 Blocked`,
  `Supabase 201 Created`. Đổi một lỗ hổng bảo mật lấy một lỗ hổng quan sát là
  món hời tồi.
- *Đưa `apiKey` NewsAPI vào `params=`*: vẫn nằm trong query string, vẫn rò vào
  log. Header là chỗ đúng.
- *Dùng dòng log thật (có token thật) làm fixture test*: sẽ ghi secret vĩnh viễn
  vào git history — biến một sự cố tạm thời thành vĩnh cửu.
