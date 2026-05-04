"""
=====================================================================
STORAGE AGENT — Lưu trữ dữ liệu (BẢN SỬA BUGS + LSP + OCP)
=====================================================================
FIX LIST:
    - [BUG] STT counter: Dùng max(STT) từ file thay vì đếm title
    - [LSP] execute(ctx: PipelineContext) → PipelineContext
    - [OCP] @AgentFactory.register("storage")
    - [SMELL] Magic numbers → Import từ config.py
=====================================================================
"""
import csv
import os
from collections import defaultdict
from modules.base_agent import BaseAgent, AgentFactory
from modules.models import Article, PipelineContext
from modules import config


@AgentFactory.register("storage")
class StorageAgent(BaseAgent):
    """Lính hậu cần — Lưu trữ dữ liệu xuống CSV."""

    def __init__(self, **kwargs):
        super().__init__("StorageAgent")

    def _generate_safe_filename(self, topic: str) -> str:
        import re
        safe_name = re.sub(r'[\\/*?:"<>|]', "", topic)
        safe_name = safe_name.strip().replace(" ", "_").lower()
        if not safe_name:
            return "unknown_topic_news.csv"
        return f"{safe_name}_news.csv"

    def _load_existing_data(self, filepath: str) -> tuple[set[str], int]:
        """
        [FIX BUG STT] Đọc file cũ, trả về:
            - Set các title đã lưu (để lọc trùng)
            - Giá trị STT lớn nhất (để đánh số tiếp theo CHÍNH XÁC)
        
        BUG CŨ: Dùng len(existing_titles) để tính STT → Sai khi có title trùng bị lọc.
        FIX: Đọc trực tiếp cột STT, lấy giá trị MAX.
        """
        existing_titles: set[str] = set()
        max_stt: int = 0

        if os.path.isfile(filepath):
            try:
                with open(filepath, mode="r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if "Tieu_De" in row:
                            existing_titles.add(row["Tieu_De"].strip())
                        if "STT" in row:
                            try:
                                stt = int(row["STT"])
                                max_stt = max(max_stt, stt)
                            except ValueError:
                                pass
            except Exception as e:
                self.log_error(f"Lỗi đọc file cũ: {e}")

        return existing_titles, max_stt

    def _print_analytics(self, new_data: list[Article]):
        source_stats: dict[str, int] = defaultdict(int)
        tag_stats: dict[str, int] = defaultdict(int)
        for art in new_data:
            source_stats[art.source] += 1
            for tag in art.tags:
                tag_stats[tag] += 1

        self.log_info("Thong ke nguon tin moi:")
        for source, count in source_stats.items():
            self.log_info(f"   [Nguon] {source}: {count} bai")
        if tag_stats:
            for tag, count in tag_stats.items():
                self.log_info(f"   [Tag] {tag}: xuat hien {count} lan")

    async def execute(self, ctx: PipelineContext) -> PipelineContext:
        """
        [FIX LSP] Chữ ký thống nhất: nhận PipelineContext, trả PipelineContext.
        Đọc ctx.articles để lưu, đọc ctx.topic để đặt tên file.
        """
        os.makedirs(config.OUTPUT_DIR, exist_ok=True)
        filepath = os.path.join(config.OUTPUT_DIR, self._generate_safe_filename(ctx.topic))
        file_exists = os.path.isfile(filepath)

        # Đọc lịch sử + lấy STT max CHÍNH XÁC
        existing_titles, max_stt = self._load_existing_data(filepath)

        # Lọc tin mới
        new_data = [art for art in ctx.articles if art.title.strip() not in existing_titles]

        if not new_data:
            self.log_info("Khong co tin moi. Du lieu cu giu nguyen an toan.")
            return ctx

        self._print_analytics(new_data)

        # Ghi nối tiếp — STT bắt đầu từ max_stt + 1 (FIX BUG)
        try:
            with open(filepath, mode="a", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=config.CSV_FIELDNAMES)
                if not file_exists:
                    writer.writeheader()

                for i, art in enumerate(new_data, max_stt + 1):
                    writer.writerow({
                        "STT": i,
                        "Tieu_De": art.title,
                        "Nguon": art.source,
                        "Ngay": art.date,
                        "Tags": ", ".join(art.tags),
                        "Link_Bai": art.url,
                    })
            self.log_info(f"Da noi them {len(new_data)} tin MOI vao: {filepath}")
        except Exception as e:
            self.log_error(f"Loi ghi file CSV: {e}")

        return ctx
