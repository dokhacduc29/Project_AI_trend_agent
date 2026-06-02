# Tiêu chuẩn Code (Enterprise Grade) dành cho AI_Trend_Agent

Dựa trên chuẩn "Standarized Project Initialization", đây là "Luật Thép" (Iron Laws) và kỷ luật quy trình làm việc khi viết/chỉnh sửa code cho dự án này. Mọi AI Agent phải tuân thủ nghiêm ngặt. Việc vi phạm sẽ dẫn đến từ chối thực thi.

## ⚡ 10 LUẬT THÉP CỐT LÕI (IRON LAWS - PYTHON VERSION)

| # | Luật | Yêu cầu bắt buộc |
|---|------|------------------|
| L01 | **Không Hardcode Secrets** | API Keys (NewsAPI, OpenAI, Telegram), token, mật khẩu tuyệt đối KHÔNG xuất hiện trong code. Bắt buộc dùng `python-dotenv` và file `.env`. |
| L02 | **Logging thay vì Print** | Cấm dùng `print()`. Bắt buộc dùng thư viện `logging` của Python (INFO, ERROR) để ghi nhận luồng hoạt động. |
| L03 | **Bất đồng bộ (Asyncio)** | Cấm dùng `time.sleep()` hoặc `requests` đồng bộ trong các tác vụ I/O nặng (call API đa nguồn). Bắt buộc dùng `asyncio` và `httpx` / `aiohttp`. |
| L04 | **Không SQL Injection** | Khi tích hợp Database, tuyệt đối không dùng string format (f-string) để nối chuỗi SQL. Bắt buộc dùng SQLAlchemy ORM hoặc Parameterized Queries. |
| L05 | **API Backend chuẩn mực** | Nếu xây dựng API endpoint, chỉ sử dụng `FastAPI`. Mọi endpoint phải có phân trang (Pagination) và Rate Limiting. |
| L06 | **Soft Delete (Xóa mềm)** | Khi làm việc với DB, không dùng lệnh DELETE vĩnh viễn. Sử dụng cờ `is_deleted = True` và `deleted_at`. |
| L07 | **Fault Tolerance bắt buộc** | Mọi API call bên ngoài phải có `timeout` và `try-except` (HTTPError, Timeout) để chống crash. |
| L08 | **Type Hinting & Docstring** | Mọi hàm/class phải có Type Hinting (VD: `def clean(data: list) -> list:`) và Docstring ngắn gọn giải thích Params/Return. |
| L09 | **Không Magic Numbers/Strings** | Các hằng số (VD: số lượng bài lấy, URLs) phải đặt thành biến in hoa (VD: `MAX_ARTICLES = 5`) ở đầu file hoặc lưu config. |
| L10 | **Nhật ký Quyết định (Memory Log)** | Mọi thay đổi lớn về kiến trúc hoặc thư viện cốt lõi phải được ghi lại để theo dõi. |

## 📋 QUY TẮC ĐẶT TÊN (NAMING CONVENTION)
- **Tài liệu Docs (.md):** Bắt buộc `lowercase-with-hyphens.md` (VD: `agent-guide.md`). Không dùng dấu gạch dưới `_`, không viết hoa.
- **File Code Python (.py):** `snake_case.py` (VD: `module1_cleaner.py`).
- **Class / OOP:** `PascalCase`.
- **Hàm / Biến (Functions/Variables):** `snake_case`.

## 📌 KỶ LUẬT QUY TRÌNH (TASK WORKFLOW DISCIPLINE)
Với mọi tác vụ lớn (> 1 file, > 30 dòng code), AI Agent phải tuân thủ luồng sau:
1. **Lập Kế hoạch (Task Plan):** Mô tả rõ ràng 3-5 hành động cụ thể sẽ làm, liệt kê danh sách file bị ảnh hưởng.
2. **Chờ Xác nhận (Wait for User CONFIRM):** Dừng lại chờ User nói "OK" hoặc "Proceed" trước khi bắt tay vào sửa code (trừ các lệnh sửa lỗi khẩn cấp/bugfix nhỏ).
3. **Xử lý Mơ hồ (Ambiguity Handling):** Nếu yêu cầu từ User không rõ ràng, gắn tag `[VERIFY]` và hỏi lại để làm rõ, TUYỆT ĐỐI KHÔNG tự bịa nội dung (hallucinate).
4. **Output Format:** Trình bày bằng Markdown chuyên nghiệp (dùng bảng, gạch đầu dòng, code block). Không dùng Heading 1 (`#`) trong các báo cáo nhỏ để tránh lạm dụng.
