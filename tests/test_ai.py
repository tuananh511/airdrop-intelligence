import json
from types import SimpleNamespace

from src.ai.gemini_provider import GeminiProvider
from src.models import Project, ProjectSource


def _project() -> Project:
    return Project(
        title="Test Project",
        source=ProjectSource.AIRDROPS_IO,
        source_url="https://airdrops.io/test",
    )


class _FakeModels:
    def __init__(self, response_text: str | None = None, error: Exception | None = None):
        self._response_text = response_text
        self._error = error

    def generate_content(self, **kwargs):
        if self._error is not None:
            raise self._error
        return SimpleNamespace(text=self._response_text)


def _make_provider(monkeypatch) -> GeminiProvider:
    """Tạo GeminiProvider với settings hợp lệ (fake key) - không gọi mạng thật."""
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "x")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "x")
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key-for-test")
    import src.utils.config as config_module

    config_module.get_settings.cache_clear()
    return GeminiProvider()


def test_evaluate_parses_valid_json_response(monkeypatch):
    provider = _make_provider(monkeypatch)
    valid_response = json.dumps(
        {
            "worth": 80,
            "risk": 20,
            "time_estimate": "20 minutes",
            "capital_required": "0 USD",
            "has_active_github": True,
            "network_stage": "Testnet",
            "strong_backers": None,
            "suitable_for_low_capital": True,
            "summary": "Đáng làm, ít rủi ro.",
        }
    )
    provider._client = SimpleNamespace(models=_FakeModels(response_text=valid_response))

    result = provider.evaluate(_project())

    assert result is not None
    assert result.worth == 80
    assert result.risk == 20
    assert result.summary == "Đáng làm, ít rủi ro."


def test_evaluate_returns_none_on_invalid_json(monkeypatch):
    provider = _make_provider(monkeypatch)
    provider._client = SimpleNamespace(models=_FakeModels(response_text="not valid json{{{"))

    assert provider.evaluate(_project()) is None


def test_evaluate_returns_none_when_api_raises(monkeypatch):
    provider = _make_provider(monkeypatch)
    provider._client = SimpleNamespace(models=_FakeModels(error=RuntimeError("API down")))

    assert provider.evaluate(_project()) is None


def test_evaluate_returns_none_on_schema_mismatch(monkeypatch):
    """JSON hợp lệ nhưng thiếu field bắt buộc (vd 'worth') -> ValidationError -> None."""
    provider = _make_provider(monkeypatch)
    incomplete = json.dumps({"risk": 20, "summary": "thiếu worth"})
    provider._client = SimpleNamespace(models=_FakeModels(response_text=incomplete))

    assert provider.evaluate(_project()) is None
