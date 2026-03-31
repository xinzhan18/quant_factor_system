# Preprocessing Vectorization + Cache Layer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reduce `/mine` batch evaluation from 15–30 min to ~3–6 min by vectorizing three Python hot-path loops and adding a preprocessing cache layer.

**Architecture:** Three independent hot-path vectorizations (Tasks 1–3) followed by one cache layer integration (Task 4). Task 4 depends on Task 2 (the new `log_mcap_wide` parameter in `neutralize`) and Task 4 also requires a minor signature update to `preprocess_for_ic` to thread `log_mcap_wide` through to `neutralize`. The cache uses SHA-256 of `(expression + IS_window)` as its key — computed once per candidate by callers, passed into `_compute_daily_ics` as a hint.

**Tech Stack:** pandas groupby transform, numpy einsum, hashlib SHA-256, `core.factor_stats.daily_cross_sectional_ic` (already vectorized).

**Spec:** `docs/superpowers/specs/2026-03-31-preprocessing-vectorization-design.md`

---

## File Map

| File | Role |
|------|------|
| `src/mining/preprocessing.py` | Tasks 1 & 2: vectorize `clean_factor_values`, `neutralize`; add `clean_factor()` method; update `preprocess_for_ic` signature |
| `src/mining/evaluator.py` | Tasks 3 & 4: vectorize `_compute_lib_corrs_sampled`; add cache + pre-pivot |
| `tests/mining/test_preprocessing_vec.py` | New: equivalence + guard tests for Tasks 1 & 2 |
| `tests/mining/test_evaluator.py` | Extend: corr-sampled + cache tests for Tasks 3 & 4 |

Run all tests with: `pytest tests/mining/ -v`

---

## Task 1: Vectorize `clean_factor_values`

**Files:**
- Modify: `src/mining/preprocessing.py:81-143`
- Test: `tests/mining/test_preprocessing_vec.py` (new file)

### Background

`clean_factor_values` currently uses `groupby(level="datetime")[col].transform(_process_group)` where `_process_group` is a Python callback — ~1250 Python function calls per IS window.

The replacement uses vectorized pandas `groupby` chains. Two correctness guards preserved:
- Dates with `n_valid < 3`: left unchanged (not clipped or z-scored).
- `mad == 0` or `std == 0`: no division.

Only `winsorize_method="mad"` + `standardize_method="zscore"` (the defaults) are vectorized. The `sigma` and `rank` branches keep existing logic.

- [ ] **Step 1.1: Create test file with failing tests**

Create `tests/mining/test_preprocessing_vec.py`:

```python
"""Tests for vectorized preprocessing equivalence and edge-case guards."""
import numpy as np
import pandas as pd
import pytest
from unittest.mock import patch

from mining.config import MiningConfig
from mining.preprocessing import FactorPreprocessor


def _make_factor(dates, instruments, values, col="factor"):
    idx = pd.MultiIndex.from_product([dates, instruments], names=["datetime", "instrument"])
    return pd.DataFrame({col: values}, index=idx)


@pytest.fixture
def config():
    return MiningConfig(
        winsorize_method="mad", winsorize_n=5.0, standardize_method="zscore",
        neutralize_mode="none", filter_suspend=False, filter_limit=False,
    )


@pytest.fixture
def preprocessor(config):
    return FactorPreprocessor(config)


class TestCleanFactorValuesVectorized:

    def test_output_shape_unchanged(self, preprocessor):
        dates = pd.bdate_range("2023-01-02", periods=20)
        instruments = [f"S{i:03d}" for i in range(50)]
        np.random.seed(0)
        vals = np.random.randn(len(dates) * len(instruments))
        df = _make_factor(dates, instruments, vals)
        result = preprocessor.clean_factor_values(df)
        assert result.shape == df.shape

    def test_sparse_date_guard_preserved(self, preprocessor):
        """Dates with < 3 valid values must be left unchanged."""
        dates = pd.bdate_range("2023-01-02", periods=3)
        instruments = ["A", "B", "C", "D"]
        # date 1: only 1 valid (< 3) — must be left as-is
        vals = [1.0, 2.0, 3.0, 4.0,
                100.0, np.nan, np.nan, np.nan,
                1.0, 2.0, 3.0, 4.0]
        df = _make_factor(dates, instruments, vals)
        result = preprocessor.clean_factor_values(df)
        assert result.loc[(dates[1], "A"), "factor"] == pytest.approx(100.0)

    def test_inf_replaced_with_nan(self, preprocessor):
        dates = pd.bdate_range("2023-01-02", periods=2)
        instruments = [f"S{i}" for i in range(10)]
        vals = np.random.randn(20)
        vals[5] = np.inf
        vals[12] = -np.inf
        df = _make_factor(dates, instruments, vals)
        result = preprocessor.clean_factor_values(df)
        assert result["factor"].isna().sum() >= 2

    def test_mad_zero_does_not_crash(self, preprocessor):
        """Constant cross-section (MAD=0) must not crash."""
        dates = pd.bdate_range("2023-01-02", periods=2)
        instruments = [f"S{i}" for i in range(10)]
        vals = [5.0] * 10 + list(np.random.randn(10))
        df = _make_factor(dates, instruments, vals)
        assert preprocessor.clean_factor_values(df) is not None

    def test_output_approximately_zscore(self, preprocessor):
        """After cleaning, values per date should be ~zero-mean unit-variance."""
        dates = pd.bdate_range("2023-01-02", periods=10)
        instruments = [f"S{i:03d}" for i in range(100)]
        np.random.seed(42)
        vals = np.random.randn(len(dates) * len(instruments))
        df = _make_factor(dates, instruments, vals)
        result = preprocessor.clean_factor_values(df)
        for dt in dates:
            day_vals = result.xs(dt, level="datetime")["factor"].dropna()
            if len(day_vals) >= 3:
                assert abs(day_vals.mean()) < 0.1
                assert abs(day_vals.std() - 1.0) < 0.15

    def test_vectorized_matches_legacy(self, preprocessor):
        """Vectorized output must match _clean_factor_values_legacy on same input."""
        dates = pd.bdate_range("2023-01-02", periods=30)
        instruments = [f"S{i:03d}" for i in range(60)]
        np.random.seed(7)
        vals = np.random.randn(len(dates) * len(instruments))
        vals[10] = 50.0
        vals[200] = np.nan
        vals[500] = -30.0
        df = _make_factor(dates, instruments, vals)
        new_result = preprocessor.clean_factor_values(df)
        old_result = preprocessor._clean_factor_values_legacy(df)
        pd.testing.assert_frame_equal(
            new_result.dropna(), old_result.dropna(), check_exact=False, atol=1e-6,
        )
```

- [ ] **Step 1.2: Run — confirm failure**

```bash
cd /Users/xinzhan/.openclaw/workspace/quant_factor_system
pytest tests/mining/test_preprocessing_vec.py::TestCleanFactorValuesVectorized -v
```

Expected: ERROR — `_clean_factor_values_legacy` does not exist.

- [ ] **Step 1.3: Rename old method + add vectorized version**

In `src/mining/preprocessing.py`:

**a)** Rename the existing `clean_factor_values` to `_clean_factor_values_legacy` (move the entire existing body verbatim, update the docstring to say "Legacy").

**b)** Add the new `clean_factor_values`:

```python
def clean_factor_values(self, factor: pd.DataFrame) -> pd.DataFrame:
    """Clean raw factor values: inf->NaN, winsorize, standardize.

    Vectorized via pandas groupby chains (no Python callback).
    Falls back to legacy for standardize_method='rank' (non-default).
    Dates with fewer than 3 valid values are left unchanged.
    """
    result = factor.copy()
    col = result.columns[0]

    if self.config.standardize_method == "rank":
        return self._clean_factor_values_legacy(factor)

    # Step 1: inf → NaN
    result[col] = result[col].replace([np.inf, -np.inf], np.nan)

    # Per-date valid count — guard for sparse dates
    n_valid = result.groupby(level="datetime")[col].transform("count")

    if self.config.winsorize_method == "mad":
        med = result.groupby(level="datetime")[col].transform("median")
        mad = (result[col] - med).abs().groupby(level="datetime").transform("median") * 1.4826
        mad = mad.replace(0, np.nan)
        lo = med - self.config.winsorize_n * mad
        hi = med + self.config.winsorize_n * mad
        clipped = result[col].clip(lo, hi)
        result[col] = result[col].where(n_valid < 3, clipped)
    else:  # sigma
        mean_w = result.groupby(level="datetime")[col].transform("mean")
        std_w = result.groupby(level="datetime")[col].transform("std").replace(0, np.nan)
        lo = mean_w - self.config.winsorize_n * std_w
        hi = mean_w + self.config.winsorize_n * std_w
        clipped = result[col].clip(lo, hi)
        result[col] = result[col].where(n_valid < 3, clipped)

    # zscore standardize — vectorized
    mean_z = result.groupby(level="datetime")[col].transform("mean")
    std_z = result.groupby(level="datetime")[col].transform("std").replace(0, np.nan)
    zscored = (result[col] - mean_z) / std_z
    result[col] = result[col].where(n_valid < 3, zscored)
    return result
```

- [ ] **Step 1.4: Run — confirm pass**

```bash
pytest tests/mining/test_preprocessing_vec.py::TestCleanFactorValuesVectorized -v
pytest tests/mining/test_evaluator.py -v
```

Expected: all PASS.

- [ ] **Step 1.5: Commit**

```bash
git add src/mining/preprocessing.py tests/mining/test_preprocessing_vec.py
git commit -m "perf: vectorize clean_factor_values — eliminate Python groupby callback"
```

---

## Task 2: Vectorize `neutralize` + update `preprocess_for_ic`

**Files:**
- Modify: `src/mining/preprocessing.py` — `neutralize`, `preprocess_for_ic`, add `clean_factor`
- Test: `tests/mining/test_preprocessing_vec.py` (add class)

### Background

`neutralize` with `market_cap` mode loops ~1250 dates in Python. The batched path uses einsum over a pre-pivoted `log_mcap_wide` numpy array.

**Interface changes in this task:**
1. `neutralize` gains `log_mcap_wide` and `log_mcap_wide_columns` optional kwargs.
2. `preprocess_for_ic` gains the same two kwargs and threads them to `neutralize`.
3. New public method `clean_factor(factor, **aux_data) -> pd.DataFrame` runs clean_factor_values + neutralize only (no returns masking). This is used by the cache layer in Task 4.

The `industry` and `both` modes keep the existing per-date loop — not the default, not a bottleneck.

- [ ] **Step 2.1: Add failing tests**

Append to `tests/mining/test_preprocessing_vec.py`:

```python
class TestNeutralizeVectorized:

    @pytest.fixture
    def mcap_config(self):
        return MiningConfig(
            winsorize_method="mad", winsorize_n=5.0, standardize_method="zscore",
            neutralize_mode="market_cap", filter_suspend=False, filter_limit=False,
        )

    @pytest.fixture
    def mcap_preprocessor(self, mcap_config):
        return FactorPreprocessor(mcap_config)

    def _make_mcap(self, dates, instruments):
        idx = pd.MultiIndex.from_product(
            [dates, instruments], names=["datetime", "instrument"]
        )
        np.random.seed(1)
        return pd.DataFrame(
            {"$market_cap": np.random.uniform(1e9, 1e12, len(idx))}, index=idx
        )

    def _build_log_mcap_wide(self, mcap_df, factor_dates):
        """Simulate what _load_aux_data will produce."""
        mcap_wide_df = (
            mcap_df["$market_cap"]
            .unstack("instrument")
            .reindex(factor_dates)  # align to factor dates
            .clip(lower=1.0)
            .ffill()
        )
        return (
            np.log(mcap_wide_df.values),
            mcap_wide_df.columns.tolist(),
            mcap_wide_df.index.tolist(),   # date index stored alongside
        )

    def test_batched_matches_legacy(self, mcap_preprocessor):
        """Batched einsum OLS residuals must match per-date loop on same input."""
        dates = pd.bdate_range("2023-01-02", periods=30)
        instruments = [f"S{i:03d}" for i in range(80)]
        np.random.seed(42)
        vals = np.random.randn(len(dates) * len(instruments))
        df = _make_factor(dates, instruments, vals)
        mcap_df = self._make_mcap(dates, instruments)
        log_mcap_wide, log_mcap_cols, log_mcap_dates = self._build_log_mcap_wide(mcap_df, dates)

        result_vec = mcap_preprocessor.neutralize(
            df.copy(), market_cap=mcap_df,
            log_mcap_wide=log_mcap_wide,
            log_mcap_wide_columns=log_mcap_cols,
            log_mcap_wide_dates=log_mcap_dates,
        )
        result_legacy = mcap_preprocessor.neutralize(df.copy(), market_cap=mcap_df)

        pd.testing.assert_frame_equal(
            result_vec.dropna(), result_legacy.dropna(), check_exact=False, atol=1e-5,
        )

    def test_sparse_date_guard_preserved(self, mcap_preprocessor):
        """Dates with < 10 valid stocks must NOT be residualized."""
        dates = pd.bdate_range("2023-01-02", periods=3)
        instruments = [f"S{i:03d}" for i in range(20)]
        np.random.seed(5)
        vals = np.random.randn(len(dates) * len(instruments))
        # date 1: leave only 5 valid
        vals[20:35] = np.nan
        df = _make_factor(dates, instruments, vals)
        mcap_df = self._make_mcap(dates, instruments)
        log_mcap_wide, log_mcap_cols, log_mcap_dates = self._build_log_mcap_wide(mcap_df, dates)

        result = mcap_preprocessor.neutralize(
            df.copy(), market_cap=mcap_df,
            log_mcap_wide=log_mcap_wide,
            log_mcap_wide_columns=log_mcap_cols,
            log_mcap_wide_dates=log_mcap_dates,
        )
        date1 = dates[1]
        original = df.xs(date1, level="datetime")["factor"]
        result_day = result.xs(date1, level="datetime")[result.columns[0]]
        pd.testing.assert_series_equal(
            original.dropna(), result_day.dropna(), check_exact=False, atol=1e-10,
        )

    def test_fallback_without_log_mcap_wide(self, mcap_preprocessor):
        """Without log_mcap_wide, must fall back to legacy path."""
        dates = pd.bdate_range("2023-01-02", periods=5)
        instruments = [f"S{i:03d}" for i in range(20)]
        np.random.seed(3)
        vals = np.random.randn(len(dates) * len(instruments))
        df = _make_factor(dates, instruments, vals)
        mcap_df = self._make_mcap(dates, instruments)
        result = mcap_preprocessor.neutralize(df.copy(), market_cap=mcap_df)
        assert result.shape == df.shape

    def test_preprocess_for_ic_threads_log_mcap_wide(self, mcap_preprocessor):
        """preprocess_for_ic must accept and thread log_mcap_wide to neutralize."""
        dates = pd.bdate_range("2023-01-02", periods=5)
        instruments = [f"S{i:03d}" for i in range(20)]
        np.random.seed(9)
        factor = _make_factor(dates, instruments, np.random.randn(len(dates) * len(instruments)))
        returns = _make_factor(dates, instruments,
                               np.random.randn(len(dates) * len(instruments)), col="ret")
        mcap_df = self._make_mcap(dates, instruments)
        log_mcap_wide, log_mcap_cols, log_mcap_dates = self._build_log_mcap_wide(mcap_df, dates)

        # Must not raise TypeError
        cleaned, masked = mcap_preprocessor.preprocess_for_ic(
            factor=factor, returns=returns, market_cap=mcap_df,
            log_mcap_wide=log_mcap_wide,
            log_mcap_wide_columns=log_mcap_cols,
            log_mcap_wide_dates=log_mcap_dates,
        )
        assert cleaned.shape == factor.shape
```

- [ ] **Step 2.2: Run — confirm failure**

```bash
pytest tests/mining/test_preprocessing_vec.py::TestNeutralizeVectorized -v
```

Expected: FAIL — `neutralize` and `preprocess_for_ic` don't accept the new kwargs.

- [ ] **Step 2.3: Update `neutralize` signature + add batched path**

In `src/mining/preprocessing.py`, update `neutralize` signature:

```python
def neutralize(
    self,
    factor: pd.DataFrame,
    market_cap: Optional[pd.DataFrame] = None,
    industry: Optional[pd.DataFrame] = None,
    log_mcap_wide: Optional["np.ndarray"] = None,
    log_mcap_wide_columns: Optional[list] = None,
    log_mcap_wide_dates: Optional[list] = None,
) -> pd.DataFrame:
    """Neutralize factor for market cap and/or industry exposure.

    Fast path: batched einsum OLS when log_mcap_wide is provided and
    neutralize_mode == 'market_cap'. Otherwise uses per-date loop.
    """
    if self.config.neutralize_mode == "none":
        return factor

    # Fast batched path for market_cap-only mode
    if (self.config.neutralize_mode == "market_cap"
            and log_mcap_wide is not None
            and log_mcap_wide_columns is not None):
        return self._neutralize_mcap_batched(
            factor, log_mcap_wide, log_mcap_wide_columns,
            log_mcap_wide_dates or [],
        )

    # ... existing per-date loop code unchanged below ...
```

Add private method `_neutralize_mcap_batched` **immediately before** the `neutralize` method:

```python
def _neutralize_mcap_batched(
    self,
    factor: pd.DataFrame,
    log_mcap_wide: "np.ndarray",
    log_mcap_wide_columns: list,
    log_mcap_wide_dates: list,
) -> pd.DataFrame:
    """Batched OLS neutralization for market_cap mode (vectorized via einsum).

    log_mcap_wide: (n_mcap_dates, n_stocks) numpy array, pre-computed by _load_aux_data.
    log_mcap_wide_columns: stock identifiers for axis=1 of log_mcap_wide.
    log_mcap_wide_dates: datetime values for axis=0 of log_mcap_wide.

    Restores original values for dates with fewer than 10 valid stocks.
    """
    result = factor.copy()
    col = result.columns[0]

    # Pivot factor to (n_dates × n_stocks), aligning columns to log_mcap order
    factor_wide_df = result[col].unstack("instrument").reindex(
        columns=log_mcap_wide_columns
    )

    # Align log_mcap_wide rows to factor dates (date ranges may differ slightly)
    factor_dates = factor_wide_df.index.tolist()
    if log_mcap_wide_dates:
        mcap_date_index = {d: i for i, d in enumerate(log_mcap_wide_dates)}
        row_indices = [mcap_date_index[d] for d in factor_dates if d in mcap_date_index]
        aligned_dates = [d for d in factor_dates if d in mcap_date_index]
        if not aligned_dates:
            return factor  # no overlap — fall back unchanged
        log_mcap_aligned = log_mcap_wide[row_indices]          # (n_aligned, n_stocks)
        factor_wide_aligned = factor_wide_df.loc[aligned_dates].values.astype(float)
    else:
        # Assume same date order
        n = min(len(factor_dates), log_mcap_wide.shape[0])
        log_mcap_aligned = log_mcap_wide[:n]
        factor_wide_aligned = factor_wide_df.values[:n].astype(float)
        aligned_dates = factor_dates[:n]

    n_dates, n_stocks = factor_wide_aligned.shape

    # Valid mask: non-NaN in both factor and mcap
    valid = ~np.isnan(factor_wide_aligned) & ~np.isnan(log_mcap_aligned)
    n_valid_per_date = valid.sum(axis=1)

    # Build design matrix X: (n_dates, n_stocks, 2) = [ones, log_mcap]
    ones = np.ones((n_dates, n_stocks))
    X = np.stack([ones, log_mcap_aligned], axis=2)

    # Zero-out NaN positions so they don't corrupt einsum
    f_clean = np.where(valid, factor_wide_aligned, 0.0)
    X_clean = np.where(valid[:, :, None], X, 0.0)

    # Batched OLS: XTX[t] = sum_s X[t,s,:]^T X[t,s,:]
    XTX = np.einsum("tsi,tsj->tij", X_clean, X_clean)   # (n_dates, 2, 2)
    XTy = np.einsum("tsi,ts->ti", X_clean, f_clean)      # (n_dates, 2)

    # Solve for beta: shape (n_dates, 2)
    try:
        beta = np.linalg.solve(XTX, XTy)
    except np.linalg.LinAlgError:
        beta = np.zeros((n_dates, 2))
        for t in range(n_dates):
            try:
                b, _, _, _ = np.linalg.lstsq(XTX[t:t+1].T, XTy[t:t+1].T, rcond=None)
                beta[t] = b.ravel()
            except Exception:
                pass

    # Residuals: factor - X @ beta
    fitted = np.einsum("tsi,ti->ts", X, beta)
    residuals = factor_wide_aligned - fitted

    # Restore sparse dates (< 10 valid) AFTER residualization — do NOT overwrite with fit
    sparse = n_valid_per_date < 10
    residuals[sparse] = factor_wide_aligned[sparse]

    # Restore NaN positions
    residuals = np.where(valid, residuals, np.nan)

    # Write back: re-stack into original MultiIndex
    residuals_df = pd.DataFrame(
        residuals,
        index=pd.Index(aligned_dates, name="datetime"),
        columns=pd.Index(log_mcap_wide_columns, name="instrument"),
    )
    residuals_stacked = residuals_df.stack(dropna=False)
    residuals_stacked.index.names = ["datetime", "instrument"]
    result[col] = residuals_stacked.reindex(result.index)
    return result
```

- [ ] **Step 2.4: Update `preprocess_for_ic` signature to thread new kwargs**

In `src/mining/preprocessing.py`, update `preprocess_for_ic` to accept and pass through the new kwargs:

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
    log_mcap_wide: Optional["np.ndarray"] = None,
    log_mcap_wide_columns: Optional[list] = None,
    log_mcap_wide_dates: Optional[list] = None,
):
    # ... existing tradable mask + clean logic unchanged ...
    if self.config.neutralize_mode != "none":
        cleaned_factor = self.neutralize(
            cleaned_factor,
            market_cap=market_cap,
            industry=industry,
            log_mcap_wide=log_mcap_wide,
            log_mcap_wide_columns=log_mcap_wide_columns,
            log_mcap_wide_dates=log_mcap_wide_dates,
        )
    # ... rest unchanged ...
```

- [ ] **Step 2.5: Add `clean_factor` method** (used by Task 4 cache)

```python
def clean_factor(
    self,
    factor: pd.DataFrame,
    market_cap: Optional[pd.DataFrame] = None,
    industry: Optional[pd.DataFrame] = None,
    log_mcap_wide: Optional["np.ndarray"] = None,
    log_mcap_wide_columns: Optional[list] = None,
    log_mcap_wide_dates: Optional[list] = None,
) -> pd.DataFrame:
    """Run clean_factor_values + neutralize only (no returns masking).

    Used by the preprocessing cache layer in FactorMiningEvaluator.
    Returns the cleaned + neutralized factor DataFrame.
    """
    cleaned = self.clean_factor_values(factor)
    if self.config.neutralize_mode != "none":
        cleaned = self.neutralize(
            cleaned,
            market_cap=market_cap,
            industry=industry,
            log_mcap_wide=log_mcap_wide,
            log_mcap_wide_columns=log_mcap_wide_columns,
            log_mcap_wide_dates=log_mcap_wide_dates,
        )
    return cleaned
```

- [ ] **Step 2.6: Run — confirm pass**

```bash
pytest tests/mining/test_preprocessing_vec.py -v
pytest tests/mining/ -v
```

Expected: all PASS.

- [ ] **Step 2.7: Commit**

```bash
git add src/mining/preprocessing.py tests/mining/test_preprocessing_vec.py
git commit -m "perf: vectorize neutralize market_cap mode; add clean_factor method; thread log_mcap_wide through preprocess_for_ic"
```

---

## Task 3: Vectorize `_compute_lib_corrs_sampled`

**Files:**
- Modify: `src/mining/evaluator.py:497-570`
- Test: `tests/mining/test_evaluator.py` (add class)

### Background

The inner `for _, grp in merged.groupby("time"):` loop runs ~60 times per library factor. `daily_cross_sectional_ic` in `core/factor_stats.py` computes the same Spearman IC without any date loop. We replace the inner loop with a single vectorized call per library factor.

Note on semantics: `daily_cross_sectional_ic(factor_df, returns_df, ...)` is designed for (factor, returns) but accepts any two `[time, symbol, value]` DataFrames and computes their Pearson-of-ranks correlation — which is exactly Spearman rank correlation between two factor series. This is mathematically correct for the correlation check use case.

The old code had a `len(merged) < 30` total-row guard. The new `min_obs=10` is a per-date guard — these are not equivalent but the behavioral difference only affects edge cases with very sparse data (< 30 total rows). This is acceptable since the Probe phase already validated the factor has data.

- [ ] **Step 3.1: Add test**

In `tests/mining/test_evaluator.py`, add:

```python
class TestCorrelationSampledVectorized:
    """Verify _compute_lib_corrs_sampled vectorized path matches old inner-loop result."""

    def _make_flat(self, dates, instruments, seed=0):
        np.random.seed(seed)
        rows = [{"time": d, "symbol": inst, "value": np.random.randn()}
                for d in dates for inst in instruments]
        return pd.DataFrame(rows)

    def test_vectorized_matches_per_date_loop(self, evaluator):
        """New path must produce correlation within 1e-6 of old inner-loop."""
        from core.factor_stats import daily_cross_sectional_ic as _vec_ic
        dates = pd.bdate_range("2024-01-02", periods=20)
        instruments = [f"S{i:03d}" for i in range(40)]

        cand = self._make_flat(dates, instruments, seed=1)
        lib_f = self._make_flat(dates, instruments, seed=2)

        # Old inner-loop computation
        merged = cand.merge(lib_f, on=["time", "symbol"], suffixes=("_c", "_l"))
        old_daily = []
        for _, grp in merged.groupby("time"):
            if len(grp) < 10:
                continue
            rc = grp["value_c"].rank()
            rl = grp["value_l"].rank()
            if rc.std() > 1e-9 and rl.std() > 1e-9:
                old_daily.append(rc.corr(rl))
        old_corr = abs(float(np.nanmean(old_daily)))

        # New vectorized computation
        corr_series = _vec_ic(cand, lib_f, method="spearman", min_obs=10)
        new_corr = abs(float(corr_series.mean()))

        assert abs(new_corr - old_corr) < 1e-6, f"new={new_corr:.8f} old={old_corr:.8f}"
```

- [ ] **Step 3.2: Run — confirm pass** (validates approach before code change)

```bash
pytest tests/mining/test_evaluator.py::TestCorrelationSampledVectorized -v
```

Expected: PASS — confirms `daily_cross_sectional_ic` produces the same result.

- [ ] **Step 3.3: Replace inner loop in `_compute_lib_corrs_sampled`**

In `src/mining/evaluator.py`, at the top of the `_compute_lib_corrs_sampled` method add the import (or ensure it's already imported at module level):

```python
from core.factor_stats import daily_cross_sectional_ic as _vec_ic
```

Then replace the per-factor inner loop (old code with `for _, grp in merged.groupby("time"):`):

```python
# NEW — vectorized: one call to daily_cross_sectional_ic per lib factor
for fname in lib_factor_names:
    sub = lib_df[lib_df["factor_name"] == fname][["time", "symbol", "value"]]
    if sub.empty:
        continue
    corr_series = _vec_ic(cand, sub, method="spearman", min_obs=10)
    if not corr_series.empty:
        result[fname] = abs(float(corr_series.mean()))
```

- [ ] **Step 3.4: Run — confirm pass**

```bash
pytest tests/mining/test_evaluator.py -v
pytest tests/mining/ -v
```

Expected: all PASS.

- [ ] **Step 3.5: Commit**

```bash
git add src/mining/evaluator.py tests/mining/test_evaluator.py
git commit -m "perf: replace _compute_lib_corrs_sampled inner date loop with vectorized daily_cross_sectional_ic"
```

---

## Task 4: Cache Layer + Pre-Pivot `log_mcap_wide`

**Files:**
- Modify: `src/mining/evaluator.py` — `__init__`, `evaluate_batch`, `_load_aux_data`, `_compute_daily_ics`, `_correlation_check`, `_compute_report_cards`
- Test: `tests/mining/test_evaluator.py` (add class)

**Depends on:** Task 2 (requires `clean_factor()` method and updated `preprocess_for_ic` that accepts `log_mcap_wide` kwargs).

### Background

**Cache design:**
- Key: `sha256(f"{expr_or_code}_{IS_start}_{IS_end}".encode()).hexdigest()[:16]` — derived from the candidate expression and window, NOT from the values bytes. Fast to compute, collision-resistant.
- Value: cleaned + neutralized factor DataFrame (output of `preprocessor.clean_factor()`).
- Cache is populated by `_compute_daily_ics` when a `preproc_cache_key` hint is passed by callers.
- Returns masking is cheap and horizon-dependent — computed fresh each time, never cached.

**Pre-pivot:**
`_load_aux_data` computes `log_mcap_wide` (plus date index and column list) once and stores in `aux`. This flows to `preprocess_for_ic` → `neutralize` via `**aux_data`. The batched einsum path in `neutralize` uses it directly.

- [ ] **Step 4.1: Add failing tests**

In `tests/mining/test_evaluator.py`, add:

```python
import hashlib

class TestPreprocessingCache:

    def _make_multiindex_df(self, dates, instruments, seed=0, col="factor"):
        idx = pd.MultiIndex.from_product(
            [dates, instruments], names=["datetime", "instrument"]
        )
        np.random.seed(seed)
        return pd.DataFrame({col: np.random.randn(len(idx))}, index=idx)

    def _make_cache_key(self, expr, start, end):
        raw = f"{expr}_{start}_{end}".encode()
        return hashlib.sha256(raw).hexdigest()[:16]

    def test_cache_key_is_expression_based(self, evaluator):
        """Cache key must be derived from expression string, not values bytes."""
        key = evaluator._make_preproc_cache_key("Rank($close, 20)", "2020-01-01", "2024-12-31")
        expected = self._make_cache_key("Rank($close, 20)", "2020-01-01", "2024-12-31")
        assert key == expected

    def test_cache_miss_then_hit(self, evaluator):
        """Second _compute_daily_ics call with same key must use cached factor."""
        from unittest.mock import patch as mpatch
        dates = pd.bdate_range("2023-01-02", periods=10)
        instruments = [f"S{i:03d}" for i in range(30)]
        factor_df = self._make_multiindex_df(dates, instruments, seed=0)
        returns_df = self._make_multiindex_df(dates, instruments, seed=1, col="ret")

        call_count = [0]
        original_clean = evaluator._preprocessor.clean_factor

        def counting_clean(*args, **kwargs):
            call_count[0] += 1
            return original_clean(*args, **kwargs)

        evaluator._preprocessed_factor_cache.clear()
        with mpatch.object(evaluator._preprocessor, "clean_factor",
                           side_effect=counting_clean):
            cache_key = evaluator._make_preproc_cache_key(
                "test_expr", "2023-01-02", "2023-01-13"
            )
            evaluator._compute_daily_ics(
                factor_df, returns_df, preproc_cache_key=cache_key
            )
            assert call_count[0] == 1, "First call must invoke clean_factor once"
            evaluator._compute_daily_ics(
                factor_df, returns_df, preproc_cache_key=cache_key
            )
            assert call_count[0] == 1, "Second call must hit cache (no clean_factor call)"

    def test_cache_cleared_between_batches(self, evaluator):
        """evaluate_batch must clear _preprocessed_factor_cache at start."""
        from unittest.mock import patch as mpatch
        evaluator._preprocessed_factor_cache["stale_key"] = "stale_value"
        # Patch the internal stages so evaluate_batch can run with empty input
        with mpatch.object(evaluator, "_fast_ic_screening", return_value=[]):
            with mpatch.object(evaluator, "_correlation_check", return_value=([], [])):
                try:
                    evaluator.evaluate_batch([])
                except Exception:
                    pass
        assert "stale_key" not in evaluator._preprocessed_factor_cache

    def test_different_windows_separate_entries(self, evaluator):
        """IS and OOS windows must produce distinct cache keys."""
        key_is  = evaluator._make_preproc_cache_key("expr", "2020-01-01", "2024-12-31")
        key_oos = evaluator._make_preproc_cache_key("expr", "2024-01-01", "2024-12-31")
        assert key_is != key_oos

    def test_multi_horizon_reuses_cached_factor(self, evaluator):
        """Same factor with two different returns DataFrames must call clean_factor once."""
        from unittest.mock import patch as mpatch
        dates = pd.bdate_range("2023-01-02", periods=10)
        instruments = [f"S{i:03d}" for i in range(30)]
        factor_df = self._make_multiindex_df(dates, instruments, seed=0)
        returns_h1 = self._make_multiindex_df(dates, instruments, seed=1, col="ret")
        returns_h5 = self._make_multiindex_df(dates, instruments, seed=2, col="ret")

        call_count = [0]
        original_clean = evaluator._preprocessor.clean_factor

        def counting_clean(*args, **kwargs):
            call_count[0] += 1
            return original_clean(*args, **kwargs)

        evaluator._preprocessed_factor_cache.clear()
        cache_key = evaluator._make_preproc_cache_key("test_expr", "2023-01-02", "2023-01-13")

        with mpatch.object(evaluator._preprocessor, "clean_factor",
                           side_effect=counting_clean):
            # horizon 1
            evaluator._compute_daily_ics(
                factor_df, returns_h1, preproc_cache_key=cache_key
            )
            # horizon 5 — same factor, different returns
            evaluator._compute_daily_ics(
                factor_df, returns_h5, preproc_cache_key=cache_key
            )

        assert call_count[0] == 1, (
            "clean_factor must be called once even for multiple horizons with same factor"
        )
```

- [ ] **Step 4.2: Run — confirm failure**

```bash
pytest tests/mining/test_evaluator.py::TestPreprocessingCache -v
```

Expected: FAIL — `_preprocessed_factor_cache`, `_make_preproc_cache_key`, and `preproc_cache_key` parameter do not exist yet.

- [ ] **Step 4.3: Add cache fields to `__init__`**

In `src/mining/evaluator.py`, in `__init__` after the existing cache declarations:

```python
# Preprocessing cache: maps preproc_cache_key -> cleaned+neutralized factor DataFrame
# Valid only within one evaluate_batch() call; cleared at the start of each batch.
self._preprocessed_factor_cache: Dict[str, pd.DataFrame] = {}
```

- [ ] **Step 4.4: Add `_make_preproc_cache_key` helper**

Add as a method on `FactorMiningEvaluator`:

```python
@staticmethod
def _make_preproc_cache_key(expression_or_code: str, start: str, end: str) -> str:
    """Stable cache key for preprocessed factor values.

    Uses SHA-256 of (expression + IS_window) — fast, collision-resistant.
    Does NOT hash the values array (too large); uses expression identity instead.
    """
    import hashlib
    raw = f"{expression_or_code}_{start}_{end}".encode()
    return hashlib.sha256(raw).hexdigest()[:16]
```

- [ ] **Step 4.5: Clear cache in `evaluate_batch`**

In `evaluate_batch` (around line 893), after the existing `.clear()` calls:

```python
self._factor_cache.clear()
self._subset_factor_cache = {}
self._lib_values_cache = {}
self._preprocessed_factor_cache.clear()    # ← add
```

- [ ] **Step 4.6: Update `_compute_daily_ics` to use cache**

Replace `_compute_daily_ics` with the cache-aware version:

```python
def _compute_daily_ics(
    self, factor_values: pd.DataFrame, returns: pd.DataFrame,
    aux_data: Optional[Dict[str, pd.DataFrame]] = None,
    preproc_cache_key: Optional[str] = None,
) -> pd.Series:
    """Compute daily cross-sectional Spearman IC.

    When preproc_cache_key is provided, caches the cleaned+neutralized factor
    to avoid re-running clean_factor_values + neutralize for the same IS window
    across Stage 2 / Stage 3 / multi-horizon calls.
    """
    if aux_data:
        if preproc_cache_key and preproc_cache_key in self._preprocessed_factor_cache:
            # Cache hit: use stored cleaned factor; only compute returns mask (cheap)
            cleaned_factor = self._preprocessed_factor_cache[preproc_cache_key]
            tradable_mask = self._preprocessor.build_tradable_mask(
                volume=aux_data.get("volume"),
                close=aux_data.get("close"),
                limit_up=aux_data.get("limit_up"),
                limit_down=aux_data.get("limit_down"),
            )
            masked_returns = self._preprocessor.mask_returns(returns, tradable_mask)
        else:
            # Cache miss: run full clean+neutralize
            # Extract only the kwargs that preprocess_for_ic accepts
            preproc_kwargs = {
                k: aux_data[k] for k in (
                    "volume", "close", "limit_up", "limit_down",
                    "market_cap", "industry",
                    "log_mcap_wide", "log_mcap_wide_columns", "log_mcap_wide_dates",
                ) if k in aux_data
            }
            cleaned_factor, masked_returns = self._preprocessor.preprocess_for_ic(
                factor=factor_values, returns=returns, **preproc_kwargs,
            )
            if preproc_cache_key:
                self._preprocessed_factor_cache[preproc_cache_key] = cleaned_factor
        factor_values = cleaned_factor
        returns = masked_returns

    flat_factor = multiindex_to_flat(factor_values)
    flat_returns = multiindex_to_flat(returns)
    return _shared_daily_ic(flat_factor, flat_returns, method="spearman", min_obs=3)
```

- [ ] **Step 4.7: Pass cache key from `_correlation_check`**

In `_correlation_check`, in the per-candidate loop where `_compute_ic_from_frames` is called, thread the cache key. Since `_compute_ic_from_frames` calls `_compute_daily_ics`, update `_compute_ic_from_frames` to accept and forward the key:

```python
def _compute_ic_from_frames(
    self, factor_values: pd.DataFrame, returns: pd.DataFrame,
    aux_data: Optional[Dict[str, pd.DataFrame]] = None,
    preproc_cache_key: Optional[str] = None,
) -> Dict[str, Any]:
    daily_ics = self._compute_daily_ics(
        factor_values, returns, aux_data, preproc_cache_key=preproc_cache_key,
    )
    ...  # rest unchanged
```

In `_correlation_check`, where `full_ic` is computed per candidate:

```python
# Build cache key for this candidate's IS window
ckey_expr = c.get("expression") or c.get("code", "")
preproc_key = self._make_preproc_cache_key(
    ckey_expr, self.config.train_start, self.config.train_end
)
full_ic = self._compute_ic_from_frames(
    factor_vals, returns, aux_data=aux,
    preproc_cache_key=preproc_key,
)
```

In `_compute_stats_and_rc` (inside `_compute_report_cards`), thread the same key for Stage 3:

```python
ckey_expr = c.get("expression") or c.get("code", "")
preproc_key = self._make_preproc_cache_key(
    ckey_expr, self.config.train_start, self.config.train_end
)
# Pass preproc_key to _compute_daily_ics via _compute_ic_from_frames
daily_ics_is = self._compute_daily_ics(
    vals_is, returns_is, aux_data=aux_is, preproc_cache_key=preproc_key,
)
# Multi-horizon: same factor, different returns — cache hit after first call
for h, ret_h in returns_multi.items():
    if h != 1:
        daily_ics_by_horizon[h] = self._compute_daily_ics(
            vals_is, ret_h, aux_data=aux_is, preproc_cache_key=preproc_key,
        )
```

- [ ] **Step 4.8: Pre-pivot `log_mcap_wide` in `_load_aux_data`**

In `_load_aux_data`, after `aux["market_cap"] = mcap_df[["$market_cap"]]`:

```python
# Pre-pivot log_mcap_wide for vectorized neutralize (Task 2)
try:
    mcap_series = mcap_df["$market_cap"]
    mcap_wide_df = mcap_series.unstack("instrument").clip(lower=1.0).ffill()
    aux["log_mcap_wide"] = np.log(mcap_wide_df.values)
    aux["log_mcap_wide_columns"] = mcap_wide_df.columns.tolist()
    aux["log_mcap_wide_dates"] = mcap_wide_df.index.tolist()
except Exception as e:
    logger.debug("Could not pre-pivot log_mcap_wide: %s", e)
```

Also ensure `import numpy as np` is at the top (it already is — verify).

- [ ] **Step 4.9: Run — confirm pass**

```bash
pytest tests/mining/test_evaluator.py -v
pytest tests/mining/ -v
```

Expected: all PASS.

- [ ] **Step 4.10: Commit**

```bash
git add src/mining/evaluator.py tests/mining/test_evaluator.py
git commit -m "perf: add preprocessed factor cache + pre-pivot log_mcap_wide — Stage 3 IS preprocessing hits cache"
```

---

## Final Verification

- [ ] **Run full test suite**

```bash
pytest tests/ -v --tb=short 2>&1 | tail -40
```

Expected: 0 failures.

- [ ] **Smoke-test probe** (requires DB + Qlib to be running)

```bash
PYTHONPATH=src python3 -m mining probe "Std(\$close, 20)" --start 2024-01-01 --end 2024-12-31
```

Expected: IC value printed, no crash.

- [ ] **Final commit**

```bash
git add -A
git commit -m "perf: complete preprocessing vectorization + cache — ~5-8x batch speedup

- Vectorize clean_factor_values (no Python callback, 3-5x)
- Vectorize neutralize market_cap mode with batched einsum OLS (10-15x)
- Replace _compute_lib_corrs_sampled inner date loop (6-10x)
- Add preprocessed factor cache + pre-pivot log_mcap_wide"
```
