"""
=====================================================================
SUPABASE STORAGE AGENT — Lưu trữ lên PostgreSQL cloud (Phase 5)
=====================================================================
Thay thế StorageAgent (CSV) bằng Supabase PostgreSQL.
- Dedupe tự động qua constraint url UNIQUE trên DB
- Dùng asyncio.to_thread để không block Event Loop
- Upsert thay insert để bỏ qua trùng lặp không lỗi
=====================================================================
"""
import os
import asyncio
from supabase import create_client, Client
from ai_trend_agent.application.base_agent import BaseAgent, AgentFactory
from ai_trend_agent.domain.models import Article, PipelineContext


@AgentFactory.register("storage")
class SupabaseStorageAgent(BaseAgent):
    """Lính hậu cần — Lưu trữ dữ liệu lên Supabase PostgreSQL."""

    # [ADR 0003 + 0010] Critical: lưu hỏng thì đừng đăng.
    # Dedupe của toàn hệ thống dựa vào constraint UNIQUE(url) trên bảng này.
    # Storage chết mà pipeline vẫn đi tiếp → DiscordAgent đăng bài không được
    # lưu, và chu kỳ sau đăng lại y hệt vì không còn gì để đối chiếu url.
    is_critical = True

    def __init__(self, **kwargs):
        super().__init__("SupabaseStorageAgent")
        self._client: Client | None = None
        # [B3a] Số bài THỰC SỰ chèn mới ở lần chạy gần nhất. `run_pipeline` đọc
        # để ghi vào nhật ký run. Phải là số chèn THẬT chứ không phải số bài gửi
        # đi: upsert(ignore_duplicates=True) bỏ qua bài đã có, nên hai con số
        # thường lệch nhau và chỉ con số này nói đúng "chu kỳ thu được gì mới".
        self.last_saved_count: int | None = None

    def _get_client(self) -> Client:
        if self._client is None:
            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_KEY")
            if not url or not key:
                raise ValueError("Thiếu SUPABASE_URL hoặc SUPABASE_KEY trong .env")
            self._client = create_client(url, key)
        return self._client

    def _article_to_row(self, art: Article, topic: str = "") -> dict:
        return {
            "title": art.title,
            "source": art.source,
            "date": art.date,
            "tags": ", ".join(art.tags),
            "summary": art.summary,
            "sentiment": art.sentiment.value if hasattr(art.sentiment, "value") else str(art.sentiment),
            "url": art.url,
            "topic": topic,
        }

    def _insert_sync(self, rows: list[dict]) -> int:
        """Upsert vào Supabase — bỏ qua nếu url đã tồn tại."""
        client = self._get_client()
        result = (
            client.table("articles")
            .upsert(rows, on_conflict="url", ignore_duplicates=True)
            .execute()
        )
        return len(result.data) if result.data else 0

    async def execute(self, ctx: PipelineContext) -> PipelineContext:
        if not ctx.articles:
            self.log_info("Không có bài báo nào để lưu.")
            self.last_saved_count = 0
            return ctx

        rows = [self._article_to_row(art, ctx.topic) for art in ctx.articles]
        self.log_info(f"Đang lưu {len(rows)} bài lên Supabase...")

        # KHÔNG bọc try/except ở đây: agent này là critical, để lỗi nổi lên cho
        # run_pipeline dừng chu kỳ. Nuốt lỗi tại chỗ sẽ vô hiệu hoá is_critical
        # và biến "mất toàn bộ dữ liệu" thành một dòng log không ai đọc.
        inserted = await asyncio.to_thread(self._insert_sync, rows)
        self.last_saved_count = inserted
        self.log_info(f"Đã lưu thành công {inserted} bài mới vào Supabase.")

        return ctx
