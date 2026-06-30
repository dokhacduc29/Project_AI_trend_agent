"""
=====================================================================
EVAL SUITE — Chấm điểm parser & robustness output AI (ADR 0006)
=====================================================================
TẠI SAO?
    Trước đây không có cách nào biết bộ parse JSON của AI (sentiment,
    relevance) đúng hay sai khi đổi prompt/model — chính là "test gap /
    untested hotspot" mà code-review-graph cảnh báo, và là "validators +
    trace-level grading" mà agents-best-practices/evals.md yêu cầu.

PHẠM VI (deterministic, KHÔNG gọi mạng):
    1. ACCURACY — feed các response RAW đã biết → assert sentiment parse đúng,
       tính accuracy tổng thể và chốt ngưỡng tối thiểu.
    2. ROBUSTNESS — JSON hỏng / rỗng / markdown-wrapped → KHÔNG crash,
       về mặc định an toàn (NEUTRAL).
    3. BUDGET — vượt trần GEMINI_MAX_CALLS_PER_CYCLE → trả fallback,
       tăng bộ đếm 'blocked' (deterministic stopping).

Chạy:  cd Backend && pytest ai_trend_agent.Tests/test_evals.py -v
=====================================================================
"""
import os
import sys
import json
import asyncio

# Nạp động các thư mục Backend vào sys.path (giống test_agents.py)
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
for layer in ["ai_trend_agent.Domain", "ai_trend_agent.Application", "ai_trend_agent.Infrastructure"]:
    layer_dir = os.path.join(backend_dir, layer)
    if layer_dir not in sys.path:
        sys.path.insert(0, layer_dir)

from models import Article, Sentiment
from ai_agent import SummarizationAgent
import gemini_client
import config

# Ngưỡng accuracy tối thiểu cho parser sentiment (chốt regression)
MIN_SENTIMENT_ACCURACY = 0.95

_GOLDEN_PATH = os.path.join(os.path.dirname(__file__), "evals", "golden_sentiment.json")


def _load_golden() -> dict:
    with open(_GOLDEN_PATH, encoding="utf-8") as f:
        return json.load(f)


def _parse_one(agent: SummarizationAgent, response: str) -> Article:
    """Đẩy 1 response RAW qua parser, trả về Article đã được gán sentiment."""
    art = Article(title="probe", source="eval", date="2026-06-30", url="")
    agent._parse_batch_response(response, [art])
    return art


def test_sentiment_parse_accuracy():
    """ACCURACY: parser map sentiment đúng >= ngưỡng trên golden set."""
    golden = _load_golden()
    agent = SummarizationAgent()

    total = len(golden["cases"])
    correct = 0
    misses = []
    for case in golden["cases"]:
        art = _parse_one(agent, case["response"])
        if art.sentiment.value == case["expected"]:
            correct += 1
        else:
            misses.append((case["title"], art.sentiment.value, case["expected"]))

    accuracy = correct / total
    assert accuracy >= MIN_SENTIMENT_ACCURACY, (
        f"Accuracy {accuracy:.2%} < ngưỡng {MIN_SENTIMENT_ACCURACY:.0%}. "
        f"Sai: {misses}"
    )


def test_parser_robustness_no_crash():
    """ROBUSTNESS: input hỏng/rỗng KHÔNG crash, sentiment giữ mặc định NEUTRAL."""
    golden = _load_golden()
    agent = SummarizationAgent()
    for case in golden["robustness"]:
        art = _parse_one(agent, case["response"])
        if case.get("expect_default_neutral"):
            assert art.sentiment == Sentiment.NEUTRAL, case["title"]
        assert art.summary == "", "Bài không được sửa khi parse thất bại"


def test_gemini_budget_enforced():
    """BUDGET: vượt trần lời gọi/chu kỳ → trả fallback + tăng 'blocked'."""
    gemini_client.reset_budget()
    logs: list[str] = []

    async def hammer():
        # Ép _budget.calls tới sát trần mà không gọi mạng thật
        gemini_client._budget["calls"] = config.GEMINI_MAX_CALLS_PER_CYCLE
        out = await gemini_client.generate_with_retry(
            client=None,            # không dùng vì budget chặn trước khi gọi
            model="x",
            prompt="p",
            log_error=logs.append,
            fallback="[BUDGET_FALLBACK]",
        )
        return out

    out = asyncio.run(hammer())
    report = gemini_client.budget_report()
    assert out == "[BUDGET_FALLBACK]"
    assert report["blocked"] == 1
    assert any("BUDGET" in m for m in logs)


def test_budget_resets_per_cycle():
    """reset_budget() đưa mọi bộ đếm về 0 (cô lập giữa các chu kỳ)."""
    gemini_client._budget.update(calls=5, in_chars=999, blocked=2)
    gemini_client.reset_budget()
    r = gemini_client.budget_report()
    assert r == {"calls": 0, "approx_input_tokens": 0, "blocked": 0}
