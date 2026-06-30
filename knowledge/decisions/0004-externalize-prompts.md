# ADR 0004 — Tách prompt ra file (prompt-as-artifact)

- **Ngày**: 2026-06-30
- **Trạng thái**: Accepted
- **Phase**: Hardening
- **Nguồn chuẩn mực**: github/spec-kit — *"specifications become executable… maintained as separate, evolving markdown documents"*, tách **"what"** khỏi **"how"/tech stack**.

## Bối cảnh

Prompt của 3 agent (`analyzer`, `trend`, `cleaner`) là f-string nhúng
thẳng trong code logic. Hệ quả: tinh chỉnh wording phải sửa file `.py`,
không version hóa/diff/review prompt độc lập, không A-B test được, dễ lẫn
lỗi giữa thay đổi logic và thay đổi prompt.

## Quyết định

- Thêm `Backend/prompts/*.txt`: mỗi prompt một file, dùng `string.Template`
  (`$bien`) làm placeholder. Lý do chọn `Template` thay `str.format`: prompt
  chứa JSON mẫu với `{ }` literal — `Template` không đụng tới `{ }`.
- Thêm `ai_trend_agent.Application/prompt_loader.py`: `render_prompt(name,
  **vars)` nạp + cache + `safe_substitute`.
- 3 agent gọi `render_prompt("analyzer"|"trend"|"cleaner", ...)`.

## Hệ quả

- **Tích cực**: prompt trở thành artifact tách biệt — sửa wording không
  đụng code; diff prompt sạch trong git; mở đường cho versioning/A-B test.
- **Tiêu cực**: thêm một lớp gián tiếp (phải mở file `.txt` để đọc prompt).
- **Tương thích ngược**: nội dung prompt giữ nguyên byte-for-byte → hành vi
  AI không đổi.

## Phương án đã loại

- *Jinja2*: thừa cho nhu cầu hiện tại, thêm dependency.
- *Hằng số prompt trong config.py*: vẫn là code, không giải quyết việc tách
  artifact & xuống dòng/đa ngôn ngữ khó đọc.
