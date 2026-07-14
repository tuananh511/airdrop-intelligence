from bs4 import BeautifulSoup

from src.crawler.airdrops_io import AirdropsIoCrawler, _match_project_slug
from src.crawler.galxe import GalxeCrawler
from src.crawler.layer3 import Layer3Crawler
from src.crawler.zealy import ZealyCrawler

FAKE_HTML = """
<html><body>
<nav><a href="/latest/">Latest</a><a href="/hot/">Hot</a><a href="/faq/">FAQ</a></nav>
<div class="card">
  <a href="https://airdrops.io/beep"><img/></a>
  <h3>Beep</h3>
  <ul><li>Actions: Complete Quests, Deploy AI agents</li></ul>
  <span>Ongoing</span>
  <a href="https://airdrops.io/visit/q8a3/">CLAIM AIRDROP</a>
</div>
<div class="card">
  <a href="https://airdrops.io/rialto"><img/></a>
  <h3>Rialto</h3>
  <ul><li>Actions: Sign Up, Trade</li></ul>
  <span>Ended</span>
</div>
</body></html>
"""


def test_match_project_slug_accepts_project_link():
    assert _match_project_slug("https://airdrops.io/beep") == "beep"
    assert _match_project_slug("https://airdrops.io/beep/") == "beep"


def test_match_project_slug_rejects_nav_links():
    assert _match_project_slug("https://airdrops.io/latest/") is None
    assert _match_project_slug("https://airdrops.io/visit/q8a3/") is None
    assert _match_project_slug("") is None


def test_airdrops_io_parse_logic_with_mock_html(monkeypatch):
    """Test logic parse bằng cách monkeypatch fetch_text - không gọi mạng thật."""
    import src.crawler.airdrops_io as module

    monkeypatch.setattr(module, "fetch_text", lambda url: FAKE_HTML)

    crawler = AirdropsIoCrawler()
    results = crawler.crawl()

    assert len(results) == 2
    beep = next(r for r in results if r["title"] == "Beep")
    assert beep["source_url"] == "https://airdrops.io/beep/"
    assert beep["description"].startswith("Actions:")
    assert beep["tags"] == ["Ongoing"]


def test_airdrops_io_crawl_never_raises_on_network_error(monkeypatch):
    """Nếu fetch_text raise lỗi, crawl() phải trả về [] chứ không raise (spec bắt buộc)."""
    import src.crawler.airdrops_io as module

    def _boom(url):
        raise RuntimeError("network down")

    monkeypatch.setattr(module, "fetch_text", _boom)

    crawler = AirdropsIoCrawler()
    assert crawler.crawl() == []


def test_stub_crawlers_return_empty_list():
    assert GalxeCrawler().crawl() == []
    assert Layer3Crawler().crawl() == []
    assert ZealyCrawler().crawl() == []
