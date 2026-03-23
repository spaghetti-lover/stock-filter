from datetime import datetime, timedelta
from vnstock import Vnstock


def get_all_symbols() -> list[dict]:
  """Get all stock symbols from HOSE and HNX exchanges."""
  stock = Vnstock().stock(symbol="VN30F1M", source="VCI")
  df = stock.listing.symbols_by_exchange()
  df = df[df["exchange"].isin(["HOSE", "HNX"])]
  return df[["symbol", "exchange"]].to_dict(orient="records")


def get_trading_history(symbol: str, days: int = 100) -> list[dict]:
  """Get daily OHLCV history for a symbol."""
  stock = Vnstock().stock(symbol=symbol, source="VCI")
  end = datetime.now().strftime("%Y-%m-%d")
  start = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
  df = stock.quote.history(start=start, end=end)
  return df.to_dict(orient="records")


def get_intraday(symbol: str) -> list[dict]:
  """Get intraday snapshots for a symbol."""
  stock = Vnstock().stock(symbol=symbol, source="VCI")
  df = stock.quote.intraday()
  return df.to_dict(orient="records")