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

### 4. Đồng bộ Lộ trình Chiến lược (Roadmap .v2)
- Cập nhật ánh xạ thực tế các kỹ năng Python Backend đã được lập trình hoàn chỉnh vào cột Trạng thái của file `Roadmap .v2.csv` (đánh dấu `✅ Done` cho các ngày thuộc Phase 2, 3, 4, 5 tương ứng với mã nguồn Core ETL hiện hành).

### 5. Hoàn thiện Toàn diện Giai đoạn 5 (Tối ưu Đa nhân & Kiểm thử)
- **Threading xử lý File (Day 42)**: Tích hợp thành công cơ chế `asyncio.to_thread` vào `storage.py` để đẩy các tác vụ I/O ghi đĩa đồng bộ sang luồng nền riêng biệt, loại bỏ rủi ro ách tắc Event Loop.
- **Profiling Hệ thống (Day 47)**: Bổ sung cờ `--profile` vào `main.py` kích hoạt `cProfile` cho phép đo lường và in báo cáo Top 30 hàm tiêu tốn nhiều thời gian nhất.
- **Unit Testing Chuyên nghiệp (Day 49)**: Khởi tạo bộ kiểm thử tự động `Backend/ai_trend_agent.Tests/test_agents.py` sử dụng khung `pytest` và `pytest-asyncio` xác thực độ chính xác của các thuật toán lõi.

### 6. Gộp Nhánh Chính Thức (Merge to Main)
- Gộp toàn bộ thành quả Giai đoạn 4 và Giai đoạn 5 từ nhánh `feature-phase-4-ai` sang nhánh `main` để thiết lập trạng thái chuẩn làm mặc định cho các lượt tải/clone mã nguồn mới.
