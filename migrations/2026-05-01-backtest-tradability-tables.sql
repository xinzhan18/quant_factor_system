-- Backtest tradability tables: ST status (PIT) + instrument lifecycle.
-- Run once via:
--   psql -h localhost -U postgres -d quant_data -f \
--       migrations/2026-05-01-backtest-tradability-tables.sql

CREATE TABLE IF NOT EXISTS instrument_st_status (
    datetime    DATE         NOT NULL,
    instrument  VARCHAR(16)  NOT NULL,
    is_st       BOOLEAN      NOT NULL,
    PRIMARY KEY (datetime, instrument)
);
CREATE INDEX IF NOT EXISTS idx_st_datetime ON instrument_st_status(datetime);

CREATE TABLE IF NOT EXISTS instrument_lifecycle (
    instrument      VARCHAR(16)  PRIMARY KEY,
    listing_date    DATE         NOT NULL,
    delisting_date  DATE,
    board           VARCHAR(16)  NOT NULL  -- main | chinext | star | bse
);
