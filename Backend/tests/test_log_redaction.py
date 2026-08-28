"""
=====================================================================
TEST — Che secret trong log
=====================================================================
Bối cảnh: một chu kỳ production thật đã in webhook Discord ra log 4 lần.
Test này chốt lại hành vi che, và đảm bảo log chẩn đoán KHÔNG bị che nhầm.
=====================================================================
"""
import io
import logging


from ai_trend_agent.application.log_redaction import redact, install_secret_redaction, REDACTION_MARK


# Mô phỏng ĐÚNG hình dạng dòng log mà httpx sinh ra khi gọi webhook Discord.
# Token dưới đây là GIẢ — không bao giờ đặt secret thật vào test: log thì xoay
# vòng rồi mất, còn git history thì vĩnh viễn.
FAKE_DISCORD_ID = "000000000000000000"
FAKE_DISCORD_TOKEN = "FAKEtokenFORtestsONLY-notARealSecret_0123456789abcdefGHIJKLMN"
FAKE_DISCORD_LOG = (
    f"HTTP Request: POST https://discord.com/api/webhooks/{FAKE_DISCORD_ID}/"
    f"{FAKE_DISCORD_TOKEN} "
    '"HTTP/1.1 204 No Content"'
)


def test_redacts_discord_webhook_token():
    out = redact(FAKE_DISCORD_LOG)
    assert FAKE_DISCORD_TOKEN not in out
    assert REDACTION_MARK in out
    # Giữ lại webhook id để còn truy vết được là kênh nào
    assert f"webhooks/{FAKE_DISCORD_ID}/" in out
    # Giữ lại status code để còn chẩn đoán
    assert "204 No Content" in out


def test_redacts_apikey_in_query_string():
    out = redact("GET https://newsapi.org/v2/everything?q=ai&apiKey=abc123secret&language=en")
    assert "abc123secret" not in out
    assert "q=ai" in out          # tham số vô hại được giữ
    assert "language=en" in out


def test_redacts_bearer_token():
    assert "s3cr3t" not in redact("Authorization: Bearer s3cr3t.token.value")


def test_keeps_diagnostic_logs_intact():
    """Dòng 403 của Reddit là thứ đã phát hiện Reddit chết — không được đụng vào."""
    line = 'HTTP Request: GET https://www.reddit.com/r/ArtificialIntelligence/new.json?limit=5 "HTTP/1.1 403 Blocked"'
    assert redact(line) == line

    newsapi = 'HTTP Request: GET https://newsapi.org/v2/everything?q=ai&language=en&pageSize=10 "HTTP/1.1 200 OK"'
    assert redact(newsapi) == newsapi


def test_filter_redacts_bytes_actually_written():
    """
    Đường thật: logger -> handler -> filter -> stream.
    Kiểm tra ĐÚNG THỨ được ghi ra, không phải gọi filter bằng tay.
    """
    stream = io.StringIO()
    logger = logging.getLogger("test_redaction_e2e")
    logger.setLevel(logging.INFO)
    logger.propagate = False           # tránh rò lên root handler của pytest
    handler = logging.StreamHandler(stream)
    logger.addHandler(handler)
    install_secret_redaction(logger)

    try:
        logger.info(FAKE_DISCORD_LOG)
    finally:
        logger.removeHandler(handler)

    written = stream.getvalue()
    assert FAKE_DISCORD_TOKEN not in written
    assert REDACTION_MARK in written
    assert "204 No Content" in written


def test_httpx_child_logger_is_redacted_via_root_handler():
    """
    Trường hợp thật sự quan trọng: `httpx` là logger CON, record của nó
    propagate lên handler của root. Filter phải bắt được ở đó.
    """
    stream = io.StringIO()
    root = logging.getLogger("test_redaction_root")
    root.setLevel(logging.INFO)
    root.propagate = False
    handler = logging.StreamHandler(stream)
    root.addHandler(handler)
    install_secret_redaction(root)

    child = logging.getLogger("test_redaction_root.httpx")
    try:
        child.info(FAKE_DISCORD_LOG)
    finally:
        root.removeHandler(handler)

    assert FAKE_DISCORD_TOKEN not in stream.getvalue()


def test_install_is_idempotent():
    logger = logging.getLogger("test_redaction_idempotent")
    handler = logging.StreamHandler()
    logger.addHandler(handler)

    install_secret_redaction(logger)
    install_secret_redaction(logger)

    assert len(handler.filters) == 1
    logger.removeHandler(handler)
