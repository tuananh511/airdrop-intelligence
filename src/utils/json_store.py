"""Helper đọc/ghi file JSON dùng làm storage (thay database).

Ghi file theo kiểu atomic (ghi ra file tạm rồi rename) để tránh corrupt
data nếu job bị kill giữa chừng trên GitHub Actions.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from src.utils.logger import get_logger

logger = get_logger(__name__)


def read_json(path: str | Path, default: Any) -> Any:
    """Đọc file JSON. Nếu file chưa tồn tại hoặc lỗi parse, trả về `default` và log warning."""
    p = Path(path)
    if not p.exists():
        logger.info("File %s chưa tồn tại, dùng giá trị mặc định.", p)
        return default

    try:
        with p.open("r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as exc:
        logger.warning("File %s bị lỗi JSON (%s), dùng giá trị mặc định.", p, exc)
        return default


def write_json(path: str | Path, data: Any) -> None:
    """Ghi data ra file JSON theo kiểu atomic (tránh corrupt nếu bị interrupt)."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    fd, tmp_path = tempfile.mkstemp(dir=p.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        os.replace(tmp_path, p)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise

    logger.debug("Đã ghi %s", p)
