-- =============================================================================
-- Vietnam Stock Filter — TimescaleDB Schema
-- =============================================================================
-- Database: TimescaleDB (PostgreSQL extension for time-series data)
--
-- Why TimescaleDB:
--   • Stock trading data is time-series by nature (daily sessions, intraday ticks)
--   • gtgd20 requires rolling 20-session window queries — hypertable partitioning
--     keeps these fast as data grows
--   • Full PostgreSQL SQL: supports relational joins between stock metadata and
--     time-series tables without any special query language
--   • Compatible with SQLAlchemy / asyncpg out of the box
--
-- Schema overview:
--   stocks               — static stock metadata (symbol, exchange, status)
--   trading_sessions     — one row per stock per trading day (hypertable)
--   intraday_snapshots   — cumulative value snapshots per intraday time slot (hypertable)
--   intraday_distribution — reference table for expected intraday cumulative %
--   stock_summary        — view that reconstructs the /stocks API response fields
-- =============================================================================

-- Enable TimescaleDB extension (run once per database)
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- =============================================================================
-- 1. stocks — stock metadata
-- =============================================================================

CREATE TABLE stocks (
    symbol          VARCHAR(10)     PRIMARY KEY,
    exchange        VARCHAR(10)     NOT NULL
                        CHECK (exchange IN ('HOSE', 'HNX', 'UPCOM')),
    status          VARCHAR(20)     NOT NULL DEFAULT 'normal'
                        CHECK (status IN ('normal', 'warning', 'control', 'restriction')),
    company_name    VARCHAR(255),
    sector          VARCHAR(100),
    listed_at       DATE,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- 2. trading_sessions — daily OHLCV data per stock (time-series hypertable)
--
-- Stores one row per (session_date, symbol).
-- Used to compute:
--   • gtgd20             = AVG(total_value) over the last 20 sessions
--   • history_sessions   = COUNT(*) of available sessions for the symbol
--   • current_price      = close_price of the most recent session
-- =============================================================================

CREATE TABLE trading_sessions (
    session_date    DATE            NOT NULL,
    symbol          VARCHAR(10)     NOT NULL REFERENCES stocks(symbol),
    open_price      NUMERIC(15, 2)  NOT NULL,
    close_price     NUMERIC(15, 2)  NOT NULL,   -- used as current_price
    high_price      NUMERIC(15, 2)  NOT NULL,
    low_price       NUMERIC(15, 2)  NOT NULL,
    ref_price       NUMERIC(15, 2),             -- previous session close (reference price)
    total_volume    BIGINT          NOT NULL DEFAULT 0,  -- shares traded
    total_value     NUMERIC(20, 2)  NOT NULL DEFAULT 0,  -- VND: used for gtgd20
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    PRIMARY KEY (session_date, symbol)
);

-- Convert to TimescaleDB hypertable — partitioned by session_date
SELECT create_hypertable('trading_sessions', 'session_date');

-- Index for per-symbol lookups (gtgd20, history_sessions, current_price)
CREATE INDEX ON trading_sessions (symbol, session_date DESC);

-- =============================================================================
-- 3. intraday_snapshots — cumulative value snapshots at each intraday time slot
--
-- Stores one row per (snapshot_time, symbol), taken at the standard Vietnam
-- market time slots defined in intraday_distribution.
-- Used to compute:
--   • today_value            = cumulative_value of the latest snapshot today
--   • avg_intraday_expected  = expected_cumulative of the latest snapshot today
-- =============================================================================

CREATE TABLE intraday_snapshots (
    snapshot_time           TIMESTAMPTZ     NOT NULL,
    symbol                  VARCHAR(10)     NOT NULL REFERENCES stocks(symbol),
    current_price           NUMERIC(15, 2)  NOT NULL,
    cumulative_value        NUMERIC(20, 2)  NOT NULL DEFAULT 0,  -- VND accumulated so far today
    expected_cumulative     NUMERIC(20, 2)  NOT NULL DEFAULT 0,  -- VND expected by this time slot
    PRIMARY KEY (snapshot_time, symbol)
);

-- Convert to TimescaleDB hypertable — partitioned by snapshot_time
SELECT create_hypertable('intraday_snapshots', 'snapshot_time');

-- Index for per-symbol latest-snapshot lookups
CREATE INDEX ON intraday_snapshots (symbol, snapshot_time DESC);

-- =============================================================================
-- 4. intraday_distribution — reference cumulative % per Vietnam market time slot
--
-- Vietnam market hours: 09:00–11:30, 13:00–15:00
-- Each row defines how much of the daily total_value is typically accumulated
-- by that time slot (used to compute avg_intraday_expected).
-- =============================================================================

CREATE TABLE intraday_distribution (
    time_slot       TIME            PRIMARY KEY,
    cumulative_pct  NUMERIC(5, 4)   NOT NULL
                        CHECK (cumulative_pct BETWEEN 0 AND 1)
);

INSERT INTO intraday_distribution (time_slot, cumulative_pct) VALUES
    ('09:00', 0.12),
    ('09:30', 0.22),
    ('10:00', 0.30),
    ('10:30', 0.37),
    ('11:00', 0.43),
    ('11:30', 0.48),
    ('13:00', 0.56),
    ('13:30', 0.65),
    ('14:00', 0.75),
    ('14:30', 0.86),
    ('15:00', 1.00);

-- =============================================================================
-- 5. stock_summary — view that reconstructs the /stocks API response
--
-- Mirrors the GetStockResponse DTO fields:
--   symbol, exchange, status, current_price,
--   gtgd20, history_sessions, today_value, avg_intraday_expected
-- =============================================================================

CREATE OR REPLACE VIEW stock_summary AS
SELECT
    s.symbol,
    s.exchange,
    s.status,

    -- current_price: close_price from the most recent trading session
    latest_session.close_price                      AS current_price,

    -- gtgd20: average total_value over the last 20 sessions
    gtgd.gtgd20,

    -- history_sessions: total number of recorded trading sessions
    gtgd.session_count                              AS history_sessions,

    -- today_value: cumulative trading value from the latest intraday snapshot today
    latest_snapshot.cumulative_value                AS today_value,

    -- avg_intraday_expected: expected cumulative value at the latest snapshot time
    latest_snapshot.expected_cumulative             AS avg_intraday_expected

FROM stocks s

-- Most recent trading session (for current_price)
LEFT JOIN LATERAL (
    SELECT close_price
    FROM trading_sessions ts
    WHERE ts.symbol = s.symbol
    ORDER BY session_date DESC
    LIMIT 1
) latest_session ON TRUE

-- Last 20 sessions: gtgd20 and history_sessions
LEFT JOIN LATERAL (
    SELECT
        AVG(total_value)    AS gtgd20,
        COUNT(*)            AS session_count
    FROM (
        SELECT total_value
        FROM trading_sessions ts
        WHERE ts.symbol = s.symbol
        ORDER BY session_date DESC
        LIMIT 20
    ) last20
) gtgd ON TRUE

-- Latest intraday snapshot today (for today_value, avg_intraday_expected)
LEFT JOIN LATERAL (
    SELECT cumulative_value, expected_cumulative
    FROM intraday_snapshots ins
    WHERE ins.symbol = s.symbol
      AND ins.snapshot_time >= CURRENT_DATE
    ORDER BY snapshot_time DESC
    LIMIT 1
) latest_snapshot ON TRUE;
