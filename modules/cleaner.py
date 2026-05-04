"""
=====================================================================
[DAY 23-26] CLEANER AGENT — "Lính dọn dẹp" làm sạch & phân loại tin
=====================================================================
GIẢI THÍCH KIẾN TRÚC:
    CleanerAgent kế thừa từ BaseAgent. Nó nhận vào danh sách bài báo "bẩn" (raw)
    và nhả ra danh sách bài báo "sạch" (đã lọc trùng, đã gán tag, đã sắp xếp).

KỸ THUẬT ÁP DỤNG:
    - [DAY 23] Inheritance: CleanerAgent(BaseAgent) — Kế thừa log_info, log_error.
    - [DAY 26] @staticmethod: Hàm extract_entities() KHÔNG CẦN self → Đánh dấu là Static.
    - [DAY 26] @property: Biến total_cleaned thành thuộc tính chỉ đọc (Read-only).
    - [DAY 18] Regex: Quét tiêu đề để gán nhãn thực thể (#OpenAI, #Google...).
    - [DAY 15] Big-O: Set lookup O(1), Duyệt O(N), Sort O(N log N).
=====================================================================
"""
import re
from modules.base_agent import BaseAgent
from modules.models import Article


class CleanerAgent(BaseAgent):
    """Lính dọn dẹp — Lọc rác, gán tag, sắp xếp thứ tự thời gian."""

    def __init__(self):
        super().__init__("CleanerAgent")
        # [DAY 24] Encapsulation: _cleaned_articles là biến NỘI BỘ
        # Bên ngoài muốn biết số lượng? Dùng property total_cleaned (xem bên dưới).
        self._cleaned_articles: list[Article] = []

    # =====================================================================
    # [DAY 26] @property — Biến method thành "thuộc tính ảo" chỉ đọc
    # =====================================================================
    # Bình thường muốn lấy số bài đã lọc, bạn phải gọi: agent.get_total()  ← Xấu
    # Với @property, bạn gọi: agent.total_cleaned  ← Đẹp, giống thuộc tính bình thường
    # Nhưng nó KHÔNG CHO PHÉP gán: agent.total_cleaned = 100  ← Lỗi ngay! (Read-only)
    #
    # TẠI SAO DÙNG PROPERTY MÀ KHÔNG DÙNG BIẾN THƯỜNG?
    # Vì biến thường có thể bị gán bừa (agent.total = -999). Property bảo vệ dữ liệu.
    @property
    def total_cleaned(self) -> int:
        """Số bài báo đã qua lọc (chỉ đọc, không cho phép gán)."""
        return len(self._cleaned_articles)

    # =====================================================================
    # [DAY 26] @staticmethod — Method KHÔNG CẦN đối tượng
    # =====================================================================
    # Hàm extract_entities() chỉ cần 1 chuỗi text đầu vào, nó không dùng self.
    # → Đánh dấu @staticmethod để nói rõ: "Hàm này KHÔNG phụ thuộc vào bất kỳ object nào".
    #
    # CÁCH GỌI:
    #   Gọi qua class (không cần tạo object): CleanerAgent.extract_entities("GPT-5 released")
    #   Gọi qua object (cũng được):           agent.extract_entities("GPT-5 released")
    @staticmethod
    def extract_entities(text: str) -> list[str]:
        """[DAY 18 Regex] Quét tiêu đề để nhận diện thực thể công nghệ."""
        tags = []
        # Mỗi cặp (pattern, tag) được gom vào tuple để code DRY (Don't Repeat Yourself)
        entity_patterns = [
            (r'\b(openai|chatgpt|gpt[-]?4[o]?)\b', "#OpenAI"),
            (r'\b(google|gemini|deepmind|alphabet)\b', "#Google"),
            (r'\b(microsoft|copilot|azure)\b', "#Microsoft"),
            (r'\b(meta|llama|zuckerberg)\b', "#Meta"),
            (r'\b(anthropic|claude)\b', "#Anthropic"),
            (r'\bapple\b', "#Apple"),
            (r'\$[\d]+[MB]?', "#Funding_Money"),
        ]
        for pattern, tag in entity_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                tags.append(tag)
        return tags

    async def execute(self, raw_articles: list[Article]) -> list[Article]:
        """
        [DAY 27] Override execute() — Luồng làm sạch chính.
        
        LUỒNG CHẠY:
            1. Duyệt từng bài báo thô
            2. Bỏ qua bài không có tiêu đề
            3. Gán tag bằng Regex (extract_entities)
            4. Làm sạch tiêu đề (xóa ký tự đặc biệt, lowercase)
            5. Lọc trùng bằng Set (O(1))
            6. Sắp xếp theo ngày mới nhất (Timsort O(N log N))
        """
        self.log_info(f"Nhận {len(raw_articles)} bài thô. Bắt đầu lọc...")
        seen: set[str] = set()
        self._cleaned_articles = []

        for article in raw_articles:
            if not article.title:
                continue

            # Gán tag trước khi làm sạch (vì làm sạch sẽ lowercase → mất chữ viết hoa)
            article.tags = self.extract_entities(article.title)

            # Chuẩn hóa tiêu đề
            clean_title = re.sub(r'[^\w\s+\-&#.]', '', article.title).lower().strip()

            # [DAY 15] Lọc trùng bằng Set: Tốc độ O(1) cho mỗi lần kiểm tra
            if clean_title and clean_title not in seen:
                article.title = clean_title
                self._cleaned_articles.append(article)
                seen.add(clean_title)

        # [DAY 16] Sắp xếp: Bài mới nhất lên đầu
        self._cleaned_articles.sort(key=lambda a: a.date, reverse=True)

        self.log_info(f"Lọc xong: {self.total_cleaned} bài sạch, độc nhất")
        return self._cleaned_articles
