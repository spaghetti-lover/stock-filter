from domain.repositories.stock_repository import ProgressCallback, StockRepository
from domain.repositories.layer1_repository import Layer1ResultRepository
from application.mappers.stock_mapper import StockMapper
from application.mappers.market_regime_mapper import MarketRegimeMapper
from application.dto.stock_dto import FilteredStocksResponse, GetStockResponse
from application.services.stock_filter import apply_filters
from logger import get_logger

log = get_logger(__name__)


class GetStockUseCase:
    def __init__(
        self,
        repo: StockRepository,
        fallback_repo: StockRepository | None = None,
        save_stocks_fn=None,
        layer1_repo: Layer1ResultRepository | None = None,
    ):
        self.repo = repo
        self.fallback_repo = fallback_repo
        self.save_stocks_fn = save_stocks_fn
        self.layer1_repo = layer1_repo

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
        exclude_ceiling_floor: bool = True,
        cv_cap: float = 200.0,
        use_cv: bool = True,
        market_regime_gate: bool = True,
        on_progress: ProgressCallback | None = None,
    ) -> FilteredStocksResponse:
        # --- Market Regime Gate ---
        regime_resp = None
        if market_regime_gate:
            regime = await self.repo.get_market_regime()
            regime_resp = MarketRegimeMapper.to_response(regime, gate_applied=True)

            if regime is not None and regime.state == "downtrend":
                return FilteredStocksResponse(
                    passed=[],
                    rejected=[],
                    market_regime=regime_resp,
                )

        # --- Per-symbol scan ---
        min_gtgd_raw = min_gtgd * 1e9
        stocks, early_rejected = await self.repo.list_stocks(
            exchanges=exchanges,
            min_gtgd=min_gtgd_raw,
            min_history_sessions=min_history if use_history else 0,
            on_progress=on_progress,
        )

        # --- Fallback: if primary repo returned nothing, try live fetch ---
        if not stocks and self.fallback_repo is not None:
            log.info("Primary repo returned no data, falling back to live fetch")
            stocks, early_rejected = await self.fallback_repo.list_stocks(
                exchanges=exchanges,
                min_gtgd=min_gtgd_raw,
                min_history_sessions=min_history if use_history else 0,
                on_progress=on_progress,
            )
            if stocks and self.save_stocks_fn is not None:
                await self.save_stocks_fn(stocks)
                log.info("Saved %d stocks to DB from fallback", len(stocks))

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
            exclude_ceiling_floor=exclude_ceiling_floor,
            cv_cap=cv_cap,
            use_cv=use_cv,
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

        # --- Persist Layer 1 results to DB ---
        if self.layer1_repo is not None:
            try:
                await self.layer1_repo.save_results(
                    [s.model_dump() for s in passed],
                    [s.model_dump() for s in rejected],
                )
            except Exception:
                log.warning("Failed to persist layer1 results", exc_info=True)

        return FilteredStocksResponse(passed=passed, rejected=rejected, market_regime=regime_resp)
