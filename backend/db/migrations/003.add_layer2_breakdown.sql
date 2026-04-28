-- depends: 002.add_passed_and_layer2

ALTER TABLE layer2_scores ADD COLUMN IF NOT EXISTS breakdown JSONB;
