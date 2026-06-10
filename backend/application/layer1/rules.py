"""Per-stock filter rules.

Each rule is a frozen dataclass that exposes ``check(stock) -> str | None``:
- returns a human-readable rejection reason (Vietnamese-friendly numbers in
  billions / millions / thousands as appropriate), or
- returns ``None`` when the stock passes that rule.

Rules are pure value objects — no I/O, no shared state. Ordering is owned by
``FilterCriteria.active_rules()``; the first non-None reason wins (see
``apply_filters``).
"""

from dataclasses import dataclass
from typing import Protocol

from application.dto.stock_dto import GetStockResponse


class FilterRule(Protocol):
    def check(self, stock: GetStockResponse) -> str | None: ...


@dataclass(frozen=True)
class ExchangeAllowlistRule:
    allowed: frozenset[str]

    def check(self, stock: GetStockResponse) -> str | None:
        if stock.exchange not in self.allowed:
            return f"Exchange {stock.exchange} not in {sorted(self.allowed)}"
        return None


@dataclass(frozen=True)
class StatusAllowlistRule:
    allowed: frozenset[str]

    def check(self, stock: GetStockResponse) -> str | None:
        if stock.status not in self.allowed:
            return f"Trading status: {stock.status}"
        return None


@dataclass(frozen=True)
class MinGtgdRule:
    threshold_vnd: float

    def check(self, stock: GetStockResponse) -> str | None:
        if stock.gtgd20 < self.threshold_vnd:
            return f"GTGD20 {stock.gtgd20 / 1e9:.1f}B < {self.threshold_vnd / 1e9:.0f}B"
        return None


@dataclass(frozen=True)
class MinHistoryRule:
    sessions: int

    def check(self, stock: GetStockResponse) -> str | None:
        if stock.history_sessions < self.sessions:
            return f"Only {stock.history_sessions} sessions of history (need {self.sessions})"
        return None


@dataclass(frozen=True)
class MinPriceRule:
    # stock.current_price is quoted in thousands of VND; threshold is raw VND.
    threshold_vnd: float

    def check(self, stock: GetStockResponse) -> str | None:
        price_vnd = stock.current_price * 1000
        if price_vnd < self.threshold_vnd:
            return f"Price {price_vnd:,.0f} VND < {self.threshold_vnd:,.0f} VND"
        return None


@dataclass(frozen=True)
class MinIntradayRatioRule:
    ratio: float

    def check(self, stock: GetStockResponse) -> str | None:
        # Auto-pass when the stock has no expected intraday yet (pre-open / no history).
        if stock.avg_intraday_expected <= 0:
            return None
        actual_ratio = stock.today_value / stock.avg_intraday_expected
        if actual_ratio < self.ratio:
            return (
                f"Intraday activity {actual_ratio * 100:.0f}% of expected "
                f"({stock.today_value / 1e9:.2f}B / {stock.avg_intraday_expected / 1e9:.2f}B expected)"
            )
        return None


@dataclass(frozen=True)
class MinVolumeRule:
    threshold_vnd: float

    def check(self, stock: GetStockResponse) -> str | None:
        if stock.today_value < self.threshold_vnd:
            return f"Volume {stock.today_value / 1e6:.1f}M VND < {self.threshold_vnd / 1e6:.0f}M VND"
        return None


@dataclass(frozen=True)
class CvCapRule:
    cap_pct: float

    def check(self, stock: GetStockResponse) -> str | None:
        if stock.cv is not None and stock.cv >= self.cap_pct:
            return f"CV {stock.cv:.0f}% >= cap {self.cap_pct:.0f}% (unstable liquidity)"
        return None


@dataclass(frozen=True)
class ExcludeCeilingFloorRule:
    def check(self, stock: GetStockResponse) -> str | None:
        if stock.is_ceiling:
            return "At ceiling price — full bid, not suitable for wave trading"
        if stock.is_floor:
            return "At floor price — cannot exit, not suitable for wave trading"
        return None
