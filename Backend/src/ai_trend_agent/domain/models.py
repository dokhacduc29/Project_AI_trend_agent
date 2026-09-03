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
from datetime import datetime
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
    relevance_score: int = -1             # [Phase B] Điểm liên quan 0-10 do AI chấm (-1 = chưa chấm)

    # ── [v5.0 / B2] Trường chỉ có khi bài ĐÃ được lưu ─────────────────────
    # Bài vừa cào về chưa có danh tính trong kho, nên cả ba đều None/rỗng.
    # Chỉ repository (đọc từ Supabase) mới điền chúng.
    #
    # Vì sao đặt ở đây thay vì tạo type `StoredArticle` riêng: `id` là danh
    # tính thật của một thực thể đã được lưu — đặt trên entity là cách làm
    # chuẩn. Tách type riêng thì đúng hơn về lý thuyết nhưng phải nuôi thêm
    # một model gần trùng và code map qua lại, không đáng cho phạm vi v5.0.
    #
    # Cả ba đều CÓ giá trị mặc định nên pipeline v4.0 dựng Article như cũ
    # vẫn chạy nguyên vẹn (ràng buộc C-04).
    id: int | None = None                 # Khoá chính trong Supabase
    created_at: datetime | None = None    # Thời điểm hệ thống thu thập (DB tự sinh)
    topic: str = ""                       # Chủ đề của chu kỳ đã thu thập bài này

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
class TrendReport:
    """
    [Phase A] Kết quả phân tích xu hướng XUYÊN SUỐT nhiều bài báo.

    Khác với Article.summary (tóm tắt TỪNG bài), TrendReport tổng hợp
    bức tranh lớn: các xu hướng đang nổi, tâm lý chung của thị trường.
    """
    trends: list[str] = field(default_factory=list)       # 3-5 xu hướng nổi (mỗi dòng 1 xu hướng)
    overall_sentiment: Sentiment = Sentiment.NEUTRAL      # Tâm lý tổng quan
    insight: str = ""                                     # Nhận định tổng quan 1-2 câu
    generated: bool = False                               # True nếu AI đã sinh thành công

    def __str__(self) -> str:
        if not self.generated or not self.trends:
            return "Chưa có phân tích xu hướng."
        lines = [f"- {t}" for t in self.trends]
        return (
            f"Tâm lý chung: {self.overall_sentiment.value}\n"
            + "\n".join(lines)
            + (f"\nNhận định: {self.insight}" if self.insight else "")
        )


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
    trend_report: "TrendReport" = field(default_factory=lambda: TrendReport())  # [Phase A] Phân tích xu hướng
