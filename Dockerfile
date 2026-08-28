# =====================================================================
# Dockerfile — AI Trend Agent v4.0
# Multi-stage build: giảm image size, tách build vs runtime deps
# =====================================================================

# ──────────────────────────────────────────────
# STAGE 1: Builder — cài dependencies vào /install
# ──────────────────────────────────────────────
FROM python:3.13-slim AS builder

WORKDIR /build

# Cai DEPENDENCY truoc, tach khoi source: doi code khong lam mat cache layer nay.
# requirements-runtime.txt = nguon su that DUY NHAT cho deps cua image.
# Dev-only libs (pytest, dashboard) nam o requirements.txt va khong vao day.
COPY Backend/requirements-runtime.txt .

# --no-cache-dir: khong luu pip cache vao image
# --prefix: cai vao /install thay vi system site-packages
RUN pip install --no-cache-dir --prefix=/install -r requirements-runtime.txt

# Cai CHINH PACKAGE (src-layout, khai bao o pyproject.toml). --no-deps vi deps
# da cai o layer tren. Sau buoc nay `ai_trend_agent` nam trong site-packages va
# console script `ai-trend-worker` co trong /install/bin -> runtime khong con
# can PYTHONPATH tro vao tung thu muc layer nhu ban cu.
COPY pyproject.toml README.md ./
COPY Backend/src ./Backend/src
RUN pip install --no-cache-dir --prefix=/install --no-deps .


# ──────────────────────────────────────────────
# STAGE 2: Runtime — image cuối chỉ chứa những gì cần thiết
# ──────────────────────────────────────────────
FROM python:3.13-slim AS runtime

# Vá CVE OS của base image ngay lúc build. Base python:3.13-slim đọng lại
# util-linux cũ (CVE-2026-53612..53615, HIGH, đã có bản vá) cho tới khi Docker Hub
# rebuild base — Trivy chặn HIGH/CRITICAL có bản vá. apt upgrade để không phụ thuộc
# lịch rebuild của base. Xoá apt lists để không phình image.
RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

# Metadata
LABEL maintainer="dokhacduc29" \
      version="5.0.0" \
      description="AI Trend Agent - automated AI news pipeline"

# Tạo non-root user để chạy app (security best practice)
RUN addgroup --system appgroup && \
    adduser --system --ingroup appgroup --no-create-home appuser

WORKDIR /app

# Copy installed packages từ builder stage
COPY --from=builder /install /usr/local

# Vá CVE package Python của base image + gỡ pip khỏi runtime.
#
# (1) setuptools 70.3.0 (ship kèm python:3.13-slim) dính CVE-2025-47273 (HIGH, path
#     traversal PackageIndex). Đây là gói CÀI THẬT (dist-info) nên nâng lên bản có vá.
#
# (2) msgpack==1.1.2 + setuptools==70.3.0 KHÔNG hề được cài — chúng chỉ là bản
#     pip VENDORED (pip/_vendor/vendor.txt + bom.cdx.json). Trivy đọc 2 manifest đó
#     của pip và báo HIGH (GHSA-6v7p-g79w-8964, CVE-2025-47273) dù gói cài thật đã vá
#     (msgpack 1.2.1, setuptools 84.0.0). Job one-shot này không cần pip lúc chạy →
#     gỡ hẳn pip: diệt false-positive TẬN GỐC (không suppress) + giảm attack surface.
#     Giữ lại setuptools 84.0.0 để pkg_resources còn dùng được cho các lib runtime.
RUN pip install --no-cache-dir --upgrade "setuptools>=78.1.1" \
    && SP="$(python -c 'import site; print(site.getsitepackages()[0])')" \
    && rm -rf "${SP}/pip" "${SP}"/pip-*.dist-info /usr/local/bin/pip* \
    && ! python -c "import pip" 2>/dev/null \
    && echo "pip removed from runtime image"

# KHONG con COPY source vao /app: package da duoc CAI vao site-packages o
# builder stage. /app chi con la thu muc lam viec cho data runtime.

# Tạo thư mục data với quyền ghi cho appuser (AI cache + CSV fallback)
RUN mkdir -p /app/data && chown appuser:appgroup /app/data

# ──────────────────────────────────────────────
# Environment Variables (non-secret defaults)
# Secrets (API keys) được inject qua K8s Secret hoặc --env-file
# ──────────────────────────────────────────────
# Khong con PYTHONPATH: package duoc CAI chuan vao site-packages nen Python tu
# tim thay. Ban cu phai tro PYTHONPATH vao tung thu muc layer vi ten thu muc co
# dau cham (ai_trend_agent.Domain) khong phai package Python hop le.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TOPIC="Artificial Intelligence"

# Chạy với non-root user
USER appuser

# [ADR 0011] KHÔNG có HEALTHCHECK.
# Container này là job one-shot (chạy 1 chu kỳ rồi thoát), không phải service.
# HEALTHCHECK cũ chỉ kiểm tra một file tồn tại — luôn PASS kể cả khi event loop
# treo, nên là tín hiệu giả. Với job ngắn, "sống/chết" do exit code quyết định,
# và K8s CronJob dùng activeDeadlineSeconds + backoffLimit thay cho probe.

# Entry point: console script sinh boi pyproject.toml [project.scripts].
CMD ["ai-trend-worker"]
