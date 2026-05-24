"""Catalog of supported AI-filter conditions over `GetStockResponse`.

Single source of truth: predicate + label template + param schema. The same
catalog is sent to the LLM (so it knows the allowed vocabulary) and to the
frontend (so chip labels stay consistent).
"""

from dataclasses import dataclass
from typing import Any, Callable

from application.dto.ai_filter_dto import AIFilterCatalogEntry, AIFilterParamSpec
from application.dto.stock_dto import GetStockResponse


Predicate = Callable[[GetStockResponse, dict[str, Any]], tuple[bool, str | None]]


@dataclass(frozen=True)
class CatalogEntry:
    key: str
    label_template: str
    description: str
    params: tuple[AIFilterParamSpec, ...]
    predicate: Predicate

    def render_label(self, params: dict[str, Any]) -> str:
        merged = {p.name: p.default for p in self.params}
        merged.update(params or {})
        try:
            return self.label_template.format(**merged)
        except (KeyError, IndexError):
            return self.label_template


# ---- predicates ----------------------------------------------------------

def _high_liquidity(s: GetStockResponse, p: dict[str, Any]) -> tuple[bool, str | None]:
    min_billion = float(p.get("min_billion", 20.0))
    threshold = min_billion * 1e9
    if s.gtgd20 >= threshold:
        return True, None
    return False, f"GTGD20 {s.gtgd20 / 1e9:.1f}B < {min_billion:.0f}B"


def _low_liquidity(s: GetStockResponse, p: dict[str, Any]) -> tuple[bool, str | None]:
    max_billion = float(p.get("max_billion", 5.0))
    threshold = max_billion * 1e9
    if s.gtgd20 < threshold:
        return True, None
    return False, f"GTGD20 {s.gtgd20 / 1e9:.1f}B >= {max_billion:.0f}B"


def _stable_cv(s: GetStockResponse, p: dict[str, Any]) -> tuple[bool, str | None]:
    cv_cap = float(p.get("cv_cap", 100.0))
    if s.cv is None:
        return False, "CV not available"
    if s.cv < cv_cap:
        return True, None
    return False, f"CV {s.cv:.0f}% >= {cv_cap:.0f}%"


def _volume_surge(s: GetStockResponse, p: dict[str, Any]) -> tuple[bool, str | None]:
    ratio = float(p.get("ratio", 1.5))
    if s.intraday_ratio is None:
        return False, "Intraday ratio not available"
    if s.intraday_ratio >= ratio:
        return True, None
    return False, f"Intraday ratio {s.intraday_ratio:.2f} < {ratio:.2f}"


def _exclude_ceiling_floor(s: GetStockResponse, _: dict[str, Any]) -> tuple[bool, str | None]:
    if s.is_ceiling:
        return False, "At ceiling price"
    if s.is_floor:
        return False, "At floor price"
    return True, None


def _exchange_in(s: GetStockResponse, p: dict[str, Any]) -> tuple[bool, str | None]:
    raw = p.get("exchanges", ["HOSE"])
    exchanges = [str(x).upper() for x in raw] if isinstance(raw, list) else [str(raw).upper()]
    if s.exchange in exchanges:
        return True, None
    return False, f"Exchange {s.exchange} not in {exchanges}"


# ---- registry ------------------------------------------------------------

CATALOG: dict[str, CatalogEntry] = {
    "high_liquidity": CatalogEntry(
        key="high_liquidity",
        label_template="High liquidity (GTGD20 ≥ {min_billion}B VND)",
        description="Average 20-session trading value is at least min_billion billion VND.",
        params=(
            AIFilterParamSpec(name="min_billion", type="float", default=20.0, description="Min GTGD20 in billion VND"),
        ),
        predicate=_high_liquidity,
    ),
    "low_liquidity": CatalogEntry(
        key="low_liquidity",
        label_template="Low liquidity (GTGD20 < {max_billion}B VND)",
        description="Average 20-session trading value is below max_billion billion VND.",
        params=(
            AIFilterParamSpec(name="max_billion", type="float", default=5.0, description="Max GTGD20 in billion VND"),
        ),
        predicate=_low_liquidity,
    ),
    "stable_cv": CatalogEntry(
        key="stable_cv",
        label_template="Low volatility (CV < {cv_cap}%)",
        description="Coefficient of variation of GTGD20 is below cv_cap percent.",
        params=(
            AIFilterParamSpec(name="cv_cap", type="float", default=100.0, description="CV cap in %"),
        ),
        predicate=_stable_cv,
    ),
    "volume_surge": CatalogEntry(
        key="volume_surge",
        label_template="Volume surge (intraday ≥ {ratio}x expected)",
        description="Today's intraday trading value is at least ratio times the expected value at this time.",
        params=(
            AIFilterParamSpec(name="ratio", type="float", default=1.5, description="Min intraday/expected ratio"),
        ),
        predicate=_volume_surge,
    ),
    "exclude_ceiling_floor": CatalogEntry(
        key="exclude_ceiling_floor",
        label_template="Exclude ceiling/floor",
        description="Drop stocks currently locked at ceiling or floor price.",
        params=(),
        predicate=_exclude_ceiling_floor,
    ),
    "exchange_in": CatalogEntry(
        key="exchange_in",
        label_template="Exchange in {exchanges}",
        description="Only stocks listed on the given exchanges (HOSE, HNX, UPCOM).",
        params=(
            AIFilterParamSpec(name="exchanges", type="list[str]", default=["HOSE"], description="Allowed exchanges"),
        ),
        predicate=_exchange_in,
    ),
}


def public_catalog() -> list[AIFilterCatalogEntry]:
    return [
        AIFilterCatalogEntry(
            key=e.key,
            label_template=e.label_template,
            description=e.description,
            params=list(e.params),
        )
        for e in CATALOG.values()
    ]
