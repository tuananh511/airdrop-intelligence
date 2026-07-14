"""Crawler cho Layer3 (layer3.xyz) - **CHƯA IMPLEMENT (V1 stub)**.

Lý do để stub thay vì code luôn:
- layer3.xyz là SPA (Next.js), trang "explore" quest có thể render phía client.
- Chưa xác nhận được endpoint API public nào để liệt kê quest mới mà không cần
  đăng nhập / API key.

Hướng làm khi quay lại (đã note trong project_memory.md):
1. Mở https://layer3.xyz/quests thật, DevTools > Network, tìm request XHR/fetch
   trả về danh sách quest (nhiều khả năng là REST JSON tới 1 subdomain api.*).
2. Nếu trang có SSR: kiểm tra thẻ <script id="__NEXT_DATA__" type="application/json">
   trong HTML thô - đây là cách nhiều site Next.js nhúng sẵn dữ liệu SSR, không
   cần gọi API riêng.
3. Viết lại `_crawl()` dựa trên phát hiện ở bước 1/2.

TODO: implement sau khi có network thật để inspect (xem project_memory.md Phase 2).
"""

from __future__ import annotations

from typing import Any

from src.crawler.base import BaseCrawler
from src.models import ProjectSource
from src.utils.logger import get_logger

logger = get_logger(__name__)


class Layer3Crawler(BaseCrawler):
    """Stub - chưa có logic crawl thật. Luôn trả về [] cho tới khi implement."""

    source = ProjectSource.LAYER3

    def _crawl(self) -> list[dict[str, Any]]:
        logger.info("Layer3 crawler chưa được implement (V1 stub) - bỏ qua nguồn này.")
        return []
