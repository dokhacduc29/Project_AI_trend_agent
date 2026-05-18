"""
=====================================================================
TELEGRAM AGENT — Gửi thông báo đến người dùng (PHASE 6)
=====================================================================
"""
import os
from base_agent import BaseAgent, AgentFactory
from models import PipelineContext

@AgentFactory.register("telegram")
class TelegramAgent(BaseAgent):
    """Lính liên lạc — Gửi tin tức đã phân tích qua Telegram Bot."""

    def __init__(self, **kwargs):
        super().__init__("TelegramAgent")

    async def execute(self, ctx: PipelineContext) -> PipelineContext:
        """
        Gửi các bài báo đã được tóm tắt (hoặc tin nổi bật) qua Telegram.
        """
        # TODO: Cần thêm logic đọc TELEGRAM_BOT_TOKEN và TELEGRAM_CHAT_ID từ .env
        telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")

        if not telegram_token or not chat_id:
            self.log_info("Thiếu TELEGRAM_BOT_TOKEN hoặc TELEGRAM_CHAT_ID. Bỏ qua bước gửi Telegram.")
            return ctx

        if not ctx.articles:
            self.log_info("Không có bài báo nào để gửi.")
            return ctx

        self.log_info(f"Chuẩn bị gửi {len(ctx.articles)} bài báo qua Telegram (Đang phát triển)...")
        
        # TODO: Implement httpx.post("https://api.telegram.org/bot<token>/sendMessage") ở đây
        
        return ctx
