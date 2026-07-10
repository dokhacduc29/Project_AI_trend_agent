"""
=====================================================================
LOG REDACTION — Che secret trước khi ghi ra log
=====================================================================
TẠI SAO CẦN FILE NÀY?
    `httpx` ghi lại TOÀN BỘ URL ở mức INFO:

        HTTP Request: POST https://discord.com/api/webhooks/<id>/<token> "204"

    Webhook Discord không có header xác thực — token nằm ngay trong URL.
    Mỗi chu kỳ pipeline in nó ra 4 lần. Log đi vào stdout container, rồi vào
    Loki/CloudWatch/Datadog, rồi vào bất kỳ ai đọc được log.

    Tắt logger httpx thì hết rò, nhưng mất luôn những dòng có giá trị chẩn đoán
    thật (`Reddit 403 Blocked` là thứ phát hiện Reddit đã chết). Nên ta GIỮ log
    và CHE phần bí mật.

Áp dụng Iron Laws:
    - L01 No hardcoded secrets — mở rộng: secret cũng không được xuất hiện ở log.
    - L02 Logging only.
=====================================================================
"""
import logging
import re

# Mỗi pattern có đúng MỘT nhóm bắt (group 1) = phần được giữ lại.
# Phần còn lại của match bị thay bằng REDACTION_MARK.
SECRET_PATTERNS: tuple[re.Pattern[str], ...] = (
    # Discord webhook: giữ lại id, che token
    re.compile(r"(discord\.com/api/webhooks/\d+/)[\w-]+"),
    # Telegram bot token trong path: /bot<token>/sendMessage
    re.compile(r"(api\.telegram\.org/bot)[\w:-]+"),
    # Bất kỳ query param nào mang tên gợi ý secret
    re.compile(r"([?&](?:apikey|api_key|key|token|access_token|secret)=)[^&\s\"']+", re.IGNORECASE),
    # Header Authorization lỡ bị log
    re.compile(r"((?:bearer|basic)\s+)[\w.\-=+/]+", re.IGNORECASE),
)

REDACTION_MARK: str = "<REDACTED>"


def redact(text: str) -> str:
    """Thay mọi secret nhận diện được trong `text` bằng REDACTION_MARK."""
    for pattern in SECRET_PATTERNS:
        text = pattern.sub(rf"\1{REDACTION_MARK}", text)
    return text


class SecretRedactingFilter(logging.Filter):
    """Filter gắn vào handler — che secret trong message trước khi format ra."""

    def filter(self, record: logging.LogRecord) -> bool:
        original = record.getMessage()
        cleaned = redact(original)
        if cleaned != original:
            # Ghi đè msg đã render; xoá args để formatter không nội suy lại bản gốc
            record.msg = cleaned
            record.args = ()
        return True


def install_secret_redaction(logger: logging.Logger | None = None) -> None:
    """
    Gắn filter vào MỌI handler của logger gốc.

    Phải gắn ở handler chứ không phải logger: filter đặt trên một logger chỉ chạy
    với record log thẳng vào nó, không chạy với record được propagate lên từ
    logger con (`httpx`, `httpcore`, ...).
    """
    target = logger or logging.getLogger()
    redactor = SecretRedactingFilter()
    for handler in target.handlers:
        if not any(isinstance(f, SecretRedactingFilter) for f in handler.filters):
            handler.addFilter(redactor)
