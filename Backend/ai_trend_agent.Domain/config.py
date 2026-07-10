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
NEWSAPI_URL: str = "https://newsapi.org/v2/everything"  # Endpoint tìm kiếm bài viết
NEWSAPI_PAGE_SIZE: int = 10          # Số bài tối đa lấy từ NewsAPI mỗi lần
NEWSAPI_LANGUAGE: str = "en"         # Ngôn ngữ bài viết yêu cầu NewsAPI trả về
GOOGLE_RSS_URL: str = "https://news.google.com/rss/search"  # Endpoint RSS tìm kiếm
GOOGLE_RSS_PARAMS: dict[str, str] = {"hl": "en-US", "gl": "US", "ceid": "US:en"}  # Locale cố định cho RSS
REDDIT_LIMIT: int = 5               # Số bài tối đa lấy từ Reddit
REDDIT_SUBREDDIT: str = "ArtificialIntelligence"  # Tên subreddit ĐÚNG CHÍNH TẢ
GOOGLE_RSS_LIMIT: int = 5           # Số bài tối đa lấy từ Google News RSS
REDDIT_USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
REDDIT_OAUTH_TOKEN_URL: str = "https://www.reddit.com/api/v1/access_token"  # Endpoint lấy access token
REDDIT_OAUTH_API_BASE: str = "https://oauth.reddit.com"  # API base khi đã xác thực OAuth

# --- RETRY CONFIG ---
GEMINI_RETRY_MAX: int = 3            # Số lần thử lại tối đa khi Gemini 503
GEMINI_RETRY_BASE_DELAY: float = 2.0 # Delay ban đầu (giây), tăng gấp đôi mỗi lần

# --- GEMINI BUDGET (ADR 0005 — budget enforcement) ---
GEMINI_MAX_CALLS_PER_CYCLE: int = 12  # Trần số request Gemini MỖI chu kỳ. Vượt → trả fallback, KHÔNG gọi (chống runaway cost/quota)
GEMINI_CONCURRENCY: int = 1           # Số request Gemini song song tối đa (free tier ~5 RPM → nối tiếp)
GEMINI_APPROX_CHARS_PER_TOKEN: int = 4 # Ước lượng token đầu vào ~ len(prompt)/4 để log chi phí

# --- PIPELINE CONFIG ---
SCHEDULE_INTERVAL_HOURS: int = 4    # Chu kỳ quét tự động (giờ)
MAX_TOPIC_LENGTH: int = 50          # Độ dài tối đa từ khóa tìm kiếm

# --- AI CONFIG (PHASE 4) ---
GEMINI_MODEL_NAME: str = "gemini-2.5-flash" # Mô hình tối ưu tốc độ/chi phí
AI_MAX_ARTICLES_PER_BATCH: int = 15         # Số bài tối đa gửi AI mỗi lần để tránh quá tải
AI_BATCH_SIZE: int = 5                      # Số bài gộp vào một prompt duy nhất (batch prompting)

# --- AI CLEANER CONFIG (PHASE B) ---
CLEANER_AI_MODEL: str = "gemini-2.5-flash"   # Model chấm điểm liên quan + gán tag
CLEANER_RELEVANCE_THRESHOLD: int = 4         # Bài < ngưỡng này bị loại (lạc đề)
CLEANER_AI_BATCH_SIZE: int = 30              # Số bài tối đa gửi AI mỗi chu kỳ

# --- TREND SYNTHESIS CONFIG (PHASE A) ---
TREND_MODEL_NAME: str = "gemini-2.5-flash"  # Mô hình dùng cho phân tích xu hướng
TREND_MAX_ARTICLES: int = 30                # Số bài tối đa đưa vào prompt phân tích xu hướng
TREND_MIN_ARTICLES: int = 3                 # Dưới ngưỡng này thì bỏ qua (không đủ để rút xu hướng)
TREND_COUNT: int = 5                        # Số xu hướng tối đa AI cần rút ra

# --- TELEGRAM CONFIG (PHASE 6 — legacy, không còn dùng trong pipeline) ---
TELEGRAM_API_BASE: str = "https://api.telegram.org"  # Endpoint gốc Bot API
TELEGRAM_MAX_MESSAGE_LENGTH: int = 4000  # Giới hạn an toàn (Telegram cap cứng 4096)
TELEGRAM_PARSE_MODE: str = "HTML"        # HTML dễ escape hơn Markdown
TELEGRAM_SEND_DELAY: float = 0.5         # Giây nghỉ giữa các chunk để tránh rate limit 429

# --- DISCORD CONFIG (PHASE 6 — publisher hiện hành, thay Telegram) ---
DISCORD_MAX_MESSAGE_LENGTH: int = 1900   # Giới hạn an toàn (Discord cap cứng 2000 ký tự/message)
DISCORD_SEND_DELAY: float = 0.6          # Giây nghỉ giữa các chunk để tránh rate limit (5 req/s)
DISCORD_USERNAME: str = "AI Trend Agent" # Tên hiển thị của webhook khi đăng bài
DISCORD_SUPPRESS_EMBEDS_FLAG: int = 4    # Bitflag SUPPRESS_EMBEDS — tắt unfurl link (card rác)

# --- STORAGE CONFIG ---
OUTPUT_DIR: str = "data"             # Thư mục lưu file CSV
CSV_FIELDNAMES: list[str] = ["STT", "Tieu_De", "Nguon", "Ngay", "Tags", "Tom_Tat", "Tam_Ly", "Link_Bai"]
