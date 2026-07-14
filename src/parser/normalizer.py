"""Chuẩn hóa dict thô (từ crawler) thành `Project` (pydantic model).

Đây là ranh giới "hợp đồng dữ liệu" giữa crawler và phần còn lại của pipeline:
sau bước này, mọi thứ phía sau chỉ làm việc với `Project`, không quan tâm
project đến từ nguồn nào / cấu trúc dict thô ra sao.
"""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from src.models import Project, ProjectCategory, ProjectSource
from src.utils.logger import get_logger

logger = get_logger(__name__)


def build_project(raw: dict[str, Any], source: ProjectSource) -> Project | None:
    """Map 1 dict thô -> `Project`. Trả về None (+ log warning) nếu dữ liệu không hợp lệ.

    Không raise exception ra ngoài - 1 project lỗi không được làm chết cả batch.
    """
    try:
        category_value = raw.get("category", ProjectCategory.OTHER)
        category = category_value if isinstance(category_value, ProjectCategory) else ProjectCategory(category_value)

        return Project(
            title=raw["title"],
            website=raw.get("website"),
            description=raw.get("description") or "",
            reward=raw.get("reward") or "Unknown",
            deadline=raw.get("deadline") or "Unknown",
            cost=raw.get("cost") or "Unknown",
            category=category,
            source=source,
            source_url=raw["source_url"],
            tags=raw.get("tags") or [],
            published_at=raw.get("published_at"),
        )
    except (ValidationError, KeyError, ValueError) as exc:
        logger.warning(
            "Bỏ qua 1 project không hợp lệ từ nguồn '%s': %s. Raw data: %s",
            source.value,
            exc,
            raw,
        )
        return None


def build_projects(raw_items: list[dict[str, Any]], source: ProjectSource) -> list[Project]:
    """Chuẩn hóa 1 danh sách dict thô, tự động bỏ qua item lỗi."""
    projects: list[Project] = []
    for raw in raw_items:
        project = build_project(raw, source)
        if project is not None:
            projects.append(project)
    return projects
