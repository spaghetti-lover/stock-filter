"""FilterCriteria — the value object behind every Layer 1 filter call.

Replaces the previous 18-argument tuple. `None` on a numeric field disables that
rule; the set-valued fields (`exchanges`, `statuses`) follow the same convention.
Thresholds are stored in canonical units (raw VND, raw %) — the route is
responsible for converting user-facing units (billions, thousands).
"""

from dataclasses import dataclass

from application.layer1.rules import (
    CvCapRule,
    ExchangeAllowlistRule,
    ExcludeCeilingFloorRule,
    FilterRule,
    MinGtgdRule,
    MinHistoryRule,
    MinIntradayRatioRule,
    MinPriceRule,
    MinVolumeRule,
    StatusAllowlistRule,
)


@dataclass(frozen=True)
class FilterCriteria:
    exchanges: frozenset[str] | None = None
    statuses: frozenset[str] | None = None
    min_gtgd_vnd: float | None = None
    min_history: int | None = None
    min_price_vnd: float | None = None
    min_intraday_ratio: float | None = None
    min_volume_vnd: float | None = None
    cv_cap_pct: float | None = None
    exclude_ceiling_floor: bool = True

    def active_rules(self) -> list[FilterRule]:
        # Order is load-bearing: first matching rule produces the rejection reason.
        rules: list[FilterRule] = []
        if self.exchanges is not None:
            rules.append(ExchangeAllowlistRule(self.exchanges))
        if self.statuses is not None:
            rules.append(StatusAllowlistRule(self.statuses))
        if self.min_gtgd_vnd is not None:
            rules.append(MinGtgdRule(self.min_gtgd_vnd))
        if self.min_history is not None:
            rules.append(MinHistoryRule(self.min_history))
        if self.min_price_vnd is not None:
            rules.append(MinPriceRule(self.min_price_vnd))
        if self.min_intraday_ratio is not None:
            rules.append(MinIntradayRatioRule(self.min_intraday_ratio))
        if self.min_volume_vnd is not None:
            rules.append(MinVolumeRule(self.min_volume_vnd))
        if self.cv_cap_pct is not None:
            rules.append(CvCapRule(self.cv_cap_pct))
        if self.exclude_ceiling_floor:
            rules.append(ExcludeCeilingFloorRule())
        return rules

    @classmethod
    def wave_trader_default(cls) -> "FilterCriteria":
        return cls(
            exchanges=frozenset({"HOSE", "HNX"}),
            min_gtgd_vnd=20e9,
            min_history=60,
            min_price_vnd=10_000,
            cv_cap_pct=200.0,
            exclude_ceiling_floor=True,
        )
