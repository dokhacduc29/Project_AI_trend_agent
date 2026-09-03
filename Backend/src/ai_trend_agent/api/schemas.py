"""
=====================================================================
SCHEMAS — Hợp đồng dữ liệu công khai của API (SRS FR-01, FR-02)
=====================================================================
VÌ SAO KHÔNG TRẢ THẲNG `Article` (dataclass domain) RA JSON?

    Vì làm vậy là ghim cấu trúc NỘI BỘ vào hợp đồng CÔNG KHAI. Đổi tên một
    field trong domain là vỡ mọi client đang gọi API. Tầng schema là lớp đệm:
    domain được tự do tiến hoá, hợp đồng ngoài chỉ đổi khi ta cố ý đổi.

    Nó cũng là chỗ duy nhất biết cách dịch giữa hai thế giới:
      - domain lưu `Sentiment.BULLISH` có value tiếng Việt "Tích cực"
      - API công khai trả "bullish"
    Hợp đồng công khai không nên phụ thuộc ngôn ngữ nội bộ của hệ thống.

Iron Laws: L05 (pagination), L08 (type hints + docstring).
=====================================================================
"""
import re
from datetime import datetime
from enum import Enum
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

from ai_trend_agent.application.ports import Page
from ai_trend_agent.domain.models import Article, PipelineRun, Sentiment

T = TypeVar("T")


class SentimentOut(str, Enum):
    """
    Giá trị `sentiment` trong hợp đồng công khai.

    Domain dùng `Sentiment` với value tiếng Việt ("Tích cực"). Ở đây dùng
    thuật ngữ tiếng Anh thị trường quen thuộc — client quốc tế đọc được, và
    hợp đồng API không bị khoá vào ngôn ngữ nội bộ.
    """

    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"

    def to_domain(self) -> Sentiment:
        """
        Dịch ngược sang enum domain, dùng khi client LỌC theo sentiment.

        Chiều xuôi (domain → công khai) nằm ở `_SENTIMENT_MAP` bên dưới; chiều
        này cần cho `?sentiment=bullish` biến thành `Sentiment.BULLISH` rồi
        repository mới đổi tiếp thành chuỗi tiếng Việt mà DB đang lưu.
        """
        return _DOMAIN_BY_OUT[self]


# Ánh xạ domain -> công khai. Đặt tường minh thay vì suy từ tên enum, để đổi
# một bên không âm thầm kéo bên kia đổi theo.
_SENTIMENT_MAP: dict[Sentiment, SentimentOut] = {
    Sentiment.BULLISH: SentimentOut.BULLISH,
    Sentiment.BEARISH: SentimentOut.BEARISH,
    Sentiment.NEUTRAL: SentimentOut.NEUTRAL,
}

# Chiều ngược lại, dựng tự động từ bảng trên để hai chiều không bao giờ lệch nhau.
_DOMAIN_BY_OUT: dict[SentimentOut, Sentiment] = {v: k for k, v in _SENTIMENT_MAP.items()}


class ArticleOut(BaseModel):
    """
    Một bài viết như API phơi bày ra ngoài (FR-01, FR-02).

    ─────────────────────────────────────────────────────────────────────
    `summary` VÀ `sentiment` CÓ THỂ LÀ null — ĐÂY LÀ CHỦ Ý (SRS P15).

    Pipeline chặn số bài gửi AI ở `AI_MAX_ARTICLES_PER_BATCH` (hiện là 15).
    Chu kỳ nào cào về nhiều hơn thì phần dư vẫn được LƯU và ĐĂNG, nhưng
    chưa từng qua AI. Trong DB chúng có `summary = ''` và
    `sentiment = 'Trung lập'` — mà 'Trung lập' là **giá trị mặc định của
    dataclass**, không phải phán đoán của AI.

    Hậu quả nếu bê nguyên ra API: gọi `?sentiment=neutral` sẽ nhận cả những
    bài chưa từng được phân tích, và không cách nào phân biệt "trung lập vì
    AI thấy vậy" với "trung lập vì chưa ai xem". Cùng loại lỗi với P14:
    chạy được, trả sai, không ai biết.

    Nên ở đây: bài chưa phân tích trả `summary: null`, `sentiment: null`,
    `analyzed: false`. API thà nói "tôi không biết" còn hơn đoán bừa.
    ─────────────────────────────────────────────────────────────────────
    """

    id: int = Field(description="Khoá chính trong kho dữ liệu")
    title: str = Field(description="Tiêu đề bài viết")
    source: str = Field(description="Tên nguồn, ví dụ 'TechCrunch AI'")
    url: str = Field(description="Link gốc. Đây cũng là khoá chống trùng của hệ thống")
    date: str | None = Field(
        default=None,
        description=(
            "Ngày xuất bản do nguồn cung cấp, ở dạng thô. CẢNH BÁO: trường này "
            "hiện trộn nhiều định dạng (ISO, RFC 822, 'N/A') nên KHÔNG dùng để "
            "lọc hay sắp xếp — xem SRS P14. Dùng `created_at` cho việc đó."
        ),
    )
    created_at: datetime | None = Field(
        default=None, description="Thời điểm hệ thống thu thập bài (đáng tin, do DB sinh)"
    )
    topic: str | None = Field(default=None, description="Chủ đề của chu kỳ đã thu thập bài này")
    tags: list[str] = Field(default_factory=list, description="Nhãn thực thể, ví dụ ['#OpenAI']")

    analyzed: bool = Field(
        description=(
            "Bài đã qua bước phân tích AI chưa. False nghĩa là `summary` và "
            "`sentiment` đều null vì chưa ai phân tích, KHÔNG phải vì không có gì để nói."
        )
    )
    summary: str | None = Field(default=None, description="Tóm tắt do AI sinh. null nếu chưa phân tích")
    sentiment: SentimentOut | None = Field(
        default=None, description="Cảm xúc do AI chấm. null nếu chưa phân tích"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id": 224,
                    "title": "Google's AI Mode can now track flight prices",
                    "source": "TechCrunch AI",
                    "url": "https://techcrunch.com/2026/08/28/google-ai-mode",
                    "date": "2026-08-28",
                    "created_at": "2026-08-28T14:54:51Z",
                    "topic": "Artificial Intelligence",
                    "tags": ["#Google"],
                    "analyzed": True,
                    "summary": "Google's AI Mode tracks flights, books hotels.",
                    "sentiment": "bullish",
                },
                {
                    "id": 231,
                    "title": "Boomers Can't Stop Gifting Their Grandkids AI-Generated Slop",
                    "source": "Wired",
                    "url": "https://www.wired.com/story/ai-slop-gifts",
                    "date": "Wed, 27 Aug 2026",
                    "created_at": "2026-08-28T14:54:51Z",
                    "topic": "Artificial Intelligence",
                    "tags": ["#AI"],
                    "analyzed": False,
                    "summary": None,
                    "sentiment": None,
                },
            ]
        }
    )

    @classmethod
    def from_domain(cls, article: Article) -> "ArticleOut":
        """
        Dựng bản công khai từ entity domain.

        Cách xác định `analyzed`: dựa vào việc `summary` có nội dung hay không.
        Đây là SUY LUẬN GIÁN TIẾP, không phải sự thật được ghi lại — DB hiện
        không có cột nào đánh dấu "đã phân tích". Nó đúng trong thực tế vì
        `SummarizationAgent` luôn điền `summary` khi chạy thành công, nhưng
        vẫn là suy luận. B3 nên thêm cột tường minh rồi đọc thẳng từ đó.
        """
        analyzed = bool((article.summary or "").strip())
        return cls(
            id=article.id or 0,
            title=article.title,
            source=article.source,
            url=article.url,
            date=article.date or None,
            created_at=article.created_at,
            topic=article.topic or None,
            tags=list(article.tags),
            analyzed=analyzed,
            # Chưa phân tích thì KHÔNG trả sentiment mặc định ra ngoài —
            # đó là im lặng của hệ thống, không phải kết luận của AI.
            summary=article.summary if analyzed else None,
            sentiment=_SENTIMENT_MAP.get(article.sentiment) if analyzed else None,
        )


class TrendItemOut(BaseModel):
    """
    Một xu hướng trong báo cáo (FR-03).

    ─────────────────────────────────────────────────────────────────────────
    `article_count` CÓ THỂ null — và đây là giới hạn thật, không phải thiếu sót.

    Domain lưu mỗi xu hướng là một CHUỖI THUẦN, ví dụ:
        "Chính phủ áp đặt quy định về AI trong trường học. (4 bài)"

    Prompt chỉ *gợi ý* mô hình ghi số bài trong ngoặc — đó là chỉ dẫn văn phong
    cho LLM, không phải trường có cấu trúc. Mô hình có thể bỏ qua, đổi cách
    viết, hoặc trả về tiếng Anh.

    Nên ở đây bóc số theo kiểu best-effort; không bóc được thì trả null thay vì
    đoán một con số. Cùng nguyên tắc với P15: thà nói "không biết" còn hơn bịa.

    Cách sửa dứt điểm là bắt prompt trả JSON có cấu trúc `{title, count}`.
    SRS mục 2.3 xếp việc sửa prompt vào NGOÀI PHẠM VI v5.0, nên để lại cho sau.
    ─────────────────────────────────────────────────────────────────────────
    """

    title: str = Field(description="Nội dung xu hướng, đã bỏ phần đếm bài ở cuối")
    article_count: int | None = Field(
        default=None, description="Số bài liên quan, null nếu không bóc được từ văn bản"
    )


# "... (4 bài)" hoặc "... (4 articles)" ở CUỐI chuỗi. Neo `$` để không nuốt
# nhầm một con số nào đó nằm giữa câu.
_TREND_COUNT_RE = re.compile(r"\s*\((\d+)\s*(?:bài|bai|articles?)\)\s*$", re.IGNORECASE)


class TrendReportOut(BaseModel):
    """Báo cáo xu hướng của chu kỳ chạy thành công gần nhất (FR-03)."""

    run_id: str = Field(description="Lần chạy đã sinh ra báo cáo này")
    topic: str = Field(description="Chủ đề của chu kỳ")
    generated_at: datetime | None = Field(default=None, description="Thời điểm chu kỳ kết thúc")
    overall_sentiment: SentimentOut = Field(description="Tâm lý chung của thị trường")
    insight: str = Field(description="Nhận định tổng quan 1-2 câu")
    trends: list[TrendItemOut] = Field(description="Các xu hướng nổi bật")
    article_count: int | None = Field(
        default=None, description="Số bài đã dùng để rút ra báo cáo (số bài chu kỳ cào về)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "run_id": "6054fbc0-b673-4595-b430-ee270b5d26f2",
                    "topic": "Artificial Intelligence",
                    "generated_at": "2026-09-03T06:24:44Z",
                    "overall_sentiment": "neutral",
                    "insight": "Thị trường AI phát triển nhanh nhưng chịu giám sát chặt về an toàn và quy định.",
                    "trends": [
                        {"title": "Chính phủ áp đặt quy định về AI trong trường học.", "article_count": 4},
                        {"title": "AI tích hợp sâu vào các ngành công nghiệp.", "article_count": 3},
                    ],
                    "article_count": 18,
                }
            ]
        }
    )

    @classmethod
    def from_run(cls, run: PipelineRun) -> "TrendReportOut":
        """
        Dựng response từ một `PipelineRun` đã có `trend_report`.

        [AC-03.3] Sắp xếp xu hướng giảm dần theo `article_count`. Xu hướng không
        bóc được số xếp cuối — không có căn cứ nào để đặt chúng lên trên.
        """
        report = run.trend_report
        assert report is not None, "chỉ gọi khi run đã có trend_report"

        items: list[TrendItemOut] = []
        for raw in report.trends:
            text = raw.strip()
            m = _TREND_COUNT_RE.search(text)
            count = int(m.group(1)) if m else None
            title = _TREND_COUNT_RE.sub("", text).strip() if m else text
            items.append(TrendItemOut(title=title, article_count=count))

        items.sort(key=lambda i: (i.article_count is not None, i.article_count or 0), reverse=True)

        return cls(
            run_id=run.run_id,
            topic=run.topic,
            generated_at=run.finished_at,
            overall_sentiment=_SENTIMENT_MAP[report.overall_sentiment],
            insight=report.insight,
            trends=items,
            article_count=run.articles_scraped,
        )


class PageMeta(BaseModel):
    """Thông tin phân trang (FR-01). Đủ để client biết còn trang nào nữa không."""

    page: int = Field(description="Trang hiện tại, đếm từ 1")
    size: int = Field(description="Số bản ghi mỗi trang")
    total_items: int = Field(description="Tổng số bản ghi khớp bộ lọc")
    total_pages: int = Field(description="Tổng số trang, làm tròn lên")
    has_next: bool = Field(description="Còn trang sau không")
    has_prev: bool = Field(description="Còn trang trước không")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "page": 1,
                    "size": 20,
                    "total_items": 196,
                    "total_pages": 10,
                    "has_next": True,
                    "has_prev": False,
                }
            ]
        }
    )


class RunCreateRequest(BaseModel):
    """Body của `POST /runs` (FR-04)."""

    topic: str = Field(
        default="Artificial Intelligence",
        min_length=1,
        max_length=50,
        description="Chủ đề cần thu thập. Tối đa 50 ký tự (AC-04.6).",
    )

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"topic": "Artificial Intelligence"}]}
    )


class RunAcceptedOut(BaseModel):
    """
    Response 202 của `POST /runs` (FR-04).

    Đây là ASYNC JOB PATTERN: server nhận việc, trả ngay `run_id` và đường dẫn
    để theo dõi, rồi mới làm việc thật ở nền. Client KHÔNG phải giữ kết nối chờ
    45 giây — nó hỏi lại `status_url` khi nào muốn.

    Mã 202 (Accepted) chứ không phải 200 hay 201: 200 hàm ý "đã xong", 201 hàm ý
    "đã tạo xong tài nguyên bạn yêu cầu". 202 nói đúng sự thật — *đã nhận, chưa
    xong*.
    """

    run_id: str = Field(description="Định danh chu kỳ vừa được xếp lịch")
    status: str = Field(description="Luôn là 'queued' tại thời điểm trả về")
    topic: str = Field(description="Chủ đề của chu kỳ")
    created_at: datetime = Field(description="Thời điểm nhận yêu cầu")
    status_url: str = Field(description="Đường dẫn để hỏi tiến độ")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "run_id": "0193f2a1-8c4e-7b3a-9f21-5d8e4c1b2a09",
                    "status": "queued",
                    "topic": "Artificial Intelligence",
                    "created_at": "2026-09-03T06:31:44Z",
                    "status_url": "/api/v1/runs/0193f2a1-8c4e-7b3a-9f21-5d8e4c1b2a09",
                }
            ]
        }
    )


class RunOut(BaseModel):
    """Trạng thái và kết quả một chu kỳ (FR-05, FR-06)."""

    run_id: str
    status: str = Field(description="queued | running | succeeded | failed")
    trigger: str = Field(description="api | cronjob | manual — ai đã khởi động chu kỳ này")
    topic: str
    started_at: datetime | None = Field(default=None)
    finished_at: datetime | None = Field(default=None)
    duration_seconds: float | None = Field(
        default=None, description="null khi chu kỳ chưa kết thúc — cố ý không trả 0 để khỏi nhầm"
    )
    articles_scraped: int | None = Field(default=None, description="Số bài thô cào về")
    articles_stored: int | None = Field(
        default=None,
        description=(
            "Số bài THỰC SỰ lưu mới. Thường nhỏ hơn `articles_scraped` vì bài đã "
            "có trong kho bị bỏ qua khi ghi."
        ),
    )
    error: str | None = Field(default=None, description="Chỉ có khi status='failed'")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "run_id": "6054fbc0-b673-4595-b430-ee270b5d26f2",
                    "status": "succeeded",
                    "trigger": "cronjob",
                    "topic": "Artificial Intelligence",
                    "started_at": "2026-09-03T06:23:59Z",
                    "finished_at": "2026-09-03T06:24:44Z",
                    "duration_seconds": 45.3,
                    "articles_scraped": 18,
                    "articles_stored": 10,
                    "error": None,
                },
                {
                    "run_id": "0193f1b0-2d3c-7a19-8e44-1c9f7b2d3e55",
                    "status": "failed",
                    "trigger": "api",
                    "topic": "Artificial Intelligence",
                    "started_at": "2026-09-03T05:10:02Z",
                    "finished_at": "2026-09-03T05:10:09Z",
                    "duration_seconds": 7.1,
                    "articles_scraped": 0,
                    "articles_stored": None,
                    "error": "ScraperAgent (critical) loi: NewsAPI tra ve 401",
                },
            ]
        }
    )

    @classmethod
    def from_domain(cls, run: PipelineRun) -> "RunOut":
        """Dựng bản công khai từ entity domain."""
        return cls(
            run_id=run.run_id,
            status=run.status.value,
            trigger=run.trigger.value,
            topic=run.topic,
            started_at=run.started_at,
            finished_at=run.finished_at,
            duration_seconds=run.duration_seconds,
            articles_scraped=run.articles_scraped,
            articles_stored=run.articles_stored,
            error=run.error,
        )


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Vỏ bọc chung cho mọi endpoint trả danh sách.

    Dùng generic để `PaginatedResponse[ArticleOut]` và
    `PaginatedResponse[RunOut]` (bước 9) chia sẻ đúng một cấu trúc — client
    học một lần, dùng ở mọi chỗ, và OpenAPI sinh ra schema riêng cho từng
    kiểu nên tài liệu vẫn chính xác.

    Tách `pagination` thành object lồng thay vì rải phẳng cạnh `items`: sau
    này thêm trường phân trang mới (vd `next_cursor`) không đụng vào tầng
    ngoài của response.
    """

    items: list[T]
    pagination: PageMeta

    @staticmethod
    def meta_of(page: Page) -> PageMeta:
        """Rút thông tin phân trang từ `Page` của tầng application."""
        return PageMeta(
            page=page.page,
            size=page.size,
            total_items=page.total_items,
            total_pages=page.total_pages,
            has_next=page.has_next,
            has_prev=page.has_prev,
        )

    @classmethod
    def from_page(cls, page: Page[Article]) -> "PaginatedResponse[ArticleOut]":
        """Chuyển `Page[Article]` thành response công khai (FR-01)."""
        return PaginatedResponse[ArticleOut](
            items=[ArticleOut.from_domain(a) for a in page.items],
            pagination=cls.meta_of(page),
        )

    @classmethod
    def from_run_page(cls, page: Page[PipelineRun]) -> "PaginatedResponse[RunOut]":
        """Chuyển `Page[PipelineRun]` thành response công khai (FR-06)."""
        return PaginatedResponse[RunOut](
            items=[RunOut.from_domain(r) for r in page.items],
            pagination=cls.meta_of(page),
        )
