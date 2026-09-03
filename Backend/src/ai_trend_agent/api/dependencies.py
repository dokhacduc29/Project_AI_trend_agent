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
from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from ai_trend_agent.application.ports import ArticleRepository
from ai_trend_agent.infrastructure.supabase_repository import SupabaseArticleRepository


@lru_cache(maxsize=1)
def _article_repository_singleton() -> SupabaseArticleRepository:
    """
    Dựng repository đúng một lần cho cả vòng đời tiến trình.

    Bản thân `SupabaseArticleRepository` dựng client LƯỜI (chỉ khi gọi truy vấn
    đầu tiên), nên hàm này không chạm mạng — import module hay khởi động app
    đều không cần sẵn credential. Thiếu biến môi trường chỉ lộ ra ở request
    thật, và lúc đó `/health/ready` sẽ báo 503 đúng như thiết kế.
    """
    return SupabaseArticleRepository()


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
