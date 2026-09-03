"""
=====================================================================
TRENDS ROUTER — FR-03: báo cáo xu hướng mới nhất
=====================================================================
Endpoint này đọc `trend_report` của lần chạy `succeeded` gần nhất.

VÌ SAO KHÔNG SINH XU HƯỚNG NGAY LÚC GỌI:
    Rút xu hướng cần một lời gọi Gemini trên toàn bộ bài viết — đo được ~20
    giây và tiêu một suất trong hạn mức free tier (ràng buộc C-03). Sinh theo
    từng request thì chỉ vài người gọi là cạn quota, và mỗi người nhận một
    báo cáo khác nhau cho cùng dữ liệu.

    Pipeline đã sinh sẵn báo cáo mỗi chu kỳ; endpoint chỉ việc đọc lại. Nhanh,
    rẻ, và mọi người thấy cùng một kết quả.

Iron Laws: L03 async, L08 type hints + docstring.
=====================================================================
"""
from fastapi import APIRouter, Request, Response

from ai_trend_agent.api.dependencies import RunRepositoryDep
from ai_trend_agent.api.rate_limit import read_limit
from ai_trend_agent.api.errors import NotFoundProblem
from ai_trend_agent.api.schemas import TrendReportOut

router = APIRouter(prefix="/api/v1/trends", tags=["trends"])


@router.get(
    "/latest",
    response_model=TrendReportOut,
    summary="Báo cáo xu hướng mới nhất",
    description=(
        "Trả về báo cáo xu hướng của chu kỳ chạy **thành công** gần nhất có sinh "
        "được báo cáo.\n\n"
        "Báo cáo được pipeline tạo sẵn ở mỗi chu kỳ, không sinh lúc gọi — nên "
        "endpoint này nhanh và không tiêu hạn mức AI.\n\n"
        "**Lưu ý**: `article_count` của từng xu hướng có thể `null`. Số bài được "
        "mô hình ghi trong văn bản chứ không phải trường có cấu trúc, nên không "
        "phải lúc nào cũng bóc ra được."
    ),
    responses={404: {"description": "Chưa có chu kỳ nào sinh được báo cáo xu hướng"}},
)
@read_limit
async def latest_trend(
    request: Request, response: Response, repo: RunRepositoryDep
) -> TrendReportOut:
    """
    FR-03 — báo cáo xu hướng mới nhất.

    [AC-03.1] Chỉ lấy chu kỳ đã `succeeded`, bỏ qua chu kỳ đang chạy dở.
    [AC-03.2] Chưa có báo cáo nào thì trả 404 với thông báo rõ ràng, KHÔNG trả
              object rỗng — object rỗng buộc client phải tự đoán xem đó là "hệ
              thống chưa chạy" hay "chạy rồi mà không có xu hướng nào".
    [AC-03.3] Xu hướng sắp xếp giảm dần theo số bài liên quan.

    [L05] `request` và `response` không dùng trong thân hàm nhưng BẮT BUỘC phải
    có: slowapi tìm `request` theo tên để lấy IP, và nhét `X-RateLimit-*` vào
    `response`. Thiếu `response` thì endpoint trả 500 ở ĐƯỜNG THÀNH CÔNG.
    """
    run = await repo.latest_with_trend()
    if run is None or run.trend_report is None:
        raise NotFoundProblem(
            "Chưa có chu kỳ nào sinh được báo cáo xu hướng",
            title="No trend report available",
        )
    return TrendReportOut.from_run(run)
