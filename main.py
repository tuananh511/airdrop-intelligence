"""Entry point của Airdrop Intelligence Bot.

Luồng chạy chính (V1 + V2 + V3):
crawl (mỗi nguồn trong ALL_CRAWLERS, lỗi thì bỏ qua nguồn đó)
  -> parse/normalize (dict thô -> Project)
  -> merge (dedupe project trùng giữa các nguồn)
  -> rule-based score (V2, luôn chạy - không tốn API call)
  -> filter theo history.json (chỉ giữ project chưa từng gửi)
  -> [optional, ENABLE_AI_SCORING=true] AI score (V3, Gemini) - chỉ chạy cho
     project MỚI để tiết kiệm API call, không chạy lại cho project đã biết
  -> gửi Telegram cho project mới
  -> ghi lại data/projects.json (toàn bộ project đang active)
     + data/history.json (thêm các project vừa gửi THÀNH CÔNG)

Không có logic nghiệp vụ nào nằm trực tiếp ở đây - main.py chỉ orchestrate,
gọi tới các module trong src/. Đây là điểm duy nhất chạy khi GitHub Actions
trigger `python main.py`.
"""

from __future__ import annotations

from pathlib import Path

from src.ai import GeminiProvider
from src.crawler import ALL_CRAWLERS
from src.models import Project
from src.parser import build_projects, merge_projects
from src.scorer import RuleBasedScorer
from src.telegram import notify_new_projects
from src.utils.config import get_settings
from src.utils.history import filter_new_projects, load_history, save_history
from src.utils.json_store import write_json
from src.utils.logger import get_logger

logger = get_logger(__name__)

PROJECTS_PATH = Path("data/projects.json")

_rule_scorer = RuleBasedScorer()


def crawl_all_projects() -> list[Project]:
    """Chạy tất cả crawler trong ALL_CRAWLERS, gộp + chuẩn hóa thành list[Project]."""
    all_projects: list[Project] = []

    for crawler_cls in ALL_CRAWLERS:
        crawler = crawler_cls()
        raw_items = crawler.crawl()  # đã tự bảo vệ, luôn trả về list (rỗng nếu lỗi)
        projects = build_projects(raw_items, crawler.source)
        all_projects.extend(projects)

    return all_projects


def apply_rule_based_scores(projects: list[Project]) -> list[Project]:
    """Gắn `ProjectScore` (V2, rule-based) cho mọi project - luôn chạy, không tốn API call."""
    return [p.model_copy(update={"score": _rule_scorer.score(p)}) for p in projects]


def apply_ai_scores(projects: list[Project]) -> list[Project]:
    """Gắn `AIScore` (V3, Gemini) cho danh sách project - CHỈ gọi khi ENABLE_AI_SCORING=true.

    Chỉ nên truyền vào đây các project MỚI (chưa từng gửi) để tiết kiệm API call -
    không có lý do gì để chấm điểm lại AI cho project đã biết từ trước.
    """
    provider = GeminiProvider()
    scored: list[Project] = []

    for project in projects:
        ai_score = provider.evaluate(project)
        if ai_score is not None:
            scored.append(project.model_copy(update={"ai_score": ai_score}))
        else:
            scored.append(project)  # AI lỗi -> giữ nguyên project, vẫn gửi Telegram bình thường

    return scored


def run() -> None:
    """Chạy toàn bộ pipeline 1 lần (được gọi bởi GitHub Actions mỗi 2 giờ)."""
    logger.info("=== Bắt đầu chạy Airdrop Intelligence Bot ===")
    settings = get_settings()

    raw_projects = crawl_all_projects()
    logger.info("Tổng cộng %d project thô từ tất cả nguồn.", len(raw_projects))

    merged_projects = merge_projects(raw_projects)
    merged_projects = apply_rule_based_scores(merged_projects)
    logger.info("Sau khi merge/dedupe: %d project.", len(merged_projects))

    history = load_history()
    new_projects = filter_new_projects(merged_projects, history)
    logger.info("Project mới (chưa từng gửi): %d.", len(new_projects))

    if new_projects and settings.enable_ai_scoring:
        logger.info("ENABLE_AI_SCORING=true - chấm điểm AI cho %d project mới.", len(new_projects))
        new_projects = apply_ai_scores(new_projects)
        # Đồng bộ lại ai_score vào merged_projects để lưu vào projects.json.
        scored_by_id = {p.unique_id: p for p in new_projects}
        merged_projects = [scored_by_id.get(p.unique_id, p) for p in merged_projects]

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
