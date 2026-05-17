import os
from abc import ABC, abstractmethod
from typing import ClassVar

import httpx

_DEFAULT_UA = (
    "Mozilla/5.0 StockFilterBot/1.0 "
    "(+research; contact: phungducanh2511@gmail.com)"
)


def build_http_client(timeout: float = 20.0) -> httpx.AsyncClient:
    ua = os.environ.get("SCRAPER_USER_AGENT", _DEFAULT_UA)
    return httpx.AsyncClient(
        headers={"User-Agent": ua, "Accept-Language": "vi,en;q=0.8"},
        timeout=timeout,
        follow_redirects=True,
    )


class DiscussionScraper(ABC):
    source: ClassVar[str]

    @abstractmethod
    async def run(self, repo) -> int:
        """Crawl posts, batch-save to repo, advance cursors. Return inserted count."""
        pass
