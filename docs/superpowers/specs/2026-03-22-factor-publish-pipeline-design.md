# Factor Publish Pipeline Design

**Date**: 2026-03-22
**Status**: Draft
**Goal**: After mining evaluator admits a factor, automatically persist its values to DB, generate an HTML report, and display it in the dashboard.

## Context

Currently, when a factor passes the multi-stage evaluation pipeline (`mining/evaluator.py`), only summary metrics are saved to YAML files (`mining/library/`). The factor values DataFrame computed during evaluation is discarded. There is no way to view factor performance in the dashboard or as a standalone report.

The old factor infrastructure (`data/storage/factor_storage.py`, `data/loaders.py` `DATABASE_FACTORS` dict, `daily_factors_wide` table) was built for hardcoded manual factors. It is being fully replaced by this mining-centric pipeline.

## Data Flow

```
mining/evaluator.py evaluate_batch()
    ↓ BatchResult.admitted (factor dict + cached values)
mining/library.py admit()
    ↓ Saves YAML, calls publisher
mining/publisher.py FactorPublisher.publish()
    ├→ 1. Write factor metadata + metrics → DB table: mining_factors
    ├→ 2. Write factor values (datetime×instrument) → DB table: mining_factor_values
    └→ 3. Generate HTML report → mining/reports/factor_XXX.html
         └ Uses visualization/report.py FactorReportGenerator
```

Dashboard reads from DB tables directly.

## Database Tables

### Table: `mining_factors` — Factor metadata + evaluation metrics

```sql
CREATE TABLE mining_factors (
    factor_id    VARCHAR(10) PRIMARY KEY,  -- "001", "002", matches YAML library
    name         VARCHAR(200) NOT NULL,
    expression   TEXT NOT NULL,
    category     VARCHAR(50),
    ic_mean      FLOAT,         -- Full-sample IC mean
    ic_ir        FLOAT,         -- IC information ratio
    ic_mean_is   FLOAT,         -- In-sample IC
    ic_mean_oos  FLOAT,         -- Out-of-sample IC
    ic_win_rate  FLOAT,         -- Proportion of positive IC days
    ls_return    FLOAT,         -- Long-short return (Q5-Q1)
    monotonicity FLOAT,         -- Quantile return monotonicity
    train_start  DATE,
    train_end    DATE,
    test_start   DATE,
    test_end     DATE,
    admitted_at  DATE NOT NULL,
    report_path  VARCHAR(500)   -- Path to HTML report
);
```

### Table: `mining_factor_values` — Factor values (narrow table)

```sql
CREATE TABLE mining_factor_values (
    factor_id   VARCHAR(10) NOT NULL,
    symbol      VARCHAR(20) NOT NULL,
    trade_date  DATE NOT NULL,
    value       DOUBLE PRECISION,
    PRIMARY KEY (factor_id, symbol, trade_date)
);

-- Index for dashboard queries (load all values for one factor)
CREATE INDEX idx_mfv_factor_date ON mining_factor_values (factor_id, trade_date);
```

Estimated size: ~600K rows per factor (500 stocks × 1200 trading days). 100 factors ≈ 60M rows.

If using TimescaleDB, convert to hypertable partitioned by `trade_date`. Otherwise standard PostgreSQL with the index above is sufficient.

## New Module: `mining/publisher.py`

Single responsibility: persist an admitted factor to DB and generate HTML report.

```python
class FactorPublisher:
    def __init__(self, config: MiningConfig):
        self.config = config
        self._conn = None

    @staticmethod
    def ensure_tables(conn):
        """Create tables if not exist. Idempotent — safe to call on every publish."""
        with conn.cursor() as cur:
            cur.execute("CREATE TABLE IF NOT EXISTS mining_factors (...)")
            cur.execute("CREATE TABLE IF NOT EXISTS mining_factor_values (...)")
        conn.commit()

    def publish(self, factor_id: str, factor_dict: dict,
                factor_values_is: pd.DataFrame,
                factor_values_oos: pd.DataFrame,
                config: MiningConfig) -> str:
        """
        Publish an admitted factor:
        1. Write metrics to mining_factors table
        2. Write factor values (IS + OOS combined) to mining_factor_values table
        3. Generate HTML report

        Steps 1-2 run in a single DB transaction. Step 3 is non-transactional
        (failure is logged but does not rollback DB writes).

        Returns: path to HTML report
        """
        conn = self._get_connection()
        self.ensure_tables(conn)
        try:
            # Combine IS + OOS values
            combined = pd.concat([factor_values_is, factor_values_oos])
            combined = combined[~combined.index.duplicated(keep='last')]

            self._save_metrics(conn, factor_id, factor_dict, config)
            self._save_values(conn, factor_id, combined)
            conn.commit()
        except Exception:
            conn.rollback()
            raise

        # Non-transactional: HTML report
        report_path = self._generate_report(factor_id, factor_dict, combined, config)
        self._update_report_path(conn, factor_id, report_path)
        conn.commit()
        return report_path

    def _get_connection(self):
        if self._conn is None:
            import psycopg2
            self._conn = psycopg2.connect(self.config.system.database.connection_string)
        return self._conn

    def _save_metrics(self, conn, factor_id, factor_dict, config):
        """INSERT ... ON CONFLICT (factor_id) DO UPDATE SET ... (upsert)."""

    def _save_values(self, conn, factor_id, factor_values):
        """DELETE existing values for factor_id, then bulk INSERT using
        psycopg2.extras.execute_values() with page_size=5000."""

    def _generate_report(self, factor_id, factor_dict, factor_values, config):
        """Convert MultiIndex DataFrame to flat format, load price data, use FactorReportGenerator."""

    def _update_report_path(self, conn, factor_id, report_path):
        """UPDATE mining_factors SET report_path = ..."""
```

### DataFrame Format Conversion

The evaluator caches factor values as Qlib-format DataFrames: MultiIndex `(datetime, instrument)` with a single column named after the expression. The publisher and visualization modules expect flat DataFrames with columns `(time, symbol, value)`.

Conversion in the publisher:

```python
def _to_flat_df(self, qlib_df: pd.DataFrame) -> pd.DataFrame:
    """Convert Qlib MultiIndex DataFrame to flat (time, symbol, value)."""
    df = qlib_df.reset_index()
    df.columns = ['time', 'symbol', 'value']
    # Convert Qlib instrument format (SH600000) to match DB convention
    # Note: Qlib instruments already use SH600000 format (same as our DB)
    return df
```

### Price Data for Reports

`FactorReportGenerator.analyze()` expects `price_df` with columns `(time, symbol, close)`, not returns. The publisher loads price data directly from the `price_daily` table (same source the dashboard uses):

```python
def _load_price_data(self, symbols, start, end):
    """Load close prices from price_daily for report generation."""
    sql = "SELECT symbol, time, close FROM price_daily WHERE symbol = ANY(%s) AND time BETWEEN %s AND %s"
    return pd.read_sql(sql, self._get_connection(), params=[symbols, start, end])
```

### Bulk Insertion Strategy

For `_save_values()`, use `psycopg2.extras.execute_values()` with `page_size=5000` to batch-insert ~600K rows efficiently (completes in seconds, not minutes):

```python
from psycopg2.extras import execute_values
flat = self._to_flat_df(factor_values)
rows = [(factor_id, r.symbol, r.time, r.value) for _, r in flat.iterrows()]
execute_values(cur, "INSERT INTO mining_factor_values (factor_id, symbol, trade_date, value) VALUES %s", rows, page_size=5000)
```

### HTML Report Generation

Uses the existing `visualization/report.py` `FactorReportGenerator`:
- IC time series chart (train/test split)
- IC distribution
- Rolling IC comparison (20d, 60d, 120d)
- Quantile group returns
- Cumulative returns by quantile
- Long-short performance

Reports saved to `mining/reports/factor_XXX.html` (one HTML file per factor, self-contained with embedded Plotly JS).

### DB Migration

Tables are created with `CREATE TABLE IF NOT EXISTS` in `FactorPublisher.ensure_tables()`. This is called on every `publish()` — idempotent and safe. No separate migration scripts or Alembic needed.

## Modified Modules

### `mining/evaluator.py`

The evaluator already caches factor values in `self._factor_cache` during evaluation. Currently this cache is internal. Change:

- After Stage 3 validation, attach the cached factor values and returns DataFrames to the admitted factor dict:
  ```python
  c["_factor_values"] = cached_vals  # IS period
  c["_factor_values_oos"] = vals_oos  # OOS period
  c["_returns"] = returns_is
  ```
- These are transient (prefixed with `_`) and NOT saved to YAML — only used by the publisher.

### `mining/library.py`

Store the `MiningConfig` so it can be passed to the publisher:

```python
class FactorLibrary:
    def __init__(self, config: MiningConfig):
        self._config = config          # ← ADD: store config for publisher
        self._dir = Path(config.library_dir)
        # ... rest unchanged ...
```

After `admit()` saves the YAML entry, call `FactorPublisher.publish()`:

```python
def admit(self, factor: Dict[str, Any]) -> str:
    factor_id = ...  # existing logic
    # ... save YAML as before ...

    if "_factor_values" in factor:
        from .publisher import FactorPublisher
        publisher = FactorPublisher(self._config)
        publisher.publish(
            factor_id=factor_id,
            factor_dict=factor,
            factor_values_is=factor["_factor_values"],
            factor_values_oos=factor["_factor_values_oos"],
            config=self._config,
        )
    return factor_id
```

The `replace()` method follows the same pattern — the publisher uses `INSERT ... ON CONFLICT (factor_id) DO UPDATE` for the metrics table, and `DELETE + INSERT` for factor values:

```python
def replace(self, old_id: str, new_factor: Dict[str, Any]) -> str:
    # ... existing YAML logic (unchanged) ...

    if "_factor_values" in new_factor:
        from .publisher import FactorPublisher
        publisher = FactorPublisher(self._config)
        publisher.publish(
            factor_id=old_id,
            factor_dict=new_factor,
            factor_values_is=new_factor["_factor_values"],
            factor_values_oos=new_factor["_factor_values_oos"],
            config=self._config,
        )
    return old_id
```

The publisher's `_save_metrics()` uses `INSERT ... ON CONFLICT (factor_id) DO UPDATE SET ...` (upsert) so both admit and replace use the same `publish()` method. The `_save_values()` deletes existing values for the factor_id before inserting new ones.

### `data/loaders.py`

Rewrite to read from the new tables instead of hardcoded `DATABASE_FACTORS`:

```python
def get_available_factors(connection) -> List[dict]:
    """Read factor list from mining_factors table."""
    sql = "SELECT factor_id, name, expression, category, ic_mean, ic_ir, admitted_at FROM mining_factors ORDER BY admitted_at DESC"
    return pd.read_sql(sql, connection).to_dict('records')

def get_factor_data(factor_id: str, connection) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """Read factor values from mining_factor_values table."""
    sql = "SELECT symbol, trade_date AS time, value FROM mining_factor_values WHERE factor_id = %s ORDER BY trade_date, symbol"
    df = pd.read_sql(sql, connection, params=[factor_id])
    if df.empty:
        return None, f"No data for factor {factor_id}"
    return df, None
```

Remove the old `DATABASE_FACTORS` dict and all old wide-table query logic.

### `data/storage/factor_storage.py`

Archive to `_archive/data/storage/factor_storage.py`. The old `FactorConfig` SQLAlchemy model, wide tables, and narrow table infrastructure are no longer needed. The new publisher uses plain SQL via psycopg2 (consistent with the rest of the data layer).

### `dashboard/pages/Factors.py`

Rewrite to use the new data loaders:

1. **Factor list**: Read from `mining_factors` table via `get_available_factors()`
2. **Factor selector**: Dropdown shows factor name + IC + category
3. **IC Analysis**: Load factor values from `mining_factor_values`, load prices from existing `price_daily` table, compute IC using `ICAnalyzer`
4. **Report link**: Show link to the pre-generated HTML report for quick access

The page structure (IC charts, group returns, statistics) stays the same — only the data source changes.

## What Gets Deleted/Archived

| File | Action | Reason |
|------|--------|--------|
| `data/storage/factor_storage.py` | Archive to `_archive/` | Old wide-table storage, replaced by publisher |
| `data/loaders.py` `DATABASE_FACTORS` dict | Delete | Hardcoded mapping, replaced by DB query |
| `data/loaders.py` old query functions | Rewrite | Now read from new tables |

## What Does NOT Change

- `mining/evaluator.py` internal pipeline logic (stages 1-3)
- `mining/library.py` YAML storage (kept as version-controlled factor definitions)
- `mining/memory.py` experience memory
- `visualization/ic_analyzer.py`, `visualization/report.py` (used as-is by publisher)
- `core/config.py`, `mining/config.py`
- `data/storage/` other files (TimescaleDB for price data)

## Testing Strategy

- Unit test `FactorPublisher` with mock DB connection
- Unit test new `data/loaders.py` functions with mock DB
- Integration test: evaluate a factor → admit → verify DB has values + metrics → verify HTML exists
- Verify dashboard loads and displays mining factors
