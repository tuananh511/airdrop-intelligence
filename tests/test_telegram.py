from src.models import Project, ProjectSource
from src.telegram.notifier import format_project_message, notify_new_projects, send_message


def _project(title: str, description: str = "") -> Project:
    return Project(
        title=title,
        source=ProjectSource.AIRDROPS_IO,
        source_url=f"https://airdrops.io/{title.lower()}",
        description=description,
    )


def test_format_project_message_contains_key_fields():
    project = _project("Cool Airdrop", description="Actions: sign up and swap")
    message = format_project_message(project)

    assert "Cool Airdrop" in message
    assert "airdrops.io" in message
    assert "https://airdrops.io/cool" in message.lower() or "https://airdrops.io/cool airdrop" in message.lower()
    assert "sign up and swap" in message


def test_format_project_message_escapes_html():
    project = _project("A & B <script>")
    message = format_project_message(project)
    assert "&amp;" in message
    assert "<script>" not in message


def test_format_project_message_truncates_long_description():
    long_desc = "x" * 500
    project = _project("Long Desc Project", description=long_desc)
    message = format_project_message(project)
    # Mô tả bị cắt bớt, không đưa nguyên 500 ký tự vào message
    assert len(message) < 500 + 200


def test_send_message_success(monkeypatch):
    import src.telegram.notifier as module

    monkeypatch.setattr(module, "post_json", lambda url, payload: {"ok": True})
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "fake-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "12345")
    module.get_settings.cache_clear()

    assert send_message("hello") is True


def test_send_message_failure_returns_false(monkeypatch):
    import src.telegram.notifier as module
    from src.utils.http_client import HttpClientError

    def _boom(url, payload):
        raise HttpClientError("boom")

    monkeypatch.setattr(module, "post_json", _boom)
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "fake-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "12345")
    module.get_settings.cache_clear()

    assert send_message("hello") is False


def test_notify_new_projects_only_returns_successfully_sent(monkeypatch):
    import src.telegram.notifier as module

    calls = []

    def _fake_send(text: str) -> bool:
        calls.append(text)
        return "Fail Me" not in text

    monkeypatch.setattr(module, "send_message", _fake_send)

    projects = [_project("Send Me"), _project("Fail Me"), _project("Send Me Too")]
    sent = notify_new_projects(projects)

    assert {p.title for p in sent} == {"Send Me", "Send Me Too"}
    assert len(calls) == 3
