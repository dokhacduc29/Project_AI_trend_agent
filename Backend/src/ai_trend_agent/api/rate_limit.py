"""
=====================================================================
RATE LIMIT — Chặn lạm dụng ở tầng API (Luật Thép L05)
=====================================================================
L05 đòi API phải có phân trang VÀ rate limit. Phân trang xong từ B2; đây là
nửa còn lại, và tới trước file này nó vẫn còn thiếu.

VÌ SAO CẦN, DÙ ĐÃ CÓ API KEY:
    API key chỉ khoá `POST /runs`. Toàn bộ đường ĐỌC mở công khai, và
    `?page=999999&size=100` là một truy vấn offset sâu miễn phí — lặp lại đủ
    nhanh thì Supabase free tier chịu trước, không phải người gọi.

    Ngay cả đường ghi cũng cần: `has_active()` chặn được chu kỳ THỨ HAI chạy
    song song, nhưng không chặn được ai đó bắn 1000 request/giây để dò key.

HAI MỨC:
    Đọc 60/phút — DÙNG CHUNG cho mọi endpoint đọc, tính theo IP.
    Ghi  6/phút — riêng `POST /runs`, vì mỗi lần gọi tiêu một suất hạn mức
                  Gemini (ràng buộc C-03).

    Đường đọc dùng `shared_limit` chứ không phải `limit` cho từng route. Nếu
    mỗi endpoint một bộ đếm riêng thì hạn mức thật là 60 NHÂN số endpoint —
    một con số chẳng ai chủ ý cho phép, và nó lặng lẽ tăng lên mỗi lần thêm
    endpoint mới. Một xô dùng chung thì "60 lượt đọc mỗi phút" nghĩa đúng như
    nó nói.

─────────────────────────────────────────────────────────────────────────
KHÔNG DÙNG `SlowAPIMiddleware` — ĐÃ THỬ, NÓ IM LẶNG KHÔNG LÀM GÌ CẢ.

Cách "chuẩn" của slowapi là `default_limits` + `SlowAPIMiddleware`, áp hạn mức
cho mọi route mà không phải sửa endpoint nào. Đã dựng đúng như vậy, và đo
được: bắn 199 request liên tiếp vào `/api/v1/articles`, KHÔNG CÓ request nào
bị chặn.

Nguyên nhân: middleware của slowapi tìm hàm xử lý bằng cách duyệt `app.routes`
rồi lấy `route.endpoint`. FastAPI 0.141 không còn trải phẳng router con vào
`app.routes` nữa — nó bọc chúng trong `_IncludedRouter`, và đối tượng đó KHÔNG
có thuộc tính `endpoint`. `_find_route_handler` trả `None`, `_should_exempt`
thấy `None` thì trả `True`, và middleware coi MỌI route là được miễn trừ.

Không exception, không warning. Log sạch, `/docs` vẫn hiện, hạn mức vẫn nằm
trong cấu hình — chỉ là không bao giờ chạy. Đúng loại lỗi tệ nhất: chạy được,
sai âm thầm, không ai biết.

Nên ở đây gắn hạn mức bằng DECORATOR trên từng endpoint. Đường decorator nhận
thẳng hàm xử lý nên không phụ thuộc việc dò route, và đã kiểm chứng là chạy.
Đổi lại: thêm endpoint mới mà quên decorator thì endpoint đó không có hạn mức
— im lặng theo chiều ngược lại, nên phải nhớ.

HAI THAM SỐ BẮT BUỘC TRÊN MỌI ENDPOINT ĐƯỢC GẮN HẠN MỨC:
    `request: Request`   — slowapi tìm theo TÊN để lấy IP người gọi.
    `response: Response` — khi endpoint trả về model Pydantic (không phải
                           `Response`), slowapi nhét `X-RateLimit-*` vào
                           `kwargs["response"]`. Thiếu tham số này thì nó gọi
                           `_inject_headers(None, ...)` và endpoint trả 500 ở
                           ĐƯỜNG THÀNH CÔNG. Đã dính một lần khi dựng.
─────────────────────────────────────────────────────────────────────────

/health VÀ /health/ready CỐ Ý KHÔNG CÓ HẠN MỨC:
    Probe của Kubernetes gọi hai endpoint đó vài giây một lần, và mọi probe
    tới từ CÙNG một IP (node). Đếm chúng vào hạn mức thì đủ lâu sẽ có probe ăn
    429; K8s coi 429 là probe trượt, đánh dấu pod chưa sẵn sàng rồi cắt
    traffic — rate limit tự tay gây ra đúng sự cố nó sinh ra để ngăn.

    Không decorator = không hạn mức, nên hai endpoint đó chỉ việc không gắn.

GIỚI HẠN THẬT, NÓI TRƯỚC CHO KHỎI TƯỞNG BỞ:
    Bộ đếm nằm TRONG BỘ NHỚ tiến trình. Nhiều replica thì mỗi pod đếm riêng,
    hạn mức thực tế nhân theo số pod; pod restart thì bộ đếm về 0. v5.0 chạy
    đúng một replica nên chấp nhận được. Muốn đúng khi scale ngang thì trỏ
    `storage_uri` sang Redis — đổi một tham số, không đổi kiến trúc.

    Khoá theo IP của peer trực tiếp. Sau ingress/proxy thì đó là IP của proxy,
    tức mọi client dùng chung một xô. Muốn đúng phải đọc `X-Forwarded-For` VÀ
    chỉ tin nó khi proxy nằm trong danh sách tin cậy — tin vô điều kiện thì ai
    cũng giả mạo được IP để né hạn mức.

Iron Laws: L05 rate limit, L08 type hints + docstring, L09 no magic numbers.
=====================================================================
"""
import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from ai_trend_agent.api.errors import build_problem_response
from ai_trend_agent.domain import config

_logger = logging.getLogger("ai_trend_agent.api.rate_limit")

# Tên xô dùng chung cho mọi endpoint ĐỌC. Đặt hằng thay vì gõ chuỗi ở từng
# router — gõ sai một ký tự là endpoint đó lặng lẽ có xô riêng (Luật L09).
READ_SCOPE = "api-read"

# Cố ý KHÔNG khai `default_limits` và `application_limits`: cả hai chỉ có tác
# dụng qua `SlowAPIMiddleware`, thứ không chạy được với FastAPI 0.141 (xem
# docstring đầu file). Để lại cấu hình chết trông như đang bảo vệ cái gì đó
# còn tệ hơn là không có gì.
limiter = Limiter(
    key_func=get_remote_address,
    key_style="endpoint",
    headers_enabled=True,
)

# Alias để router đọc ra Ý ĐỊNH thay vì đọc ra cú pháp thư viện.
read_limit = limiter.shared_limit(config.RATE_LIMIT_READ, scope=READ_SCOPE)
write_limit = limiter.limit(config.RATE_LIMIT_WRITE)


def install_rate_limit(app: FastAPI) -> None:
    """
    Gắn handler 429 vào app. Gọi một lần lúc dựng app.

    CHỈ gắn handler, KHÔNG gắn middleware — hạn mức nằm ở decorator trên từng
    endpoint (lý do dài ở docstring đầu file).
    """
    # slowapi đọc limiter qua `app.state.limiter` trong handler mặc định của
    # nó. Ta thay handler đó, nhưng vẫn đặt để không phụ thuộc vào việc thư
    # viện có đường dự phòng nào khác dùng tới nó hay không.
    app.state.limiter = limiter

    @app.exception_handler(RateLimitExceeded)
    async def _handle_rate_limit(request: Request, exc: RateLimitExceeded) -> JSONResponse:
        """
        429 theo RFC 7807, không theo hình dạng mặc định của slowapi.

        Handler mặc định trả `{"error": "Rate limit exceeded: 60 per 1 minute"}`
        — đúng một hình dạng nữa cho client phải xử lý riêng, trong khi FR-09
        vừa mất công gom mọi lỗi về cùng một khuôn. Ở đây dựng lại bằng chính
        `build_problem_response` mà các handler khác dùng.

        `_inject_headers` là của slowapi: nó gắn `Retry-After` và bộ
        `X-RateLimit-*`. Không có `Retry-After` thì client chỉ biết mình bị
        chặn chứ không biết chờ bao lâu, và cách duy nhất để dò là thử lại —
        đúng thứ ta đang muốn ngăn.
        """
        _logger.warning(
            "Rate limit: %s %s tu %s (han muc %s)",
            request.method,
            request.url.path,
            get_remote_address(request),
            exc.detail,
        )
        response = build_problem_response(
            status=429,
            title="Too many requests",
            detail=f"Vượt hạn mức {exc.detail}. Vui lòng thử lại sau.",
            instance=request.url.path,
            type_slug="rate-limit",
        )
        return limiter._inject_headers(response, request.state.view_rate_limit)
