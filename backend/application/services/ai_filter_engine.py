"""Apply a list of AI-filter conditions over the stock snapshot."""

from application.dto.ai_filter_dto import AIFilterCondition
from application.dto.stock_dto import GetStockResponse
from application.services.ai_filter_catalog import CATALOG


def apply_ai_conditions(
    stocks: list[GetStockResponse],
    conditions: list[AIFilterCondition],
) -> tuple[list[GetStockResponse], list[GetStockResponse]]:
    """AND-compose all conditions. Returns (passed, rejected)."""
    if not conditions:
        return list(stocks), []

    valid: list[tuple[AIFilterCondition, callable]] = []  # type: ignore[type-arg]
    for cond in conditions:
        entry = CATALOG.get(cond.key)
        if entry is None:
            continue
        valid.append((cond, entry.predicate))

    passed: list[GetStockResponse] = []
    rejected: list[GetStockResponse] = []

    for stock in stocks:
        reject_reason: str | None = None
        for cond, predicate in valid:
            ok, reason = predicate(stock, cond.params or {})
            if not ok:
                reject_reason = f"{cond.label}: {reason}" if reason else cond.label
                break
        if reject_reason:
            rejected.append(stock.model_copy(update={"reject_reason": reject_reason}))
        else:
            passed.append(stock)

    return passed, rejected
