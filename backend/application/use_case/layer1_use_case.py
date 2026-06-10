from domain.repositories.layer1_stock_repository import (
    EarlyRejectKind,
    Layer1StockRepository,
    ProgressCallback,
)
from application.mappers.stock_mapper import StockMapper
from application.mappers.market_regime_mapper import MarketRegimeMapper
from application.dto.stock_dto import FilteredStocksResponse, GetStockResponse
from application.layer1 import FilterCriteria
from application.layer1.rules import MinGtgdRule
from application.services.stock_filter import apply_filters
from logger import get_logger

log = get_logger(__name__)


def _format_early_reject(
    kind: EarlyRejectKind,
    observed_gtgd: float | None,
    criteria: FilterCriteria,
) -> str:
    """Render an early-reject signal as the same user-facing message the
    in-pipeline Layer 1 rules would have produced. For BELOW_MIN_GTGD we
    actually run the rule, so MinGtgdRule is the single source of truth for
    wording."""
    if kind is EarlyRejectKind.NO_HISTORY:
        return "No trading history available"
    if kind is EarlyRejectKind.FETCH_FAILED:
        return "Failed to fetch data"
    if kind is EarlyRejectKind.BELOW_MIN_GTGD and criteria.min_gtgd_vnd is not None:
        probe = GetStockResponse(
            symbol="", exchange="", status="N/A", current_price=0.0,
            gtgd20=observed_gtgd or 0.0, history_sessions=0,
            today_value=0.0, avg_intraday_expected=0.0, intraday_ratio=None,
        )
        return MinGtgdRule(threshold_vnd=criteria.min_gtgd_vnd).check(probe) or ""
    return "Filtered before full fetch"


class Layer1UseCase:
    def __init__(
        self,
        repo: Layer1StockRepository,
        fallback_repo: Layer1StockRepository | None = None,
        save_stocks_fn=None,
    ):
        self.repo = repo
        self.fallback_repo = fallback_repo
        self.save_stocks_fn = save_stocks_fn

    async def execute(
        self,
        criteria: FilterCriteria,
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
        # Repository pre-filters cheaply (gtgd / history) before the full per-stock fetch;
        # passing 0 keeps everything when the rule is disabled.
        repo_min_gtgd = criteria.min_gtgd_vnd or 0.0
        repo_min_history = criteria.min_history or 0

        stocks, early_rejected = await self.repo.list_stocks(
            exchanges=criteria.exchanges,
            min_gtgd=repo_min_gtgd,
            min_history_sessions=repo_min_history,
            on_progress=on_progress,
        )

        # --- Fallback: if primary repo returned nothing, try live fetch ---
        if not stocks and self.fallback_repo is not None:
            log.info("Primary repo returned no data, falling back to live fetch")
            stocks, early_rejected = await self.fallback_repo.list_stocks(
                exchanges=criteria.exchanges,
                min_gtgd=repo_min_gtgd,
                min_history_sessions=repo_min_history,
                on_progress=on_progress,
            )

        responses = StockMapper.to_response_list(stocks)
        passed, rejected = apply_filters(responses, criteria)

        # Include early-rejected stocks (no history / below min_gtgd before full fetch).
        # Reasons are rendered here, not in the scanner, so MinGtgdRule remains the
        # single source of truth for the GTGD20 message.
        for symbol, exchange, kind, observed_gtgd in early_rejected:
            rejected.append(GetStockResponse(
                symbol=symbol,
                exchange=exchange,
                status="N/A",
                current_price=0.0,
                gtgd20=observed_gtgd or 0.0,
                history_sessions=0,
                today_value=0.0,
                avg_intraday_expected=0.0,
                intraday_ratio=None,
                reject_reason=_format_early_reject(kind, observed_gtgd, criteria),
            ))

        # Persist all stocks with passed flag for Layer 2 handoff
        if stocks and self.save_stocks_fn is not None:
            passed_symbols = {s.symbol for s in passed}
            await self.save_stocks_fn(stocks, passed_symbols)
            log.info("Saved %d stocks to DB (%d passed)", len(stocks), len(passed_symbols))

        return FilteredStocksResponse(passed=passed, rejected=rejected, market_regime=regime_resp)
