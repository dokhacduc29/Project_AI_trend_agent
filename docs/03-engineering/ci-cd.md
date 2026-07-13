# CI/CD — GitHub Actions + GHCR + Kubernetes

> Tham chiếu: [ADR 0013](../../knowledge/decisions/0013-ci-cd-github-actions.md).
> Workflow: [`.github/workflows/ci-cd.yml`](../../.github/workflows/ci-cd.yml).

## Pipeline làm gì

```
push/PR main  ->  test (pytest)  ->  build-scan-push
                                      ├─ build image (1 lần)
                                      ├─ smoke: import closure
                                      ├─ smoke: config-guard exit 78
                                      ├─ Trivy quét CVE (fail nếu fixable HIGH/CRITICAL)
                                      └─ push GHCR (CHỈ khi push main)
```

- **PR** → chạy test + build + smoke + scan, **không** push image.
- **Push `main`** → như trên + push `ghcr.io/dokhacduc29/project_ai_trend_agent`
  với tag `:latest` và `:sha-<short>`.
- Deploy lên cluster **không tự động** (xem mục cuối).

## 1. Secrets & permissions cho pipeline

Bước **push GHCR** dùng `GITHUB_TOKEN` tự động của Actions — **không cần thêm
secret nào**. Workflow đã khai `permissions: packages: write`.

> Test và smoke test **không cần** API key thật (test độc lập mạng; smoke chạy
> với key rỗng để kiểm exit code). Chỉ khi nào bạn muốn CI chạy pipeline THẬT
> (gọi NewsAPI/Gemini/Supabase/Discord) thì mới cần thêm các secret dưới đây vào
> **Settings → Secrets and variables → Actions**:
>
> `NEWS_API_KEY`, `GEMINI_API_KEY`, `SUPABASE_URL`, `SUPABASE_KEY`,
> `DISCORD_WEBHOOK_URL`

## 2. Bật GHCR & kéo image private về cluster

Sau lần push `main` đầu tiên, package xuất hiện ở
`github.com/dokhacduc29?tab=packages`. Mặc định **private**. Cluster cần
credential để kéo.

### 2a. Tạo Personal Access Token (classic)

GitHub → Settings → Developer settings → Personal access tokens → Tokens
(classic) → Generate new token. Scope tối thiểu: **`read:packages`**.

> PAT là secret — không commit, không dán vào file trong repo.

### 2b. Tạo secret `regcred` trong namespace

PowerShell (Windows). Thay `<PAT>` bằng token vừa tạo:

```powershell
kubectl create secret docker-registry regcred `
  --docker-server=ghcr.io `
  --docker-username=dokhacduc29 `
  --docker-password=<PAT> `
  --docker-email=dokhacduc123321213@gmail.com `
  --namespace=ai-trend-agent
```

Manifest `k8s/03-deployment.yaml` đã tham chiếu `imagePullSecrets: [regcred]`.

> Muốn khỏi tạo regcred: đổi package sang **public** (trang package → Package
> settings → Change visibility), rồi bỏ khối `imagePullSecrets` trong manifest.

## 3. Deploy thủ công lên cluster

Runner GitHub (cloud) **không** với tới Docker Desktop local của bạn, nên deploy
là thao tác tay sau khi image đã lên GHCR:

```powershell
# 1. Kéo image mới nhất về node local (tùy chọn — IfNotPresent sẽ tự kéo khi chạy)
docker pull ghcr.io/dokhacduc29/project_ai_trend_agent:latest

# 2. Apply lại manifest (namespace/config/secret đã có từ session trước)
kubectl apply -f k8s/03-deployment.yaml

# 3. Bỏ suspend nếu CronJob đang treo
kubectl patch cronjob ai-trend-agent -n ai-trend-agent -p '{\"spec\":{\"suspend\":false}}'

# 4. Chạy thử một job ngay, không đợi lịch 4h
kubectl create job --from=cronjob/ai-trend-agent manual-test -n ai-trend-agent
kubectl get pods -n ai-trend-agent -w
```

> Pin phiên bản tất định: thay `:latest` trong manifest bằng `:sha-<short>` của
> commit muốn deploy (xem tag trong package GHCR).

## 4. Tự động hoá deploy (hướng mở rộng)

Muốn CI tự deploy lên cluster local cần **self-hosted runner** đặt trong cùng
mạng cluster (Settings → Actions → Runners → New self-hosted runner), rồi thêm
job `deploy` với `runs-on: self-hosted` chạy `kubectl apply`. Chưa làm ở vòng
này vì vượt phạm vi và cần máy chạy runner thường trực.
