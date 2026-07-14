"""Base interface cho mọi crawler.

Nguyên tắc bắt buộc (theo spec): nếu một nguồn lỗi thì bỏ qua, không để
toàn bộ chương trình dừng. Để đảm bảo điều này ở MỌI crawler (kể cả crawler
viết sau này), logic try/except nằm ở đây (`crawl()`), không ở từng subclass -
subclass chỉ cần lo phần lấy dữ liệu thực tế (`_crawl()`) và có thể raise
exception thoải mái, base class sẽ lo phần bảo vệ.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from src.models import ProjectSource
from src.utils.logger import get_logger

logger = get_logger(__name__)


class BaseCrawler(ABC):
    """Interface chung cho mọi crawler nguồn dữ liệu airdrop."""

    source: ProjectSource

    @abstractmethod
    def _crawl(self) -> list[dict[str, Any]]:
        """Lấy dữ liệu thô từ nguồn. Được phép raise exception bất kỳ lúc nào.

        Trả về list[dict] với các key tương ứng field của `Project`
        (title, website, description, reward, deadline, cost, category,
        source_url, tags, published_at) - key nào không có thì bỏ qua,
        `parser.normalizer` sẽ điền giá trị mặc định.
        """

    def crawl(self) -> list[dict[str, Any]]:
        """Wrapper an toàn: luôn trả về list (rỗng nếu lỗi), không bao giờ raise.

        Đây là method mà pipeline chính (main.py) sẽ gọi.
        """
        try:
            raw_items = self._crawl()
        except Exception:  # noqa: BLE001 - cố ý bắt mọi lỗi để không kill job
            logger.exception("Crawl nguồn '%s' thất bại, bỏ qua nguồn này.", self.source.value)
            return []

        logger.info("Crawl nguồn '%s': lấy được %d item.", self.source.value, len(raw_items))
        return raw_items
