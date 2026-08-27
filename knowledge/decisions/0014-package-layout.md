# ADR 0014 — Đổi sang src-layout, bỏ hack `sys.path`

- **Ngày**: 2026-08-27
- **Trạng thái**: Accepted
- **Phase**: v5.0 — bước B1 (SRS `srs-v5-api-layer.md`)

## Bối cảnh

Bốn tầng code nằm trong các thư mục đặt tên theo lối .NET: `ai_trend_agent.Domain`,
`ai_trend_agent.Application`, `ai_trend_agent.Infrastructure`, `ai_trend_agent.WebApi`.

Vấn đề: **dấu chấm trong tên thư mục khiến chúng không phải package Python hợp lệ.**
Python hiểu dấu chấm là toán tử phân cấp package, nên `import ai_trend_agent.Domain`
không bao giờ hoạt động. Hệ quả dây chuyền:

1. Mọi entrypoint phải tự chèn đường dẫn vào `sys.path` lúc chạy. Đoạn hack này bị
   **lặp nguyên văn ở 5 file** (`worker/main.py` và cả 4 file test), tổng 10 dòng
   `sys.path.insert`.
2. Import phải viết dạng phẳng (`from models import Article`) — không biểu đạt được
   tầng nào sở hữu module đó, và dễ đụng tên với thư viện ngoài.
3. Không `pip install -e .` được, nên không có console script, không đóng gói được.
4. `pyrightconfig.json` phải liệt kê thủ công từng thư mục vào `extraPaths`.
5. Dockerfile phải set `PYTHONPATH` trỏ vào 4 thư mục.

Điều này chặn bước B2 (thêm tầng FastAPI): nếu giữ nguyên, mọi file trong `api/`
cũng phải copy đoạn hack — tức là mang khuyết điểm vào đúng phần code mà người
đọc repo soi kỹ nhất.

## Quyết định

Chuyển sang **src-layout chuẩn Python**:

```
Backend/src/ai_trend_agent/
├── domain/          (từ ai_trend_agent.Domain)
├── application/     (từ ai_trend_agent.Application)
├── infrastructure/  (từ ai_trend_agent.Infrastructure)
├── prompts/         (từ Backend/prompts — nay là package data)
└── worker/          (từ ai_trend_agent.WebApi)
Backend/tests/       (từ ai_trend_agent.Tests)
```

Kèm theo:

- **`pyproject.toml`** ở gốc repo, khai báo `package-dir = {"" = "Backend/src"}`.
- **Import tuyệt đối**: `from ai_trend_agent.domain.models import Article`.
- **Console script** `ai-trend-worker` trỏ tới `ai_trend_agent.worker.main:cli`.
  Khối `if __name__ == "__main__"` được tách thành hàm `cli()` để entry point gọi được.
- **`prompts/` thành package data** khai báo trong `[tool.setuptools.package-data]`.

## Vì sao `prompts/` phải chuyển vào trong package

`prompt_loader.py` xác định thư mục prompt bằng `dirname(dirname(__file__))`. Ở bản cũ,
file nằm tại `Backend/ai_trend_agent.Application/` nên hai cấp lên chính là `Backend/`,
khớp với `Backend/prompts/`. Sau khi chuyển sang `Backend/src/ai_trend_agent/application/`,
hai cấp lên trở thành `Backend/src/` — **prompt sẽ không tìm thấy**.

Đáng lo hơn: lỗi này chỉ lộ ra lúc *runtime* khi agent gọi Gemini, không phải lúc build,
nên có thể lọt qua CI cũ.

Cách xử lý: đưa `prompts/` vào trong package (`ai_trend_agent/prompts/`) và khai báo
package-data. Prompt đi theo package khi cài, hết phụ thuộc vào vị trí thư mục `Backend/`.
Đúng tinh thần ADR 0004 (prompt là artifact có version), nay còn được đóng gói cùng code.

CI được bổ sung **smoke test thứ 3** nạp cả 3 prompt trong image thật, để lỗi loại này
không bao giờ lọt tới runtime nữa.

## Hệ quả

**Tích cực**

- Xóa 10 dòng hack `sys.path` ở 5 file. Entrypoint mới (API ở B2) không cần hack.
- Import nói rõ tầng: `from ai_trend_agent.application.base_agent import BaseAgent`.
- `pip install -e .` chạy được → có console script, đóng gói wheel được.
- Dockerfile bỏ hẳn `PYTHONPATH`; runtime không còn COPY source vào `/app` mà **cài**
  package vào site-packages — sạch hơn và đúng chuẩn.
- `pyrightconfig.json` rút từ 5 dòng `extraPaths` xuống 1.

**Tiêu cực / đánh đổi**

- Diff rất lớn (đổi tên toàn bộ file). Dùng `git mv` để giữ lịch sử; `git log --follow`
  vẫn truy được.
- Ai đang có checkout cũ phải chạy lại `pip install -e .`.
- Tên thư mục không còn "trông giống .NET". Chấp nhận: quy ước Python quan trọng hơn
  sự tương đồng hình thức với .NET — và tầng vẫn được biểu đạt rõ qua tên package.

## Kiểm chứng

- 18/18 test cũ pass, **không sửa nội dung test** (chỉ đổi import và xóa hack).
- `pip install -e .` thành công; `import ai_trend_agent` trả `__version__ = 5.0.0`.
- Wheel build ra chứa đủ 3 file prompt tại `ai_trend_agent/prompts/`.
- Cài wheel vào thư mục sạch rồi nạp prompt: `PROMPT_DIR` trỏ đúng vị trí **đã cài**
  (không phải source), cả 3 prompt đọc được.

## Liên quan

- ADR 0004 — prompt-as-artifact (nay prompt là package data).
- ADR 0013 — CI/CD (smoke test cập nhật theo layout mới, thêm smoke test prompt).
- SRS v5.0 mục 5 vấn đề **P2**, mục 10 bước **B1**.
