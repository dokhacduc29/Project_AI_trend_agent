"""
=====================================================================
PORTS — Hợp đồng giữa Application và thế giới bên ngoài (SRS mục 8.2)
=====================================================================
VẤN ĐỀ ĐANG SỬA (SRS P4):
    Tới v4.0, dự án đặt tên thư mục theo Clean Architecture nhưng KHÔNG có
    interface nào: `main.py` import thẳng `supabase_storage` (concrete), và
    agent tự gọi `os.getenv` để dựng client bên trong. Kết quả là chiều phụ
    thuộc trỏ RA NGOÀI — "Clean Architecture" chỉ tồn tại ở tên thư mục.

    Hệ quả đo được: `ScraperAgent` 215 dòng không có nổi một test, vì không
    có chỗ nào để thay phụ thuộc bằng bản giả.

GIẢI PHÁP:
    Application tuyên bố nó CẦN GÌ (file này). Infrastructure lo LÀM BẰNG GÌ
    (Supabase, Postgres, hay một dict trong bộ nhớ khi test). Chiều phụ thuộc
    quay vào trong.

VÌ SAO DÙNG `Protocol` MÀ KHÔNG PHẢI `ABC`:
    - `ABC` là nominal typing: lớp hiện thực PHẢI kế thừa. Nghĩa là
      infrastructure buộc phải import application.
    - `Protocol` là structural typing (PEP 544): chỉ cần có đúng method với
      đúng chữ ký là đủ. Infrastructure không cần import gì từ đây, coupling
      bằng 0. Test viết một class thường vài dòng là thay được.

    Đánh đổi phải nói rõ: thiếu method thì KHÔNG nổ lúc khởi tạo như `ABC`,
    mà nổ lúc gọi. Bù lại repo đã có `pyrightconfig.json` — sai lệch bị bắt ở
    tầng phân tích tĩnh, trước khi chạy.

Iron Laws: L03 async-first, L08 type hints + docstring.
=====================================================================
"""
from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Generic, Protocol, TypeVar

from ai_trend_agent.domain.models import Article, RunStatus, RunTrigger, Sentiment, TrendReport

T = TypeVar("T")


@dataclass(frozen=True)
class Page(Generic[T]):
    """
    Một trang kết quả, kèm đủ thông tin để client biết còn trang nào nữa không.

    Cố ý KHÔNG phụ thuộc Pydantic hay FastAPI: đây là khái niệm của tầng
    application, phải dùng được cả ở worker lẫn ở test không có HTTP.
    Việc chuyển sang JSON là chuyện của `api/schemas.py`.
    """

    items: list[T]
    total_items: int
    page: int
    size: int

    @property
    def total_pages(self) -> int:
        """Số trang, làm tròn LÊN. Không có bản ghi nào thì vẫn tính là 0 trang."""
        if self.size <= 0:
            return 0
        return -(-self.total_items // self.size)  # ceil bằng số nguyên, tránh float

    @property
    def has_next(self) -> bool:
        return self.page < self.total_pages

    @property
    def has_prev(self) -> bool:
        return self.page > 1


class ArticleSort(str, Enum):
    """
    Cách sắp xếp hợp lệ cho danh sách bài viết (FR-01).

    Quy ước dấu trừ nghĩa là giảm dần — giống cú pháp `ordering` của
    Django REST Framework, quen thuộc với người dùng API.

    Kế thừa `str` để giá trị enum dùng trực tiếp được trong query string và
    trong OpenAPI schema mà không cần chuyển đổi.

    CHƯA CÓ `date` / `-date` Ở v5.0. SRS bản 1.0 có liệt kê hai lựa chọn này,
    nhưng cột `date` đang trộn ba định dạng (xem giải thích dài ở
    `ArticleFilters`) nên sắp xếp theo nó cho ra thứ tự vô nghĩa. Thà thiếu
    một lựa chọn còn hơn ghi trong OpenAPI rằng nó chạy rồi trả về rác.
    Sẽ bổ sung ở B3 sau khi có cột `published_at` sạch.
    """

    CREATED_AT_ASC = "created_at"
    CREATED_AT_DESC = "-created_at"

    @property
    def column(self) -> str:
        """Tên cột trong DB, đã bỏ dấu trừ."""
        return self.value.lstrip("-")

    @property
    def descending(self) -> bool:
        """True nếu sắp xếp giảm dần."""
        return self.value.startswith("-")


@dataclass(frozen=True)
class ArticleFilters:
    """
    Điều kiện lọc + phân trang cho `list_paginated` (FR-01).

    Gom vào một object thay vì truyền 7 tham số rời: thêm bộ lọc mới sau này
    không phải sửa chữ ký của protocol và mọi lớp hiện thực nó.

    `frozen=True` vì đây là object mô tả một truy vấn — không ai được sửa nó
    giữa chừng sau khi đã dựng xong.

    ─────────────────────────────────────────────────────────────────────────
    QUAN TRỌNG — `date_from` / `date_to` HIỆN LỌC THEO `created_at`,
    KHÔNG PHẢI CỘT `date`.

    Lý do: khảo sát 178 bản ghi thật (2026-08-28) cho thấy cột `date` kiểu
    `text` đang trộn ba định dạng:
        92 bản ghi  "Wed, 15 Jul 2026"  (RFC 822 — RSS đẩy thẳng pubDate)
        76 bản ghi  "2026-08-26"        (ISO — NewsAPI cắt publishedAt[:10])
        10 bản ghi  "N/A"               (fallback khi parse hỏng)

    Cột `text` so sánh theo thứ tự chữ cái, nên `"Wed, 15 Jul 2026"` LỚN HƠN
    `"2026-08-01"` (vì 'W' > '2'). Hệ quả: mọi bản ghi RFC 822 luôn khớp bất
    kỳ bộ lọc `date_from` nào — lọc và sắp xếp theo `date` đều cho kết quả sai.

    Đây là lỗi dữ liệu có sẵn từ pipeline v4.0 (SRS P14), không phải do tầng
    API sinh ra. `created_at` là `timestamptz` do Postgres tự sinh nên sạch
    100% — dùng tạm cột này để bộ lọc CHẠY ĐÚNG, thay vì chạy sai âm thầm.

    Kế hoạch dứt điểm ở B3: thêm cột `published_at date`, chuẩn hoá scraper
    về ISO, backfill 178 bản ghi cũ, rồi chuyển bộ lọc sang `published_at`.
    Tên tham số API giữ nguyên `date_from`/`date_to` nên hợp đồng không vỡ.
    ─────────────────────────────────────────────────────────────────────────
    """

    page: int = 1
    size: int = 20
    topic: str | None = None
    sentiment: Sentiment | None = None
    date_from: date | None = None
    date_to: date | None = None
    sort: ArticleSort = ArticleSort.CREATED_AT_DESC

    @property
    def offset(self) -> int:
        """Số bản ghi bỏ qua. Trang 1 → offset 0."""
        return (self.page - 1) * self.size


class ArticleRepository(Protocol):
    """
    Hợp đồng truy cập kho bài viết.

    Bản hiện thực thật dùng Supabase (`infrastructure/supabase_repository.py`).
    Test dùng bản in-memory — chỉ cần một class có đúng ba method này, không
    phải kế thừa gì.

    GHI CHÚ PHẠM VI: chưa có `save_many` ở đây. Đường ghi hiện vẫn do
    `SupabaseStorageAgent` đảm nhiệm trong pipeline v4.0 và ràng buộc C-04
    cấm làm hỏng pipeline đang chạy. Khi worker được chuyển sang dùng
    repository, `save_many` sẽ gia nhập protocol này. Cố ý không khai báo
    trước một method chưa ai hiện thực.
    """

    async def list_paginated(self, filters: ArticleFilters) -> Page[Article]:
        """Trả về một trang bài viết khớp bộ lọc, kèm tổng số bản ghi."""
        ...

    async def get_by_id(self, article_id: int) -> Article | None:
        """Trả về bài viết theo id, hoặc `None` nếu không có. KHÔNG raise."""
        ...

    async def ping(self) -> None:
        """
        Kiểm tra kho dữ liệu có phản hồi không — phục vụ readiness probe (FR-07).

        Trả về bình thường nghĩa là khỏe; hỏng thì raise. Cố ý không trả bool:
        thông điệp lỗi của exception chính là thứ cần đưa vào response 503.
        """
        ...


class RunRepository(Protocol):
    """
    Hợp đồng ghi lại lịch sử các lần chạy pipeline (FR-04 → FR-06).

    Ba method ở đây là ĐƯỜNG GHI, đủ cho worker ghi nhật ký chu kỳ của mình.
    Các method ĐỌC (`get`, `list_paginated`, `latest_with_trend`, `has_active`)
    sẽ gia nhập khi làm router `/runs` và `/trends/latest` — giữ nguyên tắc
    không khai báo method chưa ai hiện thực.

    LƯU Ý VỀ TÍNH CHỊU LỖI: mọi lời gọi ở đây là ENRICHMENT theo phân loại của
    ADR 0003. Ghi nhật ký hỏng thì log rồi đi tiếp — tuyệt đối không được làm
    chết chu kỳ thu thập dữ liệu. Mất một dòng nhật ký còn hơn mất cả mẻ tin.
    """

    async def create(self, *, topic: str, trigger: RunTrigger) -> str:
        """Tạo bản ghi run mới, trả về `run_id` (UUID dạng chuỗi)."""
        ...

    async def mark_running(self, run_id: str) -> None:
        """Chuyển sang `running` và đóng dấu `started_at`."""
        ...

    async def finish(
        self,
        run_id: str,
        *,
        status: RunStatus,
        articles_scraped: int | None = None,
        articles_stored: int | None = None,
        trend_report: TrendReport | None = None,
        error: str | None = None,
    ) -> None:
        """Kết thúc run: ghi trạng thái cuối, số liệu, báo cáo xu hướng, lỗi nếu có."""
        ...
