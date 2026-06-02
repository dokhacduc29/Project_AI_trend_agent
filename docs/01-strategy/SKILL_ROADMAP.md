# Trạng thái Dự án & Lộ trình (Project Roadmap)

Lộ trình này đối chiếu trực tiếp với file `Roadmap .v2.csv` của dự án.

## Đã hoàn thành (Phase 1 & 2 - Pythonic & Data Scaling)
- Thu thập cơ bản đa nguồn (Requests, JSON, XML/RSS).
- Clean Data (Set, List Comprehensions, Regex cơ bản).
- Lên lịch tự động (Schedule).
- Giao diện phụ trợ (Streamlit Dashboard).

## Đang thực thi (Current Focus)
**Trọng tâm là Day 18, 19, 20:**
1. **Regular Expressions (Regex) nâng cao:** Đã áp dụng để trích xuất Entities (Tags), cần mở rộng khi có dữ liệu phức tạp hơn.
2. **Kiến trúc Module và Package (TÁI CẤU TRÚC - REFACTOR):** 
   - Gom file config ra ngoài.
   - Tích hợp `logging` thay thế cho print.
   - Thiết lập cấu trúc thư mục chuẩn mực.
3. **Database Integration:** Bắt đầu chuyển hướng sang sử dụng Database (SQLAlchemy) thay vì CSV.

## Chỉ thị cốt lõi cho AI Agent
- Khi được yêu cầu viết code, hãy **ưu tiên** các giải pháp nằm trong phần **"Đang thực thi"** (Đặc biệt là ưu tiên Logging và Refactor).
- Nếu người dùng yêu cầu làm Docker hay Cloud Deploy ngay lúc này, hãy **cảnh báo** nhắc nhở rằng chúng ta cần hoàn thành Refactor Module và thiết lập Database trước khi đóng gói lên Cloud.
