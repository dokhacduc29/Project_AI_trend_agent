import re
from collections import namedtuple

# =====================================================================
# [DAY 14] TỐI ƯU BỘ NHỚ VỚI NAMEDTUPLE (Thay thế Dictionary)
# =====================================================================
# Tối ưu hiệu suất (Big-O Memory): 
# - Dictionary tốn nhiều bộ nhớ vì phải lưu trữ con trỏ băm (Hash Table overhead).
# - namedtuple tốn bộ nhớ ít y hệt Tuple thông thường, nhưng lại cho phép gọi bằng tên biến (vd: article.title).
Article = namedtuple('Article', ['title', 'source', 'date', 'url', 'tags'])

def validate_topic(user_input: str) -> str:
    """Kiểm tra và chuẩn hóa từ khóa đầu vào của người dùng."""
    topic = user_input.strip()
    if not topic:
        return "Artificial Intelligence"

    # [DAY 18 Regex] Lọc lấy "phần hồn" (chữ cái và chữ số)
    essence = re.sub(r'[^a-zA-Z0-9\s]', '', topic).strip()
    if not essence:
        return None

    clean_topic = re.sub(r'[\\/*?:"<>|]', "", topic).strip()
    return clean_topic[:50]

def generate_safe_filename(topic: str) -> str:
    """Biến đổi từ khóa thành tên file CSV an toàn cho hệ điều hành."""
    safe_name = re.sub(r'[\\/*?:"<>|]', "", topic)
    safe_name = safe_name.strip().replace(" ", "_").lower()
    if not safe_name:
        return "unknown_topic_news.csv"
    return f"{safe_name}_news.csv"