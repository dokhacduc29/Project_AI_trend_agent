"""
=====================================================================
[DAY 24] STORAGE AGENT — "Lính hậu cần" lưu trữ dữ liệu
=====================================================================
GIẢI THÍCH KIẾN TRÚC:
    StorageAgent chịu trách nhiệm duy nhất: Nhận danh sách bài báo sạch → Ghi xuống file.
    Hiện tại nó ghi CSV, nhưng nhờ tính ĐA HÌNH (Polymorphism), sau này bạn có thể
    tạo thêm class DatabaseStorageAgent kế thừa từ StorageAgent và Override method save()
    để ghi vào SQLite hoặc PostgreSQL mà KHÔNG CẦN SỬA code ở main.py.

KỸ THUẬT ÁP DỤNG:
    - [DAY 23] Inheritance: StorageAgent(BaseAgent)
    - [DAY 24] Polymorphism: Method save() có thể bị Override ở class con trong tương lai.
    - [DAY 24] Encapsulation: _existing_titles, _filename là biến nội bộ.
    - [DAY 26] @property: filename là thuộc tính chỉ đọc.
    - [DAY 14] defaultdict: Thống kê nguồn tin.
=====================================================================
"""
import csv
import os
from collections import defaultdict
from modules.base_agent import BaseAgent
from modules.models import Article


class StorageAgent(BaseAgent):
    """Lính hậu cần — Lưu trữ dữ liệu xuống CSV (có thể mở rộng sang Database)."""

    def __init__(self, output_dir: str = "data"):
        super().__init__("StorageAgent")
        self._output_dir = output_dir
        # [DAY 24] Encapsulation: Biến nội bộ, không ai bên ngoài nên truy cập trực tiếp.
        self._existing_titles: set[str] = set()
        self._filename: str = ""

    @property
    def filename(self) -> str:
        """[DAY 26] @property — Đường dẫn file CSV hiện tại (chỉ đọc)."""
        return self._filename

    def _generate_safe_filename(self, topic: str) -> str:
        """[Nội bộ] Tạo tên file an toàn cho hệ điều hành."""
        import re
        safe_name = re.sub(r'[\\/*?:"<>|]', "", topic)
        safe_name = safe_name.strip().replace(" ", "_").lower()
        if not safe_name:
            return "unknown_topic_news.csv"
        return f"{safe_name}_news.csv"

    def _load_existing_titles(self):
        """
        [Nội bộ] Đọc file CSV cũ để lấy danh sách tiêu đề đã lưu.
        Mục đích: Chống trùng lặp khi ghi nối (Append).
        """
        if os.path.isfile(self._filename):
            try:
                with open(self._filename, mode="r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    self._existing_titles = {
                        row["Tieu_De"].strip() for row in reader if "Tieu_De" in row
                    }
            except Exception as e:
                self.log_error(f"Lỗi đọc file cũ: {e}")

    def _print_analytics(self, new_data: list[Article]):
        """
        [DAY 14] Thống kê nguồn tin bằng defaultdict.
        In ra bảng phân tích ngắn gọn trên Terminal.
        """
        source_stats: dict[str, int] = defaultdict(int)
        tag_stats: dict[str, int] = defaultdict(int)

        for art in new_data:
            source_stats[art.source] += 1
            for tag in art.tags:
                tag_stats[tag] += 1

        self.log_info("📊 Thống kê nguồn tin mới:")
        for source, count in source_stats.items():
            self.log_info(f"   [Nguồn] {source}: {count} bài")
        if tag_stats:
            for tag, count in tag_stats.items():
                self.log_info(f"   [Tag] {tag}: xuất hiện {count} lần")

    async def execute(self, articles: list[Article], topic: str) -> bool:
        """
        [DAY 27] Override execute() — Luồng lưu trữ chính.
        
        [DAY 24] POLYMORPHISM (Tính đa hình) ẩn chứa ở đây:
            Hiện tại method này ghi CSV. Sau này khi bạn học Day 51-52 (SQL/SQLAlchemy),
            bạn sẽ tạo class DatabaseStorageAgent(StorageAgent) và Override method execute()
            để ghi vào Database. Code trong main.py sẽ KHÔNG CẦN SỬA GÌ CẢ vì nó chỉ gọi
            agent.execute() — không quan tâm bên trong ghi CSV hay ghi DB.
            Đó chính là sức mạnh của Đa hình!
        """
        # 1. Chuẩn bị đường dẫn
        os.makedirs(self._output_dir, exist_ok=True)
        self._filename = os.path.join(self._output_dir, self._generate_safe_filename(topic))
        file_exists = os.path.isfile(self._filename)

        # 2. Đọc lịch sử chống trùng
        self._load_existing_titles()

        # 3. Lọc tin mới
        new_data = [art for art in articles if art.title.strip() not in self._existing_titles]

        if not new_data:
            self.log_info("Không có tin mới. Dữ liệu cũ giữ nguyên an toàn.")
            return False

        # 4. In báo cáo Analytics
        self._print_analytics(new_data)

        # 5. Ghi nối tiếp (Append-only)
        try:
            with open(self._filename, mode="a", encoding="utf-8", newline="") as f:
                fieldnames = ["STT", "Tieu_De", "Nguon", "Ngay", "Tags", "Link_Bai"]
                writer = csv.DictWriter(f, fieldnames=fieldnames)

                if not file_exists:
                    writer.writeheader()

                start_idx = len(self._existing_titles) + 1
                for i, art in enumerate(new_data, start_idx):
                    writer.writerow({
                        "STT": i,
                        "Tieu_De": art.title,
                        "Nguon": art.source,
                        "Ngay": art.date,
                        "Tags": ", ".join(art.tags),
                        "Link_Bai": art.url,
                    })

            self.log_info(f"Đã nối thêm {len(new_data)} tin MỚI vào: {self._filename}")
            return True

        except Exception as e:
            self.log_error(f"Lỗi ghi file CSV: {e}")
            return False
