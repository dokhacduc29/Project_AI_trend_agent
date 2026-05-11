---
name: coding-rules
description: Iron Laws (10 luật thép) và naming convention bắt buộc khi viết hoặc sửa code Python trong dự án này. Áp dụng cho mọi PR, commit, và code review.
---

# Coding Rules — AI Trend Agent (Iron Laws)

> Vi phạm = từ chối thực thi. Ưu tiên đọc trước khi sinh bất kỳ dòng code nào.

## ⚡ 10 LUẬT THÉP

### L01 — Không Hardcode Secrets
- API keys, token, password **TUYỆT ĐỐI** không xuất hiện trong source code.
- Dùng `python-dotenv` + `.env` (đã `.gitignore`).
- Đọc qua `os.getenv("KEY_NAME")` sau `load_dotenv()`.

### L02 — Logging thay vì Print
- **Cấm** `print()` trong code production.
- Dùng module `logging`:
```python
import logging
logging.info("...")
logging.error("...")
```

### L03 — Async-first cho I/O
- I/O nặng (API calls) **bắt buộc** dùng `asyncio` + `httpx`.
- **Cấm** `time.sleep()`, `requests` đồng bộ trong context async.
- Multi-source fetch dùng `asyncio.gather()`.

### L04 — No SQL Injection
- Khi tích hợp DB: dùng SQLAlchemy ORM hoặc parameterized query.
- **Cấm** f-string nối SQL: `f"SELECT ... WHERE id={user_input}"`.

### L05 — API Backend chuẩn
- Nếu xây REST API: chỉ dùng `FastAPI`.
- Mỗi endpoint phải có Pagination + Rate Limiting.

### L06 — Soft Delete
- DB không dùng `DELETE` cứng.
- Cờ `is_deleted: bool = False` + `deleted_at: datetime | None`.

### L07 — Fault Tolerance
- Mọi external call:
  - `timeout=` (giá trị từ `config.REQUEST_TIMEOUT`).
  - Bọc `try/except (httpx.HTTPError, httpx.TimeoutException, ...)`.
  - Log lỗi, **KHÔNG** để crash pipeline.

### L08 — Type Hints + Docstring
```python
async def fetch(url: str, timeout: float = 10.0) -> list[Article]:
    """Fetch articles from a URL.

    Args:
        url: Endpoint URL.
        timeout: Seconds before giving up.

    Returns:
        List of Article objects (empty on error).
    """
```

### L09 — No Magic Numbers/Strings
- Hằng số → `modules/config.py` (UPPER_SNAKE).
- VD: `MAX_ARTICLES`, `REQUEST_TIMEOUT`, `OUTPUT_DIR`.

### L10 — Decision Log
- Mọi thay đổi kiến trúc / thư viện cốt lõi → ADR mới trong `knowledge/decisions/`.
- Format: `NNNN-tieu-de-quyet-dinh.md` (Architecture Decision Record).

---

## 📋 Naming Convention

| Loại | Quy tắc | Ví dụ |
|------|---------|-------|
| Python file | `snake_case.py` | `ai_agent.py` |
| Markdown | `lowercase-with-hyphens.md` | `agent-guide.md` |
| Class | `PascalCase` | `ScraperAgent` |
| Function/var | `snake_case` | `fetch_articles` |
| Constant | `UPPER_SNAKE_CASE` | `MAX_TOPIC_LENGTH` |
| Branch | `feat/...`, `fix/...`, `refactor/...` | `feat/sqlite-storage` |

## 📌 Task Workflow Discipline

Với task >1 file hoặc >30 dòng:

1. **Plan** — 3-5 bước cụ thể + list file ảnh hưởng.
2. **Confirm** — chờ user `OK`/`proceed` (trừ bugfix nhỏ).
3. **Ambiguity** — gắn `[VERIFY]` khi yêu cầu mơ hồ. KHÔNG bịa.
4. **Output** — Markdown sạch, không dùng H1 (`#`) trong báo cáo nhỏ.

## ✅ Pre-commit Checklist

- [ ] Không có `print()` mới?
- [ ] Không có magic number ngoài `config.py`?
- [ ] Mọi hàm public có type hint + docstring?
- [ ] External call có `timeout` + `try/except`?
- [ ] Không có secret nào lọt vào diff?
- [ ] Đã chạy `python main.py` thử ít nhất 1 chu kỳ?
