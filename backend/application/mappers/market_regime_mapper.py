from domain.value_objects.market_regime import MarketRegime
from application.dto.stock_dto import MarketRegimeResponse


class MarketRegimeMapper:

    @staticmethod
    def to_response(regime: MarketRegime | None, *, gate_applied: bool) -> MarketRegimeResponse | None:
        if not gate_applied:
            return None

        if regime is None:
            return MarketRegimeResponse(
                state="unknown",
                message="Unable to fetch VN-Index — proceeding without regime gate",
                gate_applied=True,
            )

        messages = {
            "downtrend": "Market in downtrend — screener suspended",
            "choppy": "MARKET CAUTION — VN-Index in choppy range",
        }

        return MarketRegimeResponse(
            state=regime.state,
            vnindex_close=regime.vnindex_close,
            vnindex_ma5=regime.vnindex_ma5,
            vnindex_ma20=regime.vnindex_ma20,
            ratio=regime.ratio,
            message=messages.get(regime.state),
            gate_applied=True,
        )
