"""
=====================================================================
GEMINI CLIENT — Helper gọi Gemini dùng chung (REFACTOR Phase B+)
=====================================================================
Trước đây logic retry exponential backoff bị LẶP ở 3 agent
(ai_agent, trend_agent, cleaner) — vi phạm DRY (ghi nhận ở ADR 0002).

File này gom về một chỗ: mọi agent gọi `generate_with_retry(...)`.

Iron Laws: L03 async, L07 fault tolerance, L08 type hints, L09 no magic.
=====================================================================
"""
import random
import asyncio
from collections.abc import Callable
from google import genai
import config

# Các mã lỗi tạm thời nên thử lại (không phải lỗi do code/sai key)
_RETRYABLE_CODES = ("503", "429", "UNAVAILABLE", "RESOURCE_EXHAUSTED")


async def generate_with_retry(
    client: genai.Client,
    model: str,
    prompt: str,
    *,
    log_error: Callable[[str], None],
    fallback: str = "[]",
) -> str:
    """
    Gọi Gemini generate_content với retry exponential backoff + jitter.

    Args:
        client: Gemini Client đã khởi tạo.
        model: Tên model (vd config.GEMINI_MODEL_NAME).
        prompt: Nội dung gửi cho model.
        log_error: Hàm ghi log lỗi của agent gọi (vd self.log_error).
        fallback: Giá trị trả về khi thất bại ("[]" cho JSON array, "{}" cho object).

    Returns:
        response.text nếu thành công, ngược lại trả `fallback`.
    """
    delay = config.GEMINI_RETRY_BASE_DELAY
    for attempt in range(1, config.GEMINI_RETRY_MAX + 1):
        try:
            response = await client.aio.models.generate_content(
                model=model,
                contents=prompt,
            )
            return response.text or fallback
        except Exception as e:
            is_retryable = any(code in str(e) for code in _RETRYABLE_CODES)
            if is_retryable and attempt < config.GEMINI_RETRY_MAX:
                wait = delay + random.uniform(0, delay * 0.3)
                log_error(f"Lỗi gọi Gemini (lần {attempt}): {e} — thử lại sau {wait:.1f}s")
                await asyncio.sleep(wait)
                delay *= 2
            else:
                log_error(f"Lỗi gọi Gemini: {e}")
                return fallback
    return fallback
