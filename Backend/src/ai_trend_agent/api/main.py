"""
=====================================================================
FASTAPI APP — Tầng REST API của AI Trend Agent (v5.0, SRS mục 6)
=====================================================================
VÌ SAO CÓ TẦNG NÀY?
    Tới v4.0, hệ thống chỉ là một job chạy theo lịch: CronJob gọi worker,
    worker cào tin rồi ghi Supabase rồi thoát. Dữ liệu nằm im trong DB,
    không ai truy vấn được nếu không mở thẳng Supabase console.

    Tầng API biến nó từ "script chạy theo lịch" thành "service truy vấn được".

QUAN HỆ VỚI WORKER:
    api/main.py và worker/main.py là HAI CỬA VÀO của cùng một lõi. Cả hai
    dùng chung domain + application, không nhân bản logic pipeline.

ĐƯỜNG DẪN:
    /api/v1/...  — tài nguyên nghiệp vụ, CÓ đánh version vì hợp đồng với
                   client có thể đổi.
    /health      — probe hạ tầng, KHÔNG đánh version: K8s gọi theo quy ước,
                   và nó không phải hợp đồng nghiệp vụ.
    /docs        — Swagger UI (FR-08).

Iron Laws: L03 async-first, L05 FastAPI, L08 type hints + docstring.
=====================================================================
"""
from fastapi import FastAPI

from ai_trend_agent import __version__
from ai_trend_agent.api.errors import install_error_handlers
from ai_trend_agent.api.routers import articles, health, trends

# Mô tả hiển thị ngay đầu trang /docs — coi như trang bìa của API.
_DESCRIPTION = """
REST API phục vụ dữ liệu tin tức AI do pipeline ETL thu thập.

**Nguồn dữ liệu**: NewsAPI, TechCrunch AI (RSS), Google News (RSS) — cào song song,
làm sạch bằng regex + Gemini, chấm cảm xúc, tổng hợp xu hướng, lưu PostgreSQL.

Xem thêm: [repo trên GitHub](https://github.com/dokhacduc29/Project_AI_trend_agent)
"""

# Nhóm endpoint trong Swagger cho dễ đọc, thay vì một danh sách phẳng.
_TAGS_METADATA = [
    {"name": "articles", "description": "Truy vấn bài viết đã thu thập — phân trang và lọc."},
    {"name": "trends", "description": "Báo cáo xu hướng do AI tổng hợp mỗi chu kỳ."},
    {"name": "health", "description": "Probe hạ tầng cho Kubernetes (liveness / readiness)."},
]

app = FastAPI(
    title="AI Trend Agent API",
    description=_DESCRIPTION,
    version=__version__,
    openapi_tags=_TAGS_METADATA,
    docs_url="/docs",
    redoc_url=None,       # Chỉ giữ Swagger; ReDoc không thêm giá trị ở dự án này.
    openapi_url="/openapi.json",
)

# [FR-09] Gắn handler RFC 7807 TRƯỚC khi khai báo router, để mọi lỗi — kể cả
# 404 do không khớp route nào — đều ra cùng một hình dạng. Nếu bỏ bước này,
# client gặp ba định dạng lỗi khác nhau tuỳ loại: HTTPException, lỗi
# validation của Pydantic, và HTML 500 của Starlette.
install_error_handlers(app)

# Tài nguyên nghiệp vụ nằm dưới /api/v1 (prefix khai trong chính router).
app.include_router(articles.router)
app.include_router(trends.router)

# Health nằm ở GỐC (không có /api/v1) — xem giải thích ở docstring đầu file.
app.include_router(health.router)


def run() -> None:
    """
    Điểm vào console script `ai-trend-api` (khai báo ở pyproject.toml).

    Import uvicorn ngay trong hàm, không ở đầu module: worker (CronJob) import
    package này để dùng chung code nhưng KHÔNG cần server ASGI. Để import ở
    top-level thì worker phải nạp uvicorn một cách vô ích mỗi lần khởi động.

    Host mặc định 0.0.0.0 vì trong container phải nghe trên mọi interface thì
    K8s Service mới định tuyến vào được; 127.0.0.1 sẽ chỉ nghe trong pod.
    """
    import os

    import uvicorn

    uvicorn.run(
        "ai_trend_agent.api.main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", "8080")),
        reload=os.getenv("API_RELOAD", "").lower() in ("1", "true", "yes"),
    )
