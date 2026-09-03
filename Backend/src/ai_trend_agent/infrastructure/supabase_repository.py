"""
=====================================================================
SUPABASE REPOSITORY — Hiện thực `ArticleRepository` (SRS mục 8.2)
=====================================================================
ĐÂY LÀ ADAPTER: nơi duy nhất trong hệ thống biết dữ liệu thật trông thế nào.

Tầng application chỉ nói "cho tôi một trang bài viết khớp bộ lọc này"
(`ArticleRepository`). File này lo phần bẩn: cột `sentiment` lưu tiếng Việt,
cột `tags` là chuỗi nối bằng dấu phẩy, `created_at` về dạng chuỗi ISO chứ
không phải `datetime`.

CHÚ Ý — LỚP NÀY KHÔNG KẾ THỪA `ArticleRepository`.
Đó là chủ ý: port khai bằng `Protocol` (structural typing) nên chỉ cần có
đúng method là thoả mãn. Nhờ vậy infrastructure không phải import application
— chiều phụ thuộc sạch, và pyright vẫn bắt được nếu chữ ký lệch.

VÌ SAO BỌC `asyncio.to_thread`:
Client supabase-py là ĐỒNG BỘ. Gọi thẳng trong `async def` sẽ chặn event
loop, khiến mọi request khác đứng chờ. Cùng cách xử lý với
`SupabaseStorageAgent` (ADR 0010).

Iron Laws: L03 async-first, L04 no SQL injection (query builder tham số hoá),
L07 fault tolerance, L08 type hints + docstring.
=====================================================================
"""
import asyncio
import os
from datetime import date, datetime, timedelta
from typing import Any

from supabase import Client, create_client

from ai_trend_agent.application.ports import ArticleFilters, Page
from ai_trend_agent.domain.models import Article, Sentiment

# Bảng nguồn. Đặt hằng thay vì rải chuỗi "articles" khắp file (Luật L09).
_TABLE = "articles"

# DB lưu `sentiment` bằng CHÍNH value tiếng Việt của enum (xem
# `SupabaseStorageAgent._article_to_row`). Bảng tra ngược để đọc lên.
# Dựng từ enum thay vì gõ tay, để đổi value trong domain không làm lệch chỗ này.
_SENTIMENT_BY_DB_VALUE: dict[str, Sentiment] = {s.value: s for s in Sentiment}


def _parse_tags(raw: str | None) -> list[str]:
    """
    `"#OpenAI, #Google"` → `["#OpenAI", "#Google"]`.

    Cột `tags` là TEXT nối bằng dấu phẩy chứ không phải mảng Postgres — đó là
    quyết định từ v4.0, giữ nguyên để không phải migrate. Chuỗi rỗng hoặc NULL
    trả về list rỗng, không phải `[""]`.
    """
    if not raw or not raw.strip():
        return []
    return [t.strip() for t in raw.split(",") if t.strip()]


def _parse_created_at(raw: str | None) -> datetime | None:
    """
    Chuỗi ISO của Postgres → `datetime`.

    Supabase trả `"2026-08-28T07:54:52.796107+00:00"`. `fromisoformat` của
    Python 3.11+ đọc được dạng này. Hỏng thì trả None thay vì raise — một
    bản ghi có timestamp lạ không đáng làm sập cả trang kết quả.
    """
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw)
    except (ValueError, TypeError):
        return None


def _row_to_article(row: dict[str, Any]) -> Article:
    """Một dòng DB → entity domain. Chỗ duy nhất biết tên cột thật."""
    return Article(
        title=row.get("title") or "",
        source=row.get("source") or "",
        date=row.get("date") or "",
        url=row.get("url") or "",
        tags=_parse_tags(row.get("tags")),
        summary=row.get("summary") or "",
        sentiment=_SENTIMENT_BY_DB_VALUE.get(row.get("sentiment") or "", Sentiment.NEUTRAL),
        id=row.get("id"),
        created_at=_parse_created_at(row.get("created_at")),
        topic=row.get("topic") or "",
    )


class SupabaseArticleRepository:
    """
    Đọc bài viết từ Supabase PostgreSQL.

    Chỉ ĐỌC. Đường ghi vẫn do `SupabaseStorageAgent` đảm nhiệm trong pipeline
    v4.0 — ràng buộc C-04 cấm làm hỏng thứ đang chạy. Khi worker được chuyển
    sang dùng repository thì `save_many` mới gia nhập.
    """

    def __init__(self, client: Client | None = None) -> None:
        """
        Nhận client qua tham số để test tiêm được bản giả — đây chính là thứ
        v4.0 thiếu (SRS P3): agent tự gọi `os.getenv` bên trong nên không có
        chỗ nào thay phụ thuộc.

        Không truyền gì thì mới tự dựng từ biến môi trường, và dựng LƯỜI
        (lazy) để import module này không bắt buộc phải có sẵn credential.
        """
        self._client = client

    def _get_client(self) -> Client:
        if self._client is None:
            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_KEY")
            if not url or not key:
                raise ValueError("Thiếu SUPABASE_URL hoặc SUPABASE_KEY")
            self._client = create_client(url, key)
        return self._client

    # ── Truy vấn đồng bộ (chạy trong thread riêng) ────────────────────────

    def _build_query(self, filters: ArticleFilters, *, for_count: bool = False):
        """
        Dựng query từ bộ lọc. Dùng chung cho cả lấy dữ liệu lẫn đếm.

        Mọi giá trị đi qua query builder của supabase-py (tham số hoá), không
        nối chuỗi SQL — Luật L04.
        """
        q = self._get_client().table(_TABLE).select("*", count="exact")

        if filters.topic:
            q = q.eq("topic", filters.topic)

        if filters.sentiment is not None:
            # Lọc bằng đúng chuỗi tiếng Việt mà DB đang lưu.
            q = q.eq("sentiment", filters.sentiment.value)
            # [P15] LOẠI bài chưa qua AI khỏi kết quả lọc theo sentiment.
            #
            # Bài chưa phân tích mang 'Trung lập' vì đó là GIÁ TRỊ MẶC ĐỊNH
            # của dataclass, không phải phán đoán của AI. Không loại thì
            # `?sentiment=neutral` trả về những bài mà API lại hiển thị
            # `sentiment: null` — response tự mâu thuẫn với bộ lọc vừa dùng.
            #
            # Dùng `summary` làm dấu hiệu "đã phân tích" vì DB chưa có cột
            # tường minh nào. Đây là suy luận gián tiếp; B3 nên thêm cột thật.
            q = q.neq("summary", "")

        # [P14] Lọc theo `created_at`, KHÔNG theo cột `date`.
        # Cột `date` trộn RFC 822 / ISO / "N/A" nên so sánh chuỗi cho kết quả
        # sai. `created_at` là timestamptz do Postgres sinh, sạch 100%.
        if filters.date_from is not None:
            q = q.gte("created_at", filters.date_from.isoformat())
        if filters.date_to is not None:
            # `date_to` là một NGÀY, người dùng mong nó bao trọn cả ngày đó.
            # `lte("created_at", "2026-08-28")` sẽ cắt mất mọi bài sau 00:00,
            # nên dùng `lt` với ngày kế tiếp.
            q = q.lt("created_at", (filters.date_to + timedelta(days=1)).isoformat())

        if not for_count:
            q = q.order(filters.sort.column, desc=filters.sort.descending)

            # ── KHOÁ PHỤ BẮT BUỘC: `id` ──────────────────────────────────
            # Không có dòng này thì phân trang VỪA TRÙNG VỪA SÓT bài.
            #
            # Đo trên dữ liệu thật: 196 bản ghi nhưng chỉ 23 giá trị
            # `created_at` khác nhau — vì mỗi chu kỳ pipeline ghi cả lô cùng
            # một timestamp (có nhóm 18 bản ghi trùng khít).
            #
            # SQL không đảm bảo thứ tự ổn định giữa các lần truy vấn khi khoá
            # sắp xếp có giá trị bằng nhau. Mỗi request phân trang là một truy
            # vấn RIÊNG, nên các dòng cùng timestamp có thể xáo lại giữa hai
            # lần gọi: một bản ghi lọt vào cả trang 1 lẫn trang 2, trong khi
            # bản ghi khác không xuất hiện ở trang nào.
            #
            # Đã tái hiện được: trang1=[231,232,233], trang2=[232,234,236].
            #
            # `id` là khoá chính nên duy nhất tuyệt đối → thứ tự trở thành
            # xác định. Cùng chiều với khoá chính để thứ tự đọc tự nhiên.
            q = q.order("id", desc=filters.sort.descending)

            # `range` của PostgREST bao gồm CẢ HAI đầu, nên trang 20 bản ghi
            # là range(offset, offset + size - 1) chứ không phải + size.
            start = filters.offset
            q = q.range(start, start + filters.size - 1)

        return q

    def _list_sync(self, filters: ArticleFilters) -> tuple[list[dict[str, Any]], int]:
        res = self._build_query(filters).execute()
        return (res.data or []), (res.count or 0)

    def _get_by_id_sync(self, article_id: int) -> dict[str, Any] | None:
        res = self._get_client().table(_TABLE).select("*").eq("id", article_id).limit(1).execute()
        rows = res.data or []
        return rows[0] if rows else None

    def _ping_sync(self) -> None:
        # Truy vấn nhẹ nhất có thể: lấy đúng một cột, đúng một dòng.
        self._get_client().table(_TABLE).select("id").limit(1).execute()

    # ── Giao diện async (đúng chữ ký của port) ────────────────────────────

    async def list_paginated(self, filters: ArticleFilters) -> Page[Article]:
        """Trả một trang bài viết khớp bộ lọc, kèm tổng số bản ghi (FR-01)."""
        rows, total = await asyncio.to_thread(self._list_sync, filters)
        return Page(
            items=[_row_to_article(r) for r in rows],
            total_items=total,
            page=filters.page,
            size=filters.size,
        )

    async def get_by_id(self, article_id: int) -> Article | None:
        """Một bài theo id, `None` nếu không có. Không raise (FR-02)."""
        row = await asyncio.to_thread(self._get_by_id_sync, article_id)
        return _row_to_article(row) if row else None

    async def ping(self) -> None:
        """Kiểm tra DB phản hồi được — phục vụ readiness probe (FR-07)."""
        await asyncio.to_thread(self._ping_sync)
