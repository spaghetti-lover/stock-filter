from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class DiscussionPost:
    source: str
    external_id: str
    url: str
    posted_at: datetime
    author: str | None
    title: str | None
    body: str
    ticker_symbols: tuple[str, ...]
