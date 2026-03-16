from dataclasses import dataclass
from typing import Optional


@dataclass
class Stock:
    symbol: str
    name: str
    exchange: str
    sector: Optional[str] = None
    industry: Optional[str] = None
