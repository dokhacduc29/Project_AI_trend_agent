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
import re
import random
import asyncio
from collections.abc import Callable
from google import genai
from ai_trend_agent.domain import config
_RETRYABLE_CODES = ("503", "429", "UNAVAILABLE", "RESOURCE_EXHAUSTED")
_RETRY_DELAY_RE = re.compile(r"retryDelay['\"]:\s*['\"](\d+(?:\.\d+)?)s")

# -----------------------------------------------------------------
# [ADR 0005] BUDGET — Trần số lời gọi Gemini mỗi chu kỳ.
# Tham chiếu "budget enforcement... deterministic stopping with explicit
# reason" (DenisSergeevitch/agents-best-practices). Trạng thái ở cấp module,
# reset() ở đầu mỗi chu kỳ pipeline.
# -----------------------------------------------------------------
_budget: dict[str, int] = {"calls": 0, "in_chars": 0, "blocked": 0}


def reset_budget() -> None:
    """Đặt lại bộ đếm budget — gọi ở đầu MỖI chu kỳ pipeline."""
    _budget.update(calls=0, in_chars=0, blocked=0)


def budget_report() -> dict[str, int]:
    """Trả về thống kê budget của chu kỳ hiện tại (để log/observability)."""
    approx_tokens = _budget["in_chars"] // max(config.GEMINI_APPROX_CHARS_PER_TOKEN, 1)
    return {
        "calls": _budget["calls"],
        "approx_input_tokens": approx_tokens,
        "blocked": _budget["blocked"],
    }


def _parse_retry_delay(error_str: str) -> float | None:
    """Trích xuất số giây từ trường retryDelay trong 429 response."""
    m = _RETRY_DELAY_RE.search(error_str)
    return float(m.group(1)) if m else None


async def generate_with_retry(
    client: genai.Client,
    model: str,
    prompt: str,
    *,
    log_error: Callable[[str], None],
    fallback: str = "[]",
) -> str:
    """
    Gọi Gemini generate_content với retry.
    - 429: dùng retryDelay từ response (thường 30-60s) thay vì backoff ngắn.
    - 503: exponential backoff + jitter.
    - [ADR 0005] Budget: vượt trần GEMINI_MAX_CALLS_PER_CYCLE → KHÔNG gọi,
      trả fallback kèm lý do rõ ràng (deterministic stopping).
    """
    if _budget["calls"] >= config.GEMINI_MAX_CALLS_PER_CYCLE:
        _budget["blocked"] += 1
        log_error(
            f"[BUDGET] Đã đạt trần {config.GEMINI_MAX_CALLS_PER_CYCLE} lời gọi Gemini/chu kỳ "
            f"— bỏ qua request này, trả fallback."
        )
        return fallback

    _budget["calls"] += 1
    _budget["in_chars"] += len(prompt)

    exp_delay = config.GEMINI_RETRY_BASE_DELAY
    for attempt in range(1, config.GEMINI_RETRY_MAX + 1):
        try:
            response = await client.aio.models.generate_content(
                model=model,
                contents=prompt,
            )
            return response.text or fallback
        except Exception as e:
            err_str = str(e)
            is_retryable = any(code in err_str for code in _RETRYABLE_CODES)
            if is_retryable and attempt < config.GEMINI_RETRY_MAX:
                api_delay = _parse_retry_delay(err_str)
                if api_delay is not None:
                    # 429: chờ đúng thời gian API yêu cầu + jitter nhỏ
                    wait = api_delay + random.uniform(1, 3)
                else:
                    # 503: exponential backoff
                    wait = exp_delay + random.uniform(0, exp_delay * 0.3)
                    exp_delay *= 2
                log_error(f"Lỗi gọi Gemini (lần {attempt}): {e} — thử lại sau {wait:.1f}s")
                await asyncio.sleep(wait)
            else:
                log_error(f"Lỗi gọi Gemini: {e}")
                return fallback
    return fallback
