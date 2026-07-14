"""RuleBasedScorer - chấm `worth_score` bằng luật cố định, không gọi AI.

Chạy được ngay cả khi `ENABLE_AI_SCORING=false` (không tốn API call, không cần
mạng). Điểm số ở đây mang tính tương đối - dùng để lọc/sắp xếp sơ bộ, không
thay thế đánh giá kỹ hơn của AI scorer (V3) khi được bật.
"""

from __future__ import annotations

from src.models import Project, ProjectScore
from src.scorer.base import ProjectScorer

_BASE_SCORE = 50
_MIN_SCORE = 0
_MAX_SCORE = 100


class RuleBasedScorer(ProjectScorer):
    """Chấm điểm dựa trên các tín hiệu có sẵn trong dữ liệu đã crawl (không cần AI)."""

    def score(self, project: Project) -> ProjectScore:
        points = _BASE_SCORE
        reasons: list[str] = [f"Điểm khởi đầu: {_BASE_SCORE}"]

        tags_lower = {t.lower() for t in project.tags}

        if project.reward != "Unknown" and project.reward.strip():
            points += 15
            reasons.append("+15: có thông tin phần thưởng rõ ràng")

        if project.deadline != "Unknown" and project.deadline.strip():
            points += 10
            reasons.append("+10: có deadline rõ ràng (tạo tính cấp thiết)")

        if len(project.description) > 30:
            points += 10
            reasons.append("+10: mô tả đầy đủ chi tiết (>30 ký tự)")

        if "ongoing" in tags_lower:
            points += 5
            reasons.append("+5: đang trong giai đoạn Ongoing")

        if "ended" in tags_lower:
            points -= 30
            reasons.append("-30: đã kết thúc (Ended) - có thể không còn giá trị")

        cost_lower = project.cost.lower()
        if "free" in cost_lower or cost_lower in {"0", "0 usd", "unknown"}:
            points += 5
            reasons.append("+5: không tốn vốn / chi phí thấp")

        points = max(_MIN_SCORE, min(_MAX_SCORE, points))

        return ProjectScore(worth_score=points, reasons=reasons)
