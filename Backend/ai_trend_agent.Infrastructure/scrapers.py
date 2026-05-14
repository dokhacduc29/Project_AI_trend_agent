"""
=====================================================================
SCRAPER AGENT — Cào tin đa nguồn (BẢN SỬA TOÀN BỘ BUGS & SMELLS)
=====================================================================
FIX LIST:
    - [SMELL] Magic numbers → Import từ config.py
    - [LSP] execute() signature thống nhất: nhận/trả PipelineContext
    - [OCP] Tự đăng ký vào Factory bằng decorator @AgentFactory.register
=====================================================================
"""
import httpx
import asyncio
import xml.etree.ElementTree as ET
from base_agent import BaseAgent, AgentFactory
from models import Article, PipelineContext
import config


@AgentFactory.register("scraper")
class ScraperAgent(BaseAgent):
    """Lính trinh sát — Cào tin từ 3 nguồn."""

    def __init__(self, **kwargs):
        super().__init__("ScraperAgent")

    async def execute(self, ctx: PipelineContext) -> PipelineContext:
        """
        [FIX LSP] Chữ ký thống nhất: nhận PipelineContext, trả PipelineContext.
        Agent tự đọc api_key và topic từ context, không cần truyền riêng.
        """
        self.log_info(f"Bắt đầu cào tin về: '{ctx.topic}'")

        async with httpx.AsyncClient() as client:
            tasks = [
                self._fetch_newsapi(client, ctx.api_key, ctx.topic),
                self._fetch_reddit(client),
                self._fetch_google_rss(client, ctx.topic),
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for idx, result in enumerate(results):
                if isinstance(result, list):
                    ctx.articles.extend(result)
                elif isinstance(result, Exception):
                    self.log_error(f"Task {idx} thất bại: {result}")

        self.log_info(f"Thu thập xong: {len(ctx.articles)} bài thô")
        return ctx

    async def _fetch_newsapi(self, client: httpx.AsyncClient, api_key: str, topic: str) -> list[Article]:
        url = (
            f"https://newsapi.org/v2/everything"
            f"?q={topic}&language=en"
            f"&pageSize={config.NEWSAPI_PAGE_SIZE}"
            f"&apiKey={api_key}"
        )
        try:
            response = await client.get(url, timeout=config.REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            if data.get("status") == "ok":
                return [
                    Article(
                        title=post.get("title", ""),
                        source=post.get("source", {}).get("name", "Unknown"),
                        date=post.get("publishedAt", "1970-01-01")[:10],
                        url=post.get("url", ""),
                    )
                    for post in data.get("articles", [])
                    if post.get("title") and "[Removed]" not in post.get("title")
                ]
            self.log_error(f"NewsAPI trả về lỗi: {data.get('message')}")
            return []
        except Exception as e:
            self.log_error(f"Lỗi mạng NewsAPI: {e}")
            return []

    async def _fetch_reddit(self, client: httpx.AsyncClient) -> list[Article]:
        headers = {"User-Agent": config.REDDIT_USER_AGENT}
        url = f"https://www.reddit.com/r/{config.REDDIT_SUBREDDIT}/new.json?limit={config.REDDIT_LIMIT}"
        try:
            res = await client.get(url, headers=headers, timeout=config.REQUEST_TIMEOUT)
            res.raise_for_status()
            posts = res.json()["data"]["children"]
            return [
                Article(
                    title=p["data"].get("title", ""),
                    source="Reddit",
                    date="N/A",
                    url=f"https://www.reddit.com{p['data'].get('permalink', '')}",
                )
                for p in posts
            ]
        except Exception as e:
            self.log_error(f"Lỗi Reddit: {e}")
            return []

    async def _fetch_google_rss(self, client: httpx.AsyncClient, topic: str) -> list[Article]:
        url = f"https://news.google.com/rss/search?q={topic}&hl=en-US&gl=US&ceid=US:en"
        try:
            res = await client.get(url, timeout=config.REQUEST_TIMEOUT)
            res.raise_for_status()
            root = ET.fromstring(res.text)
            articles = []
            for item in root.findall(".//item")[: config.GOOGLE_RSS_LIMIT]:
                title = item.find("title").text if item.find("title") is not None else ""
                link = item.find("link").text if item.find("link") is not None else ""
                pub_date = item.find("pubDate").text if item.find("pubDate") is not None else "N/A"
                source_el = item.find("source")
                source = source_el.text if source_el is not None else "Google News RSS"
                articles.append(Article(title=title, source=source, date=pub_date[:16], url=link))
            return articles
        except Exception as e:
            self.log_error(f"Lỗi Google RSS: {e}")
            return []
