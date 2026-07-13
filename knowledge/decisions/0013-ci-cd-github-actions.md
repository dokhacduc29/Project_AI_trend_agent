# ADR 0013 — CI/CD bằng GitHub Actions (test → build → smoke → scan → push GHCR)

- **Ngày**: 2026-07-13
- **Trạng thái**: Accepted
- **Phase**: CI/CD (mục roadmap cuối cùng)

## Bối cảnh

App đã đóng gói Docker multi-stage (ADR 0008) và chạy dưới CronJob one-shot
trên Kubernetes (ADR 0011), nhưng image vẫn `build` tay ở local với
`imagePullPolicy: Never`. Không có pipeline tự động: mỗi lần đổi code phải nhớ
build đúng, không ai kiểm test/CVE trước khi deploy. Roadmap còn treo đúng một
mục: "CI/CD: GitHub Actions pipeline".

## Quyết định

Thêm `.github/workflows/ci-cd.yml` với hai job nối tiếp:

1. **test** — `pytest` chạy trên runner. Image production **không** chứa
   `ai_trend_agent.Tests/` (đã loại trong `.dockerignore`), nên test phải chạy
   ở tầng CI, không phải trong image. `test_agents.py` tự inject `sys.path` →
   không cần `PYTHONPATH` hay secret; toàn bộ test độc lập mạng.

2. **build-scan-push** (`needs: test`) — build image **đúng một lần**
   (`load: true` vào docker của runner), rồi tái dùng cùng image đó cho mọi
   bước sau (không build lại, không lệch image):
   - **Smoke 1 — import closure**: `docker run` import mọi module runtime
     (`scrapers, cleaner, ai_agent, trend_agent, supabase_storage,
     discord_agent, gemini_client, config`). Bắt thiếu dependency / lệch
     version ngay ở image thật, không đợi tới runtime cluster.
   - **Smoke 2 — config-guard exits 78**: chạy entrypoint thật với
     `NEWS_API_KEY` rỗng; `main.py` phải thoát `78` (EXIT_CONFIG_ERROR) trước
     khi chạm mạng. Chứng minh wiring dotenv + config-guard + exit code (ADR
     0011) hoạt động, không cần secret, tất định.
   - **Trivy scan**: `ignore-unfixed: true`, `severity: HIGH,CRITICAL`,
     `exit-code: 1` — chỉ **fail khi CVE có bản vá**. CVE base-image chưa có
     fix không chặn pipeline; lỗi báo ra là lỗi *actionable*.
   - **Push GHCR**: chỉ khi `push` lên `main` (PR chỉ build/smoke/scan, không
     push). Tag `:latest` + `:sha-<short>`. Dùng `GITHUB_TOKEN` +
     `permissions: packages: write`, không cần PAT cho bước push.

Tên image phải **lowercase** cho GHCR (`github.repository` giữ chữ HOA
`Project_AI_trend_agent`) → hạ chữ bằng `${GITHUB_REPOSITORY,,}`.

Manifest `k8s/03-deployment.yaml`: `image` → `ghcr.io/dokhacduc29/
project_ai_trend_agent:latest`, `imagePullPolicy: Never` → `IfNotPresent`,
thêm `imagePullSecrets: [regcred]` (GHCR package để **private**).

## Hệ quả

- **Tích cực**: mỗi push lên `main` được test + quét CVE + đóng image tất định
  trước khi có thể deploy. PR được kiểm mà không đẩy rác lên registry. Exit
  code 78 giờ là bất biến được CI canh giữ, không chỉ verify tay một lần.
- **Tiêu cực / giới hạn**:
  - **Không auto-deploy lên cluster**: runner cloud không với tới Docker
    Desktop local. `kubectl apply` là **thủ công** (xem
    `docs/03-engineering/ci-cd.md`). Muốn deploy tự động cần self-hosted runner
    trong mạng của cluster — hoãn lại.
  - User phải tự thêm GitHub Secrets cho pipeline **nếu** sau này CI cần chạy
    pipeline thật (hiện test + smoke KHÔNG cần secret). Kéo image private về
    cluster cần `regcred` tạo từ PAT (`read:packages`).
- **Tương thích ngược**: build local cũ vẫn chạy được (`docker build`); chỉ
  manifest đổi nguồn image. Muốn quay lại local: đổi `image` + `Never` và bỏ
  `imagePullSecrets`.

## Phương án đã loại

- **Chỉ CI (không push registry)**: nhẹ hơn nhưng không đạt mục tiêu "deploy
  sát thực tế" — image vẫn kẹt ở local.
- **Auto-deploy từ runner cloud**: bất khả với cluster local không expose ra
  ngoài; giả lập bước này sẽ là deploy "dối".
- **GHCR public**: bỏ được `regcred` nhưng phơi image ra công khai; chọn
  private + regcred để sát môi trường doanh nghiệp (và để học tạo regcred).
- **Trivy report-only (`exit-code 0`)**: scan không gác cổng thật; chọn fail
  trên CVE fixable để pipeline có răng.
- **Build hai lần (build-push-action với `push:true` riêng)**: tốn thời gian
  và có nguy cơ scan một image khác image được push; chọn build một lần rồi
  `docker tag` + `push`.
