"""Gửi thông báo project mới qua Telegram Bot API.

Dùng Bot API thuần (không cần thư viện python-telegram-bot) - chỉ 1 endpoint
`sendMessage`, không cần thêm dependency nặng cho việc đơn giản này.
"""

from __future__ import annotations

from src.models import Project
from src.utils.config import get_settings
from src.utils.http_client import HttpClientError, post_json
from src.utils.logger import get_logger

logger = get_logger(__name__)

_MAX_DESCRIPTION_LENGTH = 300


def _escape_html(text: str) -> str:
    """Escape ký tự đặc biệt HTML - Telegram parse_mode=HTML yêu cầu escape &, <, >."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def format_project_message(project: Project) -> str:
    """Format 1 Project thành message Telegram (HTML parse mode)."""
    lines = [
        f"🎯 <b>{_escape_html(project.title)}</b>",
        f"📡 Nguồn: {project.source.value}",
        f"🔗 {project.source_url}",
    ]

    if project.website and str(project.website) != str(project.source_url):
        lines.append(f"🌐 Website: {project.website}")

    if project.description:
        description = project.description
        if len(description) > _MAX_DESCRIPTION_LENGTH:
            description = description[: _MAX_DESCRIPTION_LENGTH - 3] + "..."
        lines.append(f"📝 {_escape_html(description)}")

    if project.ai_score is not None:
        # Có AI score (V3, Gemini) -> ưu tiên hiển thị (chi tiết hơn rule-based).
        ai = project.ai_score
        lines.append("")
        lines.append(f"🤖 <b>AI đánh giá</b> — Đáng làm: {ai.worth}/100 | Rủi ro: {ai.risk}/100")
        lines.append(f"⏱ Thời gian: {ai.time_estimate} | 💰 Vốn cần: {ai.capital_required}")
        if ai.summary:
            lines.append(f"💬 {_escape_html(ai.summary)}")
    elif project.score is not None:
        # Không có AI score -> hiển thị điểm rule-based (V2) làm tham khảo nhanh.
        lines.append(f"⭐ Điểm sơ bộ: {project.score.worth_score}/100")

    return "\n".join(lines)


def send_message(text: str) -> bool:
    """Gửi 1 message text tới chat Telegram đã cấu hình. Trả về True nếu thành công."""
    settings = get_settings()
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    payload = {
        "chat_id": settings.telegram_chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }

    try:
        post_json(url, payload)
        return True
    except HttpClientError:
        logger.exception("Gửi Telegram thất bại.")
        return False


def notify_new_projects(projects: list[Project]) -> list[Project]:
    """Gửi Telegram cho từng project trong danh sách.

    Trả về danh sách project đã gửi THÀNH CÔNG (để caller chỉ ghi vào history
    những project thực sự gửi được - project gửi lỗi sẽ được thử lại ở lần
    crawl kế tiếp thay vì bị coi là "đã gửi" một cách sai lệch).
    """
    sent: list[Project] = []
    for project in projects:
        message = format_project_message(project)
        if send_message(message):
            sent.append(project)
            logger.info("Đã gửi Telegram: %s", project.title)
        else:
            logger.warning(
                "Gửi Telegram thất bại cho '%s' - sẽ thử lại ở lần crawl sau.", project.title
            )
    return sent
