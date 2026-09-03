"""
=====================================================================
ARTICLES ROUTER — FR-01 (danh sách có phân trang) + FR-02 (chi tiết)
=====================================================================
Router chỉ làm ba việc, không hơn:
    1. Nhận và kiểm tra tham số HTTP
    2. Dịch chúng thành `ArticleFilters` của tầng application
    3. Đổi kết quả thành schema công khai

Nó KHÔNG biết dữ liệu nằm ở Supabase hay Postgres hay một dict trong bộ nhớ —
chỉ biết nó cần một `ArticleRepository`. Đổi kho lưu trữ không phải sửa file này.

Iron Laws: L03 async, L05 pagination, L08 type hints + docstring.
=====================================================================
"""
from datetime import date

from fastapi import APIRouter, Path, Query

from ai_trend_agent.api.dependencies import ArticleRepositoryDep
from ai_trend_agent.api.errors import FieldError, NotFoundProblem, ProblemException
from ai_trend_agent.api.schemas import ArticleOut, PaginatedResponse, SentimentOut
from ai_trend_agent.application.ports import ArticleFilters, ArticleSort

router = APIRouter(prefix="/api/v1/articles", tags=["articles"])


@router.get(
    "",
    response_model=PaginatedResponse[ArticleOut],
    summary="Danh sách bài viết",
    description=(
        "Trả về danh sách bài viết đã thu thập, có phân trang và lọc.\n\n"
        "**Lưu ý về ngày**: `date_from`/`date_to` lọc theo `created_at` — thời điểm "
        "hệ thống THU THẬP bài, không phải ngày xuất bản. Trường `date` (ngày xuất "
        "bản do nguồn cung cấp) hiện trộn nhiều định dạng nên chưa lọc được.\n\n"
        "**Lưu ý về sentiment**: lọc theo `sentiment` chỉ trả về bài ĐÃ qua phân tích AI. "
        "Bài chưa phân tích có `analyzed: false` và `sentiment: null`."
    ),
)
async def list_articles(
    repo: ArticleRepositoryDep,
    page: int = Query(1, ge=1, description="Trang hiện tại, đếm từ 1"),
    size: int = Query(20, ge=1, le=100, description="Số bản ghi mỗi trang, tối đa 100"),
    topic: str | None = Query(None, max_length=50, description="Lọc theo chủ đề"),
    sentiment: SentimentOut | None = Query(None, description="Lọc theo cảm xúc do AI chấm"),
    date_from: date | None = Query(None, description="Lọc từ ngày (theo created_at)"),
    date_to: date | None = Query(None, description="Lọc đến ngày, bao gồm cả ngày này"),
    sort: ArticleSort = Query(ArticleSort.CREATED_AT_DESC, description="Sắp xếp; dấu trừ là giảm dần"),
) -> PaginatedResponse[ArticleOut]:
    """
    FR-01 — danh sách bài viết có phân trang và lọc.

    [AC-01.4] Không có bản ghi nào khớp thì trả 200 với `items: []`, KHÔNG trả
    404. Danh sách rỗng là một câu trả lời hợp lệ; 404 nghĩa là "đường dẫn này
    không tồn tại", hoàn toàn khác nghĩa.
    """
    # [AC-01.6] Kiểm tra LIÊN TRƯỜNG. FastAPI kiểm được từng tham số riêng lẻ
    # (ge/le/max_length) nhưng không biết quan hệ giữa hai tham số. Phải tự
    # kiểm, nhưng vẫn ném ra đúng hình dạng 422 như lỗi Pydantic sinh ra —
    # client không cần phân biệt lỗi nào do framework, lỗi nào do ta viết.
    if date_from is not None and date_to is not None and date_from > date_to:
        raise ProblemException(
            status=422,
            title="Validation failed",
            detail="Khoảng ngày không hợp lệ",
            type_slug="validation",
            errors=[
                FieldError(
                    field="date_from",
                    message="phải nhỏ hơn hoặc bằng date_to",
                    received=date_from.isoformat(),
                )
            ],
        )

    filters = ArticleFilters(
        page=page,
        size=size,
        topic=topic,
        sentiment=sentiment.to_domain() if sentiment else None,
        date_from=date_from,
        date_to=date_to,
        sort=sort,
    )
    return PaginatedResponse.from_page(await repo.list_paginated(filters))


@router.get(
    "/{article_id}",
    response_model=ArticleOut,
    summary="Chi tiết một bài viết",
    responses={404: {"description": "Không tìm thấy bài viết"}},
)
async def get_article(
    repo: ArticleRepositoryDep,
    article_id: int = Path(description="Khoá chính của bài viết", ge=1),
) -> ArticleOut:
    """
    FR-02 — một bài viết theo id.

    [AC-02.2] Không tồn tại thì 404 theo RFC 7807.
    [AC-02.3] `article_id` không phải số nguyên thì FastAPI tự trả 422 nhờ khai
    kiểu `int` ở tham số path — không phải viết tay, và không bao giờ thành 500.
    """
    article = await repo.get_by_id(article_id)
    if article is None:
        raise NotFoundProblem(f"Không tìm thấy bài viết với id={article_id}")
    return ArticleOut.from_domain(article)
