from crawler import get_all_symbols, get_intraday, get_trading_history

def test_get_all_symbols():
  symbols = get_all_symbols()
  assert isinstance(symbols, list)
  assert len(symbols) > 0

def test_get_intraday():
  symbols = get_all_symbols()
  symbol = symbols[1]["symbol"]
  intraday_data = get_intraday(symbol)
  assert isinstance(intraday_data, list)
  assert len(intraday_data) > 0

def test_get_trading_history():
  symbols = get_all_symbols()
  symbol = symbols[1]["symbol"]
  history = get_trading_history(symbol, days=10)
  assert isinstance(history, list)
  assert len(history) > 0