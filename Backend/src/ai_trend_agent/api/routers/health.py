"""
=====================================================================
HEALTH ROUTER — Liveness vs Readiness (FR-07)
=====================================================================
HAI ENDPOINT NÀY KHÁC NHAU VỀ BẢN CHẤT, KHÔNG PHẢI TRÙNG LẶP:

  /health        — LIVENESS: tiến trình còn sống không?
                   TUYỆT ĐỐI không kiểm tra dependency ngoài. Nếu kiểm tra
                   database ở đây, DB sập sẽ khiến K8s tưởng pod hỏng và
                   restart pod liên tục — trong khi lỗi nằm ở DB, restart
                   không sửa được gì, chỉ làm mất luôn pod đang khỏe.

  /health/ready  — READINESS: có sẵn sàng nhận request không?
                   Ở ĐÂY mới kiểm tra dependency. Trả 503 khi DB chết →
                   K8s ngừng đẩy traffic vào pod nhưng KHÔNG giết nó, chờ
                   DB hồi thì pod tự nhận traffic lại.

Iron Laws: L03 async, L08 type hints + docstring.
=====================================================================
"""
import logging
import time

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ai_trend_agent import __version__
from ai_trend_agent.api.dependencies import ArticleRepositoryDep

_logger = logging.getLogger("ai_trend_agent.api.health")

router = APIRouter(tags=["health"])


class LivenessResponse(BaseModel):
    """Kết quả kiểm tra liveness — chỉ nói lên tiến trình có đang chạy."""

    status: str = Field(description="Luôn là 'ok' nếu tiến trình phản hồi được")
    version: str = Field(description="Phiên bản package đang chạy")

    model_config = {
        "json_schema_extra": {
            "examples": [{"status": "ok", "version": "5.0.0"}]
        }
    }


@router.get(
    "/health",
    response_model=LivenessResponse,
    summary="Liveness probe",
    description=(
        "Trả 200 chừng nào tiến trình còn phản hồi được. **Không** kiểm tra "
        "database — xem `/health/ready` nếu cần biết service có phục vụ được không."
    ),
)
async def liveness() -> LivenessResponse:
    """
    Liveness probe cho Kubernetes.

    [L05] CỐ Ý KHÔNG gắn rate limit. Probe gọi vài giây một lần và mọi probe
    tới từ CÙNG một IP (node). Đếm chúng vào hạn mức thì sớm muộn có probe ăn
    429, K8s coi đó là probe trượt rồi restart pod — rate limit tự tay gây ra
    đúng sự cố nó sinh ra để ngăn.

    Cố ý KHÔNG chạm tới database hay bất kỳ dịch vụ ngoài nào: mục đích duy nhất
    là phân biệt "tiến trình treo/chết" với "tiến trình sống". Phải trả lời rất
    nhanh (NFR: dưới 50ms) vì probe gọi lặp lại liên tục.
    """
    return LivenessResponse(status="ok", version=__version__)


class CheckResult(BaseModel):
    """Kết quả kiểm tra MỘT dependency."""

    status: str = Field(description="'ok' hoặc 'error'")
    latency_ms: int | None = Field(default=None, description="Thời gian phản hồi, chỉ có khi ok")
    detail: str | None = Field(default=None, description="Mô tả lỗi, chỉ có khi error")


class ReadinessResponse(BaseModel):
    """Kết quả readiness — có sẵn sàng nhận traffic không."""

    status: str = Field(description="'ready' hoặc 'not_ready'")
    checks: dict[str, CheckResult] = Field(description="Kết quả từng dependency")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"status": "ready", "checks": {"database": {"status": "ok", "latency_ms": 42}}},
                {
                    "status": "not_ready",
                    "checks": {
                        "database": {"status": "error", "detail": "khong ket noi duoc kho du lieu"}
                    },
                },
            ]
        }
    }


@router.get(
    "/health/ready",
    response_model=ReadinessResponse,
    # Bỏ field null khỏi response: khi ok thì không có `detail`, khi lỗi thì
    # không có `latency_ms`. Người vận hành đọc lúc sự cố, càng ít nhiễu càng tốt.
    response_model_exclude_none=True,
    summary="Readiness probe",
    description=(
        "Trả 200 khi mọi dependency phản hồi được, **503** khi không. Kubernetes "
        "dùng kết quả này để quyết định có đẩy traffic vào pod hay không."
    ),
    responses={503: {"model": ReadinessResponse, "description": "Chưa sẵn sàng nhận traffic"}},
)
async def readiness(repo: ArticleRepositoryDep) -> ReadinessResponse | JSONResponse:
    """
    Readiness probe cho Kubernetes (FR-07).

    [L05] CỐ Ý KHÔNG gắn rate limit — cùng lý do với `/health`, và ở đây hậu
    quả còn nặng hơn: probe readiness trượt thì K8s cắt traffic khỏi pod khoẻ.

    KHÁC LIVENESS Ở CHỖ NÀO: ở đây MỚI được chạm dependency ngoài. DB chết thì
    trả 503 → K8s ngừng đẩy traffic vào pod nhưng KHÔNG giết pod. DB hồi thì pod
    tự nhận traffic lại, không cần restart.

    [AC-07.3] Không yêu cầu xác thực — probe của K8s không mang API key.

    ─────────────────────────────────────────────────────────────────────────
    VÌ SAO ENDPOINT NÀY KHÔNG DÙNG RFC 7807 DÙ FR-09 BẮT MỌI LỖI PHẢI THEO:

    Đây là ngoại lệ CÓ CHỦ Ý. Người tiêu thụ `/health/ready` là Kubernetes,
    và K8s chỉ đọc MÃ TRẠNG THÁI — nó không parse body. Phần body chỉ dành cho
    người vận hành đọc khi debug, nên hình dạng "từng dependency ra sao" hữu
    ích hơn hẳn hình dạng Problem Details.

    RFC 7807 sinh ra cho lỗi mà CLIENT của API phải xử lý; 503 ở đây không
    phải lỗi của người gọi mà là trạng thái của chính service.
    ─────────────────────────────────────────────────────────────────────────

    ⚠️ LƯU Ý KHI VIẾT MANIFEST K8S — ĐO ĐƯỢC, KHÔNG PHẢI PHỎNG ĐOÁN:
        Lần gọi ĐẦU TIÊN mất ~850ms vì repository dựng client lười: khởi tạo
        supabase-py + bắt tay TLS. Các lần sau ổn định ~105ms.

        `readinessProbe` của K8s mặc định `timeoutSeconds: 1`, nên probe đầu
        tiên ngay sau khi pod khởi động RẤT DỄ trượt. Manifest phải đặt
        `timeoutSeconds` rộng hơn (3s) và có `initialDelaySeconds`, nếu không
        pod sẽ bị đánh dấu chưa sẵn sàng dù hoàn toàn khỏe.
    """
    started = time.perf_counter()
    try:
        await repo.ping()
    except Exception as exc:
        # [Bảo mật] Không đưa `str(exc)` ra ngoài: lỗi kết nối Supabase chứa
        # nguyên hostname của project. Chi tiết vào log (đã che secret theo
        # ADR 0009), response chỉ nói chung chung — cùng nguyên tắc với
        # handler 500 ở api/errors.py.
        _logger.error("Readiness that bai: khong ket noi duoc kho du lieu", exc_info=True)
        body = ReadinessResponse(
            status="not_ready",
            checks={"database": CheckResult(status="error", detail="khong ket noi duoc kho du lieu")},
        )
        # `exclude_none` phải đặt tay ở đây: nhánh này trả JSONResponse trực
        # tiếp nên KHÔNG đi qua `response_model_exclude_none` của decorator.
        return JSONResponse(status_code=503, content=body.model_dump(exclude_none=True))

    latency_ms = int((time.perf_counter() - started) * 1000)
    return ReadinessResponse(
        status="ready",
        checks={"database": CheckResult(status="ok", latency_ms=latency_ms)},
    )
