-- depends: 004.create_discussions

ALTER TABLE scraper_cursor ADD COLUMN IF NOT EXISTS scope_key VARCHAR(128) NOT NULL DEFAULT '';

ALTER TABLE scraper_cursor DROP CONSTRAINT IF EXISTS scraper_cursor_pkey;
ALTER TABLE scraper_cursor ADD PRIMARY KEY (source, scope_key);
