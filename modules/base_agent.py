"""
=====================================================================
[DAY 27] ABSTRACT BASE CLASS — "Hiến pháp" của mọi Agent
=====================================================================
GIẢI THÍCH TẠI SAO:
    Trong một đội quân, mọi binh lính đều PHẢI biết bắn súng (dù là lính bộ binh hay lính hải quân).
    Abstract Class chính là "Hiến pháp" bắt buộc mọi Agent con phải có method execute().
    Nếu một Agent con nào "lười biếng" không viết hàm execute(), Python sẽ CẤM nó khởi tạo (TypeError).

CÁCH SỬ DỤNG:
    - KHÔNG BAO GIỜ được gọi trực tiếp: BaseAgent() → Lỗi ngay!
    - Chỉ được dùng làm khuôn đúc để tạo ra các Agent con (ScraperAgent, CleanerAgent, StorageAgent).
    
KỸ THUẬT ÁP DỤNG:
    - ABC (Abstract Base Class): Module chuẩn của Python, dùng để tạo "lớp trừu tượng".
    - @abstractmethod: Decorator (Nhãn dán) đánh dấu method NÀY LÀ BẮT BUỘC. Bất kỳ class con nào
      kế thừa mà không viết lại method này sẽ bị Python từ chối chạy.
    - [DAY 23] Inheritance: Mọi Agent con dùng class AgentCon(BaseAgent) để "thừa kế" sức mạnh.
=====================================================================
"""
from abc import ABC, abstractmethod
import logging


class BaseAgent(ABC):
    """
    [DAY 21] CLASS & OBJECT — Bản thiết kế (Blueprint) của mọi Agent.
    
    Một Class giống như bản vẽ kiến trúc của một ngôi nhà.
    Bản thân bản vẽ KHÔNG PHẢI là ngôi nhà. Bạn phải "xây" (khởi tạo) nó
    thành một Object (Đối tượng) thực tế mới dùng được.
    """

    def __init__(self, agent_name: str):
        """
        [DAY 22] INSTANCE ATTRIBUTES — Thuộc tính riêng của từng đối tượng.
        
        GIẢI THÍCH:
            Mỗi khi bạn gọi ScraperAgent("Scout"), Python sẽ chạy vào đây.
            self.agent_name = "Scout" → Thuộc tính riêng của ĐỐI TƯỢNG NÀY.
            Nếu bạn tạo thêm CleanerAgent("Janitor"), nó sẽ có agent_name riêng là "Janitor".
            
        TẠI SAO CÓ CHỮ 'self'?
            'self' = "chính tôi". Khi viết self.agent_name, nghĩa là: 
            "Gán thuộc tính agent_name cho CHÍNH CÁI ĐỐI TƯỢNG ĐANG ĐƯỢC TẠO RA".
        """
        self.agent_name = agent_name
        # [DAY 24] ENCAPSULATION (Đóng gói):
        # Dấu gạch dưới _ ở đầu biến = "Biến nội bộ, KHÔNG NÊN truy cập từ bên ngoài".
        # Đây là quy ước (convention), Python không cấm cứng nhưng Dev chuyên nghiệp luôn tuân thủ.
        self._logger = logging.getLogger(agent_name)

    @abstractmethod
    async def execute(self, *args, **kwargs):
        """
        [DAY 27] ABSTRACT METHOD — "Luật bắt buộc" mà mọi Agent con PHẢI viết lại.
        
        GIẢI THÍCH:
            Hàm này CỐ TÌNH để trống (chỉ có 'pass'). 
            Nó giống như dòng chữ trong hợp đồng lao động: 
            "Nhân viên PHẢI hoàn thành nhiệm vụ được giao" — nhưng nhiệm vụ cụ thể là gì 
            thì tùy vào phòng ban (ScraperAgent, CleanerAgent...) tự quyết định.
            
        TẠI SAO DÙNG *args, **kwargs?
            Để linh hoạt tối đa: Mỗi Agent con có thể truyền vào bất kỳ tham số nào 
            mà không cần sửa lại "Hiến pháp" này.
        """
        pass

    def log_info(self, message: str):
        """
        [DAY 22] INSTANCE METHOD — Phương thức dùng chung cho MỌI Agent.
        
        GIẢI THÍCH:
            Nhờ Inheritance (Kế thừa), ScraperAgent, CleanerAgent, StorageAgent 
            đều tự động có method này mà KHÔNG CẦN viết lại.
            Giống như mọi binh lính đều biết chào cờ mà không cần huấn luyện riêng.
        """
        self._logger.info(f"[{self.agent_name}] {message}")

    def log_error(self, message: str):
        """Ghi log lỗi với tiền tố tên Agent."""
        self._logger.error(f"[{self.agent_name}] {message}")

    # =====================================================================
    # [DAY 25] DUNDER METHODS (Double UNDERscore) — Phương thức "Ma thuật"
    # =====================================================================
    # Python gọi các hàm __xxx__ này tự động ở hậu trường.
    # Bạn KHÔNG BAO GIỜ gọi trực tiếp agent.__str__(). 
    # Thay vào đó, Python sẽ tự gọi nó khi bạn viết: print(agent) hoặc str(agent).

    def __str__(self) -> str:
        """
        [DAY 25] __str__: Được gọi khi bạn dùng print(agent) hoặc str(agent).
        Mục đích: Hiển thị thông tin THÂN THIỆN cho con người đọc.
        
        VÍ DỤ:
            agent = ScraperAgent(...)
            print(agent)  → "🤖 Agent: ScraperAgent (Trạng thái: Sẵn sàng)"
        """
        return f"🤖 Agent: {self.agent_name} (Trạng thái: Sẵn sàng)"

    def __repr__(self) -> str:
        """
        [DAY 25] __repr__: Được gọi khi bạn gõ tên biến trong Terminal (REPL) hoặc debug.
        Mục đích: Hiển thị thông tin KỸ THUẬT cho lập trình viên debug.
        
        VÍ DỤ:
            Trong debugger: agent → "BaseAgent(agent_name='ScraperAgent')"
        """
        return f"{self.__class__.__name__}(agent_name='{self.agent_name}')"
