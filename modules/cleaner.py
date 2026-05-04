"""
=====================================================================
CLEANER AGENT — Làm sạch & phân loại tin (BẢN SỬA LSP + OCP)
=====================================================================
FIX LIST:
    - [LSP] execute(ctx: PipelineContext) → PipelineContext
    - [OCP] @AgentFactory.register("cleaner")
=====================================================================
"""
import re
from modules.base_agent import BaseAgent, AgentFactory
from modules.models import Article, PipelineContext


@AgentFactory.register("cleaner")
class CleanerAgent(BaseAgent):
    """Lính dọn dẹp — Lọc rác, gán tag, sắp xếp."""

    def __init__(self, **kwargs):
        super().__init__("CleanerAgent")
        self._cleaned_count: int = 0

    @property
    def total_cleaned(self) -> int:
        return self._cleaned_count

    @staticmethod
    def extract_entities(text: str) -> list[str]:
        """[DAY 18 Regex] Quét tiêu đề để gán nhãn thực thể."""
        tags = []
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

    async def execute(self, ctx: PipelineContext) -> PipelineContext:
        """
        [FIX LSP] Chữ ký thống nhất: nhận PipelineContext, trả PipelineContext.
        Đọc ctx.articles (bài thô), lọc sạch, ghi đè lại ctx.articles (bài sạch).
        """
        self.log_info(f"Nhận {len(ctx.articles)} bài thô. Bắt đầu lọc...")
        seen: set[str] = set()
        cleaned: list[Article] = []

        for article in ctx.articles:
            if not article.title:
                continue
            article.tags = self.extract_entities(article.title)
            clean_title = re.sub(r'[^\w\s+\-&#.]', '', article.title).lower().strip()
            if clean_title and clean_title not in seen:
                article.title = clean_title
                cleaned.append(article)
                seen.add(clean_title)

        cleaned.sort(key=lambda a: a.date, reverse=True)
        self._cleaned_count = len(cleaned)
        ctx.articles = cleaned

        self.log_info(f"Lọc xong: {self._cleaned_count} bài sạch, độc nhất")
        return ctx
