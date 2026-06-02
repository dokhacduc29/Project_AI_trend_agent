# Báo Cáo Tái Cấu Trúc Dự Án (Restructure Report)

Dự án AI Trend Agent đã được tái cấu trúc toàn diện theo kiến trúc chuẩn hóa đa tầng (Multi-layer Enterprise Architecture) nhằm phân tách rõ ràng trách nhiệm giữa cấu hình AI, tài liệu thiết kế, phân lớp Backend và Frontend.

## Sơ Đồ Kiến Trúc Mới

- **Root Level**: Chỉ chứa cấu hình AI toàn dự án (`CLAUDE.md`) và thư mục `.claude/commands/` định nghĩa các quy trình thao tác chuẩn.
- **Backend Layer**: Chứa mã nguồn Python lõi được ánh xạ theo các lớp Domain, Application, Infrastructure và WebApi.
- **Frontend Layer**: Dành riêng cho giao diện người dùng tương lai.
- **Docs Layer**: Chuẩn hóa thành các lớp từ 01-strategy đến 05-support kèm theo ngữ cảnh dành riêng cho AI (`ai-context/`).
