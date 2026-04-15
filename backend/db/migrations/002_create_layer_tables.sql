CREATE TABLE IF NOT EXISTS layer1_results (
    symbol                VARCHAR(20) NOT NULL,
    exchange              VARCHAR(10) NOT NULL,
    status                VARCHAR(20) NOT NULL DEFAULT 'normal',
    current_price         DOUBLE PRECISION NOT NULL DEFAULT 0,
    gtgd20                DOUBLE PRECISION NOT NULL DEFAULT 0,
    history_sessions      INTEGER NOT NULL DEFAULT 0,
    today_value           DOUBLE PRECISION NOT NULL DEFAULT 0,
    avg_intraday_expected DOUBLE PRECISION NOT NULL DEFAULT 0,
    intraday_ratio        DOUBLE PRECISION,
    is_ceiling            BOOLEAN NOT NULL DEFAULT FALSE,
    is_floor              BOOLEAN NOT NULL DEFAULT FALSE,
    cv                    DOUBLE PRECISION,
    result                VARCHAR(10) NOT NULL,
    reject_reason         TEXT,
    filtered_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (symbol)
);

CREATE INDEX IF NOT EXISTS idx_layer1_results_result ON layer1_results(result);

CREATE TABLE IF NOT EXISTS layer2_scores (
    symbol              VARCHAR(20) PRIMARY KEY,
    exchange            VARCHAR(10) NOT NULL,
    buy_score           DOUBLE PRECISION NOT NULL,
    liquidity_score     DOUBLE PRECISION NOT NULL,
    momentum_score      DOUBLE PRECISION NOT NULL,
    breakout_score      DOUBLE PRECISION NOT NULL,
    scored_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
