# Tổng quan Hệ thống AI_Trend_Agent (v1.0 -> v2.0)

## Mục tiêu
Thu thập dữ liệu xu hướng công nghệ (News, AI Trends) từ đa nguồn, làm sạch, phân loại tự động và lưu trữ để chuẩn bị cho quá trình tạo nội dung hoặc cảnh báo qua Telegram.

## Kiến trúc Hiện tại (Aggregator Model)
- **Đầu vào (Extract):** Kết nối 3 nguồn chính:
  1. NewsAPI (JSON - Tin báo chí)
  2. Reddit (JSON - Tin cộng đồng/mạng xã hội)
  3. Google News (XML/RSS - Tin tức tổng hợp nhanh)
- **Biến đổi (Transform):** 
  - NLP cơ bản: Lọc ký tự đặc biệt, lọc trùng lặp (Set).
  - Trích xuất thực thể (Regex): Tự động gán tag (VD: #OpenAI, #Google, #Money).
- **Lưu trữ (Load):** Chuyển từ CSV sang định hướng Database.
- **Tự động hóa:** Quản lý vòng lặp bằng `schedule` (mỗi 4 giờ).

## Chuẩn hóa dữ liệu (Core Schema)
Bất kể lấy từ nguồn nào (JSON hay XML), dữ liệu đầu ra BẮT BUỘC phải ép về cấu trúc Dictionary tiêu chuẩn sau:
- `title` (str): Tiêu đề bài viết.
- `source` (str): Nguồn trích xuất (NewsAPI, Reddit, Google News RSS).
- `date` (str/datetime): Thời gian xuất bản.
- `url` (str): Link bài viết gốc.
- `tags` (list): Các thẻ phân loại được tự động gán bởi AI/Regex.

## Bảo vệ hệ thống (Fault Tolerance)
- Mọi hàm call API bên ngoài (`requests.get`) bắt buộc có `timeout`.
- Sử dụng `try...except` để bắt lỗi `RequestException`, `HTTPError` để đảm bảo pipeline không bao giờ bị crash.
