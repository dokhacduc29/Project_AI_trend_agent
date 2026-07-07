"""
=====================================================================
DISCORD AGENT — Gửi thông báo đến người dùng (PHASE 6 — thay Telegram)
=====================================================================
Bắn tin tức đã phân tích về một kênh Discord qua Incoming Webhook.

TẠI SAO WEBHOOK (không phải Bot)?
    - Không cần tạo bot, không cần OAuth/intents/gateway.
    - Chỉ cần URL webhook tạo trong: Channel → Settings → Integrations
      → New Webhook → Copy URL. Dán vào DISCORD_WEBHOOK_URL trong .env.

Áp dụng Iron Laws:
    - L03 Async-first: httpx.AsyncClient cho mọi API call.
    - L07 Fault tolerance: timeout + try/except trên từng request.
    - L09 No magic numbers: hằng số → config.py.
    - L02 Logging only: không print.

Định dạng: DIGEST gộp (Markdown) — gộp các bài vào một/vài tin nhắn,
tự chia chunk khi vượt giới hạn 2000 ký tự của Discord.
=====================================================================
"""
import os
import asyncio
import httpx
from base_agent import BaseAgent, AgentFactory
from models import Article, PipelineContext, Sentiment, TrendReport
import config


# Biểu tượng cảm xúc theo sentiment để nhìn nhanh xu hướng
_SENTIMENT_EMOJI = {
    Sentiment.BULLISH: "📈",
    Sentiment.BEARISH: "📉",
    Sentiment.NEUTRAL: "➖",
}


def _escape_md(text: str) -> str:
    """Khử các ký tự Markdown của Discord để tránh vỡ định dạng tiêu đề/tóm tắt."""
    for ch in ("\\", "*", "_", "`", "~", "|", ">"):
        text = text.replace(ch, f"\\{ch}")
    return text


@AgentFactory.register("discord")
class DiscordAgent(BaseAgent):
    """Lính liên lạc — Gửi tin tức đã phân tích qua Discord Webhook."""

    def __init__(self, **kwargs):
        super().__init__("DiscordAgent")

    async def execute(self, ctx: PipelineContext) -> PipelineContext:
        """
        Gửi các bài báo đã được tóm tắt qua Discord dưới dạng digest gộp.
        Tự đọc DISCORD_WEBHOOK_URL từ .env.
        """
        webhook_url = os.getenv("DISCORD_WEBHOOK_URL")

        if not webhook_url:
            self.log_info("Thiếu DISCORD_WEBHOOK_URL. Bỏ qua bước gửi Discord.")
            return ctx

        if not ctx.articles:
            self.log_info("Không có bài báo nào để gửi.")
            return ctx

        chunks = self._build_digest_chunks(ctx.articles, ctx.topic, ctx.trend_report)
        self.log_info(f"Chuẩn bị gửi {len(ctx.articles)} bài (chia thành {len(chunks)} tin nhắn) qua Discord...")

        sent = 0
        async with httpx.AsyncClient() as client:
            for idx, chunk in enumerate(chunks, start=1):
                if await self._send_message(client, webhook_url, chunk):
                    sent += 1
                # Nghỉ giữa các chunk để tránh rate limit (trừ chunk cuối)
                if idx < len(chunks):
                    await asyncio.sleep(config.DISCORD_SEND_DELAY)

        self.log_info(f"Đã gửi thành công {sent}/{len(chunks)} tin nhắn qua Discord.")
        return ctx

    async def _send_message(self, client: httpx.AsyncClient, webhook_url: str, content: str) -> bool:
        """Gửi một tin nhắn qua webhook. Trả True nếu thành công, False nếu lỗi."""
        payload = {
            "username": config.DISCORD_USERNAME,
            "content": content,
            # Tắt unfurl link rườm rà; vẫn cho phép mention=none để an toàn
            "allowed_mentions": {"parse": []},
            # SUPPRESS_EMBEDS: chặn card preview tự sinh từ link (Google News rác)
            "flags": config.DISCORD_SUPPRESS_EMBEDS_FLAG,
        }
        try:
            res = await client.post(webhook_url, json=payload, timeout=config.REQUEST_TIMEOUT)
            res.raise_for_status()
            return True
        except Exception as e:
            self.log_error(f"Lỗi gửi Discord: {e}")
            return False

    def _build_digest_chunks(
        self, articles: list[Article], topic: str, trend: TrendReport | None = None
    ) -> list[str]:
        """
        Gộp các bài thành digest Markdown, tự chia thành nhiều chunk khi vượt
        DISCORD_MAX_MESSAGE_LENGTH. Không bao giờ cắt giữa một bài báo.
        Nếu có TrendReport → đặt phần xu hướng lên ĐẦU chunk đầu tiên.
        """
        header = f"📰 **AI TREND DIGEST — {_escape_md(topic.upper())}**\n\n"
        blocks = [self._format_article(i, art) for i, art in enumerate(articles, start=1)]

        chunks: list[str] = []
        first_prefix = self._format_trend(trend) + header if trend and trend.generated else header
        current = first_prefix
        for block in blocks:
            if len(current) + len(block) > config.DISCORD_MAX_MESSAGE_LENGTH and current not in (first_prefix, header):
                chunks.append(current.rstrip())
                current = header
            current += block

        if current.strip() and current not in (first_prefix, header):
            chunks.append(current.rstrip())
        elif not chunks and current.strip():
            chunks.append(current.rstrip())
        return chunks

    def _format_trend(self, trend: TrendReport) -> str:
        """Định dạng phần phân tích xu hướng (đặt đầu digest)."""
        emoji = _SENTIMENT_EMOJI.get(trend.overall_sentiment, "➖")
        lines = [f"🔮 **XU HƯỚNG AI — {emoji} {_escape_md(trend.overall_sentiment.value)}**"]
        for t in trend.trends:
            lines.append(f"• {_escape_md(t)}")
        if trend.insight:
            lines.append(f"\n💬 *{_escape_md(trend.insight)}*")
        return "\n".join(lines) + "\n\n" + "─" * 15 + "\n\n"

    def _format_article(self, index: int, art: Article) -> str:
        """Định dạng MỘT bài báo thành block Markdown cho Discord."""
        emoji = _SENTIMENT_EMOJI.get(art.sentiment, "➖")
        title = _escape_md(art.title or "Không có tiêu đề")
        source = _escape_md(art.source or "Unknown")
        summary = _escape_md(art.summary) if art.summary else ""

        # Discord render [text](url); URL không escape markdown
        title_line = f"`{index}.` {emoji} **[{title}]({art.url})**" if art.url else f"`{index}.` {emoji} **{title}**"
        lines = [title_line]
        if summary:
            lines.append(f"   📝 {summary}")
        lines.append(f"   📰 {source} | 📅 {_escape_md(art.date)}")
        return "\n".join(lines) + "\n\n"
