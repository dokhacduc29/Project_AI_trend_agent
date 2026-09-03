"""
=====================================================================
ERRORS — Problem Details theo RFC 7807 (SRS FR-09)
=====================================================================
VẤN ĐỀ NẾU KHÔNG CÓ FILE NÀY:
    FastAPI mặc định trả `{"detail": "..."}` cho HTTPException, nhưng lỗi
    validation lại trả một mảng lồng nhau hình dạng khác hẳn, còn lỗi không
    bắt được thì trả HTML 500 của Starlette. Ba hình dạng cho ba loại lỗi —
    client phải viết ba nhánh xử lý và vẫn không chắc đã đủ.

GIẢI PHÁP — RFC 7807 "Problem Details for HTTP APIs":
    Mọi lỗi, không trừ loại nào, trả về CÙNG một cấu trúc:

        type      URI định danh LOẠI lỗi — ổn định, client so khớp được
        title     tóm tắt ngắn, giống nhau ở mọi lần xảy ra cùng loại
        status    mã HTTP
        detail    mô tả riêng cho LẦN xảy ra này
        instance  đường dẫn phát sinh lỗi
        errors    (chỉ 422) liệt kê từng trường sai

    Client viết MỘT hàm xử lý lỗi cho toàn API.

    Content-Type là `application/problem+json` chứ không phải
    `application/json` — chuẩn quy định vậy, và nó giúp middleware/proxy
    phân biệt được response lỗi mà không cần đọc body.

BẢO MẬT — VÌ SAO HANDLER 500 KHÔNG NÓI GÌ CỤ THỂ (AC-09.2):
    Exception thật trong dự án này thường mang thông tin hạ tầng. Ví dụ lỗi
    kết nối Supabase chứa nguyên hostname của project; lỗi thư viện có thể
    chứa đường dẫn file trên server. Đẩy `str(exc)` ra response là rò rỉ.

    Nên: client nhận một câu chung chung, còn chi tiết + traceback đi vào
    LOG phía server. Log đã được che secret sẵn (ADR 0009), nên webhook và
    API key không lọt ra ngay cả trong log.

Iron Laws: L02 logging only, L07 fault tolerance, L08 type hints + docstring.
=====================================================================
"""
import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

_logger = logging.getLogger("ai_trend_agent.api.errors")

# Tiền tố URI cho trường `type`. Không cần phân giải được thành trang web —
# RFC 7807 chỉ yêu cầu nó là ĐỊNH DANH ổn định. Đặt dạng URL để sau này nếu
# muốn viết tài liệu cho từng loại lỗi thì có sẵn chỗ trỏ tới.
PROBLEM_TYPE_BASE = "https://api.aitrendagent.dev/errors"

# Chuẩn quy định content-type riêng cho response lỗi.
PROBLEM_CONTENT_TYPE = "application/problem+json"


class FieldError(BaseModel):
    """Một trường sai trong lỗi validation (422)."""

    field: str = Field(description="Tên trường bị sai, dạng đường dẫn nếu lồng nhau")
    message: str = Field(description="Sai ở chỗ nào, mô tả cho người đọc")
    received: Any | None = Field(default=None, description="Giá trị client đã gửi")


class ProblemDetail(BaseModel):
    """
    Hình dạng response lỗi. Khai báo thành model để OpenAPI **tài liệu hoá
    được cả lỗi**, không chỉ tài liệu hoá đường thành công — client biết
    trước sẽ nhận gì khi hỏng.
    """

    type: str = Field(description="URI định danh loại lỗi")
    title: str = Field(description="Tóm tắt ngắn, không đổi giữa các lần xảy ra")
    status: int = Field(description="Mã HTTP")
    detail: str = Field(description="Mô tả cụ thể cho lần xảy ra này")
    instance: str = Field(description="Đường dẫn phát sinh lỗi")
    errors: list[FieldError] | None = Field(
        default=None, description="Chỉ có ở lỗi 422 — liệt kê từng trường sai"
    )


class ProblemException(Exception):
    """
    Exception mà router chủ động ném ra khi biết rõ mình sai ở đâu.

    Dùng cái này thay vì `HTTPException` của FastAPI, để nơi ném lỗi mô tả
    được đầy đủ `type` và `title` — hai trường mà `HTTPException` không có
    chỗ chứa.
    """

    def __init__(
        self,
        *,
        status: int,
        title: str,
        detail: str,
        type_slug: str,
        errors: list[FieldError] | None = None,
    ) -> None:
        super().__init__(detail)
        self.status = status
        self.title = title
        self.detail = detail
        self.type_slug = type_slug
        self.errors = errors


class NotFoundProblem(ProblemException):
    """404 — tài nguyên không tồn tại (FR-02 AC-02.2, FR-03 AC-03.2)."""

    def __init__(self, detail: str, *, title: str = "Resource not found") -> None:
        super().__init__(status=404, title=title, detail=detail, type_slug="not-found")


class ConflictProblem(ProblemException):
    """409 — trạng thái hiện tại không cho phép thao tác (FR-04 AC-04.4)."""

    def __init__(self, detail: str, *, title: str = "Conflict") -> None:
        super().__init__(status=409, title=title, detail=detail, type_slug="conflict")


class UnauthorizedProblem(ProblemException):
    """401 — thiếu hoặc sai API key ở endpoint ghi (FR-04 AC-04.3)."""

    def __init__(self, detail: str = "Thiếu hoặc sai API key") -> None:
        super().__init__(
            status=401, title="Unauthorized", detail=detail, type_slug="unauthorized"
        )


def _problem_response(
    *,
    status: int,
    title: str,
    detail: str,
    instance: str,
    type_slug: str,
    errors: list[FieldError] | None = None,
) -> JSONResponse:
    """Dựng response RFC 7807. Mọi handler bên dưới đều đi qua đây — một chỗ duy nhất."""
    body: dict[str, Any] = {
        "type": f"{PROBLEM_TYPE_BASE}/{type_slug}",
        "title": title,
        "status": status,
        "detail": detail,
        "instance": instance,
    }
    if errors:
        body["errors"] = [e.model_dump() for e in errors]
    return JSONResponse(status_code=status, content=body, media_type=PROBLEM_CONTENT_TYPE)


# Nhãn tiếng Việt cho vài mã HTTP hay gặp, để `title` không phải lúc nào cũng
# là chuỗi máy móc. Mã không có trong đây thì dùng nhãn mặc định của HTTP.
_TITLE_BY_STATUS: dict[int, str] = {
    400: "Bad request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Resource not found",
    405: "Method not allowed",
    409: "Conflict",
    429: "Too many requests",
}

_SLUG_BY_STATUS: dict[int, str] = {
    400: "bad-request",
    401: "unauthorized",
    403: "forbidden",
    404: "not-found",
    405: "method-not-allowed",
    409: "conflict",
    429: "rate-limit",
}


def install_error_handlers(app: FastAPI) -> None:
    """
    Gắn bốn handler vào app. Gọi một lần lúc dựng app.

    Thứ tự khai báo không quan trọng — Starlette chọn handler theo KIỂU
    exception, không theo thứ tự đăng ký.
    """

    @app.exception_handler(ProblemException)
    async def _handle_problem(request: Request, exc: ProblemException) -> JSONResponse:
        """Lỗi do router chủ động ném — đã có sẵn đủ thông tin."""
        return _problem_response(
            status=exc.status,
            title=exc.title,
            detail=exc.detail,
            instance=request.url.path,
            type_slug=exc.type_slug,
            errors=exc.errors,
        )

    @app.exception_handler(StarletteHTTPException)
    async def _handle_http(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        """
        Lỗi do CHÍNH FRAMEWORK sinh ra: 404 khi không khớp route nào, 405 khi
        sai method... Bắt luôn để những lỗi này cũng cùng hình dạng — nếu
        không, client vẫn gặp `{"detail": ...}` ở các đường không ngờ tới.
        """
        return _problem_response(
            status=exc.status_code,
            title=_TITLE_BY_STATUS.get(exc.status_code, "HTTP error"),
            detail=str(exc.detail),
            instance=request.url.path,
            type_slug=_SLUG_BY_STATUS.get(exc.status_code, "http-error"),
        )

    @app.exception_handler(RequestValidationError)
    async def _handle_validation(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """
        422 — tham số hoặc body không hợp lệ (FR-09 AC-09.1).

        Pydantic trả lỗi dạng lồng nhau với `loc` là tuple kiểu
        `("query", "size")`. Ở đây làm phẳng thành chuỗi `"size"` để client
        biết ngay trường nào sai mà không phải hiểu cấu trúc nội bộ.
        Bỏ phần tử đầu ("query"/"body"/"path") vì nó chỉ nói vị trí kỹ thuật.
        """
        errors = [
            FieldError(
                field=".".join(str(p) for p in err.get("loc", [])[1:]) or "body",
                message=err.get("msg", "giá trị không hợp lệ"),
                received=err.get("input"),
            )
            for err in exc.errors()
        ]
        return _problem_response(
            status=422,
            title="Validation failed",
            detail="Dữ liệu gửi lên không hợp lệ",
            instance=request.url.path,
            type_slug="validation",
            errors=errors,
        )

    @app.exception_handler(Exception)
    async def _handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
        """
        500 — mọi lỗi không lường trước.

        [AC-09.2] KHÔNG đưa `str(exc)` vào response. Exception thật hay mang
        thông tin hạ tầng: lỗi kết nối Supabase chứa hostname của project,
        lỗi thư viện chứa đường dẫn file trên server. Client chỉ cần biết
        "phía tôi hỏng", còn chi tiết là việc của người vận hành.

        `exc_info=True` để traceback đầy đủ đi vào log. Log đã được che secret
        (ADR 0009) nên webhook/API key không lọt ra ngay cả ở đó.
        """
        _logger.error(
            "Loi khong luong truoc tai %s %s", request.method, request.url.path, exc_info=True
        )
        return _problem_response(
            status=500,
            title="Internal server error",
            detail="Đã xảy ra lỗi phía máy chủ. Vui lòng thử lại sau.",
            instance=request.url.path,
            type_slug="internal",
        )
