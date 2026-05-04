"""
=====================================================================
AI TREND AGENT v3.0 — OOP Edition (Phase 3)
=====================================================================
FILE NÀY LÀ GÌ?
    Đây là "Vị Tướng Chỉ Huy" (Orchestrator) của toàn bộ hệ thống.
    Nó KHÔNG tự tay làm bất kỳ việc gì cả. Nó chỉ:
    1. Tạo ra các Agent (nhân viên) bằng Factory Pattern
    2. Ra lệnh cho từng Agent thực thi nhiệm vụ theo đúng thứ tự ETL
    3. Lập lịch trình tự động (Schedule)

KỸ THUẬT ÁP DỤNG:
    - [DAY 29] Factory Pattern: AgentFactory.create() tạo ra bất kỳ loại Agent nào.
    - [DAY 23] Inheritance: Mọi Agent đều kế thừa từ BaseAgent.
    - [DAY 27] Abstract: Mọi Agent đều bị ép buộc phải có method execute().
=====================================================================
"""
import os
import re
import time
import schedule
import asyncio
import logging
from dotenv import load_dotenv

# =====================================================================
# CẤU HÌNH LOGGING TOÀN CỤC (Luật Thép L02)
# =====================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

from modules.scrapers import ScraperAgent
from modules.cleaner import CleanerAgent
from modules.storage import StorageAgent


# =====================================================================
# [DAY 29] FACTORY PATTERN — "Nhà máy sản xuất Agent"
# =====================================================================
# GIẢI THÍCH TẠI SAO:
#     Nếu không có Factory, bạn phải nhớ chính xác tên class của từng Agent:
#         scraper = ScraperAgent(key, topic)
#         cleaner = CleanerAgent()
#         storage = StorageAgent()
#     Rất rối khi có 10-20 loại Agent.
#
#     Với Factory, bạn chỉ cần gọi:
#         scraper = AgentFactory.create("scraper", key=key, topic=topic)
#     Factory sẽ tự biết phải tạo ra class nào. Code gọn gàng và dễ mở rộng.
#
# CÁCH THÊM AGENT MỚI:
#     Khi bạn muốn thêm "TelegramAgent" sau này, chỉ cần:
#     1. Tạo file telegram_agent.py (kế thừa BaseAgent)
#     2. Thêm 1 dòng vào _registry: "telegram": TelegramAgent
#     → main.py KHÔNG CẦN SỬA GÌ!
class AgentFactory:
    """
    [DAY 29] Nhà máy sản xuất Agent.
    Dùng Dictionary để ánh xạ tên (string) → Class tương ứng.
    """

    _registry = {
        "scraper": ScraperAgent,
        "cleaner": CleanerAgent,
        "storage": StorageAgent,
    }

    @staticmethod
    def create(agent_type: str, **kwargs):
        """
        Tạo ra Agent theo tên.
        
        VÍ DỤ:
            AgentFactory.create("scraper", api_key="abc", topic="AI")
            → Trả về: ScraperAgent(api_key="abc", topic="AI")
        
        **kwargs nghĩa là gì?
            "Keyword Arguments" — Cho phép truyền BẤT KỲ tham số nào dưới dạng key=value.
            Factory không cần biết ScraperAgent cần gì, nó chỉ chuyển tiếp toàn bộ kwargs.
        """
        agent_class = AgentFactory._registry.get(agent_type)
        if not agent_class:
            raise ValueError(f"Không tìm thấy Agent loại: '{agent_type}'. "
                             f"Các loại hợp lệ: {list(AgentFactory._registry.keys())}")
        return agent_class(**kwargs)


def validate_topic(user_input: str) -> str | None:
    """Kiểm tra và chuẩn hóa từ khóa đầu vào."""
    topic = user_input.strip()
    if not topic:
        return "Artificial Intelligence"
    essence = re.sub(r'[^a-zA-Z0-9\s]', '', topic).strip()
    if not essence:
        return None
    clean_topic = re.sub(r'[\\/*?:"<>|]', "", topic).strip()
    return clean_topic[:50]


async def run_pipeline(scraper: ScraperAgent, cleaner: CleanerAgent, storage: StorageAgent):
    """
    Luồng ETL chính: Extract → Transform → Load.
    
    GIẢI THÍCH TẠI SAO TRUYỀN OBJECT VÀO (thay vì tạo mới bên trong):
        Kỹ thuật này gọi là "Dependency Injection" (Tiêm phụ thuộc).
        Thay vì hàm tự tạo Agent, ta "tiêm" Agent đã tạo sẵn từ bên ngoài vào.
        Lợi ích: Dễ test (có thể tiêm Agent giả để test) và linh hoạt hơn.
    """
    logging.info("=" * 60)
    logging.info(f"KHỞI ĐỘNG CHU KỲ QUÉT: '{scraper.topic.upper()}'")
    logging.info("=" * 60)

    # 1. EXTRACT — Trinh sát đi cào tin
    try:
        raw_news = await scraper.execute()
        if not raw_news:
            logging.warning("Không có dữ liệu thô. Kết thúc chu kỳ.")
            return
    except Exception as e:
        logging.error(f"Lỗi kết nối API: {e}")
        return

    # 2. TRANSFORM — Dọn dẹp làm sạch
    try:
        clean_news = await cleaner.execute(raw_news)
        logging.info(f"Đã trích xuất {cleaner.total_cleaned} tin độc nhất.")
    except Exception as e:
        logging.error(f"Lỗi thuật toán làm sạch: {e}")
        return

    # 3. LOAD — Hậu cần lưu trữ
    if clean_news:
        try:
            await storage.execute(clean_news, scraper.topic)
        except Exception as e:
            logging.error(f"Lỗi lưu trữ: {e}")

    logging.info("=" * 60 + "\n")


def run_pipeline_sync_wrapper(scraper, cleaner, storage):
    """Wrapper đồng bộ để chạy async bên trong thư viện schedule."""
    asyncio.run(run_pipeline(scraper, cleaner, storage))


def main():
    """Điểm khởi chạy chương trình — Nơi "Vị Tướng" ra lệnh."""
    load_dotenv()
    api_key = os.getenv("NEWS_API_KEY")
    if not api_key:
        logging.error("Thiếu NEWS_API_KEY trong file .env!")
        return

    logging.info("🤖 CHÀO MỪNG ĐẾN VỚI AI TREND AGENT v3.0 (OOP Edition)")

    # Nhận từ khóa từ người dùng
    target_topic = None
    while not target_topic:
        try:
            raw = input("\n👉 Mời bạn nhập từ khóa cần tìm: ")
        except KeyboardInterrupt:
            logging.info("Hủy khởi động. Tạm biệt!")
            return
        target_topic = validate_topic(raw)
        if not target_topic:
            logging.error("Từ khóa không hợp lệ. Vui lòng thử lại!")

    logging.info(f"Đã chốt mục tiêu: {target_topic}")

    # =====================================================================
    # [DAY 29] SỬ DỤNG FACTORY — Tạo đội quân Agent
    # =====================================================================
    # Thay vì: scraper = ScraperAgent(api_key, target_topic)
    # Ta dùng:  scraper = AgentFactory.create("scraper", ...)
    # Lợi ích: Khi thêm Agent mới, chỉ cần thêm 1 dòng vào _registry.
    scraper = AgentFactory.create("scraper", api_key=api_key, topic=target_topic)
    cleaner = AgentFactory.create("cleaner")
    storage = AgentFactory.create("storage")

    # In thông tin Agent (tự động gọi __str__ từ Day 25)
    logging.info(f"Đã triển khai: {scraper}")
    logging.info(f"Đã triển khai: {cleaner}")
    logging.info(f"Đã triển khai: {storage}")

    # Chạy chu kỳ đầu tiên
    time.sleep(1)
    run_pipeline_sync_wrapper(scraper, cleaner, storage)

    # Lập lịch trình tự động
    schedule.every(4).hours.do(run_pipeline_sync_wrapper,
                               scraper=scraper, cleaner=cleaner, storage=storage)

    logging.info(f"AGENT ĐÃ CHUYỂN SANG CHẾ ĐỘ TRỰC CANH (4 GIỜ/LẦN)")
    logging.info("Nhấn [Ctrl + C] để tắt hệ thống.")

    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("=" * 60)
        logging.info("ĐANG TẮT HỆ THỐNG AN TOÀN...")
        logging.info("=" * 60)


if __name__ == "__main__":
    main()