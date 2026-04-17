class Layer2Score:
    def __init__(self, symbol: str, exchange: str, buy_score: float, liquidity_score: float, momentum_score: float, breakout_score: float):
        self.symbol = symbol
        self.exchange = exchange
        self.buy_score = buy_score
        self.liquidity_score = liquidity_score
        self.momentum_score = momentum_score
        self.breakout_score = breakout_score
