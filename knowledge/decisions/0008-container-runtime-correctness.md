# ADR 0008 — Container runtime correctness: một nguồn sự thật cho dependencies

- **Ngày**: 2026-07-10
- **Trạng thái**: Accepted
- **Phase**: Hardening (Tier A)

## Bối cảnh

Image Docker **chưa từng khởi động được**, kể từ khi có `Dockerfile`.

`Dockerfile` cài `google-generativeai` (SDK cũ, cung cấp `google.generativeai`),
trong khi 4 module runtime — `ai_agent.py`, `cleaner.py`, `trend_agent.py`,
`gemini_client.py` — đều `from google import genai` (SDK mới `google-genai`).
`main.py` import `gemini_client` ở top-level, nên tiến trình chết ở bước import,
trước cả khi vào `main()`.

Lỗi tồn tại được lâu vì hai lý do. Thứ nhất, `pytest` và chạy local dùng venv
của máy, nơi `google-genai` đã cài đúng — không ai chạy image. Thứ hai,
`HEALTHCHECK` chỉ kiểm tra `os.path.exists('/app/.../main.py')`, một điều kiện
luôn đúng miễn filesystem còn nguyên; nó không bao giờ báo container đã chết.

Thêm nữa, `Dockerfile` `COPY requirements.txt` rồi **không** `pip install -r`,
mà hard-code 4 package. `requirements.txt` (8 lib) và image (4 lib) đã phân kỳ:
đổi version trong `requirements.txt` không có tác dụng nào lên image.

## Quyết định

**Tách `Backend/requirements-runtime.txt`** làm nguồn sự thật duy nhất cho image:

```dockerfile
COPY Backend/requirements-runtime.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements-runtime.txt
```

Chỉ 4 package thật sự được import bởi code runtime: `httpx`, `python-dotenv`,
`google-genai`, `supabase`. (`pandas` và `streamlit` trong `requirements.txt`
**không được import ở bất kỳ đâu** — deps chết, không chỉ dev-only.)

**Pin `google-genai==2.7.0`, không phải `2.11.0` mới nhất.** 2.7.0 là version đã
chạy thật ở venv local trong nhiều chu kỳ. Version mới nhất chưa từng có dòng
code nào của dự án này chạy lên nó.

## Hệ quả

- **Tích cực**: container boot được lần đầu tiên. Không còn drift
  `Dockerfile` ↔ `requirements.txt`. Dev-only libs không lọt vào image prod.
- **Tiêu cực**: hai file requirements phải giữ đồng bộ thủ công. Nếu thêm lib
  runtime mà quên thêm vào `requirements-runtime.txt`, image sẽ chết ở import —
  nhưng lần này chết ồn ào và ngay lập tức, không âm thầm.
- **Nợ để lại**: `HEALTHCHECK` giả vẫn còn. Sau khi chuyển sang `CronJob`
  (xem `docs/03-engineering/hardening-plan.md`), probe sẽ được thay bằng
  `activeDeadlineSeconds` + `backoffLimit`, vốn là công cụ đúng cho Job.

## Nguyên tắc rút ra

**`import` thành công không chứng minh API surface còn nguyên.**

Trong quá trình sửa, `hasattr(client.aio.models, 'generate_content')` trả về
`True` trên cả hai version. Nhưng `hasattr` chỉ chứng minh *thuộc tính tồn tại*,
không chứng minh *chữ ký hàm không đổi*. Nếu 2.11 đổi tên một tham số, cả
`import` lẫn `hasattr` vẫn xanh, và lời gọi thật vẫn nổ ở runtime.

Kiểm chứng bằng cách chạy một chu kỳ production thật trong container (49 giây,
5/12 lời gọi Gemini, ghi 3 dòng Supabase, gửi 4 tin nhắn Discord) — không phải
bằng cách nhìn `import` không báo lỗi.

## Phương án đã loại

- *Sửa code sang `google.generativeai`*: SDK cũ đã deprecated; code hiện tại
  viết cho API mới (`genai.Client` + `client.aio.models.generate_content`).
- *Để `google-genai` không pin version*: build hôm nay và build tháng sau ra hai
  image khác nhau. Reproducibility mất trắng.
- *Pin `2.11.0` (mới nhất)*: chưa được kiểm chứng bởi bất kỳ lần chạy nào.
  Nâng cấp phải là một thay đổi riêng, có chu kỳ chạy thật để xác nhận.
