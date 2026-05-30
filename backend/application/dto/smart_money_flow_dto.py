from typing import Literal

from pydantic import BaseModel


class SmartMoneyFlowRow(BaseModel):
    date: str
    foreign_buy_value: float
    foreign_sell_value: float
    prop_buy_value: float
    prop_sell_value: float
    total_gtgd: float
    close_price: float

    foreign_net_pct: float
    prop_net_pct: float
    sm_net_pct: float
    sm_net_pct_uncapped: float
    dominance_pct: float
    sm_net_5d: float | None

    block_deal: bool
    divergence_type: Literal["prop_taking_profit", "prop_supporting"] | None
    signal_label: str
    signal_color: str


class SmartMoneyFlowResponse(BaseModel):
    symbol: str
    days_requested: int
    fetched_at: str
    rows: list[SmartMoneyFlowRow]
