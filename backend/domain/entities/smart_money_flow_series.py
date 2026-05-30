from domain.entities.smart_money_flow_day import SmartMoneyFlowDay


class SmartMoneyFlowSeries:
    def __init__(self, symbol: str, days_requested: int, rows: list[SmartMoneyFlowDay]):
        self.symbol = symbol
        self.days_requested = days_requested
        self.rows = rows
