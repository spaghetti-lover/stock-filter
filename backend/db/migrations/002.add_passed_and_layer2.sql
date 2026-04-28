-- depends: 001.create_stocks

-- Add passed flag to stock_metrics for Layer 1 → Layer 2 handoff
ALTER TABLE stock_metrics ADD COLUMN IF NOT EXISTS passed BOOLEAN DEFAULT FALSE;

-- Layer 2 buy scores
CREATE TABLE IF NOT EXISTS layer2_scores (
    symbol           VARCHAR(20) PRIMARY KEY,
    exchange         VARCHAR(10) NOT NULL,
    buy_score        DOUBLE PRECISION NOT NULL,
    liquidity_score  DOUBLE PRECISION NOT NULL,
    momentum_score   DOUBLE PRECISION NOT NULL,
    breakout_score   DOUBLE PRECISION NOT NULL,
    scored_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
