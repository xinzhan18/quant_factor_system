# Factor Publish Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** When the mining evaluator admits a factor, automatically persist its values to PostgreSQL, generate an HTML report, and make it viewable in the dashboard.

**Architecture:** The evaluator attaches cached factor values to admitted factor dicts. The library's `admit()`/`replace()` methods call `FactorPublisher.publish()`, which writes metrics and values to two new DB tables (`mining_factors`, `mining_factor_values`), then generates an HTML report via the existing `FactorReportGenerator`. The dashboard and `data/loaders.py` are rewritten to read from these new tables. Old factor infrastructure (`DATABASE_FACTORS`, `factor_storage.py`) is archived.

**Tech Stack:** Python 3.9, PostgreSQL/TimescaleDB, psycopg2, pandas, plotly, streamlit

**Spec:** `docs/superpowers/specs/2026-03-22-factor-publish-pipeline-design.md`

---

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `mining/publisher.py` | **Create** | Persist admitted factor to DB + generate HTML report |
| `tests/mining/test_publisher.py` | **Create** | Unit tests for FactorPublisher |
| `mining/evaluator.py` | **Modify** (lines 311-321) | Attach cached factor values to admitted factor dicts |
| `tests/mining/test_evaluator.py` | **Modify** | Verify transient keys attached after Stage 3 |
| `mining/library.py` | **Modify** (lines 17-25, 43-65, 67-90) | Store `_config`, call publisher after admit/replace |
| `tests/mining/test_library.py` | **Modify** | Verify publisher is called on admit/replace |
| `data/loaders.py` | **Rewrite** | Read from `mining_factors`/`mining_factor_values` instead of hardcoded dict |
| `tests/data/test_loaders.py` | **Create** | Unit tests for new loader functions |
| `data/storage/factor_storage.py` | **Archive** to `_archive/` | No longer needed |
| `dashboard/pages/Factors.py` | **Rewrite** | Read from new tables, show report link |

---

### Task 1: Create `mining/publisher.py` with tests

The core new module. Single class `FactorPublisher` that handles DB persistence and report generation.

**Files:**
- Create: `mining/publisher.py`
- Create: `tests/mining/test_publisher.py`

**Reference:** Read `docs/superpowers/specs/2026-03-22-factor-publish-pipeline-design.md` sections "New Module" through "DB Migration".

**Context:**
- `MiningConfig` is in `mining/config.py`. It has `self.system` which is a `SystemConfig` (from `core/config.py`). `SystemConfig` has `self.database` which is a `DatabaseConfig` with a `connection_string` property that returns `postgresql://user:pass@host:port/db`.
- `FactorReportGenerator` is in `visualization/report.py`. Usage: `gen = FactorReportGenerator(factor_name, output_dir)`, then `gen.analyze(factor_df, price_df, split_date, n_groups=5)`, then `gen.generate_charts()`, then `gen.save_charts(format='html')`.
- `factor_df` must have columns `(time, symbol, value)`. `price_df` must have columns `(time, symbol, close)`. Both are flat DataFrames (not MultiIndex).
- The evaluator produces Qlib-format DataFrames: MultiIndex `(datetime, instrument)` with a single column named after the expression. The publisher must convert these to flat format.
- Price data table is `price_daily` with columns `(time, symbol, close, ...)`.

- [ ] **Step 1: Write test file `tests/mining/test_publisher.py`**

```python
"""Tests for FactorPublisher."""

import pytest
import numpy as np
import pandas as pd
from datetime import date, datetime
from unittest.mock import MagicMock, patch, call

from mining.publisher import FactorPublisher


@pytest.fixture
def config(tmp_path):
    """MiningConfig with mock system config."""
    from mining.config import MiningConfig
    return MiningConfig(
        library_dir=str(tmp_path / "library"),
        memory_dir=str(tmp_path / "memory"),
        candidates_dir=str(tmp_path / "candidates"),
        train_start="2023-01-01",
        train_end="2023-12-31",
        test_start="2024-01-01",
        test_end="2024-06-30",
    )


@pytest.fixture
def qlib_df_is():
    """Sample Qlib-format IS factor values: MultiIndex (datetime, instrument)."""
    dates = pd.bdate_range("2023-01-02", periods=30)
    instruments = ["SH600000", "SH600001", "SH600002"]
    idx = pd.MultiIndex.from_product([dates, instruments], names=["datetime", "instrument"])
    np.random.seed(42)
    return pd.DataFrame({"Rank($close)": np.random.randn(len(idx))}, index=idx)


@pytest.fixture
def qlib_df_oos():
    """Sample Qlib-format OOS factor values."""
    dates = pd.bdate_range("2024-01-02", periods=20)
    instruments = ["SH600000", "SH600001", "SH600002"]
    idx = pd.MultiIndex.from_product([dates, instruments], names=["datetime", "instrument"])
    np.random.seed(99)
    return pd.DataFrame({"Rank($close)": np.random.randn(len(idx))}, index=idx)


class TestToFlatDf:
    def test_converts_multiindex_to_flat(self, config, qlib_df_is):
        pub = FactorPublisher(config)
        flat = pub._to_flat_df(qlib_df_is)
        assert list(flat.columns) == ["time", "symbol", "value"]
        assert len(flat) == len(qlib_df_is)
        assert flat["symbol"].iloc[0] == "SH600000"

    def test_preserves_values(self, config, qlib_df_is):
        pub = FactorPublisher(config)
        flat = pub._to_flat_df(qlib_df_is)
        original_val = qlib_df_is.iloc[0, 0]
        assert flat["value"].iloc[0] == pytest.approx(original_val)


class TestEnsureTables:
    def test_creates_tables_idempotently(self, config):
        pub = FactorPublisher(config)
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        pub.ensure_tables(mock_conn)
        # Should execute CREATE TABLE IF NOT EXISTS for both tables
        assert mock_cursor.execute.call_count >= 2
        calls_sql = [str(c) for c in mock_cursor.execute.call_args_list]
        assert any("mining_factors" in s for s in calls_sql)
        assert any("mining_factor_values" in s for s in calls_sql)
        mock_conn.commit.assert_called_once()


class TestSaveMetrics:
    def test_upserts_factor_metrics(self, config):
        pub = FactorPublisher(config)
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        factor_dict = {
            "name": "Test_Factor",
            "expression": "Rank($close)",
            "category": "momentum",
            "stage3": {
                "ic_mean_is": 0.05,
                "ic_ir_is": 0.8,
                "ic_mean_oos": 0.04,
                "ic_ir_oos": 0.6,
                "ic_win_rate": 0.65,
                "ls_return": 0.03,
                "monotonicity": 0.9,
            },
        }
        pub._save_metrics(mock_conn, "001", factor_dict, config)
        mock_cursor.execute.assert_called_once()
        sql = mock_cursor.execute.call_args[0][0]
        assert "INSERT INTO mining_factors" in sql
        assert "ON CONFLICT" in sql


class TestSaveValues:
    def test_deletes_then_inserts(self, config, qlib_df_is):
        pub = FactorPublisher(config)
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        combined = qlib_df_is  # using IS only for simplicity
        pub._save_values(mock_conn, "001", combined)

        # First call should be DELETE
        first_sql = mock_cursor.execute.call_args_list[0][0][0]
        assert "DELETE" in first_sql
        assert "mining_factor_values" in first_sql


class TestPublishEndToEnd:
    @patch.object(FactorPublisher, '_get_connection')
    @patch.object(FactorPublisher, '_generate_report')
    def test_publish_commits_on_success(self, mock_report, mock_get_conn, config, qlib_df_is, qlib_df_oos):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_get_conn.return_value = mock_conn
        mock_report.return_value = "/reports/factor_001.html"

        pub = FactorPublisher(config)
        factor_dict = {
            "name": "Test", "expression": "Rank($close)", "category": "momentum",
            "stage3": {"ic_mean_is": 0.05, "ic_ir_is": 0.8, "ic_mean_oos": 0.04,
                       "ic_ir_oos": 0.6, "ic_win_rate": 0.65, "ls_return": 0.03, "monotonicity": 0.9},
        }
        result = pub.publish("001", factor_dict, qlib_df_is, qlib_df_oos, config)
        assert result == "/reports/factor_001.html"
        assert mock_conn.commit.call_count >= 1

    @patch.object(FactorPublisher, '_get_connection')
    def test_publish_rollbacks_on_error(self, mock_get_conn, config, qlib_df_is, qlib_df_oos):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_cursor.execute.side_effect = Exception("DB error")
        mock_get_conn.return_value = mock_conn

        pub = FactorPublisher(config)
        factor_dict = {
            "name": "Test", "expression": "Rank($close)", "category": "momentum",
            "stage3": {"ic_mean_is": 0.05, "ic_ir_is": 0.8, "ic_mean_oos": 0.04,
                       "ic_ir_oos": 0.6, "ic_win_rate": 0.65, "ls_return": 0.03, "monotonicity": 0.9},
        }
        with pytest.raises(Exception, match="DB error"):
            pub.publish("001", factor_dict, qlib_df_is, qlib_df_oos, config)
        mock_conn.rollback.assert_called_once()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/xinzhan/.openclaw/workspace/quant_factor_system && python -m pytest tests/mining/test_publisher.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'mining.publisher'`

- [ ] **Step 3: Implement `mining/publisher.py`**

```python
"""Factor publisher — persist admitted factors to DB and generate HTML reports."""

from __future__ import annotations

import logging
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

from .config import MiningConfig

logger = logging.getLogger(__name__)


class FactorPublisher:
    """Persist an admitted factor to DB and generate HTML report."""

    def __init__(self, config: MiningConfig):
        self.config = config
        self._conn = None

    @staticmethod
    def ensure_tables(conn) -> None:
        """Create tables if they don't exist. Idempotent."""
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS mining_factors (
                    factor_id    VARCHAR(10) PRIMARY KEY,
                    name         VARCHAR(200) NOT NULL,
                    expression   TEXT NOT NULL,
                    category     VARCHAR(50),
                    ic_mean      FLOAT,
                    ic_ir        FLOAT,
                    ic_mean_is   FLOAT,
                    ic_mean_oos  FLOAT,
                    ic_win_rate  FLOAT,
                    ls_return    FLOAT,
                    monotonicity FLOAT,
                    train_start  DATE,
                    train_end    DATE,
                    test_start   DATE,
                    test_end     DATE,
                    admitted_at  DATE NOT NULL,
                    report_path  VARCHAR(500)
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS mining_factor_values (
                    factor_id   VARCHAR(10) NOT NULL,
                    symbol      VARCHAR(20) NOT NULL,
                    trade_date  DATE NOT NULL,
                    value       DOUBLE PRECISION,
                    PRIMARY KEY (factor_id, symbol, trade_date)
                )
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_mfv_factor_date
                ON mining_factor_values (factor_id, trade_date)
            """)
        conn.commit()

    def publish(
        self,
        factor_id: str,
        factor_dict: dict,
        factor_values_is: pd.DataFrame,
        factor_values_oos: pd.DataFrame,
        config: MiningConfig,
    ) -> str:
        """
        Publish an admitted factor.

        1. Write metrics to mining_factors (upsert)
        2. Write factor values (IS + OOS combined) to mining_factor_values
        3. Generate HTML report (non-transactional)

        Returns: path to HTML report.
        """
        conn = self._get_connection()
        self.ensure_tables(conn)

        try:
            combined = pd.concat([factor_values_is, factor_values_oos])
            combined = combined[~combined.index.duplicated(keep="last")]

            self._save_metrics(conn, factor_id, factor_dict, config)
            self._save_values(conn, factor_id, combined)
            conn.commit()
        except Exception:
            conn.rollback()
            raise

        # Non-transactional: HTML report
        try:
            report_path = self._generate_report(factor_id, factor_dict, combined, config)
            self._update_report_path(conn, factor_id, report_path)
            conn.commit()
        except Exception as e:
            logger.warning("Report generation failed for factor %s: %s", factor_id, e)
            report_path = ""

        return report_path

    def _get_connection(self):
        if self._conn is None:
            import psycopg2
            self._conn = psycopg2.connect(self.config.system.database.connection_string)
        return self._conn

    def _to_flat_df(self, qlib_df: pd.DataFrame) -> pd.DataFrame:
        """Convert Qlib MultiIndex DataFrame to flat (time, symbol, value)."""
        df = qlib_df.reset_index()
        df.columns = ["time", "symbol", "value"]
        return df

    def _save_metrics(self, conn, factor_id: str, factor_dict: dict, config: MiningConfig) -> None:
        """Upsert factor metrics into mining_factors."""
        s3 = factor_dict.get("stage3", {})
        # Compute full-sample IC as average of IS and OOS
        ic_is = s3.get("ic_mean_is")
        ic_oos = s3.get("ic_mean_oos")
        ic_mean = None
        if ic_is is not None and ic_oos is not None:
            ic_mean = (ic_is + ic_oos) / 2
        elif ic_is is not None:
            ic_mean = ic_is

        test_end = config.test_end or str(date.today())

        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO mining_factors (
                    factor_id, name, expression, category,
                    ic_mean, ic_ir, ic_mean_is, ic_mean_oos,
                    ic_win_rate, ls_return, monotonicity,
                    train_start, train_end, test_start, test_end,
                    admitted_at
                ) VALUES (
                    %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s, %s,
                    %s
                )
                ON CONFLICT (factor_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    expression = EXCLUDED.expression,
                    category = EXCLUDED.category,
                    ic_mean = EXCLUDED.ic_mean,
                    ic_ir = EXCLUDED.ic_ir,
                    ic_mean_is = EXCLUDED.ic_mean_is,
                    ic_mean_oos = EXCLUDED.ic_mean_oos,
                    ic_win_rate = EXCLUDED.ic_win_rate,
                    ls_return = EXCLUDED.ls_return,
                    monotonicity = EXCLUDED.monotonicity,
                    train_start = EXCLUDED.train_start,
                    train_end = EXCLUDED.train_end,
                    test_start = EXCLUDED.test_start,
                    test_end = EXCLUDED.test_end,
                    admitted_at = EXCLUDED.admitted_at
            """, (
                factor_id,
                factor_dict.get("name", f"factor_{factor_id}"),
                factor_dict.get("expression", ""),
                factor_dict.get("category", "other"),
                ic_mean,
                s3.get("ic_ir_is"),
                s3.get("ic_mean_is"),
                s3.get("ic_mean_oos"),
                s3.get("ic_win_rate"),
                s3.get("ls_return"),
                s3.get("monotonicity"),
                config.train_start,
                config.train_end,
                config.test_start,
                test_end,
                date.today(),
            ))

    def _save_values(self, conn, factor_id: str, factor_values: pd.DataFrame) -> None:
        """Delete existing values for factor_id, then bulk insert new values."""
        from psycopg2.extras import execute_values

        flat = self._to_flat_df(factor_values)

        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM mining_factor_values WHERE factor_id = %s",
                (factor_id,),
            )
            rows = [
                (factor_id, row.symbol, row.time, row.value)
                for row in flat.itertuples(index=False)
            ]
            if rows:
                execute_values(
                    cur,
                    "INSERT INTO mining_factor_values (factor_id, symbol, trade_date, value) VALUES %s",
                    rows,
                    page_size=5000,
                )

    def _generate_report(
        self, factor_id: str, factor_dict: dict, factor_values: pd.DataFrame, config: MiningConfig
    ) -> str:
        """Generate HTML report using FactorReportGenerator."""
        from visualization.report import FactorReportGenerator

        reports_dir = Path("mining/reports")
        reports_dir.mkdir(parents=True, exist_ok=True)

        factor_name = factor_dict.get("name", f"factor_{factor_id}")
        gen = FactorReportGenerator(factor_name=factor_name, output_dir=str(reports_dir))

        flat = self._to_flat_df(factor_values)
        price_df = self._load_price_data(flat, config)

        split_date = datetime.strptime(config.train_end, "%Y-%m-%d")
        gen.analyze(flat, price_df, split_date=split_date, n_groups=5)
        gen.generate_charts()
        saved = gen.save_charts(format="html")

        # Return first saved chart path as the report path
        if saved:
            return list(saved.values())[0]
        return ""

    def _load_price_data(self, flat_factor_df: pd.DataFrame, config: MiningConfig) -> pd.DataFrame:
        """Load close prices from price_daily for report generation."""
        symbols = flat_factor_df["symbol"].unique().tolist()
        start = flat_factor_df["time"].min()
        end = flat_factor_df["time"].max()

        sql = "SELECT symbol, time, close FROM price_daily WHERE symbol = ANY(%s) AND time BETWEEN %s AND %s"
        return pd.read_sql(sql, self._get_connection(), params=[symbols, start, end])

    def _update_report_path(self, conn, factor_id: str, report_path: str) -> None:
        """Update the report_path column for a factor."""
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE mining_factors SET report_path = %s WHERE factor_id = %s",
                (report_path, factor_id),
            )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/xinzhan/.openclaw/workspace/quant_factor_system && python -m pytest tests/mining/test_publisher.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add mining/publisher.py tests/mining/test_publisher.py
git commit -m "feat(mining): add FactorPublisher for DB persistence and HTML reports"
```

---

### Task 2: Modify `mining/evaluator.py` to attach factor values

After Stage 3 validation succeeds, attach the cached factor values and OOS values to the admitted factor dict so the publisher can access them.

**Files:**
- Modify: `mining/evaluator.py:311-321`
- Modify: `tests/mining/test_evaluator.py`

**Context:**
- In `_full_validation()` (line 275), `cached_vals` is the IS-period factor values (Qlib MultiIndex DataFrame), `vals_oos` is the OOS-period values (line 294).
- These are local variables. We need to attach them to `c` (the candidate dict) before `validated.append(c)` at line 321.
- Keys are prefixed with `_` to indicate they are transient and should NOT be saved to YAML.

- [ ] **Step 1: Write a test that verifies transient keys are attached**

Add to `tests/mining/test_evaluator.py`:

```python
class TestTransientKeys:
    """Verify _factor_values, _factor_values_oos are attached after Stage 3."""

    def test_admitted_factors_have_transient_values(self, config, sample_factor_values, sample_returns):
        """After full_validation, admitted factors should have _factor_values and _factor_values_oos."""
        from mining.evaluator import FactorMiningEvaluator

        evaluator = FactorMiningEvaluator.__new__(FactorMiningEvaluator)
        evaluator.config = config
        evaluator._factor_cache = {"Rank($close)": sample_factor_values}
        evaluator._subset_factor_cache = {}

        # Mock Qlib calls
        with patch.object(evaluator, '_get_full_universe', return_value=["SH600000"]):
            with patch.object(evaluator, '_get_returns_qlib', return_value=sample_returns):
                with patch.object(evaluator, '_compute_factor_qlib', return_value=sample_factor_values):
                    candidates = [{"name": "Test", "expression": "Rank($close)", "category": "momentum"}]
                    validated, errors = evaluator._full_validation(candidates)

        assert len(validated) == 1
        c = validated[0]
        assert "_factor_values" in c
        assert "_factor_values_oos" in c
        assert isinstance(c["_factor_values"], pd.DataFrame)
        assert isinstance(c["_factor_values_oos"], pd.DataFrame)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/xinzhan/.openclaw/workspace/quant_factor_system && python -m pytest tests/mining/test_evaluator.py::TestTransientKeys -v`
Expected: FAIL — `_factor_values` not in dict

- [ ] **Step 3: Add transient keys to `_full_validation()` in `mining/evaluator.py`**

After line 320 (`validated.append(c)`), insert before the append:

```python
                # Attach transient values for publisher (not saved to YAML)
                c["_factor_values"] = cached_vals
                c["_factor_values_oos"] = vals_oos
```

The change goes at line 320, just before `validated.append(c)`. The final block should be:

```python
                c["stage3"] = {
                    "ic_mean_is": ic_is.get("ic_mean"),
                    "ic_ir_is": ic_is.get("ic_ir"),
                    "ic_mean_oos": ic_oos.get("ic_mean"),
                    "ic_ir_oos": ic_oos.get("ic_ir"),
                    "ic_win_rate": ic_is.get("ic_win_rate"),
                    "quantile_returns": quantile_ret,
                    "ls_return": ls_return,
                    "monotonicity": monotonicity,
                }
                # Attach transient values for publisher (not saved to YAML)
                c["_factor_values"] = cached_vals
                c["_factor_values_oos"] = vals_oos
                validated.append(c)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/xinzhan/.openclaw/workspace/quant_factor_system && python -m pytest tests/mining/test_evaluator.py::TestTransientKeys -v`
Expected: PASS

- [ ] **Step 5: Run all evaluator tests**

Run: `cd /Users/xinzhan/.openclaw/workspace/quant_factor_system && python -m pytest tests/mining/test_evaluator.py -v`
Expected: All PASS

- [ ] **Step 6: Commit**

```bash
git add mining/evaluator.py tests/mining/test_evaluator.py
git commit -m "feat(mining): attach transient factor values to admitted factors for publisher"
```

---

### Task 3: Modify `mining/library.py` to store config and call publisher

Add `self._config` to `FactorLibrary.__init__()` and call `FactorPublisher.publish()` after `admit()` and `replace()` save YAML.

**Files:**
- Modify: `mining/library.py:17-25, 43-65, 67-90`
- Modify: `tests/mining/test_library.py`

**Context:**
- `FactorLibrary.__init__` currently stores `self._dir` and `self._factors_dir` from `config`. We add `self._config = config`.
- The publisher call should be guarded by `if "_factor_values" in factor:` — factors admitted without transient values (e.g., manual library loads) skip publishing.
- The publisher is imported lazily inside the method to avoid circular imports.
- Existing tests must still pass — they don't supply `_factor_values` so publisher should NOT be called.

- [ ] **Step 1: Write tests for publisher integration**

Add to `tests/mining/test_library.py`:

```python
from unittest.mock import patch, MagicMock


class TestPublisherIntegration:
    def test_admit_calls_publisher_when_values_present(self, library):
        with patch("mining.library.FactorPublisher") as MockPub:
            mock_instance = MockPub.return_value
            mock_instance.publish.return_value = "/reports/factor_001.html"

            factor = {
                "name": "Test", "expression": "Rank($close)", "category": "momentum",
                "batch": "b1", "metrics": {"ic_mean": 0.05},
                "stage3": {"ic_mean_is": 0.05, "ic_ir_is": 0.8, "ic_mean_oos": 0.04,
                           "ic_ir_oos": 0.6, "ic_win_rate": 0.65, "ls_return": 0.03, "monotonicity": 0.9},
                "_factor_values": MagicMock(),  # Qlib DataFrame
                "_factor_values_oos": MagicMock(),
            }
            factor_id = library.admit(factor)
            assert factor_id == "001"
            mock_instance.publish.assert_called_once()

    def test_admit_skips_publisher_when_no_values(self, library):
        with patch("mining.library.FactorPublisher") as MockPub:
            factor = {
                "name": "Test", "expression": "Rank($close)", "category": "momentum",
                "batch": "b1", "metrics": {"ic_mean": 0.05},
            }
            library.admit(factor)
            MockPub.assert_not_called()

    def test_replace_calls_publisher_when_values_present(self, library):
        # First admit without values
        library.admit({
            "name": "Old", "expression": "Rank($close)", "category": "momentum",
            "batch": "b1", "metrics": {"ic_mean": 0.04},
        })
        with patch("mining.library.FactorPublisher") as MockPub:
            mock_instance = MockPub.return_value
            mock_instance.publish.return_value = "/reports/factor_001.html"

            new_factor = {
                "name": "Better", "expression": "Rank(Div($close, $vwap))",
                "category": "momentum", "batch": "b2", "metrics": {"ic_mean": 0.07},
                "stage3": {"ic_mean_is": 0.07, "ic_ir_is": 1.0, "ic_mean_oos": 0.05,
                           "ic_ir_oos": 0.7, "ic_win_rate": 0.7, "ls_return": 0.04, "monotonicity": 0.95},
                "_factor_values": MagicMock(),
                "_factor_values_oos": MagicMock(),
            }
            library.replace("001", new_factor)
            mock_instance.publish.assert_called_once()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/xinzhan/.openclaw/workspace/quant_factor_system && python -m pytest tests/mining/test_library.py::TestPublisherIntegration -v`
Expected: FAIL — publisher never called

- [ ] **Step 3: Modify `mining/library.py`**

Changes:
1. Add `self._config = config` to `__init__`
2. Add publisher call at end of `admit()`
3. Add publisher call at end of `replace()`

In `__init__` (line 20), add `self._config = config` as first line:

```python
    def __init__(self, config: MiningConfig):
        self._config = config
        self._dir = Path(config.library_dir)
        self._factors_dir = self._dir / "factors"
        self._factors_dir.mkdir(parents=True, exist_ok=True)
        self._index_path = self._dir / "library.yaml"
```

At end of `admit()` (after line 64 `logger.info(...)`, before `return factor_id`), add:

```python
        # Publish to DB if transient values are present
        if "_factor_values" in factor:
            try:
                from .publisher import FactorPublisher
                publisher = FactorPublisher(self._config)
                publisher.publish(
                    factor_id=factor_id,
                    factor_dict=factor,
                    factor_values_is=factor["_factor_values"],
                    factor_values_oos=factor["_factor_values_oos"],
                    config=self._config,
                )
            except Exception as e:
                logger.warning("Failed to publish factor %s: %s", factor_id, e)
```

At end of `replace()` (after line 89 `logger.info(...)`, before `return old_id`), add:

```python
        # Publish to DB if transient values are present
        if "_factor_values" in new_factor:
            try:
                from .publisher import FactorPublisher
                publisher = FactorPublisher(self._config)
                publisher.publish(
                    factor_id=old_id,
                    factor_dict=new_factor,
                    factor_values_is=new_factor["_factor_values"],
                    factor_values_oos=new_factor["_factor_values_oos"],
                    config=self._config,
                )
            except Exception as e:
                logger.warning("Failed to publish factor %s: %s", old_id, e)
```

- [ ] **Step 4: Run all library tests**

Run: `cd /Users/xinzhan/.openclaw/workspace/quant_factor_system && python -m pytest tests/mining/test_library.py -v`
Expected: All PASS (existing tests still work because they don't supply `_factor_values`)

- [ ] **Step 5: Commit**

```bash
git add mining/library.py tests/mining/test_library.py
git commit -m "feat(mining): library calls publisher on admit/replace when values present"
```

---

### Task 4: Rewrite `data/loaders.py` for new tables

Replace the hardcoded `DATABASE_FACTORS` dict and old query functions with functions that read from `mining_factors` and `mining_factor_values` tables.

**Files:**
- Modify: `data/loaders.py`
- Create: `tests/data/test_loaders.py`

**Context:**
- Keep `get_price_data()` and `get_database_tables()` and `_validate_identifier()` unchanged — they work with `price_daily` and are still needed.
- Replace `DATABASE_FACTORS`, `get_factor_data()`, `get_available_factors()`, `get_factor_overview()` with new implementations.
- New `get_available_factors(connection)` returns list of dicts from `mining_factors` table.
- New `get_factor_data(factor_id, connection)` returns flat DataFrame from `mining_factor_values`.
- Dashboard currently calls `get_available_factors()` (no args) and `get_factor_data(factor_name, conn)`. We change signatures.

- [ ] **Step 1: Write tests for new loader functions**

```python
"""Tests for data/loaders.py — mining factor loading."""

import pytest
import pandas as pd
from unittest.mock import MagicMock, patch


class TestGetAvailableFactors:
    def test_returns_factor_list(self):
        from data.loaders import get_available_factors

        mock_conn = MagicMock()
        mock_df = pd.DataFrame([
            {"factor_id": "001", "name": "VWAP_Dev", "expression": "Rank($close)",
             "category": "vwap", "ic_mean": 0.05, "ic_ir": 0.8, "admitted_at": "2026-03-22"},
        ])
        with patch("data.loaders.pd.read_sql", return_value=mock_df):
            result = get_available_factors(mock_conn)
        assert len(result) == 1
        assert result[0]["factor_id"] == "001"
        assert result[0]["name"] == "VWAP_Dev"

    def test_returns_empty_list(self):
        from data.loaders import get_available_factors

        mock_conn = MagicMock()
        with patch("data.loaders.pd.read_sql", return_value=pd.DataFrame()):
            result = get_available_factors(mock_conn)
        assert result == []


class TestGetFactorData:
    def test_returns_dataframe(self):
        from data.loaders import get_factor_data

        mock_conn = MagicMock()
        mock_df = pd.DataFrame({
            "symbol": ["SH600000", "SH600001"],
            "time": pd.to_datetime(["2024-01-02", "2024-01-02"]),
            "value": [1.5, -0.3],
        })
        with patch("data.loaders.pd.read_sql", return_value=mock_df):
            df, err = get_factor_data("001", mock_conn)
        assert err is None
        assert len(df) == 2
        assert list(df.columns) == ["symbol", "time", "value"]

    def test_returns_none_for_empty(self):
        from data.loaders import get_factor_data

        mock_conn = MagicMock()
        with patch("data.loaders.pd.read_sql", return_value=pd.DataFrame()):
            df, err = get_factor_data("999", mock_conn)
        assert df is None
        assert "No data" in err
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/xinzhan/.openclaw/workspace/quant_factor_system && python -m pytest tests/data/test_loaders.py -v`
Expected: FAIL — old `get_available_factors()` takes no `connection` arg / old `get_factor_data()` takes `factor_name`

- [ ] **Step 3: Rewrite `data/loaders.py`**

Replace the full file content with:

```python
"""
数据加载模块 — 从 mining DB 表加载因子和价格数据
Data Loaders Module

职责：
- 从 mining_factors / mining_factor_values 表加载因子数据
- 从 price_daily 表加载价格数据
- 被 Dashboard 页面调用
"""

import re
import pandas as pd
from typing import List, Tuple, Optional


def _validate_identifier(name: str) -> str:
    """验证SQL标识符（表名/列名）是否安全"""
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name):
        raise ValueError(f"不安全的SQL标识符: {name}")
    return name


def get_available_factors(connection) -> List[dict]:
    """Read factor list from mining_factors table."""
    sql = """
        SELECT factor_id, name, expression, category, ic_mean, ic_ir, admitted_at
        FROM mining_factors
        ORDER BY admitted_at DESC
    """
    df = pd.read_sql(sql, connection)
    if df.empty:
        return []
    return df.to_dict("records")


def get_factor_data(
    factor_id: str,
    connection,
) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """Read factor values from mining_factor_values table."""
    sql = """
        SELECT symbol, trade_date AS time, value
        FROM mining_factor_values
        WHERE factor_id = %s
        ORDER BY trade_date, symbol
    """
    try:
        df = pd.read_sql(sql, connection, params=[factor_id])
        if df.empty:
            return None, f"No data for factor {factor_id}"
        return df, None
    except Exception as e:
        return None, str(e)


def get_factor_metrics(factor_id: str, connection) -> Optional[dict]:
    """Read full metrics for a single factor."""
    sql = "SELECT * FROM mining_factors WHERE factor_id = %s"
    df = pd.read_sql(sql, connection, params=[factor_id])
    if df.empty:
        return None
    return df.iloc[0].to_dict()


def get_price_data(
    symbols: List[str],
    start_date: str,
    end_date: str,
    connection,
    table_name: str = 'price_daily'
) -> Optional[pd.DataFrame]:
    """从数据库获取价格数据"""
    try:
        if not symbols:
            return None
        cursor = connection.cursor()
        _validate_identifier(table_name)
        placeholders = ','.join(['%s'] * len(symbols))
        cursor.execute(f"""
            SELECT time, symbol, close
            FROM {table_name}
            WHERE symbol IN ({placeholders})
            AND time >= %s AND time <= %s
            ORDER BY symbol, time
        """, symbols + [start_date, end_date])
        cols = ['time', 'symbol', 'close']
        rows = cursor.fetchall()
        if not rows:
            return None
        return pd.DataFrame(rows, columns=cols)
    except Exception:
        return None


def get_database_tables(connection) -> List[str]:
    """获取数据库中所有表"""
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name NOT LIKE 'pg_%%'
            AND table_name NOT LIKE 'sql_%%'
            ORDER BY table_name
        """)
        return [row[0] for row in cursor.fetchall()]
    except Exception:
        return []


__all__ = [
    'get_available_factors',
    'get_factor_data',
    'get_factor_metrics',
    'get_price_data',
    'get_database_tables',
]
```

- [ ] **Step 4: Run tests**

Run: `cd /Users/xinzhan/.openclaw/workspace/quant_factor_system && python -m pytest tests/data/test_loaders.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add data/loaders.py tests/data/test_loaders.py
git commit -m "refactor(data): rewrite loaders to read from mining DB tables"
```

---

### Task 5: Archive `data/storage/factor_storage.py`

Move the old factor storage module to the archive.

**Files:**
- Move: `data/storage/factor_storage.py` → `_archive/data/storage/factor_storage.py`

**Context:**
- Check that nothing imports `factor_storage` before archiving (except `_archive/`).

- [ ] **Step 1: Search for imports of factor_storage**

Run: `cd /Users/xinzhan/.openclaw/workspace/quant_factor_system && grep -r "factor_storage" --include="*.py" -l | grep -v _archive | grep -v __pycache__`

If any files import it (other than `_archive/`), note them — they need updating first.

- [ ] **Step 2: Archive the file**

```bash
mkdir -p _archive/data/storage
mv data/storage/factor_storage.py _archive/data/storage/factor_storage.py
```

- [ ] **Step 3: Update `data/storage/__init__.py` to remove FactorStorage import**

Remove the `from .factor_storage import (FactorStorage,)` block (lines 23-25) and remove `'FactorStorage'` from `__all__` (line 53).

- [ ] **Step 4: Commit**

```bash
git add data/storage/factor_storage.py data/storage/__init__.py _archive/data/storage/factor_storage.py
git commit -m "refactor(data): archive old factor_storage.py (replaced by mining/publisher.py)"
```

---

### Task 6: Rewrite `dashboard/pages/Factors.py`

Rewrite the dashboard to load factors from the new `mining_factors`/`mining_factor_values` tables.

**Files:**
- Rewrite: `dashboard/pages/Factors.py`

**Context:**
- Uses Streamlit (`import streamlit as st`).
- The old page calls `get_available_factors()` (no args, returns list of names from `DATABASE_FACTORS`).
- The new page calls `get_available_factors(connection)` which returns list of dicts with `factor_id`, `name`, `expression`, `category`, `ic_mean`, `ic_ir`, `admitted_at`.
- The old page calls `get_factor_data(factor_name, conn)` — new calls `get_factor_data(factor_id, conn)`.
- Keep the same visual structure: sidebar selector, IC analysis, group returns, rolling IC.
- Add link to pre-generated HTML report if `report_path` exists.
- Use `ICAnalyzer` and the chart generation functions from the old page.
- Connect to DB using `TimescaleDB` from `quant_factor_system.data`.

- [ ] **Step 1: Rewrite `dashboard/pages/Factors.py`**

```python
"""
因子评估页面 — 从 mining DB 表加载因子
Factor Evaluation Page — reads from mining_factors / mining_factor_values tables
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime as dt

from quant_factor_system.data import TimescaleDB
from quant_factor_system.data.loaders import (
    get_available_factors,
    get_factor_data,
    get_factor_metrics,
    get_price_data,
)
from quant_factor_system.visualization import ICAnalyzer


def generate_ic_chart(rolling_ic_df: pd.DataFrame, split_date: dt, factor_name: str) -> go.Figure:
    """生成IC时间序列图"""
    fig = px.line(
        rolling_ic_df,
        x='date',
        y='IC',
        color='period' if 'period' in rolling_ic_df.columns else None,
        title=f"{factor_name} 滚动IC (60日)",
        color_discrete_map={'训练集': 'green', '测试集': 'red'}
    )
    if split_date:
        split_str = split_date.strftime('%Y-%m-%d')
        fig.add_shape(
            type="line", x0=split_str, x1=split_str, y0=0, y1=1,
            xref="x", yref="paper",
            line=dict(dash="dash", color="gray", width=2)
        )
        fig.add_annotation(
            x=split_str, y=1, xref="x", yref="paper",
            text="训练/测试分界", showarrow=False, yshift=10
        )
    fig.add_hline(y=0, line_dash="dot", line_color="black")
    fig.add_hline(y=0.02, line_dash="dot", line_color="blue", annotation_text="IC=0.02")
    fig.add_hline(y=-0.02, line_dash="dot", line_color="blue", annotation_text="IC=-0.02")
    fig.update_layout(template='plotly_white', height=400)
    return fig


def generate_group_returns_chart(cumulative_returns: pd.DataFrame, factor_name: str) -> go.Figure:
    """生成分组累计收益图"""
    fig = px.line(
        cumulative_returns,
        title=f"{factor_name} 各分组累计收益曲线",
        labels={'value': '累计收益', 'time': '日期', 'group': '分组'}
    )
    fig.update_layout(template='plotly_white', height=400)
    return fig


def generate_long_short_chart(cumulative_returns: pd.DataFrame) -> go.Figure:
    """生成多空组合图"""
    q5_col = [c for c in cumulative_returns.columns if 'Q5' in str(c)]
    q1_col = [c for c in cumulative_returns.columns if 'Q1' in str(c)]
    if not q5_col or not q1_col:
        return None
    long_short = cumulative_returns[q5_col[0]] - cumulative_returns[q1_col[0]]
    fig = px.line(long_short, title="多空组合累计收益 (Q5-Q1)")
    fig.add_hline(y=0, line_dash="dot", line_color="black")
    fig.update_layout(template='plotly_white', height=350)
    return fig


def generate_group_bar_chart(mean_returns: pd.Series) -> go.Figure:
    """生成分组年化收益柱状图"""
    fig = px.bar(
        x=mean_returns.index, y=mean_returns.values * 100,
        title="各分组年化收益率",
        labels={'x': '分组', 'y': '年化收益率 (%)'},
        color=mean_returns.values,
        color_continuous_scale='RdYlGn'
    )
    fig.add_hline(y=0, line_dash="dot", line_color="black")
    fig.update_layout(template='plotly_white', height=350)
    return fig


def generate_multi_rolling_ic_chart(daily_ic: pd.DataFrame) -> go.Figure:
    """生成多窗口滚动IC图"""
    windows = [20, 60, 120]
    rolling_data = {}
    for w in windows:
        rolling_data[f'IC_{w}d'] = daily_ic['IC'].rolling(window=w, min_periods=10).mean()
    df = pd.DataFrame(rolling_data).dropna()
    if df.empty:
        return None
    fig = px.line(df, title="不同窗口滚动IC对比")
    fig.add_hline(y=0, line_dash="dot", line_color="black")
    fig.add_hline(y=0.02, line_dash="dot", line_color="blue", annotation_text="IC=0.02")
    fig.add_hline(y=-0.02, line_dash="dot", line_color="blue", annotation_text="IC=-0.02")
    fig.update_layout(template='plotly_white', height=400)
    return fig


def compute_group_returns(merged: pd.DataFrame) -> dict:
    """计算分组收益"""
    merged = merged.dropna(subset=['value', 'future_return'])
    merged['group'] = pd.qcut(merged['value'], q=5, labels=['Q1(低)', 'Q2', 'Q3', 'Q4', 'Q5(高)'])
    group_returns = merged.groupby(['time', 'group'])['future_return'].mean().reset_index()
    group_returns_pivot = group_returns.pivot(index='time', columns='group', values='future_return')
    cumulative_returns = (1 + group_returns_pivot).cumprod() - 1
    mean_returns = group_returns_pivot.mean() * 252
    stats = group_returns_pivot.std() * (252 ** 0.5)
    sharpe = mean_returns / stats
    return {
        'group_returns_pivot': group_returns_pivot,
        'cumulative_returns': cumulative_returns,
        'mean_returns': mean_returns,
        'sharpe': sharpe,
        'std': stats,
    }


def main():
    st.set_page_config(page_title="因子评估 - QuantFactor", page_icon="📈", layout="wide")
    st.title("📈 因子评估")

    db = TimescaleDB()
    conn = db.connection

    # ==================== 侧边栏 ====================
    with st.sidebar:
        st.header("⚙️ 因子设置")

        factors = get_available_factors(conn)
        if not factors:
            st.warning("数据库中尚无已入库的因子。请先运行因子挖掘流程。")
            return

        # Build selector options
        factor_options = {
            f"{f['factor_id']}: {f['name']} (IC={f.get('ic_mean', 0):.4f})" if f.get('ic_mean') else f"{f['factor_id']}: {f['name']}": f
            for f in factors
        }
        selected_label = st.selectbox("选择因子", options=list(factor_options.keys()))
        selected = factor_options[selected_label]

        factor_id = selected["factor_id"]
        factor_name = selected["name"]

        # Load factor values
        with st.spinner('正在加载因子数据...'):
            factor_df, error = get_factor_data(factor_id, conn)

        if error:
            st.warning(f"⚠️ {error}")
            return

        if factor_df is None or factor_df.empty:
            st.warning("无数据")
            return

        # Load metrics
        metrics = get_factor_metrics(factor_id, conn)

        # Factor info
        st.success(f"✅ {factor_name}")
        if metrics:
            st.caption(f"表达式: `{metrics.get('expression', '')}`")
            st.caption(f"类别: {metrics.get('category', '')} | 入库: {metrics.get('admitted_at', '')}")

            # Report link
            report_path = metrics.get("report_path")
            if report_path:
                st.markdown(f"[📄 查看HTML报告]({report_path})")

    # ==================== 数据范围 ====================
    min_date = factor_df['time'].min()
    max_date = factor_df['time'].max()

    # Use train/test split from metrics if available
    if metrics and metrics.get('train_end'):
        split_date = pd.to_datetime(metrics['train_end'])
    else:
        split_date = min_date + (max_date - min_date) / 2

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("数据条数", f"{len(factor_df):,}")
    with col2:
        st.metric("股票数", f"{factor_df['symbol'].nunique():,}")
    with col3:
        st.metric("开始日期", min_date.strftime('%Y-%m-%d') if hasattr(min_date, 'strftime') else str(min_date))
    with col4:
        st.metric("结束日期", max_date.strftime('%Y-%m-%d') if hasattr(max_date, 'strftime') else str(max_date))

    # ==================== 指标概览 ====================
    if metrics:
        st.subheader("📊 评估指标概览")
        m1, m2, m3, m4, m5 = st.columns(5)
        with m1:
            st.metric("IC (IS)", f"{metrics.get('ic_mean_is', 0):.4f}" if metrics.get('ic_mean_is') else "N/A")
        with m2:
            st.metric("IC (OOS)", f"{metrics.get('ic_mean_oos', 0):.4f}" if metrics.get('ic_mean_oos') else "N/A")
        with m3:
            st.metric("IC IR", f"{metrics.get('ic_ir', 0):.2f}" if metrics.get('ic_ir') else "N/A")
        with m4:
            st.metric("多空收益", f"{metrics.get('ls_return', 0):.4f}" if metrics.get('ls_return') else "N/A")
        with m5:
            st.metric("单调性", f"{metrics.get('monotonicity', 0):.2f}" if metrics.get('monotonicity') else "N/A")

    # ==================== IC 分析 ====================
    st.subheader("📈 IC分析 (信息系数)")

    symbols = factor_df['symbol'].unique().tolist()
    with st.spinner('正在获取价格数据...'):
        price_df = get_price_data(
            symbols,
            min_date.strftime('%Y-%m-%d') if hasattr(min_date, 'strftime') else str(min_date),
            max_date.strftime('%Y-%m-%d') if hasattr(max_date, 'strftime') else str(max_date),
            conn
        )

    if price_df is not None and not price_df.empty:
        analyzer = ICAnalyzer(factor_name)
        with st.spinner('正在计算IC...'):
            ic_result = analyzer.compute_ic(factor_df, price_df, split_date)

        if 'error' not in ic_result:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("整体IC", f"{ic_result.get('ic_all', 0):.4f}")
            with col2:
                st.metric("🟢 训练集IC", f"{ic_result.get('ic_train', 0):.4f}")
            with col3:
                st.metric("🔴 测试集IC", f"{ic_result.get('ic_test', 0):.4f}")

            # IC 时间序列
            if 'rolling_ic' in ic_result:
                rolling_ic = ic_result['rolling_ic'].copy()
                if 'period' in rolling_ic.columns:
                    rolling_ic['period'] = rolling_ic['period'].map({'train': '训练集', 'test': '测试集'})

                st.write("### 📉 IC时间序列")
                fig_ic = generate_ic_chart(rolling_ic, split_date, factor_name)
                st.plotly_chart(fig_ic, use_container_width=True)

                # IC 分布
                st.write("### 📊 IC分布")
                col1, col2 = st.columns(2)
                with col1:
                    fig_ic_hist = px.histogram(
                        rolling_ic, x='IC', nbins=30,
                        color='period' if 'period' in rolling_ic.columns else None,
                        color_discrete_map={'训练集': 'green', '测试集': 'red'},
                        title="IC分布直方图", marginal='box'
                    )
                    fig_ic_hist.add_vline(x=0, line_dash="dot", line_color="black")
                    fig_ic_hist.update_layout(template='plotly_white', height=400)
                    st.plotly_chart(fig_ic_hist, use_container_width=True)
                with col2:
                    ic_stats = rolling_ic.groupby('period')['IC'].agg(['mean', 'std', 'min', 'max', 'median']) if 'period' in rolling_ic.columns else rolling_ic['IC'].agg(['mean', 'std', 'min', 'max', 'median']).to_frame().T
                    st.write("**IC统计指标:**")
                    st.dataframe(ic_stats.style.format("{:.4f}"), use_container_width=True)

                # 多窗口滚动IC
                st.write("### 📈 滚动IC对比")
                daily_ic = rolling_ic[['date', 'IC']].copy()
                fig_multi = generate_multi_rolling_ic_chart(daily_ic)
                if fig_multi:
                    st.plotly_chart(fig_multi, use_container_width=True)
        else:
            st.warning(f"IC计算失败: {ic_result.get('error')}")

        # ==================== 分组收益 ====================
        st.subheader("🎯 因子分组收益分析")
        merged = pd.merge(factor_df, price_df, on=['time', 'symbol'], how='inner')
        merged = merged.sort_values(['symbol', 'time'])
        merged['future_return'] = merged.groupby('symbol')['close'].pct_change().shift(-1)
        merged = merged.dropna(subset=['value', 'future_return'])
        merged = merged[merged['future_return'].abs() < 0.11]

        if len(merged) > 100:
            with st.spinner('正在计算分组收益...'):
                group_result = compute_group_returns(merged)

            st.write("### 📊 各分组年化收益率")
            fig_bar = generate_group_bar_chart(group_result['mean_returns'])
            st.plotly_chart(fig_bar, use_container_width=True)

            st.write("### 📈 各分组累计收益曲线")
            fig_cum = generate_group_returns_chart(group_result['cumulative_returns'], factor_name)
            st.plotly_chart(fig_cum, use_container_width=True)

            st.write("### 🔄 多空组合 (Q5-Q1)")
            fig_ls = generate_long_short_chart(group_result['cumulative_returns'])
            if fig_ls:
                st.plotly_chart(fig_ls, use_container_width=True)

            st.write("**分组收益统计:**")
            stats_df = pd.DataFrame({
                '分组': group_result['mean_returns'].index,
                '年化收益(%)': (group_result['mean_returns'] * 100).round(2),
                '收益标准差(%)': (group_result['std'] * 100).round(2),
                '夏普比率': group_result['sharpe'].round(2)
            })
            st.dataframe(stats_df, use_container_width=True)
    else:
        st.warning("无法获取价格数据")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify no syntax errors**

Run: `cd /Users/xinzhan/.openclaw/workspace/quant_factor_system && python -c "import ast; ast.parse(open('dashboard/pages/Factors.py').read()); print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add dashboard/pages/Factors.py
git commit -m "refactor(dashboard): rewrite Factors page to read from mining DB tables"
```

---

### Task 7: Run all tests and verify

Run the complete test suite to ensure nothing is broken.

**Files:** None (verification only)

- [ ] **Step 1: Run full test suite**

Run: `cd /Users/xinzhan/.openclaw/workspace/quant_factor_system && python -m pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 2: Verify imports work**

Run: `cd /Users/xinzhan/.openclaw/workspace/quant_factor_system && python -c "from mining.publisher import FactorPublisher; print('publisher OK')"`
Run: `cd /Users/xinzhan/.openclaw/workspace/quant_factor_system && python -c "from data.loaders import get_available_factors, get_factor_data; print('loaders OK')"`
Expected: Both print OK

- [ ] **Step 3: Final commit if any fixups needed**

```bash
git add -A
git commit -m "fix: address test/import issues from publish pipeline integration"
```
