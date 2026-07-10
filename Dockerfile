# =====================================================================
# Dockerfile — AI Trend Agent v4.0
# Multi-stage build: giảm image size, tách build vs runtime deps
# =====================================================================

# ──────────────────────────────────────────────
# STAGE 1: Builder — cài dependencies vào /install
# ──────────────────────────────────────────────
FROM python:3.13-slim AS builder

WORKDIR /install

# Chỉ copy requirements trước để tận dụng Docker layer cache
# requirements-runtime.txt = nguồn sự thật DUY NHẤT cho deps của image.
# Dev-only libs (pytest, dashboard) nằm ở requirements.txt và không vào đây.
COPY Backend/requirements-runtime.txt .

# --no-cache-dir: không lưu pip cache vào image
# --prefix: cài vào /install thay vì system site-packages
RUN pip install --no-cache-dir --prefix=/install -r requirements-runtime.txt


# ──────────────────────────────────────────────
# STAGE 2: Runtime — image cuối chỉ chứa những gì cần thiết
# ──────────────────────────────────────────────
FROM python:3.13-slim AS runtime

# Metadata
LABEL maintainer="dokhacduc29" \
      version="4.0.0" \
      description="AI Trend Agent - automated AI news pipeline"

# Tạo non-root user để chạy app (security best practice)
RUN addgroup --system appgroup && \
    adduser --system --ingroup appgroup --no-create-home appuser

WORKDIR /app

# Copy installed packages từ builder stage
COPY --from=builder /install /usr/local

# Copy source code (chỉ cần Backend/)
COPY --chown=appuser:appgroup Backend/ .

# Tạo thư mục data với quyền ghi cho appuser (AI cache + CSV fallback)
RUN mkdir -p /app/data && chown appuser:appgroup /app/data

# ──────────────────────────────────────────────
# Environment Variables (non-secret defaults)
# Secrets (API keys) được inject qua K8s Secret hoặc --env-file
# ──────────────────────────────────────────────
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app:/app/ai_trend_agent.Domain:/app/ai_trend_agent.Application:/app/ai_trend_agent.Infrastructure \
    TOPIC="Artificial Intelligence"

# Chạy với non-root user
USER appuser

# Healthcheck — kiểm tra process còn sống
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import os; exit(0 if os.path.exists('/app/ai_trend_agent.WebApi/main.py') else 1)"

# Entry point: chạy app
CMD ["python", "ai_trend_agent.WebApi/main.py"]
