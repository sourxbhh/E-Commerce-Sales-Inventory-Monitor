-- Idempotent migration for users who ran docker compose with the
-- older schema. Safe to re-run.
USE ecommerce_rt;

-- widen name (FakeStoreAPI titles can be long)
ALTER TABLE products MODIFY COLUMN name VARCHAR(500) NOT NULL;

-- add FakeStoreAPI columns if missing
ALTER TABLE products
    ADD COLUMN IF NOT EXISTS source       VARCHAR(40)   DEFAULT 'fakestoreapi',
    ADD COLUMN IF NOT EXISTS image_url    VARCHAR(500),
    ADD COLUMN IF NOT EXISTS description  TEXT,
    ADD COLUMN IF NOT EXISTS rating_rate  DECIMAL(3,2),
    ADD COLUMN IF NOT EXISTS rating_count INT;

ALTER TABLE products
    ADD INDEX IF NOT EXISTS idx_source (source);
