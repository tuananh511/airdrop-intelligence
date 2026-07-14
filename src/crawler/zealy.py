"""Crawler cho Zealy (zealy.io) - **CHƯA IMPLEMENT (V1 stub)**.

Lý do để stub thay vì code luôn:
- Zealy có public API (api-v2.zealy.io) NHƯNG API này hoạt động theo từng
  community cụ thể (cần biết trước `subdomain` + `x-api-key`), không có
  endpoint "khám phá community/quest mới trên toàn platform".
- Nghĩa là Zealy không hợp với mô hình "tự động phát hiện airdrop mới" như
  airdrops.io - cần một danh sách community đã biết trước (curated list).

Hướng làm khi quay lại (đã note trong project_memory.md):
1. Quyết định nguồn danh sách community: tự tổng hợp thủ công 1 danh sách
   subdomain Zealy đáng chú ý (JSON riêng trong data/), rồi dùng API
   `GET https://api-v2.zealy.io/public/communities/{subdomain}` (cần API key,
   xin miễn phí tại docs.zealy.io) để lấy info + quest của từng community đó.
2. Hoặc: bỏ Zealy ra khỏi phạm vi tự động, giữ làm nguồn "theo dõi thủ công".

TODO: implement sau khi user quyết định hướng đi (curated list vs bỏ hẳn).
Xem project_memory.md Phase 2.
"""

from __future__ import annotations

from typing import Any

from src.crawler.base import BaseCrawler
from src.models import ProjectSource
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ZealyCrawler(BaseCrawler):
    """Stub - chưa có logic crawl thật. Luôn trả về [] cho tới khi implement."""

    source = ProjectSource.ZEALY

    def _crawl(self) -> list[dict[str, Any]]:
        logger.info("Zealy crawler chưa được implement (V1 stub) - bỏ qua nguồn này.")
        return []
