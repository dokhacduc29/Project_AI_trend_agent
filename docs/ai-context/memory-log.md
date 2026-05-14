# Nhật Ký Quyết Định & Bộ Nhớ (Memory Log)

Ghi nhận các quyết định thiết kế quan trọng, thay đổi kiến trúc và trạng thái hệ thống qua các giai đoạn phát triển.

## [2026-05-14] Chuẩn hóa Kiến trúc Đa lớp & Rà soát Luật Thép

### 1. Trạng thái Hệ thống
- **Cấu trúc**: Hoàn tất chuyển đổi mã nguồn Core ETL về mô hình phân lớp chuẩn (`Backend` chứa `Domain`, `Application`, `Infrastructure`, `WebApi`).
- **Orchestrator**: Điểm dẫn nhập chính thức chuyển sang `Backend/ai_trend_agent.WebApi/main.py`.

### 2. Xử lý Ánh xạ IDE (Static Analysis)
- Cấu hình file `settings.json` và `pyrightconfig.json` sử dụng đường dẫn tuyệt đối chuẩn gạch chéo xuôi (`/`) để Pylance/Pyright giải quyết hoàn hảo các câu lệnh import phẳng (flat import) mà không cần can thiệp mã nguồn.
- Tạo file `.env` toàn cục cấp gốc định nghĩa biến `PYTHONPATH` hỗ trợ VS Code Python Extension đồng bộ môi trường phân tích ngầm định.

### 3. Kết quả Rà soát Code theo 22 Nguyên Tắc Tối Cao
- **L01 (No Commit Secret)**: Tuân thủ 100%. Mọi API Key (`NEWS_API_KEY`, `GEMINI_API_KEY`) đều nạp động qua `PipelineContext` từ file `.env` không được commit.
- **L04 (Layer Boundary)**: Lớp `Domain` chỉ chứa hằng số/dataclasses thuần túy. Lớp `Application` định nghĩa interfaces/decorators độc lập. Lớp `Infrastructure` kế thừa và triển khai gọi I/O bên ngoài.
- **L05 (No Blocking Async)**: Tận dụng hoàn toàn I/O bất đồng bộ qua `httpx.AsyncClient` và `asyncio.gather()`. Không sử dụng các tác vụ chờ đồng bộ gây nghẽn luồng.
- **L16 (No Sensitive Logging)**: Thông tin ghi nhận giới hạn ở mức độ đo lường hiệu suất (Timer), số lượng bản ghi và thông tin tracing cơ bản.
- **L19 (No Magic Numbers)**: Các thông số vòng đời, kích thước trang, định mức truy vấn đều được quản lý tập trung tại `config.py`.
