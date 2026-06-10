import asyncio

from domain.entities.smart_money_flow_day import SmartMoneyFlowDay
from domain.entities.smart_money_flow_series import SmartMoneyFlowSeries
from domain.repositories.smart_money_flow_repository import SmartMoneyFlowRepository
from infrastructure.market_data.data import get_smart_money_raw
from infrastructure.concurrency import executor
from logger import get_logger

log = get_logger(__name__)


class SmartMoneyFlowRepositoryImpl(SmartMoneyFlowRepository):
    async def get_flow(self, symbol: str, days: int) -> SmartMoneyFlowSeries:
        loop = asyncio.get_event_loop()
        raw, warning = await loop.run_in_executor(executor, get_smart_money_raw, symbol, days)
        rows = [
            SmartMoneyFlowDay(
                date=r["date"],
                foreign_buy_value=r["foreign_buy_value"],
                foreign_sell_value=r["foreign_sell_value"],
                prop_buy_value=r["prop_buy_value"],
                prop_sell_value=r["prop_sell_value"],
                total_gtgd=r["total_gtgd"],
                close_price=r["close_price"],
            )
            for r in raw
        ]
        return SmartMoneyFlowSeries(symbol=symbol, days_requested=days, rows=rows, warning=warning)
