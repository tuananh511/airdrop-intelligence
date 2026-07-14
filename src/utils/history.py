"""Quản lý `data/history.json` - danh sách project đã từng gửi Telegram.

Chỉ lưu `unique_id` (string), không lưu toàn bộ Project, để file nhỏ gọn.
"""

from __future__ import annotations

from pathlib import Path

from src.models import Project
from src.utils.json_store import read_json, write_json
from src.utils.logger import get_logger

logger = get_logger(__name__)

HISTORY_PATH = Path("data/history.json")


def load_history(path: Path = HISTORY_PATH) -> set[str]:
    """Đọc danh sách unique_id đã gửi từ trước."""
    data = read_json(path, default=[])
    return set(data)


def save_history(history: set[str], path: Path = HISTORY_PATH) -> None:
    """Ghi lại danh sách unique_id (sorted để diff git dễ đọc)."""
    write_json(path, sorted(history))


def filter_new_projects(projects: list[Project], history: set[str]) -> list[Project]:
    """Lọc ra các project CHƯA có trong history (chưa từng gửi Telegram)."""
    return [p for p in projects if p.unique_id not in history]
