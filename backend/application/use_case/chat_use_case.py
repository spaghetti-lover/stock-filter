import json

from domain.agents.agent_provider import AgentProvider
from application.dto.chat_dto import ChatRequest, ChatResponse

_SYSTEM_PROMPT = """You are a helpful assistant for analyzing Vietnamese stocks (HOSE, HNX, UPCOM).
You have access to tools that can fetch live stock data. Use them when users ask about specific stocks.

Available tools:
- list_symbols: list all stock symbols (can filter by exchange)
- trading_history: get daily OHLCV data for a symbol
- intraday_data: get today's intraday ticks for a symbol
- stock_price: get current price and key metrics for a symbol
- compare_stocks: compare metrics for 2-5 symbols side by side

Metrics explained:
- GTGD20: average trading value over the last 20 sessions (billion VND)
- Intraday ratio: today's trading value vs expected value at this time of day (%)
- History sessions: number of trading sessions with available data
- Status: trading status (normal, warning, control, restriction)
- Price: current closing price (VND, stored in thousands)

Always use tools to fetch data rather than guessing. Respond in the same language the user writes in (Vietnamese or English)."""


class ChatUseCase:
    def __init__(self, provider: AgentProvider):
        self._provider = provider

    async def execute(self, request: ChatRequest) -> ChatResponse:
        system = _SYSTEM_PROMPT
        if request.stocks_context:
            stocks_json = json.dumps(request.stocks_context[:200], ensure_ascii=False)
            system += f"\n\nCurrent filtered stock data:\n{stocks_json}"

        messages = [{"role": m.role, "content": m.content} for m in request.messages]
        reply = await self._provider.chat(messages=messages, system_prompt=system)

        return ChatResponse(
            response=reply,
            provider=type(self._provider).__name__,
        )
