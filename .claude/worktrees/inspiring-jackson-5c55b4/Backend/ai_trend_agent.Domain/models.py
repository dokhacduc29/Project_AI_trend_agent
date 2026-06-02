"""
=====================================================================
[DAY 28] MODELS — Cấu trúc dữ liệu cốt lõi
=====================================================================
FIX LSP (Liskov Substitution Principle):
    Vấn đề cũ: execute() có 3 chữ ký khác nhau → Không thể gọi đa hình.
    Giải pháp: Tạo PipelineContext — MỌI Agent đều nhận/trả CÙNG 1 loại context.
    
    ScraperAgent.execute(ctx) → Điền ctx.articles, trả ctx
    CleanerAgent.execute(ctx) → Lọc ctx.articles, trả ctx  
    StorageAgent.execute(ctx) → Lưu ctx.articles, trả ctx
    
    Giờ đây mọi agent đều có chữ ký: execute(ctx: PipelineContext) -> PipelineContext
    → Polymorphism THẬT SỰ hoạt động!
=====================================================================
"""
from dataclasses import dataclass, field
from enum import Enum

class Sentiment(Enum):
    """[DAY 38] Định nghĩa trạng thái thị trường."""
    BULLISH = "Tích cực"
    BEARISH = "Tiêu cực"
    NEUTRAL = "Trung lập"


@dataclass
class Article:
    """Bản thiết kế cho MỘT bài báo."""
    title: str
    source: str
    date: str
    url: str
    tags: list[str] = field(default_factory=list)
    summary: str = ""                     # [Phase 4] Nội dung tóm tắt từ AI
    sentiment: Sentiment = Sentiment.NEUTRAL # [Phase 4] Đánh giá tích cực/tiêu cực

    def __str__(self) -> str:
        tag_str = ", ".join(self.tags) if self.tags else "Chưa phân loại"
        return f"[{self.source}] {self.title} | {self.date} | Tags: {tag_str}"

    def __len__(self) -> int:
        return len(self.title)

    def __eq__(self, other) -> bool:
        if not isinstance(other, Article):
            return False
        return self.title.lower() == other.title.lower()

    def __hash__(self) -> int:
        return hash(self.title.lower())


@dataclass
class PipelineContext:
    """
    [FIX LSP] Đối tượng ngữ cảnh dùng chung cho MỌI Agent.
    
    TẠI SAO CẦN LỚP NÀY?
        Trước: ScraperAgent.execute() nhận 0 tham số, CleanerAgent nhận 1, StorageAgent nhận 2.
        → Không thể gọi agent.execute(ctx) đồng nhất. Polymorphism bị phá vỡ.
        
        Giờ: Mọi Agent đều nhận 1 PipelineContext và trả về PipelineContext.
        Mỗi Agent tự đọc cái nó cần (topic, api_key, articles) từ context.

    """
    topic: str = ""
    api_key: str = ""          # NewsAPI key
    gemini_api_key: str = ""   # [Phase 4] Gemini API key
    articles: list[Article] = field(default_factory=list)
