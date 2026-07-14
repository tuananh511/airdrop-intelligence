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
    # Dùng User-Agent giống trình duyệt thật thay vì tự nhận diện là bot -
    # một số site (vd airdrops.io) có WAF/bot-detection chặn UA lạ.
    # Nếu vẫn bị chặn (403) khi chạy trên GitHub Actions, đây là chỗ đầu tiên cần thử đổi.
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
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


def post_json(url: str, json_body: dict[str, Any]) -> Any:
    """POST request với JSON body, trả về response đã parse JSON. Raise HttpClientError nếu fail.

    Dùng cho Telegram Bot API và các API khác cần POST (khác GET của crawler).
    """
    settings = get_settings()

    @_retry_config()
    def _do_request() -> Any:
        logger.debug("POST %s", url)
        with httpx.Client(timeout=settings.http_timeout_seconds, headers=DEFAULT_HEADERS) as client:
            response = client.post(url, json=json_body)
            response.raise_for_status()
            return response.json()

    try:
        return _do_request()
    except Exception as exc:  # noqa: BLE001
        raise HttpClientError(f"Không thể POST tới {url}: {exc}") from exc
