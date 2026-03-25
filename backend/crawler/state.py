from dataclasses import dataclass
from datetime import datetime
from typing import Literal


@dataclass
class CrawlerState:
    status: Literal["idle", "running", "done", "error"] = "idle"
    started_at: datetime | None = None
    finished_at: datetime | None = None
    total: int = 0
    processed: int = 0
    current_symbol: str = ""
    error: str = ""


_state = CrawlerState()


def get_state() -> CrawlerState:
    return _state
