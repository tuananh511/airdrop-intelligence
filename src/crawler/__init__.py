from src.crawler.airdrops_io import AirdropsIoCrawler
from src.crawler.base import BaseCrawler
from src.crawler.galxe import GalxeCrawler
from src.crawler.layer3 import Layer3Crawler
from src.crawler.zealy import ZealyCrawler

# Danh sach crawler se chay trong pipeline chinh (main.py).
# Them crawler moi o day khi implement xong.
ALL_CRAWLERS: list[type[BaseCrawler]] = [
    AirdropsIoCrawler,
    GalxeCrawler,
    Layer3Crawler,
    ZealyCrawler,
]

__all__ = [
    "ALL_CRAWLERS",
    "AirdropsIoCrawler",
    "BaseCrawler",
    "GalxeCrawler",
    "Layer3Crawler",
    "ZealyCrawler",
]
