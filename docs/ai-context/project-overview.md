# Tổng Quan Dự Án (Project Overview)

AI Trend Agent là một pipeline ETL bất đồng bộ tự động thu thập, làm sạch, phân
tích và phát hành tin xu hướng AI, xây trên nguyên lý SOLID (Factory + Strategy +
Pipeline qua các `BaseAgent`, Python 3.13 async).

**Luồng end-to-end:**
1. **Thu thập** — song song từ NewsAPI, Reddit (JSON), Google News (RSS) qua `httpx` + `asyncio.gather`.
2. **Làm sạch** — dedupe + tag bằng regex, kết hợp tinh chỉnh bằng AI (Hybrid Cleaner, ADR 0002).
3. **Phân tích AI** — tóm tắt, sentiment và tổng hợp xu hướng bằng **Google Gemini** (`TrendSynthesisAgent`, ADR 0001), prompt tách ra `prompts/` (ADR 0004), có giới hạn ngân sách gọi (ADR 0005).
4. **Lưu trữ** — **Supabase PostgreSQL** (chính), CSV là fallback legacy.
5. **Phát hành** — **Discord** qua Incoming Webhook (`DiscordAgent`, ADR 0007 — thay thế Telegram).

**Đặc tính vận hành:** pipeline phân biệt agent *critical* (lỗi → dừng) và
*enrichment* (lỗi → degrade, vẫn chạy tiếp) — ADR 0003; có eval suite kiểm thử
độ bền parser/output AI — ADR 0006.

Chi tiết kiến trúc và luật: xem `agent-guide.md`; lịch sử quyết định: `memory-log.md`.
