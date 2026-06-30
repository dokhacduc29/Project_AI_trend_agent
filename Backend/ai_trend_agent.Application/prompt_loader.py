"""
=====================================================================
PROMPT LOADER — Tách prompt ra khỏi code (spec-driven, ADR 0004)
=====================================================================
TẠI SAO?
    Trước đây prompt là f-string nhúng trong từng agent (ai_agent, trend,
    cleaner) → muốn tinh chỉnh wording phải sửa code logic, không version
    hóa riêng, không review/A-B test prompt độc lập được.

    Nay: mỗi prompt là một file .txt trong Backend/prompts/. Agent chỉ gọi
    render_prompt("ten", **bien). Đây là nguyên tắc "spec/prompt là artifact
    tách biệt, version hóa" (tham chiếu github/spec-kit: tách 'what' khỏi code).

CÚ PHÁP PLACEHOLDER:
    Dùng string.Template ($bien) thay vì str.format, vì prompt chứa JSON
    mẫu với dấu { } literal — Template không đụng tới { } nên an toàn.
    Ví dụ trong file .txt:  "Chủ đề: $topic\n$corpus"

Iron Laws: L08 type hints + docstring, L09 no magic (đường dẫn tập trung).
=====================================================================
"""
import os
from string import Template

# Backend/prompts/  (file này nằm ở Backend/ai_trend_agent.Application/)
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROMPT_DIR: str = os.path.join(_BACKEND_DIR, "prompts")

_cache: dict[str, Template] = {}


def load_prompt(name: str) -> Template:
    """Đọc (và cache) một template prompt theo tên file (không kèm .txt)."""
    if name not in _cache:
        path = os.path.join(PROMPT_DIR, f"{name}.txt")
        with open(path, encoding="utf-8") as f:
            _cache[name] = Template(f.read())
    return _cache[name]


def render_prompt(name: str, **kwargs: object) -> str:
    """Nạp template + thay biến. safe_substitute → biến thiếu không raise."""
    return load_prompt(name).safe_substitute(**kwargs)
