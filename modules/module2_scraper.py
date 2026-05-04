import httpx
import asyncio
import xml.etree.ElementTree as ET
import logging
from modules.module4_utils import Article

async def get_news_from_newsapi(client: httpx.AsyncClient, api_key: str, topic="Artificial Intelligence") -> list:
    url = f"https://newsapi.org/v2/everything?q={topic}&language=en&pageSize=10&apiKey={api_key}"
    try:
        response = await client.get(url, timeout=10.0)
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") == "ok":
            # [DAY 14] Đúc dữ liệu thành đối tượng Article (NamedTuple) thay vì Dictionary
            articles = [
                Article(
                    title=post.get("title", ""),
                    source=post.get("source", {}).get("name", "Unknown"),
                    date=post.get("publishedAt", "1970-01-01")[:10],
                    url=post.get("url", ""),
                    tags=[]
                )
                for post in data.get("articles", [])
                if post.get("title") and "[Removed]" not in post.get("title")
            ]
            return articles
        else:
            logging.error(f"Lỗi cấu trúc dữ liệu từ NewsAPI: {data.get('message')}")
            return []
    except Exception as e:
        logging.error(f"LỖI MẠNG NewsAPI: {e}")
        return []

async def get_news_from_reddit(client: httpx.AsyncClient, topic: str) -> list:
    headers = {"User-Agent": "AI-Trend-Agent-V2"}
    url = f"https://www.reddit.com/r/ArtificialInteligence/new.json?limit=5"
    try:
        res = await client.get(url, headers=headers, timeout=10.0)
        res.raise_for_status()
        data = res.json()
        posts = data['data']['children']
        
        return [
            Article(
                title=p['data'].get("title", ""),
                source="Reddit",
                date="N/A", 
                url=f"https://www.reddit.com{p['data'].get('permalink', '')}",
                tags=[]
            )
            for p in posts
        ]
    except Exception as e:
        logging.error(f"Lỗi truy xuất Reddit: {e}")
        return []

async def get_news_from_google_rss(client: httpx.AsyncClient, topic: str) -> list:
    url = f"https://news.google.com/rss/search?q={topic}&hl=en-US&gl=US&ceid=US:en"
    try:
        res = await client.get(url, timeout=10.0)
        res.raise_for_status()
        root = ET.fromstring(res.text)
        articles = []
        for item in root.findall('.//item')[:5]:
            title = item.find('title').text if item.find('title') is not None else ""
            link = item.find('link').text if item.find('link') is not None else ""
            pub_date = item.find('pubDate').text if item.find('pubDate') is not None else "N/A"
            source_elem = item.find('source')
            source = source_elem.text if source_elem is not None else "Google News RSS"
            
            articles.append(Article(title=title, source=source, date=pub_date[:16], url=link, tags=[]))
            
        return articles
    except Exception as e:
        logging.error(f"Lỗi Google News RSS: {e}")
        return []

async def get_all_sources(api_key: str, topic: str) -> list:
    all_news = []
    async with httpx.AsyncClient() as client:
        tasks = [
            get_news_from_newsapi(client, api_key, topic),
            get_news_from_reddit(client, topic),
            get_news_from_google_rss(client, topic)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for idx, result in enumerate(results):
            if isinstance(result, list):
                all_news.extend(result)
            elif isinstance(result, Exception):
                logging.error(f"Lỗi nghiêm trọng ở Task số {idx}: {result}")
    return all_news