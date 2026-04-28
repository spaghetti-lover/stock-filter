CREATE TABLE IF NOT EXISTS stock_metrics (
    symbol                VARCHAR(20) PRIMARY KEY,
    exchange              VARCHAR(10) NOT NULL,
    status                VARCHAR(20) NOT NULL DEFAULT 'normal',
    price                 DOUBLE PRECISION NOT NULL,
    gtgd20                DOUBLE PRECISION NOT NULL,
    history_sessions      INTEGER NOT NULL,
    today_value           DOUBLE PRECISION NOT NULL DEFAULT 0,
    avg_intraday_expected DOUBLE PRECISION NOT NULL DEFAULT 0,
    intraday_ratio        DOUBLE PRECISION,
    is_ceiling            BOOLEAN NOT NULL DEFAULT FALSE,
    is_floor              BOOLEAN NOT NULL DEFAULT FALSE,
    cv                    DOUBLE PRECISION,
    crawled_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_stock_metrics_exchange ON stock_metrics(exchange);

CREATE TABLE IF NOT EXISTS crawl_log (
    id            SERIAL PRIMARY KEY,
    started_at    TIMESTAMPTZ NOT NULL,
    finished_at   TIMESTAMPTZ,
    status        VARCHAR(20) NOT NULL DEFAULT 'running',
    total_symbols INTEGER,
    success_count INTEGER,
    error_message TEXT
);
