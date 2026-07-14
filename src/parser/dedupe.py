"""Deduplicate + merge project xuất hiện ở nhiều nguồn.

Key merge = `Project.dedupe_key` (title đã normalize). Khi 2 project trùng
key, giữ lại bản "giàu thông tin hơn" và cộng dồn tags/nguồn.
"""

from __future__ import annotations

from src.models import Project
from src.utils.logger import get_logger

logger = get_logger(__name__)

_UNKNOWN = "Unknown"


def _richer_value(a: str, b: str) -> str:
    """Chọn giá trị 'giàu thông tin hơn' giữa 2 field cùng loại (vd 2 cái 'reward' khác nguồn)."""
    if a == _UNKNOWN and b != _UNKNOWN:
        return b
    if b == _UNKNOWN and a != _UNKNOWN:
        return a
    return a if len(a) >= len(b) else b


def _merge_two(a: Project, b: Project) -> Project:
    """Merge 2 project trùng `dedupe_key` thành 1 bản duy nhất."""
    merged_tags = sorted(set(a.tags) | set(b.tags) | {a.source.value, b.source.value})

    description = a.description if len(a.description) >= len(b.description) else b.description
    published_at = a.published_at or b.published_at
    website = a.website or b.website

    return a.model_copy(
        update={
            "description": description,
            "reward": _richer_value(a.reward, b.reward),
            "deadline": _richer_value(a.deadline, b.deadline),
            "cost": _richer_value(a.cost, b.cost),
            "website": website,
            "tags": merged_tags,
            "published_at": published_at,
        }
    )


def merge_projects(projects: list[Project]) -> list[Project]:
    """Nhận list project (có thể trùng nhau giữa các nguồn) -> list đã merge, unique theo dedupe_key."""
    merged: dict[str, Project] = {}

    for project in projects:
        key = project.dedupe_key
        if key not in merged:
            merged[key] = project
        else:
            before = merged[key]
            merged[key] = _merge_two(before, project)
            logger.debug(
                "Merge project trùng: '%s' (nguồn %s + %s)",
                project.title,
                before.source.value,
                project.source.value,
            )

    return list(merged.values())
