from domain.entities.stock import Stock
from application.dto.stock_dto import GetStockResponse

class StockMapper:

    @staticmethod
    def to_response(stock: Stock) -> GetStockResponse:
        return GetStockResponse(
            symbol=stock.symbol,
            exchange=stock.exchange,
            status=stock.status,
            current_price=stock.price,
            gtgd20=stock.gtgd20,
            history_sessions=stock.history_sessions,
            today_value=stock.today_value,
            avg_intraday_expected=stock.avg_intraday_expected,
            intraday_ratio=stock.intraday_ratio,
            is_ceiling=stock.is_ceiling,
            is_floor=stock.is_floor,
            cv=stock.cv,
        )

    @staticmethod
    def to_response_list(stocks: list[Stock]) -> list[GetStockResponse]:
        return [StockMapper.to_response(stock) for stock in stocks]