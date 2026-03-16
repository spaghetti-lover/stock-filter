```
backend/
│
├── app/
│
│   ├── domain/                # Business logic (không phụ thuộc framework)
│   │   ├── entities/
│   │   │   ├── stock.py
│   │   │   └── ohlcv.py
│   │   │
│   │   ├── repositories/
│   │   │   └── market_data_repository.py
│   │   │
│   │   ├── services/
│   │   │   └── stock_filter_service.py
│   │   │
│   │   └── rules/
│   │       ├── liquidity_rule.py
│   │       ├── price_rule.py
│   │       ├── intraday_activity_rule.py
│   │       └── data_quality_rule.py
│
│   ├── usecases/              # Application logic
│   │   └── run_stock_screener.py
│
│   ├── interfaces/            # Interface adapters
│   │   ├── api/
│   │   │   └── screener_controller.py
│   │   │
│   │   └── cli/
│   │       └── run_screener.py
│
│   ├── infrastructure/        # External systems
│   │   ├── data_providers/
│   │   │   ├── fireant_api.py
│   │   │   └── tcbs_api.py
│   │   │
│   │   ├── repositories/
│   │   │   └── market_data_repository_impl.py
│   │   │
│   │   └── cache/
│   │       └── redis_cache.py
│
│   ├── config/
│   │   └── settings.py
│
│   └── main.py                # API entrypoint
│
├── scripts/
│   └── run_daily_screen.py
│
├── tests/
│   ├── domain/
│   ├── usecases/
│   └── integration/
│
├── requirements.txt
```