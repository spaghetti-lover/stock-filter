"""Gemini implementation using the Google Gemini ADK with function calling (MCP-equivalent)."""

import asyncio
import json
import os

from fastapi import HTTPException
from google import genai
from google.genai import types
from google.genai.errors import ClientError

from domain.agents.agent_provider import AgentProvider
from infrastructure.market_data.data import get_all_symbols, get_trading_history, get_intraday


def _to_gemini_role(role: str) -> str:
    return "model" if role == "assistant" else "user"


# ── Tool implementations (mirror stock_tools.py logic) ───────────────────────

async def _list_symbols(exchange: str = "") -> dict:
    exchange_filter = exchange.upper() if exchange else ""
    symbols = await asyncio.to_thread(get_all_symbols)
    if exchange_filter:
        symbols = [s for s in symbols if s["exchange"] == exchange_filter]
    return {"total": len(symbols), "symbols": symbols}


async def _trading_history(symbol: str, days: int = 30) -> dict:
    rows = await asyncio.to_thread(get_trading_history, symbol.upper(), days)
    if not rows:
        return {"error": f"No trading history found for {symbol}"}
    return {"symbol": symbol, "sessions": len(rows), "history": rows}


async def _intraday_data(symbol: str) -> dict:
    rows = await asyncio.to_thread(get_intraday, symbol.upper())
    if not rows:
        return {"error": f"No intraday data for {symbol} (market may be closed)"}
    return {"symbol": symbol, "ticks": len(rows), "data": rows}


async def _stock_price(symbol: str) -> dict:
    rows = await asyncio.to_thread(get_trading_history, symbol.upper(), 30)
    if not rows:
        return {"error": f"No data found for {symbol}"}
    latest = rows[-1]
    last_20 = rows[-20:] if len(rows) >= 20 else rows
    gtgd20 = sum(r["close"] * 1000 * r["volume"] for r in last_20) / len(last_20)
    avg_volume = sum(r["volume"] for r in last_20) / len(last_20)
    return {
        "symbol": symbol,
        "current_price": latest["close"],
        "price_unit": "thousand VND",
        "latest_date": str(latest.get("time")),
        "high_30d": max(r["high"] for r in rows),
        "low_30d": min(r["low"] for r in rows),
        "avg_volume_20d": round(avg_volume),
        "gtgd20_billion": round(gtgd20 / 1e9, 2),
    }


async def _compare_stocks(symbols: str) -> dict | list:
    symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    if len(symbol_list) < 2:
        return {"error": "Provide at least 2 symbols separated by commas"}
    if len(symbol_list) > 5:
        return {"error": "Maximum 5 symbols for comparison"}
    results = []
    for sym in symbol_list:
        rows = await asyncio.to_thread(get_trading_history, sym, 30)
        if not rows:
            results.append({"symbol": sym, "error": "no data"})
            continue
        latest = rows[-1]
        last_20 = rows[-20:] if len(rows) >= 20 else rows
        gtgd20 = sum(r["close"] * 1000 * r["volume"] for r in last_20) / len(last_20)
        results.append({
            "symbol": sym,
            "current_price": latest["close"],
            "high_30d": max(r["high"] for r in rows),
            "low_30d": min(r["low"] for r in rows),
            "gtgd20_billion": round(gtgd20 / 1e9, 2),
            "sessions": len(rows),
        })
    return results


_TOOL_DISPATCH = {
    "list_symbols": _list_symbols,
    "trading_history": _trading_history,
    "intraday_data": _intraday_data,
    "stock_price": _stock_price,
    "compare_stocks": _compare_stocks,
}

# ── Gemini function declarations ──────────────────────────────────────────────

_TOOLS = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="list_symbols",
            description="List all stock symbols from HOSE and HNX exchanges. Returns symbol and exchange for each stock.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "exchange": types.Schema(
                        type=types.Type.STRING,
                        description="Filter by exchange: HOSE or HNX. Leave empty for all.",
                    ),
                },
            ),
        ),
        types.FunctionDeclaration(
            name="trading_history",
            description="Get daily OHLCV (open, high, low, close, volume) history for a stock symbol.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "symbol": types.Schema(type=types.Type.STRING, description="Stock symbol, e.g. VCB"),
                    "days": types.Schema(type=types.Type.INTEGER, description="Number of calendar days to look back (default 30)"),
                },
                required=["symbol"],
            ),
        ),
        types.FunctionDeclaration(
            name="intraday_data",
            description="Get today's intraday tick data (time, price, volume) for a stock symbol. Only available during trading hours 9:00-15:00 Vietnam time.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "symbol": types.Schema(type=types.Type.STRING, description="Stock symbol, e.g. VCB"),
                },
                required=["symbol"],
            ),
        ),
        types.FunctionDeclaration(
            name="stock_price",
            description="Get the current (latest closing) price and key metrics for a stock: price, 30-day high/low, average volume, GTGD20.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "symbol": types.Schema(type=types.Type.STRING, description="Stock symbol, e.g. VCB"),
                },
                required=["symbol"],
            ),
        ),
        types.FunctionDeclaration(
            name="compare_stocks",
            description="Compare key metrics for 2-5 stock symbols side by side: price, GTGD20, 30-day high/low.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "symbols": types.Schema(
                        type=types.Type.STRING,
                        description="Comma-separated list of 2-5 stock symbols, e.g. VCB,TCB,MBB",
                    ),
                },
                required=["symbols"],
            ),
        ),
    ]
)


class GeminiAgent(AgentProvider):
    def __init__(self, model: str = "gemini-2.5-flash"):
        self._model = model
        self._client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])

    async def chat(self, messages: list[dict], system_prompt: str) -> str:
        history: list[types.ContentOrDict] = [
            {
                "role": _to_gemini_role(m["role"]),
                "parts": [{"text": m["content"]}],
            }
            for m in messages[:-1]
        ]
        last_message = messages[-1]["content"]

        try:
            chat_session = self._client.aio.chats.create(
                model=self._model,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    tools=[_TOOLS],
                ),
                history=history,
            )

            response = await chat_session.send_message(last_message)

            # Agentic loop: execute tool calls and feed results back until Gemini
            # produces a final text response (same pattern Claude does via MCP).
            while response.function_calls:
                tool_response_parts = []
                for fc in response.function_calls:
                    name = fc.name or ""
                    fn = _TOOL_DISPATCH.get(name)
                    if fn is None:
                        result: dict = {"error": f"Unknown tool: {name}"}
                    else:
                        try:
                            result = await fn(**(fc.args or {}))
                        except Exception as e:
                            result = {"error": str(e)}

                    tool_response_parts.append(
                        types.Part.from_function_response(
                            name=name,
                            response={"result": json.dumps(result, ensure_ascii=False, default=str)},
                        )
                    )

                response = await chat_session.send_message(tool_response_parts)

            return response.text or ""

        except ClientError as e:
            if e.status == 429:
                raise HTTPException(
                    status_code=429,
                    detail=f"Gemini quota exceeded: {e.args[0] if e.args else 'unknown'}",
                ) from e
            raise HTTPException(
                status_code=502,
                detail=f"Gemini API error {e.status}: {e.args[0] if e.args else 'unknown'}",
            ) from e
