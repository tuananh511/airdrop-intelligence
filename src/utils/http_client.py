"""HTTP client dùng chung cho các crawler: có timeout + retry (exponential backoff).

Mọi crawler nên dùng `fetch_text` / `fetch_json` thay vì gọi requests/httpx trực tiếp,
để đảm bảo hành vi retry/timeout đồng nhất trên toàn project.
"""

from __future__ import annotations

from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.utils.config import get_settings
from src.utils.logger import get_logger

logger = get_logger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; AirdropIntelligenceBot/1.0; "
        "+https://github.com/)"
    ),
    "Accept": "text/html,application/json;q=0.9,*/*;q=0.8",
}

RETRYABLE_EXCEPTIONS = (httpx.TimeoutException, httpx.ConnectError, httpx.ReadError)


def _retry_config():
    settings = get_settings()
    return retry(
        reraise=True,
        stop=stop_after_attempt(settings.http_max_retries),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(RETRYABLE_EXCEPTIONS),
    )


class HttpClientError(RuntimeError):
    """Raised khi request thất bại sau khi đã retry hết số lần cho phép."""


def fetch_text(url: str, *, params: dict[str, Any] | None = None) -> str:
    """GET request, trả về response body dạng text. Raise HttpClientError nếu fail."""
    settings = get_settings()

    @_retry_config()
    def _do_request() -> str:
        logger.debug("GET %s", url)
        with httpx.Client(timeout=settings.http_timeout_seconds, headers=DEFAULT_HEADERS) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            return response.text

    try:
        return _do_request()
    except Exception as exc:  # noqa: BLE001 - muốn bắt mọi lỗi HTTP để wrap lại
        raise HttpClientError(f"Không thể fetch {url}: {exc}") from exc


def fetch_json(url: str, *, params: dict[str, Any] | None = None) -> Any:
    """GET request, trả về response body đã parse JSON. Raise HttpClientError nếu fail."""
    settings = get_settings()

    @_retry_config()
    def _do_request() -> Any:
        logger.debug("GET (json) %s", url)
        with httpx.Client(timeout=settings.http_timeout_seconds, headers=DEFAULT_HEADERS) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            return response.json()

    try:
        return _do_request()
    except Exception as exc:  # noqa: BLE001
        raise HttpClientError(f"Không thể fetch JSON {url}: {exc}") from exc
