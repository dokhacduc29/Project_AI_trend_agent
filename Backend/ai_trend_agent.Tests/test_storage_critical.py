"""
=====================================================================
TEST — SupabaseStorageAgent là critical và KHÔNG nuốt lỗi
=====================================================================
Bối cảnh: trước bản vá, `execute()` bọc mọi exception rồi trả ctx bình thường.
Hậu quả: nếu Supabase từ chối ghi (sai key, RLS chặn, mạng chết), pipeline vẫn
đi tiếp và DiscordAgent vẫn đăng bài — bài không được lưu, và chu kỳ sau đăng
lại y hệt vì dedupe dựa vào UNIQUE(url) trên chính bảng đó.

Xem ADR 0003 (critical vs enrichment) và ADR 0010 (RLS + secret key).
=====================================================================
"""
import pytest
import sys
import os

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
for layer in ["ai_trend_agent.Domain", "ai_trend_agent.Application", "ai_trend_agent.Infrastructure"]:
    layer_dir = os.path.join(backend_dir, layer)
    if layer_dir not in sys.path:
        sys.path.insert(0, layer_dir)

from models import Article, PipelineContext
from base_agent import AgentFactory
import supabase_storage  # noqa: F401 — side-effect: đăng ký "storage"


def _one_article() -> list[Article]:
    return [Article(title="T", source="S", date="2026-07-10", url="http://a.test/1")]


def test_storage_agent_is_critical():
    """run_pipeline đọc `is_critical` để quyết định dừng hay đi tiếp."""
    assert AgentFactory.create("storage").is_critical is True


@pytest.mark.asyncio
async def test_storage_raises_instead_of_swallowing(monkeypatch):
    """Supabase lỗi → exception phải NỔI LÊN, không bị nuốt thành log."""
    agent = AgentFactory.create("storage")

    def boom(_rows):
        raise RuntimeError("new row violates row-level security policy")

    monkeypatch.setattr(agent, "_insert_sync", boom)
    ctx = PipelineContext(topic="AI", articles=_one_article())

    with pytest.raises(RuntimeError, match="row-level security"):
        await agent.execute(ctx)


@pytest.mark.asyncio
async def test_storage_returns_ctx_on_success(monkeypatch):
    """Đường thành công không đổi: trả về ctx nguyên vẹn."""
    agent = AgentFactory.create("storage")
    monkeypatch.setattr(agent, "_insert_sync", lambda rows: len(rows))

    ctx = PipelineContext(topic="AI", articles=_one_article())
    out = await agent.execute(ctx)

    assert out is ctx
    assert len(out.articles) == 1


@pytest.mark.asyncio
async def test_storage_skips_quietly_when_no_articles(monkeypatch):
    """Không có bài → return sớm, KHÔNG gọi Supabase, không ném lỗi."""
    agent = AgentFactory.create("storage")

    def must_not_run(_rows):
        raise AssertionError("không được gọi Supabase khi ctx.articles rỗng")

    monkeypatch.setattr(agent, "_insert_sync", must_not_run)
    ctx = PipelineContext(topic="AI", articles=[])

    assert await agent.execute(ctx) is ctx
