"""
=====================================================================
[DAY 21-23] SCRAPER AGENT — "Lính trinh sát" đi cào tin đa nguồn
=====================================================================
GIẢI THÍCH KIẾN TRÚC:
    Ở Phase 2, ta có 4 hàm rời rạc (get_news_from_newsapi, get_news_from_reddit...).
    Giờ ta gom chúng thành 1 Class duy nhất: ScraperAgent.
    
    Lợi ích:
    1. Dữ liệu (api_key, topic) được lưu bên trong object → Không cần truyền đi truyền lại.
    2. Các hàm lấy tin trở thành "kỹ năng" (method) của Agent → Có tổ chức.
    3. Kế thừa (Inheritance) từ BaseAgent → Tự động có log_info, log_error mà không cần viết lại.

KỸ THUẬT ÁP DỤNG:
    - [DAY 21] Class & Object: ScraperAgent là Class, agent = ScraperAgent(...) là Object.
    - [DAY 22] Instance Attributes: self.api_key, self.topic — thuộc tính riêng của từng object.
    - [DAY 22] Instance Methods: _fetch_newsapi(), _fetch_reddit() — kỹ năng của object.
    - [DAY 23] Inheritance: ScraperAgent(BaseAgent) — Kế thừa "Hiến pháp" BaseAgent.
    - [DAY 24] Encapsulation: Dấu _ trước tên method (_fetch_*) = "Nội bộ, không gọi từ bên ngoài".
    - [DAY 26] @classmethod: Factory method from_env() tạo Agent từ file .env.
=====================================================================
"""
import httpx
import asyncio
import xml.etree.ElementTree as ET
from modules.base_agent import BaseAgent
from modules.models import Article


class ScraperAgent(BaseAgent):
    """
    [DAY 21] Lính trinh sát — Chịu trách nhiệm cào tin từ 3 nguồn.
    
    Kế thừa (Inheritance) từ BaseAgent:
        → Tự động có: __init__(agent_name), log_info(), log_error(), __str__(), __repr__()
        → Bắt buộc phải viết: execute() (vì BaseAgent yêu cầu bằng @abstractmethod)
    """

    def __init__(self, api_key: str, topic: str):
        """
        [DAY 22] Khởi tạo Agent trinh sát.
        
        GIẢI THÍCH super().__init__("ScraperAgent"):
            Dòng này gọi hàm __init__ của LỚP CHA (BaseAgent).
            Nó giống như lính mới nhập ngũ phải đến phòng nhân sự đăng ký tên trước (agent_name).
            Sau đó mới được nhận thêm trang bị riêng (api_key, topic).
        """
        super().__init__("ScraperAgent")      # Gọi __init__ của BaseAgent trước
        self.api_key = api_key                 # [DAY 22] Thuộc tính riêng: Chìa khóa API
        self.topic = topic                     # [DAY 22] Thuộc tính riêng: Từ khóa tìm kiếm

    # =====================================================================
    # [DAY 26] @classmethod — Factory Method (Phương thức Nhà máy)
    # =====================================================================
    # Khác với method thường (dùng self = đối tượng hiện tại),
    # @classmethod dùng 'cls' = chính cái LỚP (Class) đó.
    # Nó cho phép bạn tạo ra object BẰNG MỘT CÁCH KHÁC ngoài __init__ thông thường.
    #
    # VÍ DỤ SỬ DỤNG:
    #   Cách thường:  agent = ScraperAgent(api_key="abc", topic="AI")
    #   Cách Factory:  agent = ScraperAgent.from_env(topic="AI")  ← Tự đọc key từ .env
    @classmethod
    def from_env(cls, topic: str):
        """Tạo ScraperAgent bằng cách tự động đọc API key từ file .env."""
        import os
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv("NEWS_API_KEY", "")
        return cls(api_key=api_key, topic=topic)  # cls ở đây = ScraperAgent

    async def execute(self) -> list[Article]:
        """
        [DAY 27] Override (Ghi đè) method trừu tượng execute() từ BaseAgent.
        
        GIẢI THÍCH TẠI SAO PHẢI CÓ HÀM NÀY:
            BaseAgent đã đánh dấu execute() là @abstractmethod.
            Nếu ScraperAgent KHÔNG viết hàm này → Python sẽ cấm tạo object:
            TypeError: Can't instantiate abstract class ScraperAgent with abstract method execute
            
        LUỒNG CHẠY:
            1. Mở 1 session HTTP duy nhất (tiết kiệm RAM)
            2. Bắn 3 request CÙNG LÚC bằng asyncio.gather (tốc độ ánh sáng)
            3. Gom kết quả vào 1 danh sách và trả về
        """
        self.log_info(f"Bắt đầu cào tin về: '{self.topic}'")
        all_news: list[Article] = []

        async with httpx.AsyncClient() as client:
            tasks = [
                self._fetch_newsapi(client),
                self._fetch_reddit(client),
                self._fetch_google_rss(client)
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for idx, result in enumerate(results):
                if isinstance(result, list):
                    all_news.extend(result)
                elif isinstance(result, Exception):
                    self.log_error(f"Task số {idx} thất bại: {result}")

        self.log_info(f"Thu thập xong: {len(all_news)} bài thô")
        return all_news

    # =====================================================================
    # [DAY 24] ENCAPSULATION — Các method "nội bộ" (Private Convention)
    # =====================================================================
    # Dấu _ ở đầu tên method nghĩa là: "Method này chỉ dùng BÊN TRONG class thôi".
    # Bên ngoài KHÔNG NÊN gọi agent._fetch_newsapi() trực tiếp.
    # Thay vào đó, gọi agent.execute() — nó sẽ tự gọi 3 hàm _fetch bên trong.

    async def _fetch_newsapi(self, client: httpx.AsyncClient) -> list[Article]:
        """[Nội bộ] Lấy tin từ NewsAPI."""
        url = f"https://newsapi.org/v2/everything?q={self.topic}&language=en&pageSize=10&apiKey={self.api_key}"
        try:
            response = await client.get(url, timeout=10.0)
            response.raise_for_status()
            data = response.json()

            if data.get("status") == "ok":
                return [
                    Article(
                        title=post.get("title", ""),
                        source=post.get("source", {}).get("name", "Unknown"),
                        date=post.get("publishedAt", "1970-01-01")[:10],
                        url=post.get("url", "")
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
        """[Nội bộ] Lấy tin từ Reddit."""
        headers = {"User-Agent": "AI-Trend-Agent-V3-OOP"}
        url = "https://www.reddit.com/r/ArtificialInteligence/new.json?limit=5"
        try:
            res = await client.get(url, headers=headers, timeout=10.0)
            res.raise_for_status()
            posts = res.json()["data"]["children"]
            return [
                Article(
                    title=p["data"].get("title", ""),
                    source="Reddit",
                    date="N/A",
                    url=f"https://www.reddit.com{p['data'].get('permalink', '')}"
                )
                for p in posts
            ]
        except Exception as e:
            self.log_error(f"Lỗi Reddit: {e}")
            return []

    async def _fetch_google_rss(self, client: httpx.AsyncClient) -> list[Article]:
        """[Nội bộ] Lấy tin từ Google News RSS (XML)."""
        url = f"https://news.google.com/rss/search?q={self.topic}&hl=en-US&gl=US&ceid=US:en"
        try:
            res = await client.get(url, timeout=10.0)
            res.raise_for_status()
            root = ET.fromstring(res.text)
            articles = []
            for item in root.findall(".//item")[:5]:
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
