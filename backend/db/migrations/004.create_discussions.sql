-- depends: 003.add_layer2_breakdown

CREATE TABLE IF NOT EXISTS discussion_posts (
    id              BIGSERIAL PRIMARY KEY,
    source          VARCHAR(20)  NOT NULL,
    external_id     VARCHAR(128) NOT NULL,
    ticker_symbols  TEXT[]       NOT NULL DEFAULT '{}',
    author          VARCHAR(200),
    posted_at       TIMESTAMPTZ  NOT NULL,
    title           TEXT,
    body            TEXT         NOT NULL,
    url             TEXT         NOT NULL,
    fetched_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    body_tsv        TSVECTOR,
    UNIQUE (source, external_id)
);

CREATE INDEX IF NOT EXISTS idx_dp_posted_at    ON discussion_posts (posted_at DESC);
CREATE INDEX IF NOT EXISTS idx_dp_tickers_gin  ON discussion_posts USING GIN (ticker_symbols);
CREATE INDEX IF NOT EXISTS idx_dp_body_tsv_gin ON discussion_posts USING GIN (body_tsv);

CREATE OR REPLACE FUNCTION discussion_posts_tsv_trigger() RETURNS trigger AS $$
BEGIN
  NEW.body_tsv :=
    setweight(to_tsvector('simple', coalesce(NEW.title, '')), 'A') ||
    setweight(to_tsvector('simple', coalesce(NEW.body,  '')), 'B');
  RETURN NEW;
END
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_dp_tsv ON discussion_posts;
CREATE TRIGGER trg_dp_tsv BEFORE INSERT OR UPDATE OF title, body
ON discussion_posts FOR EACH ROW EXECUTE FUNCTION discussion_posts_tsv_trigger();

CREATE TABLE IF NOT EXISTS scraper_cursor (
    source           VARCHAR(20)  PRIMARY KEY,
    last_external_id VARCHAR(128),
    updated_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS discussion_crawl_log (
    id              SERIAL PRIMARY KEY,
    source          VARCHAR(20),
    started_at      TIMESTAMPTZ NOT NULL,
    finished_at     TIMESTAMPTZ,
    status          VARCHAR(20) NOT NULL DEFAULT 'running',
    inserted_count  INTEGER,
    error_message   TEXT
);
