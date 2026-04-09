from domain.repositories.stock_repository import ProgressCallback, StockRepository
from application.mappers.stock_mapper import StockMapper
from application.dto.stock_dto import FilteredStocksResponse, GetStockResponse
from application.services.stock_filter import apply_filters


class GetStockUseCase:
    def __init__(self, repo: StockRepository):
        self.repo = repo

    async def execute(
        self,
        exchanges: set[str] | None = None,
        min_gtgd: float = 0.0,
        statuses: set[str] | None = None,
        min_history: int = 0,
        min_price: float = 0.0,
        min_intraday_ratio: float = 0.0,
        min_volume: float = 0.0,
        use_exchange: bool = True,
        use_gtgd20: bool = True,
        use_status: bool = True,
        use_history: bool = True,
        use_price: bool = True,
        use_intraday: bool = True,
        use_volume: bool = True,
        on_progress: ProgressCallback | None = None,
    ) -> FilteredStocksResponse:
        min_gtgd_raw = min_gtgd * 1e9
        stocks, early_rejected = await self.repo.list_stocks(
            exchanges=exchanges,
            min_gtgd=min_gtgd_raw,
            min_history_sessions=min_history if use_history else 0,
            on_progress=on_progress,
        )
        responses = StockMapper.to_response_list(stocks)

        passed, rejected = apply_filters(
            responses,
            exchanges=exchanges,
            min_gtgd20=min_gtgd_raw,
            allowed_statuses=statuses,
            min_history=min_history,
            min_price=min_price,
            min_intraday_ratio=min_intraday_ratio,
            min_volume=min_volume,
            use_exchange=use_exchange,
            use_gtgd20=use_gtgd20,
            use_status=use_status,
            use_history=use_history,
            use_price=use_price,
            use_intraday=use_intraday,
            use_volume=use_volume,
        )

        # Include early-rejected stocks (no history / below min_gtgd before full fetch)
        for symbol, exchange, reason in early_rejected:
            rejected.append(GetStockResponse(
                symbol=symbol,
                exchange=exchange,
                status="N/A",
                current_price=0.0,
                gtgd20=0.0,
                history_sessions=0,
                today_value=0.0,
                avg_intraday_expected=0.0,
                intraday_ratio=None,
                reject_reason=reason,
            ))

        return FilteredStocksResponse(passed=passed, rejected=rejected)
