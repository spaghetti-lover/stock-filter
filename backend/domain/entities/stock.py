class Stock:
    def __init__(self, symbol: str, exchange: str, status: str, price: float, gtgd20: float, history_sessions: int, today_value: float, avg_intraday_expected: float):
        self.symbol = symbol
        self.exchange = exchange
        self.status = status
        self.price = price
        self.gtgd20 = gtgd20
        self.history_sessions = history_sessions
        self.today_value = today_value
        self.avg_intraday_expected = avg_intraday_expected