"""Test tích hợp cho main.py - dùng crawler giả + telegram giả, KHÔNG đụng file thật
trong data/ và KHÔNG gọi mạng thật."""

from __future__ import annotations

from typing import Any

import main as main_module
from src.models import ProjectSource


class _FakeCrawler:
    """Crawler giả để test - trả về raw items cố định."""

    source = ProjectSource.AIRDROPS_IO

    def __init__(self, raw_items: list[dict[str, Any]]):
        self._raw_items = raw_items

    def crawl(self) -> list[dict[str, Any]]:
        return self._raw_items


def _make_crawler_factory(raw_items: list[dict[str, Any]]):
    """Trả về 1 'class-like' callable() -> _FakeCrawler, giống cách main.py gọi crawler_cls()."""

    def factory():
        return _FakeCrawler(raw_items)

    return factory


def test_run_sends_only_new_projects_and_updates_history(monkeypatch):
    raw_a = {"title": "Alpha", "source_url": "https://airdrops.io/alpha"}
    raw_b = {"title": "Beta", "source_url": "https://airdrops.io/beta"}

    monkeypatch.setattr(main_module, "ALL_CRAWLERS", [_make_crawler_factory([raw_a, raw_b])])

    # "Beta" đã có trong history từ trước -> không được gửi lại
    monkeypatch.setattr(main_module, "load_history", lambda: {"beta"})

    saved_history: dict[str, set[str]] = {}
    monkeypatch.setattr(main_module, "save_history", lambda h: saved_history.update(final=h))

    sent_titles: list[str] = []

    def _fake_notify(projects):
        sent_titles.extend(p.title for p in projects)
        return projects  # giả định gửi thành công hết

    monkeypatch.setattr(main_module, "notify_new_projects", _fake_notify)

    written = {}
    monkeypatch.setattr(main_module, "write_json", lambda path, data: written.update(path=path, data=data))

    main_module.run()

    assert sent_titles == ["Alpha"]  # Beta bị loại vì đã có trong history
    assert "alpha" in saved_history["final"]
    assert "beta" in saved_history["final"]  # vẫn giữ lại beta cũ
    assert len(written["data"]) == 2  # projects.json lưu cả Alpha + Beta (đều đang active)


def test_run_with_no_new_projects_does_not_call_notify(monkeypatch):
    raw_a = {"title": "Alpha", "source_url": "https://airdrops.io/alpha"}
    monkeypatch.setattr(main_module, "ALL_CRAWLERS", [_make_crawler_factory([raw_a])])
    monkeypatch.setattr(main_module, "load_history", lambda: {"alpha"})
    monkeypatch.setattr(main_module, "save_history", lambda h: None)
    monkeypatch.setattr(main_module, "write_json", lambda path, data: None)

    called = False

    def _fake_notify(projects):
        nonlocal called
        called = True
        return projects

    monkeypatch.setattr(main_module, "notify_new_projects", _fake_notify)

    main_module.run()

    assert called is False
