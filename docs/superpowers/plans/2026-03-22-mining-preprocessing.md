# Mining Preprocessing Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a preprocessing layer to the mining evaluator that filters untradable stocks, cleans factor values, masks untradable returns, and optionally neutralizes for market cap / industry — all before IC calculation.

**Architecture:** A new `mining/preprocessing.py` module provides `FactorPreprocessor` class that evaluator calls after raw factor computation and before IC. Auxiliary data (limit prices) is synced to Qlib binary format via extended `DataSynchronizer`. Preprocessing config lives in `MiningConfig` with sensible defaults. ST/IPO/industry/market-cap fields are **future work** — they require new data sources that are not yet synced; the preprocessor logs warnings when filters are enabled but data is missing.

**Tech Stack:** Python, pandas, numpy, scipy, Qlib expression engine

---

## File Structure

| File | Action | Responsibility |
|------|--------|---------------|
| `mining/preprocessing.py` | **Create** | `FactorPreprocessor` — universe filter, factor cleaning, return masking, optional neutralization |
| `mining/config.py` | **Modify** | Add preprocessing config fields (MAD multiplier, neutralize_mode, etc.) |
| `mining/evaluator.py` | **Modify** | Inject preprocessing before IC calculation in all stages |
| `data/qlib_sync.py` | **Modify** | Sync auxiliary fields (limit_up, limit_down) to Qlib |
| `tests/mining/test_preprocessing.py` | **Create** | Unit tests for every preprocessing function |
| `tests/mining/test_evaluator_preprocessing.py` | **Create** | Integration tests: evaluator with preprocessing enabled |

### Future work (not in this plan)

These auxiliary fields require new data source integration and will be added later:

| Qlib field | Source | Purpose |
|-----------|--------|---------|
| `$is_st` | RiceQuant `is_st()` or name prefix | ST status flag |
| `$list_date_dist` | RiceQuant `all_instruments` listed_date | Days since listing |
| `$industry_code` | industry_classification table | Industry numeric code |
| `$market_cap` | RiceQuant `total_market_cap` | Total market cap |

When these fields become available, the preprocessor will automatically use them (the config flags and neutralization logic are already in place).

---

## Task 1: Extend DataSynchronizer to sync limit prices

**Files:**
- Modify: `data/qlib_sync.py`
- Test: `tests/data/test_qlib_sync_aux.py`

The evaluator needs limit_up/limit_down per-stock-per-day. These already exist in TimescaleDB (`price_daily` table) and in the RiceQuant source. We add them to the Qlib sync.

- [ ] **Step 1: Write failing test for auxiliary field sync**

```python
# tests/data/test_qlib_sync_aux.py
import pytest
import numpy as np
import pandas as pd
from unittest.mock import MagicMock
from data.qlib_sync import DataSynchronizer


class TestAuxFieldSync:
    """Test that auxiliary fields are synced to Qlib format."""

    def _make_mock_db(self):
        db = MagicMock()
        db.query_price.return_value = pd.DataFrame({
            "time": pd.date_range("2024-01-02", periods=3).repeat(2),
            "symbol": ["600000.SH", "000001.SZ"] * 3,
            "open": [10.0, 20.0] * 3,
            "high": [11.0, 21.0] * 3,
            "low": [9.0, 19.0] * 3,
            "close": [10.5, 20.5] * 3,
            "volume": [1e6, 2e6] * 3,
            "amount": [1e7, 2e7] * 3,
            "limit_up": [11.55, 22.55] * 3,
            "limit_down": [9.45, 18.45] * 3,
        })
        return db

    def test_limit_prices_synced(self, tmp_path):
        qlib_dir = tmp_path / "qlib_data"
        db = self._make_mock_db()
        sync = DataSynchronizer(db, qlib_dir=str(qlib_dir))
        sync.sync_daily(start="2024-01-02", end="2024-01-04")

        # limit_up.day.bin should exist
        bin_path = qlib_dir / "features" / "SH600000" / "limit_up.day.bin"
        assert bin_path.exists()

        bin_path_down = qlib_dir / "features" / "SH600000" / "limit_down.day.bin"
        assert bin_path_down.exists()

    def test_missing_limit_fields_graceful(self, tmp_path):
        """When DB has no limit fields, sync still works without them."""
        qlib_dir = tmp_path / "qlib_data"
        db = MagicMock()
        db.query_price.return_value = pd.DataFrame({
            "time": pd.date_range("2024-01-02", periods=2).repeat(1),
            "symbol": ["600000.SH"] * 2,
            "open": [10.0, 10.5],
            "high": [11.0, 11.5],
            "low": [9.0, 9.5],
            "close": [10.5, 11.0],
            "volume": [1e6, 1e6],
            "amount": [1e7, 1e7],
        })
        sync = DataSynchronizer(db, qlib_dir=str(qlib_dir))
        sync.sync_daily(start="2024-01-02", end="2024-01-03")

        # close.day.bin exists, limit_up does not
        assert (qlib_dir / "features" / "SH600000" / "close.day.bin").exists()
        assert not (qlib_dir / "features" / "SH600000" / "limit_up.day.bin").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/data/test_qlib_sync_aux.py::TestAuxFieldSync::test_limit_prices_synced -v`
Expected: FAIL — limit_up/limit_down not synced

- [ ] **Step 3: Implement — add limit_up/limit_down to sync_daily**

In `data/qlib_sync.py`:

```python
FIELDS = ["open", "high", "low", "close", "volume", "amount"]
AUX_FIELDS = ["limit_up", "limit_down"]

def sync_daily(self, ...):
    # ... existing code up to returns_1d computation ...

    # Build field list, only including aux fields that exist in the data
    all_fields = self.FIELDS + ["vwap", "returns", "returns_1d"]
    for af in self.AUX_FIELDS:
        if af in df.columns:
            all_fields.append(af)

    for symbol, group in df.groupby("symbol"):
        self._write_symbol_features(str(symbol), group, all_fields, trading_days)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/data/test_qlib_sync_aux.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add data/qlib_sync.py tests/data/test_qlib_sync_aux.py
git commit -m "feat(sync): add limit_up/limit_down to Qlib sync"
```

---

## Task 2: Add preprocessing config to MiningConfig

**Files:**
- Modify: `mining/config.py`
- Test: `tests/mining/test_preprocessing.py` (config section)

- [ ] **Step 1: Write failing test for new config defaults**

```python
# tests/mining/test_preprocessing.py (first section)
from mining.config import MiningConfig


class TestPreprocessingConfig:
    def test_preprocessing_defaults(self):
        config = MiningConfig()
        assert config.filter_suspend is True
        assert config.filter_limit is True
        assert config.winsorize_method == "mad"
        assert config.winsorize_n == 5.0
        assert config.standardize_method == "zscore"
        assert config.neutralize_mode == "none"

    def test_config_overrides(self):
        config = MiningConfig(
            winsorize_method="sigma",
            winsorize_n=3.0,
            neutralize_mode="both",
        )
        assert config.winsorize_method == "sigma"
        assert config.winsorize_n == 3.0
        assert config.neutralize_mode == "both"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/mining/test_preprocessing.py::TestPreprocessingConfig -v`
Expected: FAIL — fields do not exist on MiningConfig

- [ ] **Step 3: Add preprocessing fields to MiningConfig**

```python
@dataclass
class MiningConfig:
    # ... existing fields ...

    # === Preprocessing ===
    # Universe filtering
    filter_suspend: bool = True
    filter_limit: bool = True

    # Factor value cleaning
    winsorize_method: str = "mad"  # "mad" or "sigma"
    winsorize_n: float = 5.0  # MAD multiplier (or sigma multiplier)
    standardize_method: str = "zscore"  # "zscore" or "rank"

    # Neutralization (optional, requires $market_cap / $industry_code synced)
    neutralize_mode: str = "none"  # "none", "market_cap", "industry", "both"
```

Note: `filter_st` and `ipo_min_days` are deliberately omitted — the required data fields (`$is_st`, `$list_date_dist`) are not yet synced. They will be added when the data source integration is done.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/mining/test_preprocessing.py::TestPreprocessingConfig -v`
Expected: PASS

- [ ] **Step 5: Run all existing mining tests for no breakage**

Run: `pytest tests/mining/ -v`
Expected: All existing tests PASS (new fields have defaults)

- [ ] **Step 6: Commit**

```bash
git add mining/config.py tests/mining/test_preprocessing.py
git commit -m "feat(config): add preprocessing parameters to MiningConfig"
```

---

## Task 3: Create FactorPreprocessor — universe filtering

**Files:**
- Create: `mining/preprocessing.py`
- Test: `tests/mining/test_preprocessing.py` (append)

- [ ] **Step 1: Write failing tests for tradable mask**

```python
import numpy as np
import pandas as pd
import pytest
from mining.preprocessing import FactorPreprocessor
from mining.config import MiningConfig


def _make_index(dates, instruments):
    """Helper: create (datetime, instrument) MultiIndex."""
    return pd.MultiIndex.from_product(
        [pd.to_datetime(dates), instruments],
        names=["datetime", "instrument"],
    )


class TestUniverseFilter:
    def test_suspend_filtered(self):
        """Stocks with volume == 0 are masked out."""
        config = MiningConfig(filter_suspend=True)
        pp = FactorPreprocessor(config)

        idx = _make_index(["2024-01-02"], ["SH600000", "SZ000001"])
        volume = pd.DataFrame({"$volume": [1e6, 0.0]}, index=idx)

        mask = pp.build_tradable_mask(volume=volume)
        assert mask.loc[("2024-01-02", "SH600000")] == True
        assert mask.loc[("2024-01-02", "SZ000001")] == False

    def test_limit_up_filtered(self):
        """Stocks at limit-up price are masked for buying."""
        config = MiningConfig(filter_limit=True)
        pp = FactorPreprocessor(config)

        idx = _make_index(["2024-01-02"], ["SH600000", "SZ000001"])
        close = pd.DataFrame({"$close": [11.0, 20.0]}, index=idx)
        limit_up = pd.DataFrame({"$limit_up": [11.0, 22.0]}, index=idx)

        mask = pp.build_tradable_mask(close=close, limit_up=limit_up)
        assert mask.loc[("2024-01-02", "SH600000")] == False
        assert mask.loc[("2024-01-02", "SZ000001")] == True

    def test_limit_down_filtered(self):
        """Stocks at limit-down price are masked."""
        config = MiningConfig(filter_limit=True)
        pp = FactorPreprocessor(config)

        idx = _make_index(["2024-01-02"], ["SH600000", "SZ000001"])
        close = pd.DataFrame({"$close": [9.0, 20.0]}, index=idx)
        limit_down = pd.DataFrame({"$limit_down": [9.0, 18.0]}, index=idx)

        mask = pp.build_tradable_mask(close=close, limit_down=limit_down)
        assert mask.loc[("2024-01-02", "SH600000")] == False
        assert mask.loc[("2024-01-02", "SZ000001")] == True

    def test_warns_when_filter_enabled_but_data_missing(self, caplog):
        """When filter_suspend=True but no volume data, log a warning."""
        config = MiningConfig(filter_suspend=True, filter_limit=True)
        pp = FactorPreprocessor(config)

        idx = _make_index(["2024-01-02"], ["A", "B"])
        close = pd.DataFrame({"$close": [10.0, 20.0]}, index=idx)

        # No volume, no limit_up/limit_down — should warn about missing data
        import logging
        with caplog.at_level(logging.WARNING):
            mask = pp.build_tradable_mask(close=close)
        assert "filter_suspend enabled but volume data not provided" in caplog.text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/mining/test_preprocessing.py::TestUniverseFilter -v`
Expected: FAIL — module does not exist

- [ ] **Step 3: Implement FactorPreprocessor.build_tradable_mask**

```python
# mining/preprocessing.py
"""Factor preprocessing pipeline for the mining evaluator."""

from __future__ import annotations

import logging
from typing import Optional

import numpy as np
import pandas as pd

from .config import MiningConfig

logger = logging.getLogger(__name__)


class FactorPreprocessor:
    """Preprocessing pipeline applied uniformly to all factors before IC calculation.

    Steps (applied in order):
    1. Universe filtering: build tradable mask (suspend, limit)
    2. Factor cleaning: inf->NaN, winsorize (MAD), standardize (zscore/rank)
    3. Return masking: apply tradable mask to forward returns
    4. Neutralization (optional): market cap / industry regression residuals
    """

    def __init__(self, config: MiningConfig):
        self.config = config

    def build_tradable_mask(
        self,
        volume: Optional[pd.DataFrame] = None,
        close: Optional[pd.DataFrame] = None,
        limit_up: Optional[pd.DataFrame] = None,
        limit_down: Optional[pd.DataFrame] = None,
    ) -> pd.Series:
        """Build boolean mask: True = tradable, False = excluded.

        All inputs must have (datetime, instrument) MultiIndex.
        Combines all available filters with AND logic.
        Logs warnings when a filter is enabled but the required data is missing.
        """
        # Determine index from first available input
        ref = volume if volume is not None else close
        if ref is None:
            ref = limit_up if limit_up is not None else limit_down
        if ref is None:
            raise ValueError("At least one data input required")
        mask = pd.Series(True, index=ref.index)

        # Suspend filter: volume == 0
        if self.config.filter_suspend:
            if volume is not None:
                col = volume.columns[0]
                mask &= volume[col] > 0
            else:
                logger.warning("filter_suspend enabled but volume data not provided — skipping")

        # Limit-up filter: close >= limit_up (can't buy)
        if self.config.filter_limit:
            if close is not None and limit_up is not None:
                c_col = close.columns[0]
                lu_col = limit_up.columns[0]
                mask &= close[c_col] < limit_up[lu_col]
            elif close is not None and limit_up is None:
                logger.warning("filter_limit enabled but limit_up data not provided — skipping limit-up filter")

        # Limit-down filter: close <= limit_down (can't sell)
        if self.config.filter_limit:
            if close is not None and limit_down is not None:
                c_col = close.columns[0]
                ld_col = limit_down.columns[0]
                mask &= close[c_col] > limit_down[ld_col]
            elif close is not None and limit_down is None:
                logger.warning("filter_limit enabled but limit_down data not provided — skipping limit-down filter")

        return mask
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/mining/test_preprocessing.py::TestUniverseFilter -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add mining/preprocessing.py tests/mining/test_preprocessing.py
git commit -m "feat(preprocessing): add universe filtering (suspend, limit-up/down)"
```

---

## Task 4: Factor value cleaning — inf, winsorize, standardize

**Files:**
- Modify: `mining/preprocessing.py`
- Test: `tests/mining/test_preprocessing.py` (append)

- [ ] **Step 1: Write failing tests for factor cleaning**

```python
class TestFactorCleaning:
    def test_inf_replaced_with_nan(self):
        config = MiningConfig()
        pp = FactorPreprocessor(config)

        idx = _make_index(["2024-01-02"], ["A", "B", "C"])
        factor = pd.DataFrame({"f": [1.0, np.inf, -np.inf]}, index=idx)

        cleaned = pp.clean_factor_values(factor)
        assert np.isnan(cleaned.iloc[1, 0])
        assert np.isnan(cleaned.iloc[2, 0])
        assert cleaned.iloc[0, 0] != 0  # not zeroed, just cleaned

    def test_all_nan_no_crash(self):
        """All-NaN or all-inf factor for a date should not raise."""
        config = MiningConfig()
        pp = FactorPreprocessor(config)

        idx = _make_index(["2024-01-02"], ["A", "B", "C"])
        factor = pd.DataFrame({"f": [np.inf, np.nan, -np.inf]}, index=idx)

        cleaned = pp.clean_factor_values(factor)
        # All should be NaN after inf replacement
        assert cleaned["f"].isna().all()

    def test_mad_winsorize(self):
        """MAD winsorization clips outliers."""
        config = MiningConfig(winsorize_method="mad", winsorize_n=3.0)
        pp = FactorPreprocessor(config)

        np.random.seed(42)
        values = np.random.randn(100)
        values[0] = 100.0  # extreme outlier
        idx = _make_index(["2024-01-02"], [f"S{i:03d}" for i in range(100)])
        factor = pd.DataFrame({"f": values}, index=idx)

        cleaned = pp.clean_factor_values(factor)
        assert cleaned.iloc[0, 0] < 50.0  # clipped down

    def test_zscore_standardize(self):
        """After zscore, mean ~ 0 and std ~ 1."""
        config = MiningConfig(standardize_method="zscore")
        pp = FactorPreprocessor(config)

        values = np.arange(1.0, 101.0)
        idx = _make_index(["2024-01-02"], [f"S{i:03d}" for i in range(100)])
        factor = pd.DataFrame({"f": values}, index=idx)

        cleaned = pp.clean_factor_values(factor)
        col = cleaned.columns[0]
        # .loc["2024-01-02"] slices to instrument-only index
        day_vals = cleaned.loc["2024-01-02", col]
        assert abs(day_vals.mean()) < 0.01
        assert abs(day_vals.std() - 1.0) < 0.1

    def test_rank_standardize(self):
        """Rank standardization preserves ordinal ranking."""
        config = MiningConfig(standardize_method="rank")
        pp = FactorPreprocessor(config)

        values = np.array([100.0, 1.0, 50.0, 25.0, 75.0])
        idx = _make_index(["2024-01-02"], ["A", "B", "C", "D", "E"])
        factor = pd.DataFrame({"f": values}, index=idx)

        cleaned = pp.clean_factor_values(factor)
        col = cleaned.columns[0]
        # After .loc["2024-01-02"], index is instrument-level only
        day_vals = cleaned.loc["2024-01-02", col]
        assert day_vals.loc["A"] > day_vals.loc["B"]  # 100 > 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/mining/test_preprocessing.py::TestFactorCleaning -v`
Expected: FAIL — `clean_factor_values` does not exist

- [ ] **Step 3: Implement clean_factor_values**

Add to `mining/preprocessing.py`:

```python
def clean_factor_values(self, factor: pd.DataFrame) -> pd.DataFrame:
    """Clean raw factor values: inf->NaN, winsorize, standardize.

    Applied cross-sectionally (per date).
    """
    result = factor.copy()
    col = result.columns[0]

    # Replace inf with NaN
    result[col] = result[col].replace([np.inf, -np.inf], np.nan)

    # Cross-sectional winsorize + standardize per date
    def _process_group(group: pd.Series) -> pd.Series:
        vals = group.copy()
        valid = vals.dropna()
        if len(valid) < 3:
            return vals

        # Winsorize
        if self.config.winsorize_method == "mad":
            median = valid.median()
            mad = (valid - median).abs().median()
            mad_e = mad * 1.4826  # consistent estimator for std
            if mad_e > 0:
                upper = median + self.config.winsorize_n * mad_e
                lower = median - self.config.winsorize_n * mad_e
                vals = vals.clip(lower, upper)
        else:  # sigma
            mean, std = valid.mean(), valid.std()
            if std > 0:
                upper = mean + self.config.winsorize_n * std
                lower = mean - self.config.winsorize_n * std
                vals = vals.clip(lower, upper)

        # Standardize
        valid_after = vals.dropna()
        if len(valid_after) < 2:
            return vals
        if self.config.standardize_method == "rank":
            ranked = vals.rank(pct=True, na_option="keep")
            vals = (ranked - 0.5) * 3.46  # approximate N(0,1)
        else:  # zscore
            mean, std = valid_after.mean(), valid_after.std()
            if std > 0:
                vals = (vals - mean) / std

        return vals

    result[col] = result.groupby(level="datetime")[col].transform(_process_group)
    return result
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/mining/test_preprocessing.py::TestFactorCleaning -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add mining/preprocessing.py tests/mining/test_preprocessing.py
git commit -m "feat(preprocessing): add factor cleaning (inf, MAD winsorize, zscore/rank)"
```

---

## Task 5: Return masking — apply tradable mask to forward returns

**Files:**
- Modify: `mining/preprocessing.py`
- Test: `tests/mining/test_preprocessing.py` (append)

- [ ] **Step 1: Write failing test for return masking**

```python
class TestReturnMasking:
    def test_untradable_returns_masked(self):
        """Forward returns for untradable stocks become NaN."""
        config = MiningConfig()
        pp = FactorPreprocessor(config)

        idx = _make_index(["2024-01-02"], ["A", "B", "C"])
        returns = pd.DataFrame({"$returns_1d": [0.05, 0.03, -0.02]}, index=idx)
        mask = pd.Series([True, False, True], index=idx)

        masked = pp.mask_returns(returns, mask)
        assert masked.iloc[0, 0] == pytest.approx(0.05)
        assert np.isnan(masked.iloc[1, 0])  # B is untradable
        assert masked.iloc[2, 0] == pytest.approx(-0.02)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/mining/test_preprocessing.py::TestReturnMasking -v`
Expected: FAIL

- [ ] **Step 3: Implement mask_returns**

```python
def mask_returns(self, returns: pd.DataFrame, tradable_mask: pd.Series) -> pd.DataFrame:
    """Set forward returns to NaN where stocks are untradable."""
    result = returns.copy()
    col = result.columns[0]
    result.loc[~tradable_mask, col] = np.nan
    return result
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/mining/test_preprocessing.py::TestReturnMasking -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add mining/preprocessing.py tests/mining/test_preprocessing.py
git commit -m "feat(preprocessing): add return masking for untradable stocks"
```

---

## Task 6: Optional neutralization — market cap + industry

**Files:**
- Modify: `mining/preprocessing.py`
- Test: `tests/mining/test_preprocessing.py` (append)

Note: This is fully functional code, but requires `$market_cap` and `$industry_code` to be synced to Qlib (future work). The tests use synthetic data to verify the math works.

- [ ] **Step 1: Write failing tests for neutralization**

```python
class TestNeutralization:
    def test_market_cap_neutralize(self):
        """After market-cap neutralization, factor-cap correlation ~ 0."""
        config = MiningConfig(neutralize_mode="market_cap")
        pp = FactorPreprocessor(config)

        np.random.seed(42)
        n = 200
        market_cap = np.exp(np.random.randn(n) * 0.5 + 10)  # lognormal
        # Factor highly correlated with market cap
        factor_vals = np.log(market_cap) + np.random.randn(n) * 0.1
        idx = _make_index(["2024-01-02"], [f"S{i:03d}" for i in range(n)])
        factor = pd.DataFrame({"f": factor_vals}, index=idx)
        mcap = pd.DataFrame({"$market_cap": market_cap}, index=idx)

        neutralized = pp.neutralize(factor, market_cap=mcap)
        col = neutralized.columns[0]
        # .loc["2024-01-02"] drops datetime level
        day_vals = neutralized.loc["2024-01-02", col].values
        from scipy.stats import spearmanr
        corr, _ = spearmanr(day_vals, np.log(market_cap))
        assert abs(corr) < 0.15

    def test_no_neutralize_when_disabled(self):
        """When neutralize_mode='none', factor values unchanged."""
        config = MiningConfig(neutralize_mode="none")
        pp = FactorPreprocessor(config)

        idx = _make_index(["2024-01-02"], ["A", "B", "C"])
        factor = pd.DataFrame({"f": [1.0, 2.0, 3.0]}, index=idx)

        result = pp.neutralize(factor)
        pd.testing.assert_frame_equal(result, factor)

    def test_neutralize_warns_when_data_missing(self, caplog):
        """market_cap mode without data logs warning and returns unchanged."""
        config = MiningConfig(neutralize_mode="market_cap")
        pp = FactorPreprocessor(config)

        idx = _make_index(["2024-01-02"], ["A", "B", "C"])
        factor = pd.DataFrame({"f": [1.0, 2.0, 3.0]}, index=idx)

        import logging
        with caplog.at_level(logging.WARNING):
            result = pp.neutralize(factor)  # no market_cap passed
        # Should return unchanged and warn
        pd.testing.assert_frame_equal(result, factor)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/mining/test_preprocessing.py::TestNeutralization -v`
Expected: FAIL

- [ ] **Step 3: Implement neutralize method**

```python
def neutralize(
    self,
    factor: pd.DataFrame,
    market_cap: Optional[pd.DataFrame] = None,
    industry: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """Optionally neutralize factor for market cap and/or industry.

    Uses OLS regression: factor = alpha + beta*ln(mcap) + sum(gamma_j * industry_j) + residual
    Returns the residual.
    """
    if self.config.neutralize_mode == "none":
        return factor

    # Check if required data is available
    need_mcap = self.config.neutralize_mode in ("market_cap", "both")
    need_ind = self.config.neutralize_mode in ("industry", "both")
    if need_mcap and market_cap is None:
        logger.warning("neutralize_mode=%s but market_cap data not provided — skipping", self.config.neutralize_mode)
        if not need_ind or industry is None:
            return factor
    if need_ind and industry is None:
        logger.warning("neutralize_mode=%s but industry data not provided — skipping industry", self.config.neutralize_mode)
        if not need_mcap or market_cap is None:
            return factor

    result = factor.copy()
    col = result.columns[0]

    def _neutralize_group(group_factor, group_mcap, group_ind):
        valid = group_factor.dropna()
        if len(valid) < 10:
            return group_factor

        X_parts = []

        if need_mcap and group_mcap is not None:
            mcap_col = group_mcap.columns[0]
            mcap_vals = group_mcap.reindex(valid.index)[mcap_col]
            mcap_vals = mcap_vals.fillna(mcap_vals.median())
            log_mcap = np.log(mcap_vals.clip(lower=1.0))
            X_parts.append(log_mcap.values.reshape(-1, 1))

        if need_ind and group_ind is not None:
            ind_col = group_ind.columns[0]
            ind_vals = group_ind.reindex(valid.index)[ind_col].fillna(-1)
            dummies = pd.get_dummies(ind_vals, drop_first=True).values
            if dummies.shape[1] > 0:
                X_parts.append(dummies)

        if not X_parts:
            return group_factor

        X = np.hstack(X_parts)
        X = np.column_stack([np.ones(len(X)), X])  # intercept
        y = valid.values

        try:
            beta, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
            residuals = y - X @ beta
            result_series = group_factor.copy()
            result_series.loc[valid.index] = residuals
            return result_series
        except np.linalg.LinAlgError:
            return group_factor

    for dt in result.index.get_level_values("datetime").unique():
        dt_slice = result.index.get_level_values("datetime") == dt
        mcap_group = market_cap.loc[[dt]] if market_cap is not None and dt in market_cap.index.get_level_values("datetime") else None
        ind_group = industry.loc[[dt]] if industry is not None and dt in industry.index.get_level_values("datetime") else None

        result.loc[dt_slice, col] = _neutralize_group(
            result.loc[dt_slice, col], mcap_group, ind_group
        ).values

    return result
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/mining/test_preprocessing.py::TestNeutralization -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add mining/preprocessing.py tests/mining/test_preprocessing.py
git commit -m "feat(preprocessing): add optional market-cap/industry neutralization"
```

---

## Task 7: Convenience method — preprocess_for_ic

**Files:**
- Modify: `mining/preprocessing.py`
- Test: `tests/mining/test_preprocessing.py` (append)

- [ ] **Step 1: Write failing test**

```python
class TestPreprocessForIC:
    def test_full_pipeline(self):
        """preprocess_for_ic returns cleaned factor and masked returns."""
        config = MiningConfig(
            filter_suspend=True,
            filter_limit=True,
            winsorize_method="mad",
            standardize_method="zscore",
            neutralize_mode="none",
        )
        pp = FactorPreprocessor(config)

        idx = _make_index(["2024-01-02"], ["A", "B", "C", "D"])
        raw_factor = pd.DataFrame({"f": [1.0, np.inf, 3.0, 100.0]}, index=idx)
        raw_returns = pd.DataFrame({"$returns_1d": [0.05, 0.03, -0.02, 0.01]}, index=idx)
        volume = pd.DataFrame({"$volume": [1e6, 0.0, 1e6, 1e6]}, index=idx)
        close = pd.DataFrame({"$close": [10.0, 20.0, 10.0, 10.0]}, index=idx)
        limit_up = pd.DataFrame({"$limit_up": [11.0, 22.0, 10.0, 11.0]}, index=idx)

        clean_f, clean_r = pp.preprocess_for_ic(
            factor=raw_factor,
            returns=raw_returns,
            volume=volume,
            close=close,
            limit_up=limit_up,
        )

        # B suspended -> returns NaN
        assert np.isnan(clean_r.loc[("2024-01-02", "B")].iloc[0])
        # C at limit-up (close == limit_up) -> returns NaN
        assert np.isnan(clean_r.loc[("2024-01-02", "C")].iloc[0])
        # A normal -> returns preserved
        assert clean_r.loc[("2024-01-02", "A")].iloc[0] == pytest.approx(0.05)
        # inf in B factor -> NaN
        assert np.isnan(clean_f.loc[("2024-01-02", "B")].iloc[0])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/mining/test_preprocessing.py::TestPreprocessForIC -v`
Expected: FAIL

- [ ] **Step 3: Implement preprocess_for_ic**

```python
def preprocess_for_ic(
    self,
    factor: pd.DataFrame,
    returns: pd.DataFrame,
    volume: Optional[pd.DataFrame] = None,
    close: Optional[pd.DataFrame] = None,
    limit_up: Optional[pd.DataFrame] = None,
    limit_down: Optional[pd.DataFrame] = None,
    market_cap: Optional[pd.DataFrame] = None,
    industry: Optional[pd.DataFrame] = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Full preprocessing pipeline. Returns (cleaned_factor, masked_returns)."""
    # 1. Build tradable mask
    mask = self.build_tradable_mask(
        volume=volume, close=close, limit_up=limit_up, limit_down=limit_down,
    )

    # 2. Clean factor values
    cleaned_factor = self.clean_factor_values(factor)

    # 3. Neutralize (optional)
    if self.config.neutralize_mode != "none":
        cleaned_factor = self.neutralize(
            cleaned_factor, market_cap=market_cap, industry=industry,
        )

    # 4. Mask returns
    masked_returns = self.mask_returns(returns, mask)

    return cleaned_factor, masked_returns
```

- [ ] **Step 4: Run ALL preprocessing tests**

Run: `pytest tests/mining/test_preprocessing.py -v`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add mining/preprocessing.py tests/mining/test_preprocessing.py
git commit -m "feat(preprocessing): add preprocess_for_ic convenience method"
```

---

## Task 8: Integrate preprocessing into evaluator

**Files:**
- Modify: `mining/evaluator.py`
- Test: `tests/mining/test_evaluator_preprocessing.py`

- [ ] **Step 1: Write failing integration tests**

```python
# tests/mining/test_evaluator_preprocessing.py
import numpy as np
import pandas as pd
import pytest
from unittest.mock import patch, MagicMock, call
from mining.evaluator import FactorMiningEvaluator
from mining.config import MiningConfig


class TestEvaluatorPreprocessing:
    """Verify evaluator has preprocessor and calls it."""

    @patch("mining.evaluator.FactorMiningEvaluator._ensure_qlib_initialized")
    def test_evaluator_has_preprocessor(self, mock_init):
        config = MiningConfig(filter_suspend=True, filter_limit=True)
        evaluator = FactorMiningEvaluator(config)
        assert hasattr(evaluator, "_preprocessor")
        assert evaluator._preprocessor is not None

    @patch("mining.evaluator.FactorMiningEvaluator._ensure_qlib_initialized")
    def test_preprocessing_called_during_ic(self, mock_init):
        """Verify preprocess_for_ic is called when aux data is available."""
        config = MiningConfig()
        evaluator = FactorMiningEvaluator(config)

        # Mock the preprocessor
        evaluator._preprocessor = MagicMock()
        idx = pd.MultiIndex.from_product(
            [pd.to_datetime(["2024-01-02"]), ["A", "B"]],
            names=["datetime", "instrument"],
        )
        factor = pd.DataFrame({"f": [1.0, 2.0]}, index=idx)
        returns = pd.DataFrame({"$returns_1d": [0.01, 0.02]}, index=idx)

        # Set up mock to return the inputs unchanged
        evaluator._preprocessor.preprocess_for_ic.return_value = (factor, returns)

        # Call with aux data triggers preprocessing
        aux = {"volume": pd.DataFrame({"$volume": [1e6, 1e6]}, index=idx)}
        result = evaluator._compute_ic_from_frames(
            factor, returns, aux_data=aux,
        )
        evaluator._preprocessor.preprocess_for_ic.assert_called_once()

    @patch("mining.evaluator.FactorMiningEvaluator._ensure_qlib_initialized")
    def test_no_preprocessing_without_aux_data(self, mock_init):
        """Without aux data, preprocessing is skipped (backward compat)."""
        config = MiningConfig()
        evaluator = FactorMiningEvaluator(config)
        evaluator._preprocessor = MagicMock()

        idx = pd.MultiIndex.from_product(
            [pd.to_datetime(["2024-01-02"]), ["A", "B"]],
            names=["datetime", "instrument"],
        )
        factor = pd.DataFrame({"f": [1.0, 2.0]}, index=idx)
        returns = pd.DataFrame({"$returns_1d": [0.01, 0.02]}, index=idx)

        # No aux_data -> preprocessing NOT called
        result = evaluator._compute_ic_from_frames(factor, returns)
        evaluator._preprocessor.preprocess_for_ic.assert_not_called()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/mining/test_evaluator_preprocessing.py -v`
Expected: FAIL

- [ ] **Step 3: Modify evaluator — add preprocessor and aux data loading**

Changes to `mining/evaluator.py`:

**3a. Import and init:**

```python
from .preprocessing import FactorPreprocessor

class FactorMiningEvaluator:
    def __init__(self, config: MiningConfig):
        self.config = config
        self._factor_cache: Dict[str, pd.DataFrame] = {}
        self._subset_factor_cache: Dict[str, pd.DataFrame] = {}
        self._preprocessor = FactorPreprocessor(config)
        self._aux_cache: Dict[str, Dict[str, pd.DataFrame]] = {}
        self._ensure_qlib_initialized()
```

**3b. Add `_load_aux_data` method:**

```python
def _load_aux_data(self, instruments: list, start_time: str, end_time: str) -> Dict[str, pd.DataFrame]:
    """Load auxiliary data for preprocessing. Cached."""
    cache_key = f"{len(instruments)}_{start_time}_{end_time}"
    if cache_key in self._aux_cache:
        return self._aux_cache[cache_key]

    from qlib.data import D
    aux = {}
    try:
        fields = ["$volume", "$close"]
        # Only request limit fields if they might exist
        optional = ["$limit_up", "$limit_down"]
        all_fields = fields + optional
        aux_df = D.features(
            instruments=instruments,
            fields=all_fields,
            start_time=start_time,
            end_time=end_time,
        )
        for col in aux_df.columns:
            key = col.replace("$", "")  # $volume -> volume
            aux[key] = aux_df[[col]]
    except Exception as e:
        logger.warning("Failed to load aux data: %s — preprocessing will be limited", e)

    self._aux_cache[cache_key] = aux
    return aux
```

**3c. Modify `_compute_ic_from_frames` — add optional `aux_data` param:**

```python
def _compute_ic_from_frames(
    self,
    factor_values: pd.DataFrame,
    returns: pd.DataFrame,
    aux_data: Optional[Dict[str, pd.DataFrame]] = None,
) -> Dict[str, Any]:
    """Compute daily cross-sectional Spearman IC.
    If aux_data is provided, applies preprocessing first.
    """
    if aux_data:
        factor_values, returns = self._preprocessor.preprocess_for_ic(
            factor=factor_values, returns=returns, **aux_data,
        )

    # ... rest of existing IC computation (unchanged) ...
```

**3d. Update all call sites to pass aux_data:**

In `_fast_ic_screening`:
```python
def _fast_ic_screening(self, candidates):
    subset = self._get_fast_screening_universe()
    returns = self._get_returns_qlib(subset, self.config.train_start, self.config.train_end)
    aux = self._load_aux_data(subset, self.config.train_start, self.config.train_end)
    # ...
    ic_stats = self._compute_ic_from_frames(values, returns, aux_data=aux)
```

In `_correlation_check`:
```python
def _correlation_check(self, candidates):
    # ...
    returns = self._get_returns_qlib(full_universe, self.config.train_start, self.config.train_end)
    aux = self._load_aux_data(full_universe, self.config.train_start, self.config.train_end)
    # ...
    full_ic = self._compute_ic_from_frames(factor_vals, returns, aux_data=aux)
```

In `_full_validation`:
```python
def _full_validation(self, candidates):
    full_universe = self._get_full_universe()
    aux_is = self._load_aux_data(full_universe, self.config.train_start, self.config.train_end)
    # ...
    ic_is = self._compute_ic_from_frames(cached_vals, returns_is, aux_data=aux_is)
    # ...
    test_end = self.config.test_end or str(pd.Timestamp.now().date())
    aux_oos = self._load_aux_data(full_universe, self.config.test_start, test_end)
    ic_oos = self._compute_ic_from_frames(vals_oos, returns_oos, aux_data=aux_oos)
```

- [ ] **Step 4: Run ALL tests**

Run: `pytest tests/mining/ -v`
Expected: ALL PASS (both new and existing tests — existing tests pass `aux_data=None` by default)

- [ ] **Step 5: Commit**

```bash
git add mining/evaluator.py tests/mining/test_evaluator_preprocessing.py
git commit -m "feat(evaluator): integrate preprocessing pipeline before IC calculation"
```

---

## Task 9: Export and update __init__.py

**Files:**
- Modify: `mining/__init__.py`

- [ ] **Step 1: Add FactorPreprocessor to module exports**

```python
from .preprocessing import FactorPreprocessor
```

Add `"FactorPreprocessor"` to `__all__`.

- [ ] **Step 2: Run full test suite**

Run: `pytest tests/ -v --timeout=30`
Expected: ALL PASS

- [ ] **Step 3: Commit**

```bash
git add mining/__init__.py
git commit -m "feat(mining): export FactorPreprocessor"
```

---

## Task 10: Update factor-mine skill to document preprocessing

**Files:**
- Modify: `.claude/skills/factor-mine.md`

- [ ] **Step 1: Add preprocessing documentation to the skill**

Add a section after Step 3 (Evaluate) explaining:
- Preprocessing is automatic — the evaluator handles it internally
- LLM does NOT need to add Winsorize/Zscore to factor expressions
- Suspended stocks and limit-up/down stocks are excluded from IC calculation
- Config options: `neutralize_mode` can be set to "market_cap", "industry", or "both" (requires synced data)

- [ ] **Step 2: Commit**

```bash
git add .claude/skills/factor-mine.md
git commit -m "docs(skill): document automatic preprocessing in factor-mine"
```

---

## Dependency Order

```
Task 1 (sync limit prices) ──┐
                              ├── Task 8 (evaluator integration)
Task 2 (config)               │
    │                         │
Task 3 (universe filter)      │
    │                         │
    ├── Task 4 (factor clean) │
    │       │                 │
    └── Task 5 (return mask)  │
            │                 │
    Task 6 (neutralization)   │
            │                 │
    Task 7 (preprocess_for_ic)┘
                │
        Task 8 (evaluator integration)
                │
        Task 9 (exports)
                │
        Task 10 (docs)
```

- Tasks 1 and 2 can run in parallel
- Tasks 4 and 5 can run in parallel (both depend on 3)
- Task 8 depends on both Task 1 (aux data sync) and Task 7 (preprocessing module complete)
