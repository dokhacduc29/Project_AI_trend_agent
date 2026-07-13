# ADR 0012 — Nâng supabase-py 2.11.0 → 2.31.0 để nhận key sb_secret_

- **Ngày**: 2026-07-13
- **Trạng thái**: Accepted
- **Phase**: Hardening (Session 2 — deploy)

## Bối cảnh

Lần đầu chạy pipeline thật trong Kubernetes (Docker Desktop Kubeadm), chu kỳ
chết ở đúng một bước:

```
[SupabaseStorageAgent] Đang lưu 10 bài lên Supabase...
[CRITICAL] SupabaseStorageAgent loi: Invalid API key. Dung chu ky.
```

Chẩn đoán từng lớp:

1. **Key hợp lệ ở phía server.** Gọi REST thô (`httpx.get` với header `apikey` +
   `Authorization: Bearer`) tới `.../rest/v1/articles` trả về **HTTP 200** kèm dữ
   liệu thật. Server Supabase chấp nhận key.
2. **Lỗi nằm ở client, ngay tại `create_client()`** — không phải ở query.
   `supabase-py 2.11.0` kiểm tra key phải là JWT (`eyJ...`) khi khởi tạo client,
   và ném `SupabaseException("Invalid API key")` với key `sb_secret_` (định dạng
   mới, không phải JWT).
3. **Tái hiện được cả ngoài K8s.** `docker run --env-file` local cho cùng lỗi →
   không phải vấn đề của cluster, cũng không phải của thay đổi Session 2.

Đây là bug ngủ đông từ ADR 0010. Session 1 đổi sang `sb_secret_` nhưng chu kỳ
ghi Supabase thành công lúc đó dùng key **anon cũ**; việc kiểm chứng `sb_secret_`
làm bằng probe trực tiếp, chưa bao giờ đi qua `supabase-py`. Hôm nay là lần đầu
app thật gặp `sb_secret_` + client 2.11.0 cùng lúc.

Đúng bài học ADR 0008: pin `supabase==2.11.0` là "version đã chạy thật" — nhưng
nó **chưa từng chạy với loại key mới**.

## Quyết định

Nâng `supabase==2.11.0` → `supabase==2.31.0` (mới nhất tại thời điểm này).
2.31.0 bỏ ràng buộc key-phải-là-JWT ở `create_client`, chấp nhận `sb_secret_`.

Không lùi về key JWT `service_role` cũ (phương án B đã cân nhắc): key `sb_secret_`
là hướng có chủ đích của ADR 0010; lùi về key cũ chỉ để chiều một client lỗi thời
là đi ngược, và Supabase sẽ khai tử key JWT cũ dần.

## Kiểm chứng (không suy đoán từ `import`)

Theo nguyên tắc ADR 0008 — nâng version là thay đổi riêng, phải có chu kỳ chạy
thật xác nhận:

1. **API surface app dùng còn nguyên.** Test `create_client(url, key)` +
   `.table("articles").upsert([row], on_conflict="url", ignore_duplicates=True)
   .execute()` trên đúng một `url` đã tồn tại → ON CONFLICT DO NOTHING, trả 0
   dòng, không sửa dữ liệu. (Không dùng lệnh ghi thật để test — ADR/hardening-plan.)
2. **Không xung đột dep.** Rebuild image: `httpx==0.28.1` và `google-genai==2.7.0`
   giữ nguyên; họ supabase (postgrest/realtime/storage3/auth) đồng bộ 2.31.0.
3. **Chu kỳ xanh trọn vẹn trong cluster.** Pod chạy image mới, đọc `sb_secret_`
   từ K8s Secret: NewsAPI + Google RSS + Gemini ×4 → `201 Created` ghi 4 dòng
   Supabase → Discord 4/4 (`204`, token `<REDACTED>`) → `Chu ky hoan tat. Thoat 0`,
   `exitCode=0 reason=Completed`. Đây là bằng chứng quyết định cho phương án A.

**Chưa chụp được**: một Job tạo *từ chính CronJob* chạy tới `Completions 1/1`.
Lần thử ngay sau đó bị chặn bởi yếu tố **ngoài code**: key Gemini chạm giới hạn
free tier 20 request/ngày (`429 RESOURCE_EXHAUSTED`,
`GenerateRequestsPerDayPerProjectPerModel-FreeTier`, `quotaValue: 20`) sau nhiều
chu kỳ chạy thật trong ngày. Pipeline vẫn *degrade* đúng (Gemini là enrichment,
retry rồi trả fallback) nhưng bò chậm vì backoff ~60s/lần, có nguy cơ chạm
`activeDeadlineSeconds`. Cơ chế CronJob→Job đã được kiểm ở tầng spec + qua lần
Job `manual-verify` *trước khi vá* (chạy tới bước storage rồi Failed đúng exit
code); phần app end-to-end đã xanh qua pod standalone ở điểm 3. Việc chụp
`Completions 1/1` để lại cho ngày quota reset.

## Hệ quả

- Storage (critical) hết lỗi, pipeline đi hết vòng trong K8s.
- Nợ kỹ thuật #7 (disable legacy JWT API keys) giờ **an toàn để làm**: app đã chạy
  xanh bằng `sb_secret_`, không còn phụ thuộc key JWT cũ.
- Bài học lặp lại: "đã chạy thật ở local" chỉ đúng cho *tổ hợp* đã chạy. Đổi một
  biến (loại key) là một tổ hợp mới, cần một chu kỳ thật mới.
