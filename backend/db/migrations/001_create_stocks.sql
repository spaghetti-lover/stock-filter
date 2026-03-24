-- 001_create_stocks.sql

CREATE TABLE IF NOT EXISTS symbols (
    symbol      VARCHAR(10) PRIMARY KEY,
    exchange    VARCHAR(10) NOT NULL CHECK (exchange IN ('HOSE', 'HNX', 'UPCOM')),
    status      VARCHAR(20) NOT NULL DEFAULT 'normal'
                CHECK (status IN ('normal', 'warning', 'control', 'restriction')),
    crawled_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS trading_history (
    id          BIGSERIAL PRIMARY KEY,
    symbol      VARCHAR(10) NOT NULL REFERENCES symbols(symbol) ON DELETE CASCADE,
    trade_date  DATE NOT NULL,
    open        NUMERIC(18,2),
    high        NUMERIC(18,2),
    low         NUMERIC(18,2),
    close       NUMERIC(18,2) NOT NULL,
    volume      BIGINT NOT NULL,
    crawled_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_trading_history_symbol_date UNIQUE (symbol, trade_date)
);
CREATE INDEX IF NOT EXISTS idx_trading_history_symbol_date ON trading_history (symbol, trade_date DESC);

CREATE TABLE IF NOT EXISTS stock_metrics (
    symbol           VARCHAR(10) PRIMARY KEY REFERENCES symbols(symbol) ON DELETE CASCADE,
    current_price    NUMERIC(18,2),
    gtgd20           NUMERIC(22,2),
    history_sessions INTEGER,
    metrics_date     DATE,
    crawled_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS intraday_snapshots (
    id          BIGSERIAL PRIMARY KEY,
    symbol      VARCHAR(10) NOT NULL REFERENCES symbols(symbol) ON DELETE CASCADE,
    snap_date   DATE NOT NULL,
    snap_time   TIME NOT NULL,
    price       NUMERIC(18,2) NOT NULL,
    volume      BIGINT NOT NULL,
    crawled_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_intraday_symbol_date ON intraday_snapshots (symbol, snap_date DESC, snap_time);

CREATE TABLE IF NOT EXISTS intraday_daily (
    symbol      VARCHAR(10) NOT NULL REFERENCES symbols(symbol) ON DELETE CASCADE,
    snap_date   DATE NOT NULL,
    today_value NUMERIC(22,2) NOT NULL DEFAULT 0,
    crawled_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (symbol, snap_date)
);
