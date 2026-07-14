"""Crawler cho airdrops.io.

Đây là nguồn HTML render sẵn phía server (WordPress) nên scrape bằng
requests + BeautifulSoup ổn định, không cần headless browser.

Chiến lược parse: thay vì đoán mò class CSS cụ thể (dễ vỡ khi site đổi theme),
crawler tìm mọi thẻ <a href> trỏ tới trang chi tiết 1 project (dạng
airdrops.io/<slug>/, loại trừ các link menu/nav đã biết), sau đó tìm heading
(h2/h3/h4) gần nhất làm title. Cách này bền hơn với thay đổi giao diện nhỏ,
nhưng vẫn có thể cần điều chỉnh `_EXCLUDED_SLUGS` nếu site thêm mục menu mới.
"""

from __future__ import annotations

import re
from typing import Any

from bs4 import BeautifulSoup

from src.crawler.base import BaseCrawler
from src.models import ProjectSource
from src.utils.http_client import fetch_text
from src.utils.logger import get_logger

logger = get_logger(__name__)

LISTING_URL = "https://airdrops.io/latest/"
BASE_URL = "https://airdrops.io"

# Các slug là link menu/nav/footer, KHÔNG phải trang chi tiết project.
# Nếu sau này site airdrops.io thêm mục menu mới mà bị crawl nhầm thành
# "project", thêm slug đó vào đây.
_EXCLUDED_SLUGS = {
    "",
    "latest",
    "hot",
    "speculative",
    "confirmed",
    "claims",
    "blog",
    "contact",
    "faq",
    "calendar",
    "airdrop-alert",
    "stay-safe",
    "telegram",
    "visit",
}

_STATUS_KEYWORDS = ("ongoing", "ended", "upcoming")

_PROJECT_LINK_RE = re.compile(r"^(?:https?://airdrops\.io)?/([a-z0-9][a-z0-9-]*)/?$", re.IGNORECASE)


def _match_project_slug(href: str) -> str | None:
    """Trả về slug nếu href là link tới trang chi tiết project, ngược lại None."""
    if not href:
        return None
    match = _PROJECT_LINK_RE.match(href.strip())
    if not match:
        return None
    slug = match.group(1).lower()
    if slug in _EXCLUDED_SLUGS or slug.startswith("wp-") or slug.startswith("visit"):
        return None
    return slug


class AirdropsIoCrawler(BaseCrawler):
    """Crawl danh sách airdrop mới nhất từ airdrops.io/latest/."""

    source = ProjectSource.AIRDROPS_IO

    def _crawl(self) -> list[dict[str, Any]]:
        html = fetch_text(LISTING_URL)
        soup = BeautifulSoup(html, "html.parser")

        seen_slugs: set[str] = set()
        results: list[dict[str, Any]] = []

        for anchor in soup.find_all("a", href=True):
            slug = _match_project_slug(anchor["href"])
            if slug is None or slug in seen_slugs:
                continue

            title = self._extract_title(anchor)
            if not title:
                continue

            seen_slugs.add(slug)
            container = anchor.find_parent(["div", "article", "li"]) or anchor
            description = self._extract_description(container)
            status = self._extract_status(container)

            results.append(
                {
                    "title": title,
                    "website": None,
                    "description": description,
                    "reward": "Unknown",
                    "deadline": "Unknown",
                    "cost": "Unknown",
                    "category": "other",
                    "source_url": f"{BASE_URL}/{slug}/",
                    "tags": [status] if status else [],
                    "published_at": None,
                }
            )

        if not results:
            logger.warning(
                "airdrops.io: không tìm thấy project nào - có thể site đã đổi cấu trúc HTML, "
                "cần kiểm tra lại _EXCLUDED_SLUGS / logic parse."
            )

        return results

    @staticmethod
    def _extract_title(anchor) -> str:
        """Tìm heading (h2/h3/h4) làm title: ưu tiên nằm trong anchor, sau đó tìm ngay sau anchor."""
        heading = anchor.find(["h2", "h3", "h4"])
        if heading and heading.get_text(strip=True):
            return heading.get_text(strip=True)

        heading = anchor.find_next(["h2", "h3", "h4"])
        if heading and heading.get_text(strip=True):
            return heading.get_text(strip=True)

        return anchor.get_text(strip=True)

    @staticmethod
    def _extract_description(container) -> str:
        """Tìm dòng mô tả kiểu 'Actions: ...' gần khu vực project."""
        for tag in container.find_all(["li", "p"]):
            text = tag.get_text(strip=True)
            if text.lower().startswith("action"):
                return text
        return ""

    @staticmethod
    def _extract_status(container) -> str:
        text = container.get_text(" ", strip=True).lower()
        for keyword in _STATUS_KEYWORDS:
            if keyword in text:
                return keyword.capitalize()
        return ""
