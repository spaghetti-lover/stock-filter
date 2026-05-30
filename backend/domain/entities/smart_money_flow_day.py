class SmartMoneyFlowDay:
    def __init__(
        self,
        date: str,
        foreign_buy_value: float,
        foreign_sell_value: float,
        prop_buy_value: float,
        prop_sell_value: float,
        total_gtgd: float,
        close_price: float,
    ):
        self.date = date
        self.foreign_buy_value = foreign_buy_value
        self.foreign_sell_value = foreign_sell_value
        self.prop_buy_value = prop_buy_value
        self.prop_sell_value = prop_sell_value
        self.total_gtgd = total_gtgd
        self.close_price = close_price
