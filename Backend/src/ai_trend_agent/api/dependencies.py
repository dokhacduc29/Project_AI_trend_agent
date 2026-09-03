"""
=====================================================================
DEPENDENCIES — Nối dây phụ thuộc cho tầng API (SRS mục 8.2)
=====================================================================
ĐÂY LÀ CHỖ DUY NHẤT BIẾT "AI HIỆN THỰC PORT NÀO".

Router chỉ khai báo nó CẦN một `ArticleRepository`. File này quyết định thứ
được đưa vào là `SupabaseArticleRepository`. Đổi sang Postgres thuần hay bản
in-memory chỉ phải sửa đúng một hàm ở đây — router không biết và không cần biết.

VÌ SAO SINGLETON:
    `create_client()` của supabase-py dựng một HTTP client mới mỗi lần gọi.
    Tạo theo từng request là phí kết nối, và với free tier còn có nguy cơ cạn
    connection pool khi có nhiều request đồng thời. Repository không giữ trạng
    thái riêng cho từng request nên dùng chung một bản là an toàn.

VÌ SAO VẪN TEST ĐƯỢC DÙ LÀ SINGLETON:
    FastAPI cho phép `app.dependency_overrides[get_article_repository] = ...`
    — override chặn TRƯỚC khi hàm chạy, nên `lru_cache` bên trong không cản
    trở gì. Test tiêm một class vài dòng thoả mãn Protocol là chạy được, không
    cần mạng, không cần Supabase.

    Đây chính là thứ v4.0 thiếu (SRS P3): agent tự gọi `os.getenv` dựng client
    bên trong nên không có chỗ nào để thay phụ thuộc — hệ quả là `ScraperAgent`
    215 dòng không có nổi một test.

Iron Laws: L08 type hints + docstring.
=====================================================================
"""
import logging
import os
import secrets
from functools import lru_cache
from typing import Annotated

from fastapi import Depends, Header
from supabase import Client, create_client

from ai_trend_agent.api.errors import UnauthorizedProblem
from ai_trend_agent.application.ports import ArticleRepository, RunRepository
from ai_trend_agent.infrastructure.supabase_repository import SupabaseArticleRepository
from ai_trend_agent.infrastructure.supabase_run_repository import SupabaseRunRepository

_logger = logging.getLogger("ai_trend_agent.api.dependencies")


@lru_cache(maxsize=1)
def _supabase_client() -> Client:
    """
    MỘT client Supabase dùng chung cho mọi repository trong tiến trình API.

    Ban đầu mỗi repository tự dựng client riêng. Đo được hậu quả: request đầu
    tiên chạm `RunRepository` mất **1151ms** trong khi các lần sau chỉ 353ms —
    vì client thứ hai phải bắt tay TLS lại từ đầu, dù đã có một client khỏe
    mạnh nói chuyện với đúng project đó.

    Dùng chung một client: chỉ trả giá khởi tạo MỘT lần, và `/health/ready`
    (gọi trước khi K8s đẩy traffic vào pod) hâm nóng sẵn cho mọi endpoint.
    Thêm một lợi ích trên free tier: một connection pool thay vì hai.

    Vẫn dựng LƯỜI — import module hay khởi động app đều không cần credential.
    Thiếu biến môi trường chỉ lộ ra ở request thật, và `/health/ready` báo 503
    đúng như thiết kế.
    """
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise ValueError("Thiếu SUPABASE_URL hoặc SUPABASE_KEY")
    return create_client(url, key)


@lru_cache(maxsize=1)
def _article_repository_singleton() -> SupabaseArticleRepository:
    """Repository bài viết, dùng chung client với các repository khác."""
    return SupabaseArticleRepository(_supabase_client())


def get_article_repository() -> ArticleRepository:
    """
    Provider cho router. Kiểu trả về là PORT (`ArticleRepository`), không phải
    lớp cụ thể — để router phụ thuộc vào trừu tượng, đúng nguyên tắc DIP.
    """
    return _article_repository_singleton()


# Alias dùng ở chữ ký router: `repo: ArticleRepositoryDep`.
# Cách viết `Annotated` này là kiểu FastAPI hiện đại, thay cho
# `repo: ArticleRepository = Depends(get_article_repository)`. Ưu điểm: khai
# báo một lần dùng nhiều nơi, và không đặt giá trị mặc định có thể gọi được
# vào tham số hàm — thứ khiến hàm khó test khi gọi trực tiếp ngoài FastAPI.
ArticleRepositoryDep = Annotated[ArticleRepository, Depends(get_article_repository)]


@lru_cache(maxsize=1)
def _run_repository_singleton() -> SupabaseRunRepository:
    """Repository nhật ký chạy, dùng CHUNG client với repository bài viết."""
    return SupabaseRunRepository(_supabase_client())


def get_run_repository() -> RunRepository:
    """Provider cho router. Kiểu trả về là PORT, không phải lớp cụ thể."""
    return _run_repository_singleton()


RunRepositoryDep = Annotated[RunRepository, Depends(get_run_repository)]


def require_api_key(x_api_key: Annotated[str | None, Header()] = None) -> None:
    """
    Chặn endpoint GHI bằng API key tĩnh (FR-04 AC-04.3).

    Vì sao chỉ endpoint ghi: các endpoint đọc chỉ phơi tin tức công khai, còn
    `POST /runs` kích hoạt một chu kỳ tiêu hạn mức Gemini (ràng buộc C-03) —
    không khoá thì bất kỳ ai cũng đốt sạch quota của dự án.

    FAIL CLOSED khi chưa cấu hình: `API_KEY` không được đặt thì MỌI request đều
    bị từ chối. Chọn ngược lại (không cấu hình thì cho qua) là cái bẫy kinh
    điển — deploy quên đặt biến là endpoint mở toang mà không ai hay.

    Thông điệp lỗi giống nhau cho cả hai trường hợp "thiếu key" và "sai key":
    nói rõ "server chưa cấu hình" là tiết lộ trạng thái hệ thống cho người lạ.

    So sánh bằng `compare_digest` chứ không phải `==`: `==` thoát ra ngay tại
    ký tự đầu khác nhau nên thời gian chạy tiết lộ độ dài tiền tố đúng. Với
    endpoint có thể gọi lặp, đó là kênh rò rỉ thật.

    [SRS 2.3] v5.0 cố ý chỉ dùng key tĩnh; OAuth2/JWT/RBAC nằm ngoài phạm vi.
    """
    expected = os.getenv("API_KEY", "")
    if not expected:
        _logger.error(
            "API_KEY chua duoc cau hinh — tu choi moi request ghi (fail closed)."
        )
        raise UnauthorizedProblem()
    if not x_api_key or not secrets.compare_digest(x_api_key, expected):
        raise UnauthorizedProblem()


RequireApiKey = Depends(require_api_key)
