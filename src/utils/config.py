"""Load toàn bộ cấu hình từ biến môi trường / .env.

Không có giá trị nhạy cảm nào được hardcode trong source code.
Dùng pydantic BaseModel để validate config ngay khi khởi động,
fail-fast nếu thiếu config bắt buộc.
"""

from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError

from src.utils.logger import get_logger

logger = get_logger(__name__)


class Settings(BaseModel):
    """Toàn bộ config của ứng dụng, load 1 lần và dùng lại (singleton qua lru_cache)."""

    telegram_bot_token: str
    telegram_chat_id: str

    ai_provider: str = "gemini"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.0-flash"
    enable_ai_scoring: bool = False

    http_timeout_seconds: float = 15.0
    http_max_retries: int = 3

    log_level: str = "INFO"


class ConfigError(RuntimeError):
    """Raised khi thiếu config bắt buộc hoặc config không hợp lệ."""


def _str_to_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load và validate config. Kết quả được cache lại (chỉ đọc .env 1 lần / process)."""
    load_dotenv()

    try:
        settings = Settings(
            telegram_bot_token=os.environ["TELEGRAM_BOT_TOKEN"],
            telegram_chat_id=os.environ["TELEGRAM_CHAT_ID"],
            ai_provider=os.getenv("AI_PROVIDER", "gemini"),
            gemini_api_key=os.getenv("GEMINI_API_KEY"),
            gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
            enable_ai_scoring=_str_to_bool(os.getenv("ENABLE_AI_SCORING", "false")),
            http_timeout_seconds=float(os.getenv("HTTP_TIMEOUT_SECONDS", "15")),
            http_max_retries=int(os.getenv("HTTP_MAX_RETRIES", "3")),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )
    except KeyError as exc:
        raise ConfigError(
            f"Thiếu biến môi trường bắt buộc: {exc}. Xem .env.example để biết danh sách đầy đủ."
        ) from exc
    except ValidationError as exc:
        raise ConfigError(f"Config không hợp lệ: {exc}") from exc

    if settings.enable_ai_scoring and not settings.gemini_api_key:
        raise ConfigError(
            "ENABLE_AI_SCORING=true nhưng thiếu GEMINI_API_KEY. "
            "Điền GEMINI_API_KEY trong .env hoặc tắt ENABLE_AI_SCORING."
        )

    logger.debug("Config loaded successfully (ai_scoring=%s)", settings.enable_ai_scoring)
    return settings
