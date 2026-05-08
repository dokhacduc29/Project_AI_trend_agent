"""
=====================================================================
[DAY 31-40] SUMMARIZATION AGENT — "Bộ não" của hệ thống
=====================================================================
Áp dụng:
- Context Managers (Day 35): Quản lý phiên kết nối API an toàn.
- Generators (Day 32): Xử lý luồng dữ liệu (nếu cần stream).
- Decorators (Day 33-34): Theo dõi tốc độ và ghi log.
=====================================================================
"""
import asyncio
import google.generativeai as genai
from google.generativeai.types import generation_types

from modules.base_agent import BaseAgent, AgentFactory
from modules.models import PipelineContext, Sentiment
from modules import config
from modules.decorators import ai_timer, ai_logger


@AgentFactory.register("analyzer")
class SummarizationAgent(BaseAgent):
    """Chuyên viên phân tích — Nhận bài báo, đẩy cho Gemini tóm tắt."""

    def __init__(self, **kwargs):
        super().__init__("SummarizationAgent")
        self._model = None

    def _setup_gemini(self, api_key: str):
        """Cấu hình Gemini API."""
        genai.configure(api_key=api_key)
        # Sử dụng mô hình từ config
        self._model = genai.GenerativeModel(config.GEMINI_MODEL_NAME)

    @ai_logger
    @ai_timer
    async def _analyze_batch(self, batch_text: str) -> str:
        """
        [Day 46] Bất đồng bộ: Gọi API Gemini.
        Vì thư viện google-generativeai có hàm generate_content_async.
        """
        prompt = (
            f"Bạn là một chuyên gia phân tích tin tức thị trường AI.\n"
            f"Dưới đây là một danh sách các bài báo. Hãy tóm tắt NGẮN GỌN (tối đa 3 dòng) "
            f"và đánh giá Sentiment (Tích cực, Tiêu cực, hoặc Trung lập).\n"
            f"Định dạng trả về:\n"
            f"Tóm tắt: [Nội dung]\n"
            f"Tâm lý: [Tích cực/Tiêu cực/Trung lập]\n\n"
            f"Bài báo:\n{batch_text}"
        )
        
        try:
            # Context manager (Day 35) có thể không khả dụng trực tiếp cho hàm này
            # Nhưng ta dùng async an toàn để tránh block the thread
            response = await self._model.generate_content_async(prompt)
            return response.text
        except Exception as e:
            self.log_error(f"Lỗi khi gọi Gemini: {e}")
            return "Tóm tắt: Không thể tóm tắt do lỗi API.\nTâm lý: Trung lập"

    def _parse_ai_response(self, response_text: str, article):
        """Phân tích kết quả text từ AI về dạng Object."""
        lines = response_text.split('\n')
        summary = ""
        sentiment_val = Sentiment.NEUTRAL

        for line in lines:
            line = line.strip()
            if line.startswith("Tóm tắt:"):
                summary = line.replace("Tóm tắt:", "").strip()
            elif line.startswith("Tâm lý:"):
                sent_str = line.replace("Tâm lý:", "").strip().lower()
                if "tích cực" in sent_str:
                    sentiment_val = Sentiment.BULLISH
                elif "tiêu cực" in sent_str:
                    sentiment_val = Sentiment.BEARISH

        article.summary = summary if summary else "Không có tóm tắt."
        article.sentiment = sentiment_val

    async def execute(self, ctx: PipelineContext) -> PipelineContext:
        """
        [FIX LSP] Hàm xử lý chính.
        """
        if not ctx.gemini_api_key:
            self.log_error("Thiếu GEMINI_API_KEY. Bỏ qua phân tích AI.")
            return ctx

        if not ctx.articles:
            self.log_info("Không có bài báo nào để phân tích.")
            return ctx

        self._setup_gemini(ctx.gemini_api_key)
        self.log_info(f"Bắt đầu phân tích {len(ctx.articles)} bài báo bằng {config.GEMINI_MODEL_NAME}...")

        # [Day 31/32] Dùng logic batching/Iterables để xử lý số lượng lớn
        # Gửi từng bài (hoặc gộp batch). Để đơn giản & chất lượng, ta phân tích từng bài một
        # Tuy nhiên, để tối ưu tốc độ, ta dùng asyncio.gather (tối đa N bài cùng lúc)
        
        limit = min(len(ctx.articles), config.AI_MAX_ARTICLES_PER_BATCH)
        articles_to_process = ctx.articles[:limit]

        async def process_single_article(article):
            text_to_analyze = f"Title: {article.title}\nDate: {article.date}\nSource: {article.source}"
            response_text = await self._analyze_batch(text_to_analyze)
            self._parse_ai_response(response_text, article)

        # Chạy đồng thời các tác vụ (Day 45-46)
        tasks = [process_single_article(article) for article in articles_to_process]
        await asyncio.gather(*tasks)

        self.log_info("Hoàn thành phân tích AI.")
        return ctx
