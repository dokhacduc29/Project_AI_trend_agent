# ADR 0010 — Khoá bảng Supabase: secret key + RLS, và storage trở thành critical

- **Ngày**: 2026-07-10
- **Trạng thái**: Accepted
- **Phase**: Hardening (Tier A)

## Bối cảnh

Bảng `public.articles` chạy với **RLS tắt** và pipeline ghi bằng key có
`role='anon'`.

`anon` không phải mật khẩu. Nó là JWT được Supabase thiết kế để **nhúng thẳng
vào JavaScript trình duyệt** — dashboard gắn nhãn `public` ngay cạnh nó. Bảo mật
thật nằm ở Row Level Security, không nằm ở việc giấu key. RLS tắt nghĩa là bất
kỳ ai có `SUPABASE_URL` cộng anon key đều `SELECT`, `INSERT`, `UPDATE`, và
`DELETE` được toàn bộ bảng.

Đây không phải suy luận: chu kỳ production ngày 2026-07-10 đã ghi 3 dòng vào
bảng bằng chính anon key đó.

Project đã chuyển sang hệ API key mới của Supabase: `sb_publishable_` (thay
`anon`) và `sb_secret_` (thay `service_role`).

## Quyết định

Pipeline là **server-side job không có danh tính người dùng**. Nó dùng
`sb_secret_` — key bí mật, bỏ qua RLS, chỉ sống trong `.env` và K8s Secret.

Bật RLS trên `public.articles`, **không tạo policy nào**:

```sql
ALTER TABLE public.articles ENABLE ROW LEVEL SECURITY;
```

Không policy = từ chối tất cả với `anon` và `authenticated`. `service_role` /
secret key bỏ qua RLS hoàn toàn.

**Thứ tự thực hiện quan trọng**: đổi key **trước**, bật RLS **sau**. Secret key
hoạt động ở cả hai trạng thái RLS, nên không có khoảng trống nào pipeline bị
chặn. Làm ngược lại sẽ tạo một cửa sổ mà pipeline hỏng trong im lặng.

**Hệ quả kéo theo: `SupabaseStorageAgent.is_critical = True`**, và gỡ bỏ
`try/except Exception` nuốt lỗi trong `execute()`.

Trước bản vá, hai lớp cùng che lỗi: `execute()` bọc mọi exception rồi trả `ctx`
bình thường; và kể cả nếu nó ném ra, `run_pipeline` đọc
`getattr(agent, "is_critical", False)` → mặc định `False` → xử lý như agent
*enrichment*, log rồi đi tiếp. Kết quả: nếu key sai hoặc RLS chặn, Discord vẫn
đăng tin đều đặn, database ngừng nhận dữ liệu, và không có cảnh báo nào. Dashboard
Supabase vẫn hiện đủ dòng vì Table Editor chạy bằng role `postgres`, bỏ qua RLS.

Storage phải là critical vì **dedupe của toàn hệ thống dựa vào `UNIQUE(url)` trên
chính bảng này**. Storage chết → chu kỳ sau đăng lại y hệt các bài cũ lên Discord.

## Hệ quả

- **Tích cực**: publishable key đọc ra 0 dòng, `INSERT` bị từ chối với
  `42501: new row violates row-level security policy`. Secret key đọc 165 dòng,
  ghi bình thường. Dữ liệu không suy suyển.
- **Tiêu cực**: một cú nấc mạng của Supabase giờ làm mất một chu kỳ tin tức
  (pipeline dừng trước bước Discord). Đây là đánh đổi có chủ đích: tin không lưu
  được thì không đáng đăng.
- **Vận hành**: `sb_secret_` mạnh hơn anon nhiều. Chỉ được phép ở backend, tuyệt
  đối không vào frontend hay log (xem ADR 0009).
- **Còn treo**: nút "Disable JWT-based API keys" ở tab Legacy chưa bấm. Chỉ bấm
  sau khi chắc chắn không còn nơi nào dùng key JWT cũ.

## Phương án đã loại

- *Giữ `anon` + viết policy cho phép `anon` INSERT*: policy đó áp cho **mọi**
  người cầm anon key, mà key ấy công khai theo thiết kế. Khoá cửa rồi dán chìa
  lên cánh cửa.
- *Thêm danh tính người dùng (service account + `auth.uid()` trong policy)*:
  pattern hợp lệ, nhưng nó **dời** secret chứ không xoá secret — mật khẩu vẫn
  nằm trong `.env`. Đổi lại nhận thêm vấn đề vòng đời token: JWT `authenticated`
  mặc định sống 1 giờ, còn pipeline ngủ 4 tiếng giữa các chu kỳ. Danh tính chỉ
  đáng giá khi có ≥2 tác nhân để phân biệt; hiện pipeline là người ghi duy nhất.
- *Dùng `sb_publishable_` cho pipeline*: chính là anon key khoác áo mới.

## Kiến trúc cho tương lai

Nếu sau này có dashboard đọc bảng này (`requirements.txt` từng có `streamlit`),
hình dạng đúng **không cần danh tính người dùng nào**:

```sql
CREATE POLICY public_read ON public.articles
  FOR SELECT TO anon USING (true);
```

Pipeline ghi bằng `sb_secret_` (bỏ qua RLS). Frontend đọc bằng `sb_publishable_`
(policy cho phép SELECT, và chỉ SELECT). Đó chính xác là kịch bản mà Supabase
thiết kế cặp key này để phục vụ.
