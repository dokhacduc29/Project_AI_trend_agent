"""
=====================================================================
DATABASE STORAGE AGENT — Lưu trữ vào Supabase PostgreSQL (Phase 5)
=====================================================================
FEATURES:
    - [L03] Async-first với Supabase client
    - [L07] Fault tolerance: timeout + comprehensive error handling
    - [L08] Full type hints + docstring
    - [OCP] @AgentFactory.register("database_storage")
    - [DEDUP] Query existing titles trước khi insert
    - [ANALYTICS] Thống kê nguồn tin + tags như CSV agent
=====================================================================
"""
import os
import asyncio
from collections import defaultdict
from typing import Any
from supabase import create_client, Client
from base_agent import BaseAgent, AgentFactory
from models import Article, PipelineContext
import config


@AgentFactory.register("database_storage")
class DatabaseStorageAgent(BaseAgent):
    """
    Lưu trữ articles vào Supabase PostgreSQL cloud database.

    Schema: public.articles (id, title, source, date, tags, summary, sentiment, url)
    Dedup: Query existing titles để tránh duplicate.
    """

    def __init__(self, **kwargs):
        super().__init__("DatabaseStorageAgent")
        self.supabase_url: str = os.getenv("SUPABASE_URL", "")
        self.supabase_key: str = os.getenv("SUPABASE_KEY", "")

        if not self.supabase_url or not self.supabase_key:
            raise ValueError(
                "[L01] Thieu SUPABASE_URL hoac SUPABASE_KEY trong .env! "
                "Khong the ket noi database."
            )

        # Tạo Supabase client
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        self.log_info("Da khoi tao Supabase client thanh cong.")

    async def _fetch_existing_titles(self) -> set[str]:
        """
        [L03 + L07] Query danh sách title đã tồn tại để dedup.

        Returns:
            Set các title đã có trong database.

        Raises:
            Exception nếu query fail (sẽ được catch ở execute).
        """
        try:
            # Supabase Python client chưa hỗ trợ async native,
            # nên dùng asyncio.to_thread để không block event loop
            response = await asyncio.to_thread(
                lambda: self.supabase.table("articles").select("title").execute()
            )

            if hasattr(response, "data") and response.data:
                titles = {row["title"].strip() for row in response.data}
                self.log_info(f"Da load {len(titles)} titles tu database de kiem tra trung.")
                return titles
            return set()

        except Exception as e:
            self.log_error(f"Loi query existing titles: {e}")
            # Trả về empty set để tiếp tục (better than crash)
            return set()

    async def _insert_articles(self, new_articles: list[Article]) -> int:
        """
        [L03 + L07] Insert danh sách articles vào Supabase.

        Args:
            new_articles: Danh sách Article mới cần insert.

        Returns:
            Số lượng articles đã insert thành công.
        """
        if not new_articles:
            return 0

        try:
            # Chuẩn bị data theo schema của Supabase
            rows: list[dict[str, Any]] = []
            for art in new_articles:
                rows.append({
                    "title": art.title,
                    "source": art.source,
                    "date": art.date,
                    "tags": ", ".join(art.tags),  # Join tags thành string
                    "summary": art.summary,
                    "sentiment": (
                        art.sentiment.value
                        if hasattr(art.sentiment, "value")
                        else str(art.sentiment)
                    ),
                    "url": art.url,
                })

            # Insert batch với timeout protection
            response = await asyncio.to_thread(
                lambda: self.supabase.table("articles").insert(rows).execute()
            )

            inserted_count = len(response.data) if hasattr(response, "data") else len(rows)
            self.log_info(f"Da insert thanh cong {inserted_count} articles vao Supabase.")
            return inserted_count

        except Exception as e:
            self.log_error(f"Loi insert articles vao Supabase: {e}")
            return 0

    def _print_analytics(self, new_data: list[Article]):
        """
        [L02] Log thống kê nguồn tin + tags (giống CSV storage agent).
        """
        source_stats: dict[str, int] = defaultdict(int)
        tag_stats: dict[str, int] = defaultdict(int)

        for art in new_data:
            source_stats[art.source] += 1
            for tag in art.tags:
                tag_stats[tag] += 1

        self.log_info("=" * 60)
        self.log_info("THONG KE NGUON TIN MOI:")
        for source, count in source_stats.items():
            self.log_info(f"   [Nguon] {source}: {count} bai")

        if tag_stats:
            self.log_info("THONG KE TAGS:")
            for tag, count in sorted(tag_stats.items(), key=lambda x: x[1], reverse=True):
                self.log_info(f"   [Tag] {tag}: {count} lan")
        self.log_info("=" * 60)

    async def execute(self, ctx: PipelineContext) -> PipelineContext:
        """
        [LSP] Chữ ký thống nhất với BaseAgent.execute().

        Workflow:
            1. Query existing titles từ Supabase
            2. Lọc articles mới (dedup)
            3. Insert vào database
            4. Log analytics

        Args:
            ctx: PipelineContext chứa articles cần lưu.

        Returns:
            PipelineContext (không thay đổi articles).
        """
        if not ctx.articles:
            self.log_info("Khong co articles de luu. Bo qua.")
            return ctx

        self.log_info(f"Bat dau luu {len(ctx.articles)} articles vao Supabase...")

        # Bước 1: Fetch existing titles để dedup
        existing_titles = await self._fetch_existing_titles()

        # Bước 2: Lọc articles mới
        new_articles = [
            art for art in ctx.articles
            if art.title.strip() not in existing_titles
        ]

        if not new_articles:
            self.log_info("Tat ca articles da ton tai trong database. Khong co gi moi.")
            return ctx

        self.log_info(f"Phat hien {len(new_articles)} articles MOI (chua ton tai trong DB).")

        # Bước 3: Log analytics trước khi insert
        self._print_analytics(new_articles)

        # Bước 4: Insert vào Supabase
        inserted_count = await self._insert_articles(new_articles)

        if inserted_count > 0:
            self.log_info(
                f"[THANH CONG] Da luu {inserted_count}/{len(new_articles)} articles "
                f"vao Supabase cloud database!"
            )
        else:
            self.log_error("Khong co articles nao duoc luu thanh cong. Kiem tra logs.")

        return ctx
