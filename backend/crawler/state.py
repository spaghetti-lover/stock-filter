import threading
from dataclasses import dataclass, field
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
    failed_symbols: list[str] = field(default_factory=list)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def increment_processed(self):
        with self._lock:
            self.processed += 1

    def add_failed_symbol(self, symbol: str):
        with self._lock:
            self.failed_symbols.append(symbol)


_state = CrawlerState()


def get_state() -> CrawlerState:
    return _state
