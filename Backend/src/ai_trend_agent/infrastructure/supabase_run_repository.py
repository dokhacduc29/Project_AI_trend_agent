"""
=====================================================================
SUPABASE RUN REPOSITORY — Ghi nhật ký các lần chạy pipeline (B3a)
=====================================================================
VẤN ĐỀ ĐANG SỬA (SRS P11):
    Tới v4.0, pipeline chạy xong là mọi thứ bốc hơi. Không trả lời được những
    câu hỏi vận hành cơ bản nhất: hôm qua chạy mấy lần? lần nào hỏng? mỗi lần
    thu được bao nhiêu bài? Log có ghi nhưng log bị xoay vòng và không truy
    vấn được.

    Bảng `pipeline_runs` biến những câu hỏi đó thành truy vấn SQL, và đồng
    thời là nguồn dữ liệu cho FR-03 (/trends/latest) và FR-04→06 (/runs).

NGUYÊN TẮC QUAN TRỌNG NHẤT CỦA FILE NÀY — GHI NHẬT KÝ KHÔNG ĐƯỢC LÀM CHẾT
PIPELINE:
    Theo phân loại ADR 0003, ghi run là ENRICHMENT chứ không phải critical.
    Supabase sập lúc ghi nhật ký thì chu kỳ thu thập vẫn phải chạy tiếp và
    vẫn phải đăng Discord. Mất một dòng nhật ký còn hơn mất cả mẻ tin.

    Nên MỌI method ở đây tự nuốt lỗi và chỉ log. Đây là NGOẠI LỆ có chủ ý so
    với `SupabaseArticleRepository` — repository đó để lỗi nổi lên vì lưu bài
    hỏng là mất dữ liệu thật.

Iron Laws: L03 async-first, L04 no SQL injection, L07 fault tolerance,
           L08 type hints + docstring.
=====================================================================
"""
import asyncio
import logging
import os
import uuid
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from typing import Any

from supabase import Client, create_client

from ai_trend_agent.application.ports import Page
from ai_trend_agent.domain import config
from ai_trend_agent.domain.models import (
    PipelineRun,
    RunStatus,
    RunTrigger,
    Sentiment,
    TrendReport,
)

_TABLE = "pipeline_runs"

# Bang tra nguoc gia tri tieng Viet -> enum domain, dung tu enum de hai chieu
# khong bao gio lech nhau.
_SENTIMENT_BY_VALUE: dict[str, Sentiment] = {s.value: s for s in Sentiment}
_logger = logging.getLogger("ai_trend_agent.infrastructure.run_repository")


def _trend_to_json(report: TrendReport | None) -> dict[str, Any] | None:
    """
    `TrendReport` → dict cho cột `jsonb`.

    Bỏ qua báo cáo chưa sinh được (`generated=False`): ghi một object rỗng vào
    DB sẽ khiến `/trends/latest` sau này tưởng là có dữ liệu rồi trả về một
    báo cáo trống rỗng. NULL nói đúng sự thật hơn — cùng nguyên tắc với P15.
    """
    if report is None or not report.generated:
        return None
    data = asdict(report)
    # `overall_sentiment` là Enum, `asdict` giữ nguyên object nên phải tự đổi.
    data["overall_sentiment"] = report.overall_sentiment.value
    return data


def _trend_from_json(raw: Any) -> TrendReport | None:
    """
    Cột `jsonb` → `TrendReport`.

    Migration 002 đã ghi rõ đánh đổi của `jsonb`: DB KHÔNG kiểm tra được hình
    dạng, nên tầng ứng dụng phải tự validate khi đọc lên. Dữ liệu có thể do một
    phiên bản app cũ ghi, hoặc do ai đó sửa tay trong SQL Editor.

    Hỏng thì trả None chứ không raise: `/trends/latest` trả 404 "chưa có báo
    cáo" vẫn tốt hơn là trả 500 vì một dòng dữ liệu méo.
    """
    if not isinstance(raw, dict):
        return None
    try:
        sentiment = _SENTIMENT_BY_VALUE.get(raw.get("overall_sentiment", ""), Sentiment.NEUTRAL)
        trends = [str(t) for t in raw.get("trends", []) if str(t).strip()]
        return TrendReport(
            trends=trends,
            overall_sentiment=sentiment,
            insight=str(raw.get("insight") or ""),
            generated=bool(raw.get("generated")),
        )
    except (TypeError, ValueError, AttributeError):
        _logger.warning("Ban ghi trend_report co hinh dang la, bo qua", exc_info=True)
        return None


def _parse_dt(raw: str | None) -> datetime | None:
    """Chuỗi ISO của Postgres → datetime. Hỏng thì None, không làm sập truy vấn."""
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw)
    except (ValueError, TypeError):
        return None


def _row_to_run(row: dict[str, Any]) -> PipelineRun | None:
    """
    Một dòng `pipeline_runs` → entity domain. `None` nếu dòng không đọc được.

    `status` và `trigger` là hai cột DUY NHẤT không có giá trị mặc định hợp lý:
    một run không rõ trạng thái thì mọi phán đoán về nó đều là bịa. Nên dòng
    mang giá trị lạ — 'cancelled' do phiên bản sau thêm, NULL do ai đó sửa tay
    trong SQL Editor, hoặc thiếu hẳn cột — bị BỎ QUA thay vì đoán bừa.

    VÌ SAO KHÔNG ĐỂ LỖI NỔI LÊN: `RunStatus(row["status"])` ném `ValueError` và
    `row["trigger"]` ném `KeyError`, mà lời gọi này nằm trong vòng lặp dựng
    danh sách. Một dòng hỏng làm 500 TOÀN BỘ `GET /api/v1/runs` lẫn
    `/api/v1/trends/latest`. Đổi "một endpoint sập" thành "một dòng biến mất
    khỏi kết quả" là đánh đổi đúng — phần còn lại của lịch sử vẫn đọc được.
    Cùng nguyên tắc với `_trend_from_json` và `_parse_dt` ở trên.
    """
    try:
        status = RunStatus(row["status"])
        trigger = RunTrigger(row["trigger"])
    except (KeyError, ValueError):
        _logger.warning(
            "Bo qua dong pipeline_runs khong doc duoc (run_id=%s, status=%r, trigger=%r)",
            row.get("run_id"),
            row.get("status"),
            row.get("trigger"),
        )
        return None

    return PipelineRun(
        run_id=str(row.get("run_id") or ""),
        topic=row.get("topic") or "",
        status=status,
        trigger=trigger,
        started_at=_parse_dt(row.get("started_at")),
        finished_at=_parse_dt(row.get("finished_at")),
        articles_scraped=row.get("articles_scraped"),
        articles_stored=row.get("articles_stored"),
        trend_report=_trend_from_json(row.get("trend_report")),
        error=row.get("error"),
        created_at=_parse_dt(row.get("created_at")),
    )


class SupabaseRunRepository:
    """
    Ghi lịch sử chạy pipeline vào Supabase.

    Không kế thừa `RunRepository` — port khai bằng `Protocol` nên chỉ cần có
    đúng method là thoả mãn (xem giải thích ở `application/ports.py`).
    """

    def __init__(self, client: Client | None = None) -> None:
        """Nhận client qua tham số để test tiêm được bản giả (sửa P3)."""
        self._client = client

    def _get_client(self) -> Client:
        if self._client is None:
            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_KEY")
            if not url or not key:
                raise ValueError("Thiếu SUPABASE_URL hoặc SUPABASE_KEY")
            self._client = create_client(url, key)
        return self._client

    # ── Thao tác đồng bộ (chạy trong thread riêng) ────────────────────────

    def _insert_sync(self, row: dict[str, Any]) -> None:
        self._get_client().table(_TABLE).insert(row).execute()

    def _update_sync(self, run_id: str, patch: dict[str, Any]) -> None:
        self._get_client().table(_TABLE).update(patch).eq("run_id", run_id).execute()

    # ── Giao diện async (đúng chữ ký port) ────────────────────────────────

    async def create(self, *, topic: str, trigger: RunTrigger) -> str:
        """
        Tạo bản ghi run mới, trả `run_id`.

        Sinh UUID ở PHÍA ỨNG DỤNG chứ không để DB sinh: `POST /runs` phải trả
        `run_id` về cho client ngay trong response 202, nên phải biết id trước
        khi (và độc lập với việc) ghi xuống DB thành công.

        NÉM LỖI khi không ghi được — NGOẠI LỆ DUY NHẤT của file này, và là
        chủ ý. Trước đây method này nuốt lỗi rồi vẫn trả `run_id`, lý do ghi
        trong comment cũ là "id đã có giá trị dùng được cho luồng phía sau".
        Lý do đó sai ở đường API: `POST /runs` lấy chính `run_id` này làm
        `status_url` trả cho client, nên id của một bản ghi KHÔNG TỒN TẠI là
        một lời hứa suông — client hỏi mãi mà chỉ nhận 404.

        Mỗi call site tự quyết định thay vì bắt method này đoán hộ:
          - worker bọc `_safe_run_log` → chu kỳ vẫn chạy, chỉ mất nhật ký
          - API bắt lại → trả 503, không hứa cái mình không giữ được
        """
        run_id = str(uuid.uuid4())
        row = {
            "run_id": run_id,
            "topic": topic,
            "status": RunStatus.QUEUED.value,
            "trigger": trigger.value,
        }
        try:
            await asyncio.to_thread(self._insert_sync, row)
        except Exception:
            _logger.error("Khong ghi duoc ban ghi run moi (run_id=%s)", run_id, exc_info=True)
            raise
        return run_id

    async def mark_running(self, run_id: str) -> None:
        """Chuyển sang `running`, đóng dấu `started_at`."""
        patch = {
            "status": RunStatus.RUNNING.value,
            "started_at": datetime.now(timezone.utc).isoformat(),
        }
        try:
            await asyncio.to_thread(self._update_sync, run_id, patch)
        except Exception:
            _logger.error("Khong danh dau duoc run dang chay (run_id=%s)", run_id, exc_info=True)

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
        """
        Kết thúc run: trạng thái cuối, số liệu, báo cáo xu hướng, lỗi nếu có.

        `error` chỉ có giá trị khi `status=failed`; đã cắt ngắn để một traceback
        dài bất thường không làm phình bảng nhật ký.
        """
        patch: dict[str, Any] = {
            "status": status.value,
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "articles_scraped": articles_scraped,
            "articles_stored": articles_stored,
            "trend_report": _trend_to_json(trend_report),
            "error": error[:1000] if error else None,
        }
        try:
            await asyncio.to_thread(self._update_sync, run_id, patch)
        except Exception:
            _logger.error("Khong ghi duoc ket qua run (run_id=%s)", run_id, exc_info=True)

    # ── Đường ĐỌC ─────────────────────────────────────────────────────────

    def _latest_with_trend_sync(self) -> dict[str, Any] | None:
        """
        Run `succeeded` gần nhất CÓ báo cáo xu hướng.

        Hai điều kiện lọc đều cần thiết:
          - `status = succeeded`  : không lấy chu kỳ đang chạy dở (AC-03.1)
          - `trend_report != null`: bỏ qua chu kỳ hoàn tất nhưng
            TrendSynthesisAgent (enrichment) lỗi nên không sinh được báo cáo.
            Lấy nhầm run đó thì API trả rỗng dù có báo cáo cũ vẫn dùng được.

        Sắp xếp theo `finished_at` chứ không `created_at`: quan tâm chu kỳ nào
        KẾT THÚC gần nhất, không phải chu kỳ nào được tạo gần nhất.
        """
        res = (
            self._get_client()
            .table(_TABLE)
            .select("*")
            .eq("status", RunStatus.SUCCEEDED.value)
            .not_.is_("trend_report", "null")
            .order("finished_at", desc=True)
            .limit(1)
            .execute()
        )
        rows = res.data or []
        return rows[0] if rows else None

    async def latest_with_trend(self) -> PipelineRun | None:
        """Run `succeeded` gần nhất có báo cáo xu hướng (FR-03). None nếu chưa có."""
        row = await asyncio.to_thread(self._latest_with_trend_sync)
        return _row_to_run(row) if row else None

    def _get_sync(self, run_id: str) -> dict[str, Any] | None:
        res = self._get_client().table(_TABLE).select("*").eq("run_id", run_id).limit(1).execute()
        rows = res.data or []
        return rows[0] if rows else None

    async def get(self, run_id: str) -> PipelineRun | None:
        """Một run theo id (FR-05). None nếu không có — KHÔNG raise."""
        try:
            row = await asyncio.to_thread(self._get_sync, run_id)
        except Exception:
            # `run_id` sai định dạng UUID khiến Postgres từ chối truy vấn. Với
            # API thì đó là "không tìm thấy", không phải lỗi máy chủ.
            _logger.warning("Khong doc duoc run (run_id=%s)", run_id, exc_info=True)
            return None
        return _row_to_run(row) if row else None

    def _list_sync(self, page: int, size: int, status: RunStatus | None):
        q = self._get_client().table(_TABLE).select("*", count="exact")
        if status is not None:
            q = q.eq("status", status.value)
        # Khoá phụ `created_at` cùng lý do với bug phân trang ở articles: nhiều
        # run có thể chưa có `started_at` (NULL) nên khoá chính không đủ xác định.
        q = q.order("started_at", desc=True).order("created_at", desc=True)
        start = (page - 1) * size
        res = q.range(start, start + size - 1).execute()
        return (res.data or []), (res.count or 0)

    async def list_paginated(
        self, *, page: int = 1, size: int = 20, status: RunStatus | None = None
    ) -> Page[PipelineRun]:
        """Lịch sử chạy có phân trang (FR-06)."""
        rows, total = await asyncio.to_thread(self._list_sync, page, size, status)
        # Bỏ dòng không đọc được thay vì để nó làm 500 cả trang. `total_items`
        # vẫn là con số DB đếm được, nên trang bị lọc có thể ít hơn `size` —
        # chấp nhận: thà thiếu một dòng còn hơn mất cả endpoint.
        items = [run for run in (_row_to_run(r) for r in rows) if run is not None]
        return Page(items=items, total_items=total, page=page, size=size)

    @staticmethod
    def _stale_cutoff() -> str:
        """
        Mốc thời gian: run tạo TRƯỚC mốc này mà chưa xong thì coi như đã chết.

        Tính ở phía ứng dụng chứ không dùng `now()` của Postgres vì PostgREST
        không cho nhét biểu thức SQL vào bộ lọc. Cả hai đồng hồ đều chạy UTC
        nên lệch không đáng kể so với biên 15 phút.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(
            seconds=config.RUN_STALE_AFTER_SECONDS
        )
        return cutoff.isoformat()

    def _reap_stale_sync(self) -> int:
        """
        Đánh dấu `failed` cho mọi run chưa xong đã quá hạn.

        `select="run_id"` để PostgREST trả về các dòng vừa cập nhật — đó là
        cách duy nhất biết đã dọn bao nhiêu bản ghi.
        """
        res = (
            self._get_client()
            .table(_TABLE)
            .update(
                {
                    "status": RunStatus.FAILED.value,
                    "finished_at": datetime.now(timezone.utc).isoformat(),
                    "error": (
                        f"Run mo coi: qua {config.RUN_STALE_AFTER_SECONDS}s khong ket thuc. "
                        "Nhieu kha nang tien trinh API da chet giua chu ky "
                        "(BackgroundTasks khong song sot qua viec pod bi kill)."
                    ),
                }
            )
            .in_("status", [RunStatus.QUEUED.value, RunStatus.RUNNING.value])
            .lt("created_at", self._stale_cutoff())
            .execute()
        )
        return len(res.data or [])

    async def reap_stale(self) -> int:
        """
        Đóng sổ run mắc kẹt, trả về số bản ghi đã dọn (0 nếu không có gì).

        BEST-EFFORT: hỏng thì trả 0 và log, không raise. Đây là việc dọn dẹp
        ăn theo, không phải việc chính của request nào — để nó làm hỏng
        `POST /runs` là đổi một vấn đề nhỏ lấy một vấn đề lớn.
        """
        try:
            n = await asyncio.to_thread(self._reap_stale_sync)
        except Exception:
            _logger.error("Khong don duoc run mo coi", exc_info=True)
            return 0
        if n:
            _logger.warning("Da dong so %d run mo coi (qua han chua ket thuc)", n)
        return n

    def _has_active_sync(self) -> bool:
        res = (
            self._get_client()
            .table(_TABLE)
            .select("run_id", count="exact")
            .in_("status", [RunStatus.QUEUED.value, RunStatus.RUNNING.value])
            # Run quá hạn coi như đã chết cùng cái pod sinh ra nó. Không có
            # điều kiện này thì một pod bị kill giữa chu kỳ để lại một dòng
            # `running` chặn MỌI POST /runs về sau — endpoint tự khoá chính nó.
            .gte("created_at", self._stale_cutoff())
            .limit(1)
            .execute()
        )
        return bool(res.count)

    async def has_active(self) -> bool:
        """
        Có chu kỳ nào đang chạy không (FR-04 AC-04.4).

        Hỏng thì trả True — FAIL CLOSED. Không biết chắc là có đang chạy hay
        không thì thà từ chối kích hoạt thêm: chu kỳ thừa đốt hạn mức Gemini
        (C-03), còn một lần từ chối chỉ khiến người dùng thử lại.
        """
        try:
            return await asyncio.to_thread(self._has_active_sync)
        except Exception:
            _logger.error("Khong kiem tra duoc run dang chay — coi nhu CO", exc_info=True)
            return True
