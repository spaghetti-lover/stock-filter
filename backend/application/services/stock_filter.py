"""Stock filtering — apply a FilterCriteria to a batch of stocks.

Returns (passed, rejected). First-rejection-wins: the order of
``criteria.active_rules()`` decides which reason a multi-failing stock carries.
"""

from application.dto.stock_dto import GetStockResponse
from application.layer1 import FilterCriteria


def apply_filters(
    stocks: list[GetStockResponse],
    criteria: FilterCriteria,
) -> tuple[list[GetStockResponse], list[GetStockResponse]]:
    rules = criteria.active_rules()
    passed: list[GetStockResponse] = []
    rejected: list[GetStockResponse] = []

    for stock in stocks:
        reason: str | None = None
        for rule in rules:
            reason = rule.check(stock)
            if reason:
                break
        if reason:
            rejected.append(stock.model_copy(update={"reject_reason": reason}))
        else:
            passed.append(stock)

    return passed, rejected
