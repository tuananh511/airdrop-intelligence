"""Crawler cho Galxe (app.galxe.com) - **CHƯA IMPLEMENT (V1 stub)**.

Lý do để stub thay vì code luôn:
- app.galxe.com là SPA (React), nội dung trang "explore" render bằng JS,
  requests + BeautifulSoup sẽ chỉ thấy shell HTML rỗng.
- GraphQL API public của Galxe (graphigo.prd.galaxy.eco) dùng để lấy CHI TIẾT
  1 campaign đã biết ID, không có endpoint "liệt kê campaign mới" công khai.

Hướng làm khi quay lại (đã note trong project_memory.md):
1. Dùng trình duyệt thật mở https://app.galxe.com/explore, mở DevTools > Network,
   tìm request XHR/fetch trả về danh sách campaign (thường là GraphQL POST tới
   graphigo.prd.galaxy.eco/query) -> copy request đó (query + variables + headers).
2. Hoặc: tìm xem trang có nhúng JSON qua thẻ <script id="__NEXT_DATA__"> không
   (kỹ thuật phổ biến với site Next.js) bằng cách xem HTML thô thực tế.
3. Viết lại `_crawl()` dựa trên phát hiện ở bước 1/2.

TODO: implement sau khi có network thật để inspect (xem project_memory.md Phase 2).
"""

from __future__ import annotations

from typing import Any

from src.crawler.base import BaseCrawler
from src.models import ProjectSource
from src.utils.logger import get_logger

logger = get_logger(__name__)


class GalxeCrawler(BaseCrawler):
    """Stub - chưa có logic crawl thật. Luôn trả về [] cho tới khi implement."""

    source = ProjectSource.GALXE

    def _crawl(self) -> list[dict[str, Any]]:
        logger.info("Galxe crawler chưa được implement (V1 stub) - bỏ qua nguồn này.")
        return []
