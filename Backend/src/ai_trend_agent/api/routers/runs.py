"""
=====================================================================
RUNS ROUTER — FR-04 (kích hoạt), FR-05 (trạng thái), FR-06 (lịch sử)
=====================================================================
ASYNC JOB PATTERN — phần đáng chú ý nhất của cả tầng API.

VẤN ĐỀ: một chu kỳ pipeline chạy ~45 giây (đo được). Nếu `POST /runs` chờ chạy
xong mới trả lời thì:
    - client phải giữ kết nối 45 giây, gateway/proxy thường ngắt trước đó
    - client mất kết nối là mất luôn kết quả, dù công việc vẫn chạy
    - không cách nào biết tiến độ

GIẢI PHÁP: server NHẬN việc, trả ngay `202 Accepted` kèm `run_id` và
`status_url`, rồi làm việc thật ở nền. Client hỏi lại khi nào muốn.

    POST /api/v1/runs        → 202 { run_id, status_url }
    GET  /api/v1/runs/{id}   → 200 { status: running | succeeded | failed, ... }

VÌ SAO 202 CHỨ KHÔNG PHẢI 200/201:
    200 hàm ý "đã xong". 201 hàm ý "đã tạo xong tài nguyên bạn yêu cầu".
    202 nói đúng sự thật: *đã nhận, chưa xong*. Mã trạng thái là một phần của
    hợp đồng, chọn sai là nói dối client.

GIỚI HẠN ĐÃ BIẾT CỦA `BackgroundTasks` (SRS mục 8.4):
    Việc chạy trong tiến trình của chính API server. Pod bị kill giữa chừng thì
    run đó mắc kẹt ở `running` mãi mãi. Hàng đợi bền vững (Celery/Arq/RQ) nằm
    ngoài phạm vi v5.0. Bù lại, bản ghi `running` treo quá lâu chính là dấu
    hiệu để phát hiện run mồ côi.

Iron Laws: L03 async, L05 pagination, L07 fault tolerance, L08 type hints.
=====================================================================
"""
import logging
import os
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Path, Query, Response, status

from ai_trend_agent.api.dependencies import RequireApiKey, RunRepositoryDep
from ai_trend_agent.api.errors import ConflictProblem, NotFoundProblem
from ai_trend_agent.api.schemas import (
    PaginatedResponse,
    RunAcceptedOut,
    RunCreateRequest,
    RunOut,
)
from ai_trend_agent.application.ports import RunRepository
from ai_trend_agent.domain.models import PipelineContext, RunStatus, RunTrigger

_logger = logging.getLogger("ai_trend_agent.api.runs")

router = APIRouter(prefix="/api/v1/runs", tags=["runs"])


async def _execute_pipeline(run_repo: RunRepository, run_id: str, topic: str) -> None:
    """
    Chạy pipeline ở NỀN sau khi response 202 đã được trả về.

    Import các module nặng NGAY TRONG HÀM, không ở đầu file: kéo cả chuỗi agent
    (google-genai, supabase, httpx) vào lúc import router sẽ làm API khởi động
    chậm hẳn, trong khi phần lớn request chỉ đọc dữ liệu và không cần chúng.

    Hàm này KHÔNG ĐƯỢC để exception thoát ra. Nó chạy ngoài vòng đời request
    nên không có exception handler nào đỡ; lỗi lọt ra chỉ thành một traceback
    trong log và bản ghi run mắc kẹt ở `running` vĩnh viễn.
    """
    try:
        from ai_trend_agent.application.base_agent import AgentFactory
        from ai_trend_agent.worker.main import run_pipeline
        from ai_trend_agent.infrastructure import (  # noqa: F401 — side-effect: đăng ký agent
            ai_agent,
            cleaner,
            discord_agent,
            scrapers,
            supabase_storage,
            trend_agent,
        )

        ctx = PipelineContext(
            topic=topic,
            api_key=os.getenv("NEWS_API_KEY", ""),
            gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
        )
        agents = [
            AgentFactory.create("scraper"),
            AgentFactory.create("cleaner"),
            AgentFactory.create("analyzer"),
            AgentFactory.create("trend"),
            AgentFactory.create("storage"),
            AgentFactory.create("discord"),
        ]
        # Truyền `run_id` đã tạo ở handler để `run_pipeline` KHÔNG tạo bản ghi
        # thứ hai cho cùng một chu kỳ.
        await run_pipeline(agents, ctx, run_repo, RunTrigger.API, run_id=run_id)
    except Exception as exc:
        _logger.error("Chu ky nen that bai (run_id=%s)", run_id, exc_info=True)
        # Đóng sổ bản ghi để nó không mắc kẹt ở `running`. Bọc try/except lần
        # nữa vì chính thao tác ghi này cũng có thể hỏng.
        try:
            await run_repo.finish(
                run_id, status=RunStatus.FAILED, error=f"Loi khong luong truoc: {exc}"
            )
        except Exception:
            _logger.error("Khong dong so duoc run that bai (run_id=%s)", run_id, exc_info=True)


@router.post(
    "",
    response_model=RunAcceptedOut,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[RequireApiKey],
    summary="Kích hoạt một chu kỳ pipeline",
    description=(
        "Xếp lịch chạy một chu kỳ thu thập rồi trả về **ngay lập tức** với `run_id`.\n\n"
        "Chu kỳ mất khoảng 45 giây; theo dõi tiến độ bằng `GET /api/v1/runs/{run_id}` "
        "tại `status_url` trong response.\n\n"
        "**Cần header `X-API-Key`.** Endpoint này tiêu hạn mức Gemini nên được bảo vệ."
    ),
    responses={
        401: {"description": "Thiếu hoặc sai X-API-Key"},
        409: {"description": "Đã có chu kỳ đang chạy"},
    },
)
async def create_run(
    body: RunCreateRequest,
    background: BackgroundTasks,
    response: Response,
    repo: RunRepositoryDep,
) -> RunAcceptedOut:
    """
    FR-04 — kích hoạt chu kỳ mới.

    [AC-04.1] Trả 202 kèm `run_id` và `status_url`.
    [AC-04.2] Trả về dưới 500ms — công việc thật chạy ở nền.
    [AC-04.4] Đang có chu kỳ `queued`/`running` thì trả 409, không xếp thêm.
    [AC-04.5] Bản ghi run được tạo TRƯỚC khi response rời đi, nên `status_url`
              luôn hỏi được ngay lập tức, không có khoảng trống 404.
    """
    if await repo.has_active():
        raise ConflictProblem(
            "Đã có chu kỳ đang chạy. Chờ hoàn tất trước khi kích hoạt chu kỳ mới.",
            title="Run already in progress",
        )

    run_id = await repo.create(topic=body.topic, trigger=RunTrigger.API)

    # `Location` là header chuẩn cho 202: client theo dõi tiến độ ở đây. Nhiều
    # thư viện HTTP tự đọc header này, không cần parse body.
    status_url = f"/api/v1/runs/{run_id}"
    response.headers["Location"] = status_url

    # Giao việc SAU khi bản ghi đã tồn tại — nếu ngược lại, chu kỳ nền có thể
    # bắt đầu trước khi có gì để ghi kết quả vào.
    background.add_task(_execute_pipeline, repo, run_id, body.topic)

    return RunAcceptedOut(
        run_id=run_id,
        status=RunStatus.QUEUED.value,
        topic=body.topic,
        created_at=datetime.now(timezone.utc),
        status_url=status_url,
    )


@router.get(
    "",
    response_model=PaginatedResponse[RunOut],
    summary="Lịch sử các chu kỳ",
    description=(
        "Danh sách chu kỳ đã chạy, mới nhất trước. Trường `trigger` cho biết chu kỳ "
        "do API kích hoạt (`api`) hay do lịch CronJob (`cronjob`)."
    ),
)
async def list_runs(
    repo: RunRepositoryDep,
    page: int = Query(1, ge=1, description="Trang hiện tại"),
    size: int = Query(20, ge=1, le=100, description="Số bản ghi mỗi trang"),
    run_status: RunStatus | None = Query(
        None, alias="status", description="Lọc theo trạng thái"
    ),
) -> PaginatedResponse[RunOut]:
    """
    FR-06 — lịch sử chạy.

    [AC-06.1] Mặc định sắp xếp giảm dần theo `started_at`.
    [AC-06.2] `trigger` phân biệt run do API với run do CronJob.
    [AC-06.3] Lọc `?status=failed` chỉ trả chu kỳ thất bại.

    Tham số HTTP tên `status` nhưng biến Python tên `run_status`: `status` trùng
    với module `fastapi.status` đã import ở đầu file.
    """
    page_result = await repo.list_paginated(page=page, size=size, status=run_status)
    return PaginatedResponse.from_run_page(page_result)


@router.get(
    "/{run_id}",
    response_model=RunOut,
    summary="Trạng thái một chu kỳ",
    description=(
        "Tiến độ và kết quả của một chu kỳ. Đây là endpoint client gọi lặp lại sau "
        "khi nhận 202 từ `POST /api/v1/runs`."
    ),
    responses={404: {"description": "Không tìm thấy chu kỳ"}},
)
async def get_run(
    repo: RunRepositoryDep,
    run_id: str = Path(description="Định danh chu kỳ, dạng UUID"),
) -> RunOut:
    """
    FR-05 — trạng thái một chu kỳ.

    [AC-05.1] Không tồn tại thì 404 theo RFC 7807.
    [AC-05.2] Thất bại do agent critical thì `error` chứa tên agent gây lỗi.
    [AC-05.3] Enrichment agent lỗi vẫn là `succeeded` — đúng ngữ nghĩa ADR 0003.
    [AC-05.4] `duration_seconds` chỉ có giá trị khi `finished_at` khác null.
    """
    run = await repo.get(run_id)
    if run is None:
        raise NotFoundProblem(f"Không tìm thấy chu kỳ với run_id={run_id}")
    return RunOut.from_domain(run)
