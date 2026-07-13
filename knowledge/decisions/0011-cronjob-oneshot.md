# ADR 0011 — Deployment + `while True` → CronJob + app one-shot

- **Ngày**: 2026-07-13
- **Trạng thái**: Accepted
- **Phase**: Hardening (Session 2 — deploy)

## Bối cảnh

Pipeline là một ETL chạy theo chu kỳ 4 giờ. Cách cũ hiện thực việc "theo chu kỳ"
bằng `while True: run_pipeline(); await asyncio.sleep(4h)` bên trong `main.py`,
đóng gói thành `Deployment` với `replicas: 1` và `restartPolicy: Always`.

Mô hình này sai ở ba điểm:

1. **K8s không bao giờ biết một chu kỳ thành công hay thất bại.** Pod sống mãi;
   exit code — thứ K8s dùng để phân biệt Succeeded/Failed — không bao giờ lọt ra.
   Chu kỳ chết giữa chừng chỉ là một dòng log, `Deployment` vẫn `Running`, dashboard
   vẫn xanh. Đây chính là hệ quả của nợ kỹ thuật #1 (main.py thoát exit 0).

2. **`livenessProbe` là giả.** Nó chỉ kiểm tra `main.py` có tồn tại trên đĩa —
   luôn đúng, kể cả khi event loop treo. Một probe không bao giờ fail thì không
   phải probe.

3. **Không có trần thời gian.** Một lời gọi mạng treo (không timeout ở tầng nào)
   giữ pod sống vô hạn, `concurrencyPolicy` không tồn tại nên chu kỳ sau vẫn có thể
   chồng lên chu kỳ trước, phá vỡ giả định "1 chu kỳ tại một thời điểm" mà dedupe
   `UNIQUE(url)` và budget Gemini đều dựa vào.

## Quyết định

**Chuyển trách nhiệm lên lịch từ app sang orchestrator.**

- `main.py`: bỏ `while True`. Chạy **đúng một chu kỳ** rồi thoát. `run_pipeline`
  trả `bool` — `True` nếu đi hết pipeline, `False` nếu một agent CRITICAL lỗi.
  `main()` map giá trị đó thành exit code:
  - hoàn tất → `EXIT_OK` (0)
  - agent critical lỗi → `EXIT_PIPELINE_ERROR` (1)
  - thiếu config bắt buộc → `EXIT_CONFIG_ERROR` (78, đã có từ Session 1)

- `k8s/03-deployment.yaml`: `Deployment` → `CronJob`.
  - `schedule: "0 */4 * * *"` — khớp `config.SCHEDULE_INTERVAL_HOURS=4`. Đây giờ
    là nguồn sự thật DUY NHẤT của lịch; app không còn tự lên lịch.
  - `concurrencyPolicy: Forbid` — chu kỳ trước chưa xong thì bỏ qua chu kỳ mới.
  - `activeDeadlineSeconds: 600` — job tự chết sau 10 phút. Đây là cái THAY THẾ
    `livenessProbe` giả: với job vài chục giây, "sống/chết" do exit code và trần
    thời gian quyết định, không phải probe định kỳ.
  - `backoffLimit: 2` — lỗi thì thử lại 2 lần rồi đánh dấu Job Failed.
  - `restartPolicy: OnFailure` — bắt buộc cho Job (`Always` bị cấm).
  - `startingDeadlineSeconds: 300`, `successfulJobsHistoryLimit: 3`,
    `failedJobsHistoryLimit: 1`.

- `Dockerfile`: bỏ `HEALTHCHECK` giả. Container one-shot không cần healthcheck;
  "khỏe" nghĩa là thoát 0 đúng hạn.

## Hệ quả

- Exit code giờ có nghĩa với K8s. Chu kỳ chết = Job Failed = kích `backoffLimit`,
  không còn "xanh giả".
- Chỉ chỉnh lịch ở một nơi (`schedule`), không phải sửa code + rebuild image.
- `SCHEDULE_INTERVAL_HOURS` trong `config.py` giữ lại làm tài liệu (giá trị phải
  khớp cron `schedule`), nhưng không còn điều khiển `asyncio.sleep`.

## Còn thừa lại, chưa xử lý

- **`k8s/04-service.yaml` giờ vô nghĩa.** Nó là một `Service` trỏ `targetPort:
  8080`, nhưng app KHÔNG mở cổng HTTP nào (nó là ETL, không phải web server) —
  Service này chết ngay cả dưới `Deployment` cũ. Pod của `CronJob` lại là ephemeral,
  không có gì cố định để route tới. Giữ lại theo luật *No delete* của workspace,
  nhưng cần quyết định: xoá hẳn hay chuyển sang `_archive/`. Apply nó chỉ tạo một
  ClusterIP không có endpoint — vô hại nhưng gây hiểu nhầm.
- **Tên file `03-deployment.yaml`** giờ chứa một `CronJob`, không phải `Deployment`.
  Giữ tên để không phá thứ tự apply `00→04`. Đổi tên là một thay đổi riêng.

## Kiểm chứng

- `docker run` image v4 không truyền key → thoát `78` (đường config-error còn nguyên).
- Không còn câu lệnh `while True:` thực thi trong `main.py` (chỉ còn trong comment).
- 18/18 unit test xanh sau thay đổi.
- Trên cluster (Docker Desktop Kubeadm): `kubectl apply` toàn bộ `k8s/`, trigger
  một Job thủ công từ CronJob, xem nó đạt `Completions 1/1` và `Succeeded` —
  chứng minh mô hình one-shot chạy thật, không chỉ đúng cú pháp YAML.
