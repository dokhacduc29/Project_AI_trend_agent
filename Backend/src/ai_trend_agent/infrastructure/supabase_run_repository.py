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
from datetime import datetime, timezone
from typing import Any

from supabase import Client, create_client

from ai_trend_agent.domain.models import RunStatus, RunTrigger, TrendReport

_TABLE = "pipeline_runs"
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

        Nuốt lỗi và vẫn trả về id: id đã có giá trị dùng được cho luồng phía
        sau kể cả khi DB từ chối ghi.
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
