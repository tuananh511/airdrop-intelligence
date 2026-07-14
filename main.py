"""Entry point của Airdrop Intelligence Bot.

Luồng chạy chính (V1):
crawl (mỗi nguồn trong ALL_CRAWLERS, lỗi thì bỏ qua nguồn đó)
  -> parse/normalize (dict thô -> Project)
  -> merge (dedupe project trùng giữa các nguồn)
  -> filter theo history.json (chỉ giữ project chưa từng gửi)
  -> gửi Telegram cho project mới
  -> ghi lại data/projects.json (toàn bộ project đang active)
     + data/history.json (thêm các project vừa gửi THÀNH CÔNG)

Không có logic nghiệp vụ nào nằm trực tiếp ở đây - main.py chỉ orchestrate,
gọi tới các module trong src/. Đây là điểm duy nhất chạy khi GitHub Actions
trigger `python main.py`.
"""

from __future__ import annotations

from pathlib import Path

from src.crawler import ALL_CRAWLERS
from src.models import Project
from src.parser import build_projects, merge_projects
from src.telegram import notify_new_projects
from src.utils.history import filter_new_projects, load_history, save_history
from src.utils.json_store import write_json
from src.utils.logger import get_logger

logger = get_logger(__name__)

PROJECTS_PATH = Path("data/projects.json")


def crawl_all_projects() -> list[Project]:
    """Chạy tất cả crawler trong ALL_CRAWLERS, gộp + chuẩn hóa thành list[Project]."""
    all_projects: list[Project] = []

    for crawler_cls in ALL_CRAWLERS:
        crawler = crawler_cls()
        raw_items = crawler.crawl()  # đã tự bảo vệ, luôn trả về list (rỗng nếu lỗi)
        projects = build_projects(raw_items, crawler.source)
        all_projects.extend(projects)

    return all_projects


def run() -> None:
    """Chạy toàn bộ pipeline 1 lần (được gọi bởi GitHub Actions mỗi 2 giờ)."""
    logger.info("=== Bắt đầu chạy Airdrop Intelligence Bot ===")

    raw_projects = crawl_all_projects()
    logger.info("Tổng cộng %d project thô từ tất cả nguồn.", len(raw_projects))

    merged_projects = merge_projects(raw_projects)
    logger.info("Sau khi merge/dedupe: %d project.", len(merged_projects))

    history = load_history()
    new_projects = filter_new_projects(merged_projects, history)
    logger.info("Project mới (chưa từng gửi): %d.", len(new_projects))

    if new_projects:
        sent_projects = notify_new_projects(new_projects)
        history.update(p.unique_id for p in sent_projects)
        logger.info("Đã gửi Telegram thành công %d/%d project mới.", len(sent_projects), len(new_projects))
    else:
        logger.info("Không có project mới, không gửi Telegram.")

    write_json(PROJECTS_PATH, [p.model_dump(mode="json") for p in merged_projects])
    save_history(history)

    logger.info("=== Hoàn tất ===")


if __name__ == "__main__":
    run()
