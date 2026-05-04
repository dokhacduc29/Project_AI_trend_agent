"""
=====================================================================
[LUẬT THÉP L09] CONFIG — Tập trung MỌI hằng số / Magic Numbers
=====================================================================
TẠI SAO CẦN FILE NÀY?
    Trước đây: timeout=10.0, limit=5, pageSize=10 nằm rải rác khắp nơi.
    Nếu muốn đổi timeout thành 15s, bạn phải mò từng file → Dễ sót, dễ bug.
    
    Giờ: Tất cả nằm ở ĐÂY. Đổi 1 chỗ = áp dụng toàn hệ thống.
=====================================================================
"""

# --- SCRAPER CONFIG ---
REQUEST_TIMEOUT: float = 10.0       # Giây chờ tối đa cho mỗi API call
NEWSAPI_PAGE_SIZE: int = 10          # Số bài tối đa lấy từ NewsAPI mỗi lần
REDDIT_LIMIT: int = 5               # Số bài tối đa lấy từ Reddit
REDDIT_SUBREDDIT: str = "ArtificialIntelligence"  # Tên subreddit ĐÚNG CHÍNH TẢ
GOOGLE_RSS_LIMIT: int = 5           # Số bài tối đa lấy từ Google News RSS
REDDIT_USER_AGENT: str = "AI-Trend-Agent-V3-OOP"

# --- PIPELINE CONFIG ---
SCHEDULE_INTERVAL_HOURS: int = 4    # Chu kỳ quét tự động (giờ)
MAX_TOPIC_LENGTH: int = 50          # Độ dài tối đa từ khóa tìm kiếm

# --- STORAGE CONFIG ---
OUTPUT_DIR: str = "data"             # Thư mục lưu file CSV
CSV_FIELDNAMES: list[str] = ["STT", "Tieu_De", "Nguon", "Ngay", "Tags", "Link_Bai"]
