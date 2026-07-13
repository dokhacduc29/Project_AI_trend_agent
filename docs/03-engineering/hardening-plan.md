# Hardening Plan — lộ trình 9 session

> Nguồn: báo cáo thẩm định kỹ thuật 2026-07-10 (production-readiness 4/10), cộng
> với các phát hiện trong lúc thực thi. Mỗi session kết thúc ở trạng thái **repo
> xanh, commit được, không dở dang** — ràng buộc quan trọng nhất khi phải ngắt
> giữa chừng.

## Trạng thái

| Session | Nội dung | Trạng thái |
|---|---|---|
| 1 | Sửa SDK Dockerfile, `requirements-runtime.txt`, untrack worktree, NewsAPI header | ✅ `5fb6783` |
| — | Che secret trong log (`SecretRedactingFilter`) | ✅ `0de1e57` |
| — | Supabase: `sb_secret_` + bật RLS, storage thành critical | ✅ (ADR 0010) |
| 2 | `Deployment` + `while True` → `CronJob`; `main.py` chạy 1 chu kỳ rồi thoát | ✅ `566e490` (ADR 0011) |
| — | Nâng supabase-py 2.11→2.31 (2.11 chối key `sb_secret_`) | ✅ `a97d996` (ADR 0012) |
| 3 | Structured logging: JSON formatter, thêm `cycle_id`/`topic`/`agent` | ⬜ |
| 4 | Tạo package `ai_trend_agent/`, chuyển `domain/` + `application/`, giữ shim | ⬜ |
| 5 | Chuyển `infrastructure/` + `webapi/` + `tests/`, xoá 15 `sys.path` | ⬜ |
| 6 | Test cho `gemini_client` (retry/budget) + `_parse_batch_response` | ⬜ |
| 7 | Test cho scraper (mock httpx) + `is_critical` trong `run_pipeline` | ⬜ |
| 8 | Exception hierarchy riêng, thay `except Exception` mù | ⬜ |
| 9 | Cache ra khỏi đĩa ephemeral + queue cho bài thứ 16+ | ⬜ (cần quyết định thiết kế) |

Session 4 và 5 là một cặp, tách được vì session 4 giữ shim `sys.path` tạm thời
nên mọi thứ vẫn chạy. Ngắt sau session 4 thì repo nửa cũ nửa mới nhưng vẫn hoạt động.

## Nợ kỹ thuật còn treo

Xếp theo mức nghiêm trọng, không theo session.

**1. `main.py` thoát exit code 0 khi thiếu API key.** Hiện chỉ gây restart âm thầm
dưới `Deployment`. Nhưng sau Session 2, K8s sẽ đánh dấu Job là **Succeeded**,
`restartPolicy: OnFailure` không kích hoạt, dashboard xanh trong khi pipeline
chết. **Phải sửa ở đầu Session 2, trước khi viết CronJob YAML.**

**2. Reddit chết âm thầm.** `REDDIT_CLIENT_ID` và `REDDIT_CLIENT_SECRET` có trong
`.env` nhưng **rỗng** → code bỏ qua OAuth, rơi xuống kênh công khai, ăn `403` ở cả
hai endpoint. Pipeline đang chạy trên **2 nguồn, không phải 3**. Không ai báo lỗi
vì `except` nuốt hết.

**3. Cột `date` chứa ba định dạng trong cùng một cột `text`.** Đo trên 162 dòng:
80 dòng RFC822 (`Mon, 29 Jun 2026`, từ Google RSS), 72 dòng ISO (`2026-06-28`, từ
NewsAPI), 10 dòng `N/A`. Không sắp xếp theo thời gian được, không truy vấn "7 ngày
qua" được. Cần chuẩn hoá về `timestamptz` + migration.

**4. 153/162 title bị lowercase vĩnh viễn.** Commit `f612979` sửa cleaner để giữ
nguyên chữ hoa, nhưng `upsert(on_conflict="url", ignore_duplicates=True)` bỏ qua
dòng cũ, không cập nhật. Cần migration nếu muốn sửa.

**5. `HEALTHCHECK` giả trong `Dockerfile`.** Chỉ kiểm tra một file có tồn tại —
luôn đúng. Event loop treo, probe vẫn PASS. Sẽ tự biến mất ở Session 2: pod của
`CronJob` sống vài chục giây, `livenessProbe` gần như vô nghĩa; thay bằng
`activeDeadlineSeconds` + `backoffLimit`.

**6. `pandas` và `streamlit` là deps chết.** Không được import ở bất kỳ đâu trong
`Backend/`. Còn nằm trong `requirements.txt`.

**7. Disable legacy JWT API keys** trên Supabase. **Giờ an toàn để làm** — sau ADR
0012, pipeline đã chạy xanh trong K8s bằng `sb_secret_` (Supabase `201 Created`),
không còn phụ thuộc key JWT cũ.

**8. Key Gemini đang chạy FREE tier, không phải Pro.** Chu kỳ verify Session 2 ăn
`429 RESOURCE_EXHAUSTED` với `quotaId: GenerateRequestsPerDayPerProjectPerModel-
FreeTier`, `quotaValue: 20` (20 request/ngày cho `gemini-2.5-flash`). Trái với giả
định "đã đăng ký Pro". `GEMINI_API_KEY` trong `.env` **không gắn với gói trả phí** —
cần kiểm Google AI Studio / Cloud billing. Pipeline vẫn degrade đúng khi hết quota
(Gemini là enrichment, retry → fallback), nhưng bò chậm vì backoff ~60s/lần và có
thể chạm `activeDeadlineSeconds` của CronJob. Không phải lỗi code.

## Rủi ro đã chấp nhận

**Webhook Discord hiện tại không được xoay.** Nó đã bị `httpx` in ra log 4 lần
mỗi chu kỳ trước khi có `SecretRedactingFilter` (ADR 0009), nên phải coi là đã
lộ. Quyết định ngày 2026-07-10: **chấp nhận**, vì kênh đích là server Discord cá
nhân dùng để test, chưa công bố, không có người đọc. Thiệt hại tối đa nếu bị lạm
dụng là spam vào chính kênh test đó.

**Điều kiện kèm theo — bắt buộc**: phải xoay webhook **trước** khi kênh này (hoặc
chính webhook này) được dùng cho bất kỳ server nào có người đọc thật. Rủi ro được
chấp nhận cho *bối cảnh hiện tại*, không phải cho mọi bối cảnh tương lai. Việc
kênh test lặng lẽ trở thành kênh thật là cách thường gặp nhất để một rủi ro đã
chấp nhận biến thành một sự cố.

Cách xoay: Discord → Channel Settings → Integrations → Webhooks → xoá + tạo lại →
cập nhật `DISCORD_WEBHOOK_URL` trong `.env`.

## Nguyên tắc kiểm chứng

Rút ra từ Session 1. Áp dụng cho mọi session sau.

- **`import` thành công không chứng minh code chạy được.** Nó chứng minh giai đoạn
  *nạp*, không chứng minh giai đoạn *thực thi*. `hasattr()` chứng minh thuộc tính
  tồn tại, không chứng minh chữ ký hàm không đổi.
- **Chạy trong container, không chỉ ở máy local.** Máy local có venv riêng, cwd
  riêng, quyền admin, kho chứng chỉ riêng. Lỗi kiểu "`prompts/` bị `.dockerignore`
  loại" hay "`appuser` không ghi nổi `/app/data`" chỉ lộ ra ở đó.
- **Pin version đã kiểm chứng, không phải version mới nhất.** Nâng cấp là một thay
  đổi riêng, có chu kỳ chạy thật để xác nhận.
- **Không đưa secret thật vào test fixture.** Log xoay vòng rồi mất; git history
  thì vĩnh viễn.
- **Không dùng lệnh phá huỷ để kiểm tra rằng nó bị chặn.** `DELETE` toàn bảng để
  "chứng minh RLS chặn nó" sẽ xoá sạch dữ liệu nếu RLS không chặn. Dùng `INSERT`
  với `ON CONFLICT DO NOTHING` trên một `url` đã tồn tại: Postgres vẫn kiểm quyền,
  không dòng nào bị thêm hay sửa.
