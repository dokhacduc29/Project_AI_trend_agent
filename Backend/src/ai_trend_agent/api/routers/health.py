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
from fastapi import APIRouter
from pydantic import BaseModel, Field

from ai_trend_agent import __version__

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

    Cố ý KHÔNG chạm tới database hay bất kỳ dịch vụ ngoài nào: mục đích duy nhất
    là phân biệt "tiến trình treo/chết" với "tiến trình sống". Phải trả lời rất
    nhanh (NFR: dưới 50ms) vì probe gọi lặp lại liên tục.
    """
    return LivenessResponse(status="ok", version=__version__)
