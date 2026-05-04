"""
=====================================================================
[DAY 28] DATACLASSES — "Khuôn đúc dữ liệu" thông minh
=====================================================================
GIẢI THÍCH TẠI SAO THAY THẾ NAMEDTUPLE:
    Ở Phase 2 (Day 14), ta dùng namedtuple để lưu bài báo. Nhưng nó có 2 nhược điểm:
    1. BẤT BIẾN (Immutable): Muốn sửa tiêu đề phải dùng _replace() tạo object mới → Tốn RAM.
    2. KHÔNG CÓ Type Hinting tự động: IDE không gợi ý được kiểu dữ liệu của từng trường.
    
    Dataclass giải quyết cả 2 vấn đề:
    1. MỀM DẺO (Mutable): Gán thẳng article.title = "abc" mà không cần _replace().
    2. Type Hinting tích hợp: IDE hiểu rõ từng trường là str, list, hay int.

CÁCH SỬ DỤNG:
    article = Article(title="GPT-5 ra mắt", source="NewsAPI", date="2026-05-04", url="https://...")
    article.title = "gpt-5 ra mắt"  # Sửa trực tiếp được (Mutable)!
    print(article)                   # In ra đẹp đẽ nhờ __str__
    print(len(article))              # Trả về số ký tự tiêu đề nhờ __len__

KỸ THUẬT ÁP DỤNG:
    - @dataclass: Decorator tự động sinh __init__, __repr__, __eq__ mà bạn KHÔNG CẦN viết tay.
    - field(default_factory=list): Tạo list rỗng mặc định MỚI cho mỗi object (tránh bug chia sẻ list).
    - [DAY 25] Dunder Methods: __str__, __repr__, __len__, __eq__ được customize thủ công.
=====================================================================
"""
from dataclasses import dataclass, field


@dataclass
class Article:
    """
    Bản thiết kế (Blueprint) cho MỘT bài báo.
    
    @dataclass tự động tạo ra hàm __init__ cho bạn. Thay vì phải viết tay:
        def __init__(self, title, source, date, url, tags):
            self.title = title
            self.source = source
            ...
    Bạn chỉ cần khai báo TÊN + KIỂU DỮ LIỆU, Python tự làm phần còn lại.
    """
    title: str                              # Tiêu đề bài viết (bắt buộc)
    source: str                             # Nguồn tin: NewsAPI, Reddit, Google (bắt buộc)
    date: str                               # Ngày xuất bản (bắt buộc)
    url: str                                # Link bài viết gốc (bắt buộc)
    tags: list = field(default_factory=list) # Nhãn phân loại tự động (mặc định = list rỗng [])
    # ↑ TẠI SAO DÙNG field(default_factory=list) MÀ KHÔNG DÙNG tags: list = [] ?
    # Vì nếu dùng tags=[], TẤT CẢ các bài báo sẽ DÙNG CHUNG 1 cái list đó (Bug rất nguy hiểm).
    # field(default_factory=list) đảm bảo MỖI bài báo được CẤP RIÊNG 1 list mới.

    # =====================================================================
    # [DAY 25] DUNDER METHODS — Tùy chỉnh hành vi "ma thuật" của object
    # =====================================================================

    def __str__(self) -> str:
        """
        Được Python tự động gọi khi bạn dùng: print(article)
        Kết quả: Hiển thị thông tin thân thiện, dễ đọc cho con người.
        
        VÍ DỤ:
            print(article) → "📰 gpt-5 ra mắt | Nguồn: NewsAPI | Ngày: 2026-05-04 | Tags: #OpenAI"
        """
        tag_str = ", ".join(self.tags) if self.tags else "Chưa phân loại"
        return f"📰 {self.title} | Nguồn: {self.source} | Ngày: {self.date} | Tags: {tag_str}"

    def __len__(self) -> int:
        """
        Được Python tự động gọi khi bạn dùng: len(article)
        Trả về số ký tự của tiêu đề. Hữu ích khi muốn lọc bài có tiêu đề quá ngắn (spam).
        
        VÍ DỤ:
            len(article) → 14  (nếu tiêu đề có 14 ký tự)
        """
        return len(self.title)

    def __eq__(self, other) -> bool:
        """
        Được Python tự động gọi khi bạn so sánh: article1 == article2
        Hai bài báo được coi là "trùng nhau" nếu có CÙNG tiêu đề (sau khi lowercase).
        
        TẠI SAO CHỈ SO title?
            Vì cùng 1 bài viết có thể xuất hiện trên cả NewsAPI lẫn Google News 
            (khác source, khác url) nhưng tiêu đề là giống nhau.
        """
        if not isinstance(other, Article):
            return False
        return self.title.lower() == other.title.lower()

    def __hash__(self) -> int:
        """
        [DAY 15 - Big-O] Cho phép đưa Article vào Set để lọc trùng với tốc độ O(1).
        Nếu không có __hash__, Python sẽ CẤM bạn bỏ Article vào set().
        
        Quy tắc bắt buộc: Nếu đã viết __eq__ thì PHẢI viết __hash__.
        """
        return hash(self.title.lower())
