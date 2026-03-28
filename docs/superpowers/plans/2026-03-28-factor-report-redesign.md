# Factor Report Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign the factor report system around 7 decision questions, with upgraded analytics, new analysis dimensions, S-curve composite scoring, and updated Obsidian Markdown output.

**Architecture:** 6 analyzers (3 rewritten + 3 new) orchestrated by a rewritten `ReportDataBuilder`. Shared data preparation eliminates duplicated merge logic. Chart theme extracted to a shared module. Each analyzer is pure computation + figure generation, tested independently.

**Tech Stack:** Python 3, pandas, plotly, scipy (page_trend_test, ttest_1samp, spearmanr), psycopg2, pytest

**Spec:** `docs/superpowers/specs/2026-03-28-factor-report-redesign.md`

---

## File Structure

```
src/report/
├── __init__.py                    # MODIFY: update exports
├── builder.py                     # REWRITE: new orchestrator with 6 analyzers
├── scorer.py                      # REWRITE: 7-dim S-curve scoring
├── data_prep.py                   # CREATE: shared factor+price merge, future returns, IS/OOS split
├── analytics/
│   ├── __init__.py                # MODIFY: update exports
│   ├── ic.py                      # REWRITE: add Pearson, t-test, ICIR, MAD clip
│   ├── profit.py                  # CREATE: renamed + upgraded from groups.py
│   ├── conditional.py             # CREATE: market regime + volatility conditioning
│   ├── decay.py                   # MODIFY: absorb distribution, add 2d period, rebalance rec
│   ├── uniqueness.py              # CREATE: correlation matrix, incremental IC
│   ├── groups.py                  # DELETE: replaced by profit.py
│   └── distribution.py            # DELETE: absorbed into decay.py
├── charts/
│   ├── __init__.py                # CREATE
│   └── theme.py                   # CREATE: shared Plotly theme config
└── templates/
    └── factor_report.html.j2      # KEEP: deprecated but preserved

src/core/
└── metrics.py                     # MODIFY: add sortino_ratio, max_drawdown_duration

tests/report/
├── test_scorer.py                 # REWRITE: test 7-dim S-curve scoring
├── test_data_prep.py              # CREATE: test shared data prep
├── test_builder.py                # CREATE: integration test
├── analytics/
│   ├── test_ic.py                 # REWRITE: test new IC features
│   ├── test_profit.py             # CREATE: test ProfitAnalyzer
│   ├── test_conditional.py        # CREATE: test ConditionalAnalyzer
│   ├── test_decay.py              # CREATE: test upgraded DecayAnalyzer
│   └── test_uniqueness.py         # CREATE: test UniquenessAnalyzer

tests/core/
└── test_metrics.py                # MODIFY: add sortino + dd_duration tests
```

---

## Task 1: Foundation — Chart Theme + Data Preparation + New Metrics

**Files:**
- Create: `src/report/charts/__init__.py`
- Create: `src/report/charts/theme.py`
- Create: `src/report/data_prep.py`
- Modify: `src/core/metrics.py`
- Create: `tests/report/test_data_prep.py`
- Modify: `tests/core/test_metrics.py`

### 1.1 Chart Theme

- [ ] **Step 1: Create chart theme module**

```python
# src/report/charts/__init__.py
from .theme import apply_theme, COLORS

# src/report/charts/theme.py
"""Shared Plotly theme configuration for all report charts."""
from __future__ import annotations
import plotly.graph_objects as go
import plotly.io as pio

# Consistent color palette
COLORS = {
    "primary": "#636EFA",
    "secondary": "#EF553B",
    "positive": "#00CC96",
    "negative": "#EF553B",
    "neutral": "#AB63FA",
    "is_period": "#636EFA",
    "oos_period": "#EF553B",
    "quintile": ["#d62728", "#ff7f0e", "#bcbd22", "#2ca02c", "#1f77b4"],  # Q1(red)->Q5(blue)
    "long_short": "#9467bd",
}

# Standard chart dimensions
PNG_WIDTH = 900
PNG_HEIGHT = 400
PNG_SCALE = 2

def apply_theme(fig: go.Figure, title: str | None = None) -> go.Figure:
    """Apply consistent theme to a Plotly figure."""
    fig.update_layout(
        template="plotly_white",
        font=dict(size=12),
        title=dict(text=title, font=dict(size=14)) if title else None,
        margin=dict(l=60, r=30, t=40 if title else 20, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig
```

- [ ] **Step 2: Verify import works**

Run: `cd /Users/xinzhan/.openclaw/workspace/quant_factor_system && PYTHONPATH=src python3 -c "from report.charts import apply_theme, COLORS; print('OK')"`
Expected: `OK`

### 1.2 Data Preparation Module

- [ ] **Step 3: Write failing tests for data_prep**

```python
# tests/report/test_data_prep.py
"""Tests for shared data preparation utilities."""
import pandas as pd
import numpy as np
import pytest
from report.data_prep import merge_factor_price, split_is_oos


def _make_factor_df(n_dates=20, n_stocks=5):
    """Helper: create a flat factor DataFrame."""
    dates = pd.bdate_range("2023-01-01", periods=n_dates)
    rows = []
    for d in dates:
        for s in [f"S{i:03d}" for i in range(n_stocks)]:
            rows.append({"time": d, "symbol": s, "value": np.random.randn()})
    return pd.DataFrame(rows)


def _make_price_df(n_dates=20, n_stocks=5):
    """Helper: create a price DataFrame."""
    dates = pd.bdate_range("2023-01-01", periods=n_dates)
    rows = []
    for d in dates:
        for s in [f"S{i:03d}" for i in range(n_stocks)]:
            rows.append({"time": d, "symbol": s, "close": 10 + np.random.randn()})
    return pd.DataFrame(rows)


class TestMergeFactorPrice:
    def test_basic_merge(self):
        fdf = _make_factor_df()
        pdf = _make_price_df()
        merged = merge_factor_price(fdf, pdf)
        assert "value" in merged.columns
        assert "future_return" in merged.columns
        # NaN future_returns (last date) are dropped by merge_factor_price
        assert not merged["future_return"].isna().any()
        # Should have fewer rows than input (last date per stock dropped)
        assert len(merged) < len(fdf)

    def test_mad_clip(self):
        fdf = _make_factor_df(n_dates=50)
        pdf = _make_price_df(n_dates=50)
        # Inject extreme return
        pdf.loc[pdf.index[5], "close"] = 1000.0
        merged = merge_factor_price(fdf, pdf, clip_method="mad", clip_k=5)
        # Extreme returns should be clipped
        assert merged["future_return"].dropna().abs().max() < 1.0

    def test_fixed_clip(self):
        fdf = _make_factor_df(n_dates=50)
        pdf = _make_price_df(n_dates=50)
        merged = merge_factor_price(fdf, pdf, clip_method="fixed", clip_threshold=0.11)
        assert (merged["future_return"].dropna().abs() < 0.11).all()


class TestSplitIsOos:
    def test_split(self):
        fdf = _make_factor_df(n_dates=100)
        pdf = _make_price_df(n_dates=100)
        merged = merge_factor_price(fdf, pdf)
        split_date = merged["time"].quantile(0.7)
        is_df, oos_df = split_is_oos(merged, split_date)
        assert len(is_df) > 0
        assert len(oos_df) > 0
        assert is_df["time"].max() < oos_df["time"].min()
```

- [ ] **Step 4: Run tests to verify they fail**

Run: `cd /Users/xinzhan/.openclaw/workspace/quant_factor_system && PYTHONPATH=src python3 -m pytest tests/report/test_data_prep.py -v`
Expected: FAIL (module not found)

- [ ] **Step 5: Implement data_prep module**

```python
# src/report/data_prep.py
"""Shared data preparation for report analytics.

Centralizes factor+price merge logic, future return computation,
and IS/OOS splitting that was previously duplicated across analyzers.
"""
from __future__ import annotations
import numpy as np
import pandas as pd


def merge_factor_price(
    factor_df: pd.DataFrame,
    price_df: pd.DataFrame,
    clip_method: str = "mad",
    clip_k: float = 5.0,
    clip_threshold: float = 0.11,
) -> pd.DataFrame:
    """Merge factor values with price data and compute future returns.

    Args:
        factor_df: DataFrame with columns [time, symbol, value]
        price_df: DataFrame with columns [time, symbol, close]
        clip_method: "mad" for adaptive MAD-based clipping, "fixed" for fixed threshold
        clip_k: MAD multiplier (only used when clip_method="mad")
        clip_threshold: Fixed threshold (only used when clip_method="fixed")

    Returns:
        DataFrame with columns [time, symbol, value, future_return] where
        future_return is the 1-day forward return, clipped per clip_method.
    """
    price = price_df.copy()
    price = price.sort_values(["symbol", "time"])
    price["future_return"] = price.groupby("symbol")["close"].pct_change().shift(-1)

    merged = factor_df.merge(
        price[["time", "symbol", "future_return"]],
        on=["time", "symbol"],
        how="inner",
    )
    merged = merged.dropna(subset=["value", "future_return"])

    # Clip extreme returns
    if clip_method == "mad":
        ret = merged["future_return"]
        med = ret.median()
        mad = np.median(np.abs(ret - med))
        if mad > 0:
            lower = med - clip_k * mad
            upper = med + clip_k * mad
            merged = merged[(ret >= lower) & (ret <= upper)].copy()
    elif clip_method == "fixed":
        merged = merged[merged["future_return"].abs() < clip_threshold].copy()

    return merged.reset_index(drop=True)


def split_is_oos(
    merged_df: pd.DataFrame,
    split_date,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split merged data into in-sample and out-of-sample periods.

    Args:
        merged_df: Output of merge_factor_price
        split_date: Cutoff date (IS < split_date, OOS >= split_date)

    Returns:
        (is_df, oos_df) tuple
    """
    split_date = pd.Timestamp(split_date)
    is_df = merged_df[merged_df["time"] < split_date].copy()
    oos_df = merged_df[merged_df["time"] >= split_date].copy()
    return is_df, oos_df
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd /Users/xinzhan/.openclaw/workspace/quant_factor_system && PYTHONPATH=src python3 -m pytest tests/report/test_data_prep.py -v`
Expected: All PASS

### 1.3 New Core Metrics

- [ ] **Step 7: Write failing tests for new metrics**

Add to `tests/core/test_metrics.py`:

```python
from core.metrics import sortino_ratio, max_drawdown_duration


class TestSortinoRatio:
    def test_all_positive_returns(self):
        daily = pd.Series([0.01, 0.02, 0.01, 0.005, 0.015])
        result = sortino_ratio(daily)
        assert result > 0
        # Sortino should be higher than Sharpe when all returns positive (downside vol < total vol)

    def test_with_negative_returns(self):
        daily = pd.Series([0.01, -0.02, 0.03, -0.01, 0.02])
        result = sortino_ratio(daily)
        assert isinstance(result, float)

    def test_no_negative_returns(self):
        daily = pd.Series([0.01, 0.02, 0.03])
        result = sortino_ratio(daily)
        assert result == float("inf") or result > 100  # No downside deviation


class TestMaxDrawdownDuration:
    def test_basic_drawdown(self):
        cumulative = pd.Series([1.0, 1.1, 1.05, 0.9, 0.95, 1.0, 1.1])
        duration = max_drawdown_duration(cumulative)
        assert duration > 0
        assert isinstance(duration, int)

    def test_no_drawdown(self):
        cumulative = pd.Series([1.0, 1.1, 1.2, 1.3])
        duration = max_drawdown_duration(cumulative)
        assert duration == 0

    def test_unrecovered_drawdown(self):
        cumulative = pd.Series([1.0, 1.1, 0.9, 0.85, 0.9])
        duration = max_drawdown_duration(cumulative)
        # Duration counts from peak to end since no recovery
        assert duration >= 3
```

- [ ] **Step 8: Run tests to verify they fail**

Run: `cd /Users/xinzhan/.openclaw/workspace/quant_factor_system && PYTHONPATH=src python3 -m pytest tests/core/test_metrics.py::TestSortinoRatio -v`
Expected: FAIL (import error)

- [ ] **Step 9: Implement sortino_ratio and max_drawdown_duration**

Add to `src/core/metrics.py`:

```python
def sortino_ratio(daily_returns: pd.Series) -> float:
    """Sortino ratio: annualized return / annualized downside deviation."""
    ann_ret = annualize_return(daily_returns)
    negative_returns = daily_returns[daily_returns < 0]
    if len(negative_returns) == 0:
        return float("inf")
    downside_std = negative_returns.std() * np.sqrt(TRADING_DAYS_PER_YEAR)
    if downside_std == 0:
        return float("inf")
    return ann_ret / downside_std


def max_drawdown_duration(cumulative: pd.Series) -> int:
    """Number of trading days in the longest drawdown (peak to recovery or end)."""
    if len(cumulative) < 2:
        return 0
    running_max = cumulative.cummax()
    in_drawdown = cumulative < running_max
    if not in_drawdown.any():
        return 0
    # Find consecutive drawdown periods
    groups = (~in_drawdown).cumsum()
    dd_groups = groups[in_drawdown]
    if len(dd_groups) == 0:
        return 0
    return int(dd_groups.value_counts().max())
```

- [ ] **Step 10: Run tests to verify they pass**

Run: `cd /Users/xinzhan/.openclaw/workspace/quant_factor_system && PYTHONPATH=src python3 -m pytest tests/core/test_metrics.py -v`
Expected: All PASS

- [ ] **Step 11: Commit foundation**

```bash
git add src/report/charts/ src/report/data_prep.py src/core/metrics.py tests/report/test_data_prep.py tests/core/test_metrics.py
git commit -m "feat(report): add chart theme, data prep, sortino + DD duration metrics"
```

---

## Task 2: Rewrite ICAnalyzer

**Files:**
- Rewrite: `src/report/analytics/ic.py`
- Rewrite: `tests/report/analytics/test_ic.py`

### 2.1 Tests

- [ ] **Step 1: Write failing tests**

```python
# tests/report/analytics/test_ic.py
"""Tests for ICAnalyzer — predictive power analysis."""
import pandas as pd
import numpy as np
import pytest
from report.analytics.ic import ICAnalyzer
from report.data_prep import merge_factor_price


def _make_data(n_dates=100, n_stocks=50, signal_strength=0.05):
    """Create synthetic factor+price data with known IC."""
    np.random.seed(42)
    dates = pd.bdate_range("2023-01-01", periods=n_dates)
    factor_rows, price_rows = [], []
    for d in dates:
        for s in [f"S{i:03d}" for i in range(n_stocks)]:
            fv = np.random.randn()
            # Price has slight correlation with factor (creates positive IC)
            close = 10 + signal_strength * fv + np.random.randn() * 0.5
            factor_rows.append({"time": d, "symbol": s, "value": fv})
            price_rows.append({"time": d, "symbol": s, "close": close})
    return pd.DataFrame(factor_rows), pd.DataFrame(price_rows)


class TestICAnalyzerCompute:
    def test_returns_both_rank_and_pearson(self):
        fdf, pdf = _make_data()
        merged = merge_factor_price(fdf, pdf)
        analyzer = ICAnalyzer()
        result = analyzer.compute(merged, split_date="2023-04-01")
        assert "rank_ic" in result  # Spearman
        assert "pearson_ic" in result
        assert "summary" in result
        assert "is" in result["summary"]
        assert "oos" in result["summary"]

    def test_summary_has_required_fields(self):
        fdf, pdf = _make_data()
        merged = merge_factor_price(fdf, pdf)
        analyzer = ICAnalyzer()
        result = analyzer.compute(merged, split_date="2023-04-01")
        for period in ["is", "oos"]:
            s = result["summary"][period]
            assert "rank_ic_mean" in s
            assert "rank_ic_std" in s
            assert "ic_mean" in s  # Pearson
            assert "icir" in s
            assert "win_rate" in s
            assert "significant_rate" in s
            assert "t_stat" in s
            assert "p_value" in s

    def test_positive_signal_has_positive_ic(self):
        fdf, pdf = _make_data(n_dates=200, signal_strength=0.1)
        merged = merge_factor_price(fdf, pdf)
        analyzer = ICAnalyzer()
        result = analyzer.compute(merged, split_date="2023-07-01")
        # With positive signal, rank IC should be positive
        assert result["summary"]["is"]["rank_ic_mean"] > 0

    def test_annual_breakdown(self):
        fdf, pdf = _make_data(n_dates=200)
        merged = merge_factor_price(fdf, pdf)
        analyzer = ICAnalyzer()
        result = analyzer.compute(merged, split_date="2023-07-01")
        assert "annual" in result
        assert len(result["annual"]) > 0
        assert "year" in result["annual"][0]
        assert "rank_ic" in result["annual"][0]

    def test_monthly_heatmap(self):
        fdf, pdf = _make_data(n_dates=200)
        merged = merge_factor_price(fdf, pdf)
        analyzer = ICAnalyzer()
        result = analyzer.compute(merged, split_date="2023-07-01")
        assert "monthly_heatmap_data" in result
        # Each entry: [year, month, ic]
        if len(result["monthly_heatmap_data"]) > 0:
            assert len(result["monthly_heatmap_data"][0]) == 3


class TestICAnalyzerCharts:
    def test_all_charts_generated(self):
        fdf, pdf = _make_data()
        merged = merge_factor_price(fdf, pdf)
        analyzer = ICAnalyzer()
        result = analyzer.compute(merged, split_date="2023-04-01")
        charts = analyzer.generate_charts(result)
        expected = ["ic_timeseries", "ic_distribution", "rolling_ic", "cumulative_ic", "monthly_heatmap"]
        for name in expected:
            assert name in charts, f"Missing chart: {name}"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/xinzhan/.openclaw/workspace/quant_factor_system && PYTHONPATH=src python3 -m pytest tests/report/analytics/test_ic.py -v`
Expected: FAIL

- [ ] **Step 3: Rewrite ICAnalyzer implementation**

Rewrite `src/report/analytics/ic.py`. Key changes from current:
- New `compute(merged_df, split_date)` interface — takes pre-merged data (from `data_prep.merge_factor_price`) instead of raw factor+price DFs
- Computes both Spearman (RankIC) and Pearson IC
- Adds t-test via `scipy.stats.ttest_1samp(daily_ic_series, 0)`
- ICIR computed separately for IS and OOS
- Removes `_REGIME_LOOKUP` hardcoded dict (regimes now come from ConditionalAnalyzer)
- New `generate_charts(result)` method returns dict of chart_name → go.Figure
- Uses `report.charts.theme.apply_theme` for all figures
- Keeps backward-compatible `compute_ic(factor_df, price_df, split_date)` wrapper for `dashboard/pages/Factors.py`

Core computation:
```python
def compute(self, merged_df: pd.DataFrame, split_date) -> dict:
    """Compute IC analysis on pre-merged data.

    Args:
        merged_df: Output of data_prep.merge_factor_price with [time, symbol, value, future_return]
        split_date: IS/OOS cutoff date

    Returns:
        dict with keys: summary, rank_ic, pearson_ic, daily_rank_ic, daily_pearson_ic,
                        annual, monthly_heatmap_data
    """
```

Daily IC computation (per-date cross-sectional correlation):
```python
from scipy.stats import spearmanr, pearsonr, ttest_1samp

def _compute_daily_ic(grouped, method="spearman"):
    results = []
    for date, group in grouped:
        if len(group) < 30:  # minimum stocks for meaningful correlation
            continue
        if method == "spearman":
            corr, _ = spearmanr(group["value"], group["future_return"])
        else:
            corr, _ = pearsonr(group["value"], group["future_return"])
        results.append({"date": date, "ic": corr})
    return pd.DataFrame(results)
```

Summary computation:
```python
def _compute_summary(daily_ic_df):
    ic = daily_ic_df["ic"].dropna()
    t_stat, p_value = ttest_1samp(ic, 0) if len(ic) > 1 else (0, 1)
    return {
        "rank_ic_mean": float(ic.mean()),  # or ic_mean for Pearson
        "rank_ic_std": float(ic.std()),
        "icir": float(ic.mean() / ic.std()) if ic.std() > 0 else 0,
        "win_rate": float((ic > 0).mean()),
        "significant_rate": float((ic.abs() > 0.02).mean()),
        "t_stat": float(t_stat),
        "p_value": float(p_value),
        "n_days": len(ic),
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/xinzhan/.openclaw/workspace/quant_factor_system && PYTHONPATH=src python3 -m pytest tests/report/analytics/test_ic.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/report/analytics/ic.py tests/report/analytics/test_ic.py
git commit -m "feat(report): rewrite ICAnalyzer with Pearson IC, t-test, ICIR breakdown"
```

---

## Task 3: Create ProfitAnalyzer (upgrade from GroupReturnsAnalyzer)

**Files:**
- Create: `src/report/analytics/profit.py`
- Create: `tests/report/analytics/test_profit.py`
- Keep: `src/report/analytics/groups.py` (will be removed in Task 8 integration)

### 3.1 Tests

- [ ] **Step 1: Write failing tests**

```python
# tests/report/analytics/test_profit.py
"""Tests for ProfitAnalyzer — profitability analysis."""
import pandas as pd
import numpy as np
import pytest
from report.analytics.profit import ProfitAnalyzer
from report.data_prep import merge_factor_price


def _make_data(n_dates=200, n_stocks=50, signal_strength=0.05):
    np.random.seed(42)
    dates = pd.bdate_range("2023-01-01", periods=n_dates)
    factor_rows, price_rows = [], []
    for d in dates:
        for s in [f"S{i:03d}" for i in range(n_stocks)]:
            fv = np.random.randn()
            close = 10 + signal_strength * fv + np.random.randn() * 0.3
            factor_rows.append({"time": d, "symbol": s, "value": fv})
            price_rows.append({"time": d, "symbol": s, "close": abs(close)})
    return pd.DataFrame(factor_rows), pd.DataFrame(price_rows)


class TestProfitAnalyzerCompute:
    def test_returns_required_keys(self):
        fdf, pdf = _make_data()
        merged = merge_factor_price(fdf, pdf)
        analyzer = ProfitAnalyzer()
        result = analyzer.compute(merged, split_date="2023-07-01")
        assert "stats" in result  # list of per-group stats
        assert "ls_stats" in result  # long-short stats
        assert "monotonicity" in result
        assert "page_test_pvalue" in result
        assert "annual_group_returns" in result

    def test_stats_has_new_metrics(self):
        fdf, pdf = _make_data()
        merged = merge_factor_price(fdf, pdf)
        analyzer = ProfitAnalyzer()
        result = analyzer.compute(merged, split_date="2023-07-01")
        q1 = result["stats"][0]
        assert "sortino" in q1
        assert "calmar" in q1
        assert "max_dd_duration" in q1

    def test_five_groups(self):
        fdf, pdf = _make_data()
        merged = merge_factor_price(fdf, pdf)
        analyzer = ProfitAnalyzer()
        result = analyzer.compute(merged, split_date="2023-07-01")
        assert len(result["stats"]) == 5

    def test_page_trend_test(self):
        fdf, pdf = _make_data(signal_strength=0.2)  # Strong signal
        merged = merge_factor_price(fdf, pdf)
        analyzer = ProfitAnalyzer()
        result = analyzer.compute(merged, split_date="2023-07-01")
        assert isinstance(result["page_test_pvalue"], float)
        assert 0 <= result["page_test_pvalue"] <= 1

    def test_long_short_contribution(self):
        fdf, pdf = _make_data()
        merged = merge_factor_price(fdf, pdf)
        analyzer = ProfitAnalyzer()
        result = analyzer.compute(merged, split_date="2023-07-01")
        assert "long_contribution" in result
        assert "short_contribution" in result

    def test_annual_group_returns(self):
        fdf, pdf = _make_data(n_dates=300)
        merged = merge_factor_price(fdf, pdf)
        analyzer = ProfitAnalyzer()
        result = analyzer.compute(merged, split_date="2023-07-01")
        annual = result["annual_group_returns"]
        assert len(annual) > 0
        assert "year" in annual[0]


class TestProfitAnalyzerCharts:
    def test_all_charts_generated(self):
        fdf, pdf = _make_data()
        merged = merge_factor_price(fdf, pdf)
        analyzer = ProfitAnalyzer()
        result = analyzer.compute(merged, split_date="2023-07-01")
        charts = analyzer.generate_charts(result)
        expected = ["quintile_bar", "cumulative_returns", "long_short", "is_vs_oos_bar", "annual_group_returns"]
        for name in expected:
            assert name in charts, f"Missing chart: {name}"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/xinzhan/.openclaw/workspace/quant_factor_system && PYTHONPATH=src python3 -m pytest tests/report/analytics/test_profit.py -v`
Expected: FAIL

- [ ] **Step 3: Implement ProfitAnalyzer**

Create `src/report/analytics/profit.py`. Key design:
- New `compute(merged_df, split_date)` interface — takes pre-merged data
- Uses `pd.qcut` for quintile assignment (like existing `groups.py`)
- Computes per-group: ann_return, ann_vol, sharpe, sortino, calmar, max_dd, max_dd_duration
- L/S = Q1 - Q5 (or Q5 - Q1, direction auto-detected from monotonicity sign)
- Page's trend test: reshape daily group returns into (dates × 5) matrix, call `scipy.stats.page_trend_test`
- Annual decomposition: groupby year, compute per-group annualized return
- L/S contribution: `long_contribution = Q1_ann_return / (Q1_ann_return - Q5_ann_return)`
- `generate_charts(result)` returns dict of 5 chart figures

```python
from scipy.stats import page_trend_test
from core.metrics import (
    annualize_return, annualize_volatility, sharpe_ratio,
    sortino_ratio, calmar_ratio, max_drawdown, max_drawdown_duration,
    win_rate,
)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/xinzhan/.openclaw/workspace/quant_factor_system && PYTHONPATH=src python3 -m pytest tests/report/analytics/test_profit.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/report/analytics/profit.py tests/report/analytics/test_profit.py
git commit -m "feat(report): add ProfitAnalyzer with Sortino, Calmar, Page's test, annual decomposition"
```

---

## Task 4: Create ConditionalAnalyzer

**Files:**
- Create: `src/report/analytics/conditional.py`
- Create: `tests/report/analytics/test_conditional.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/report/analytics/test_conditional.py
"""Tests for ConditionalAnalyzer — conditional/regime analysis."""
import pandas as pd
import numpy as np
import pytest
from report.analytics.conditional import ConditionalAnalyzer
from report.data_prep import merge_factor_price


def _make_data(n_dates=300, n_stocks=50):
    np.random.seed(42)
    dates = pd.bdate_range("2022-01-01", periods=n_dates)
    factor_rows, price_rows = [], []
    for d in dates:
        for s in [f"S{i:03d}" for i in range(n_stocks)]:
            fv = np.random.randn()
            close = 10 + 0.05 * fv + np.random.randn() * 0.3
            factor_rows.append({"time": d, "symbol": s, "value": fv})
            price_rows.append({"time": d, "symbol": s, "close": abs(close)})
    return pd.DataFrame(factor_rows), pd.DataFrame(price_rows)


class TestConditionalAnalyzer:
    def test_returns_regime_ic(self):
        fdf, pdf = _make_data()
        merged = merge_factor_price(fdf, pdf)
        analyzer = ConditionalAnalyzer()
        result = analyzer.compute(merged, price_df=pdf)
        assert "regime_ic" in result
        for regime in ["bull", "bear", "range"]:
            assert regime in result["regime_ic"]
            assert "ic" in result["regime_ic"][regime]
            assert "icir" in result["regime_ic"][regime]

    def test_returns_vol_regime_ic(self):
        fdf, pdf = _make_data()
        merged = merge_factor_price(fdf, pdf)
        analyzer = ConditionalAnalyzer()
        result = analyzer.compute(merged, price_df=pdf)
        assert "vol_regime_ic" in result
        assert "high" in result["vol_regime_ic"]
        assert "low" in result["vol_regime_ic"]

    def test_regime_distribution_reasonable(self):
        """Regimes should roughly distribute as ~25% bull, 50% range, 25% bear."""
        fdf, pdf = _make_data(n_dates=500)
        merged = merge_factor_price(fdf, pdf)
        analyzer = ConditionalAnalyzer()
        result = analyzer.compute(merged, price_df=pdf)
        # At least some dates in each regime
        for regime in ["bull", "bear", "range"]:
            assert result["regime_ic"][regime]["n_days"] > 0

    def test_annual_ic(self):
        fdf, pdf = _make_data(n_dates=500)
        merged = merge_factor_price(fdf, pdf)
        analyzer = ConditionalAnalyzer()
        result = analyzer.compute(merged, price_df=pdf)
        assert "annual_ic" in result
        assert len(result["annual_ic"]) > 0
        assert "regime" in result["annual_ic"][0]


class TestConditionalCharts:
    def test_all_charts(self):
        fdf, pdf = _make_data()
        merged = merge_factor_price(fdf, pdf)
        analyzer = ConditionalAnalyzer()
        result = analyzer.compute(merged, price_df=pdf)
        charts = analyzer.generate_charts(result)
        assert "conditional_ic" in charts
        assert "annual_ic" in charts
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/xinzhan/.openclaw/workspace/quant_factor_system && PYTHONPATH=src python3 -m pytest tests/report/analytics/test_conditional.py -v`
Expected: FAIL

- [ ] **Step 3: Implement ConditionalAnalyzer**

Create `src/report/analytics/conditional.py`. Key design:

Market regime computation:
```python
def _compute_market_regimes(self, price_df: pd.DataFrame, window: int = 60) -> pd.DataFrame:
    """Compute market regime per date using market breadth indicator.

    Equal-weight universe mean return over rolling window.
    Bull: > +10%, Bear: < -10%, Range: otherwise.
    """
    # Daily equal-weight market return
    daily_market = price_df.groupby("time")["close"].mean()
    daily_market = daily_market.sort_index()
    daily_ret = daily_market.pct_change()
    cum_ret = daily_ret.rolling(window).sum()

    regime = pd.Series("range", index=cum_ret.index)
    regime[cum_ret > 0.10] = "bull"
    regime[cum_ret < -0.10] = "bear"
    return regime  # Series: date -> regime
```

Volatility regime:
```python
def _compute_vol_regimes(self, price_df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    """Split dates into high/low volatility by median of realized vol."""
    daily_ret = price_df.groupby("time")["close"].mean().pct_change()
    rvol = daily_ret.rolling(window).std() * np.sqrt(252)
    median_vol = rvol.median()
    regime = pd.Series("low", index=rvol.index)
    regime[rvol > median_vol] = "high"
    return regime
```

`compute()` signature:
```python
def compute(self, merged_df: pd.DataFrame, price_df: pd.DataFrame) -> dict:
    """Args:
        merged_df: From data_prep.merge_factor_price
        price_df: Raw price data (needed for regime computation)
    Returns:
        dict with regime_ic, vol_regime_ic, annual_ic, size_ic (null at L0), industry_ic (null at L0)
    """
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/xinzhan/.openclaw/workspace/quant_factor_system && PYTHONPATH=src python3 -m pytest tests/report/analytics/test_conditional.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/report/analytics/conditional.py tests/report/analytics/test_conditional.py
git commit -m "feat(report): add ConditionalAnalyzer with market regime + volatility conditioning"
```

---

## Task 5: Create UniquenessAnalyzer

**Files:**
- Create: `src/report/analytics/uniqueness.py`
- Create: `tests/report/analytics/test_uniqueness.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/report/analytics/test_uniqueness.py
"""Tests for UniquenessAnalyzer — factor independence analysis."""
import pandas as pd
import numpy as np
import pytest
from report.analytics.uniqueness import UniquenessAnalyzer


def _make_factor_values(n_dates=100, n_stocks=50, n_factors=5):
    """Create multiple factor value DataFrames."""
    np.random.seed(42)
    dates = pd.bdate_range("2023-01-01", periods=n_dates)
    # Target factor
    target_rows = []
    lib_factors = {}
    base_signal = {}
    for d in dates:
        for s in [f"S{i:03d}" for i in range(n_stocks)]:
            v = np.random.randn()
            target_rows.append({"time": d, "symbol": s, "value": v})
            base_signal[(d, s)] = v
    target_df = pd.DataFrame(target_rows)

    for fid in range(n_factors):
        rows = []
        for d in dates:
            for s in [f"S{i:03d}" for i in range(n_stocks)]:
                if fid == 0:
                    # First library factor highly correlated with target
                    v = base_signal[(d, s)] * 0.9 + np.random.randn() * 0.1
                else:
                    v = np.random.randn()
                rows.append({"time": d, "symbol": s, "value": v})
        lib_factors[f"F{fid:03d}"] = pd.DataFrame(rows)
    return target_df, lib_factors


class TestUniquenessCompute:
    def test_returns_required_keys(self):
        target, lib = _make_factor_values()
        analyzer = UniquenessAnalyzer()
        result = analyzer.compute(target, lib)
        assert "max_corr" in result
        assert "max_corr_factor" in result
        assert "top5_correlated" in result
        assert "incremental_ic" in result or "incremental_ic" in result

    def test_high_correlation_detected(self):
        target, lib = _make_factor_values()
        analyzer = UniquenessAnalyzer()
        result = analyzer.compute(target, lib)
        # F000 is highly correlated with target (by construction)
        assert result["max_corr"] > 0.5
        assert result["max_corr_factor"] == "F000"

    def test_empty_library(self):
        target, _ = _make_factor_values()
        analyzer = UniquenessAnalyzer()
        result = analyzer.compute(target, {})
        assert result["max_corr"] == 0.0
        assert result["top5_correlated"] == []

    def test_top5_sorted(self):
        target, lib = _make_factor_values(n_factors=10)
        analyzer = UniquenessAnalyzer()
        result = analyzer.compute(target, lib)
        corrs = [x["corr"] for x in result["top5_correlated"]]
        assert corrs == sorted(corrs, reverse=True)
        assert len(result["top5_correlated"]) <= 5


class TestUniquenessCharts:
    def test_correlation_bar(self):
        target, lib = _make_factor_values()
        analyzer = UniquenessAnalyzer()
        result = analyzer.compute(target, lib)
        charts = analyzer.generate_charts(result)
        assert "correlation_bar" in charts
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/xinzhan/.openclaw/workspace/quant_factor_system && PYTHONPATH=src python3 -m pytest tests/report/analytics/test_uniqueness.py -v`
Expected: FAIL

- [ ] **Step 3: Implement UniquenessAnalyzer**

Create `src/report/analytics/uniqueness.py`:

```python
"""UniquenessAnalyzer — factor independence analysis.

Computes cross-sectional rank correlation with all library factors
and incremental IC (residual IC after removing library factor exposures).
"""
from __future__ import annotations
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy.stats import spearmanr
from report.charts.theme import apply_theme, COLORS


class UniquenessAnalyzer:

    def compute(
        self,
        target_df: pd.DataFrame,
        library_factors: dict[str, pd.DataFrame],
        merged_df: pd.DataFrame | None = None,
    ) -> dict:
        """Compute uniqueness metrics.

        Args:
            target_df: Target factor values [time, symbol, value]
            library_factors: Dict of factor_id -> DataFrame [time, symbol, value]
            merged_df: If provided, compute incremental IC (needs future_return column)

        Returns:
            dict with max_corr, max_corr_factor, top5_correlated, incremental_ic, incremental_icir
        """
        if not library_factors:
            return {
                "max_corr": 0.0,
                "max_corr_factor": "",
                "top5_correlated": [],
                "incremental_ic": None,
                "incremental_icir": None,
            }

        # Compute pairwise cross-sectional rank correlation
        correlations = []
        for fid, fdf in library_factors.items():
            corr = self._cross_sectional_corr(target_df, fdf)
            if corr is not None:
                correlations.append({"factor": fid, "corr": round(abs(corr), 4)})

        correlations.sort(key=lambda x: x["corr"], reverse=True)
        max_entry = correlations[0] if correlations else {"factor": "", "corr": 0.0}

        result = {
            "max_corr": max_entry["corr"],
            "max_corr_factor": max_entry["factor"],
            "top5_correlated": correlations[:5],
            "incremental_ic": None,
            "incremental_icir": None,
        }

        # Incremental IC if merged_df provided
        if merged_df is not None and library_factors:
            inc_ic, inc_icir = self._compute_incremental_ic(target_df, library_factors, merged_df)
            result["incremental_ic"] = inc_ic
            result["incremental_icir"] = inc_icir

        return result

    def _cross_sectional_corr(self, df_a: pd.DataFrame, df_b: pd.DataFrame) -> float | None:
        """Average cross-sectional rank correlation between two factor DataFrames."""
        merged = df_a.merge(df_b, on=["time", "symbol"], suffixes=("_a", "_b"))
        if len(merged) < 100:
            return None
        daily_corrs = []
        for _, group in merged.groupby("time"):
            if len(group) >= 30:
                corr, _ = spearmanr(group["value_a"], group["value_b"])
                daily_corrs.append(corr)
        return float(np.mean(daily_corrs)) if daily_corrs else None

    def _compute_incremental_ic(self, target_df, library_factors, merged_df):
        """Compute IC of residuals after removing library factor exposures."""
        # Simplified: per-date OLS of target on library factors, then IC of residuals
        # ... (full implementation in actual code)
        return None, None  # placeholder, implement with np.linalg.lstsq

    def generate_charts(self, result: dict) -> dict:
        """Generate uniqueness charts."""
        charts = {}
        if result["top5_correlated"]:
            charts["correlation_bar"] = self._plot_correlation_bar(result)
        return charts

    def _plot_correlation_bar(self, result):
        """Horizontal bar chart of correlations with library factors."""
        # ... plotly implementation
```

Note: The `_compute_incremental_ic` is complex (per-date OLS). Implement a simplified version first that works:

```python
def _compute_incremental_ic(self, target_df, library_factors, merged_df):
    """IC of residuals after cross-sectional regression on library factors."""
    from scipy.stats import spearmanr

    # Build wide matrix per date: target + all library factors
    target = target_df.rename(columns={"value": "target"})
    daily_residual_ics = []

    for date, group in merged_df.groupby("time"):
        date_target = target[target["time"] == date][["symbol", "target"]]
        # Collect library factor values for this date
        lib_vals = date_target[["symbol"]].copy()
        for fid, fdf in library_factors.items():
            fdate = fdf[fdf["time"] == date][["symbol", "value"]].rename(columns={"value": fid})
            lib_vals = lib_vals.merge(fdate, on="symbol", how="inner")

        if len(lib_vals) < 30:
            continue

        lib_cols = [c for c in lib_vals.columns if c not in ("symbol",)]
        date_merged = date_target.merge(lib_vals, on="symbol")
        date_merged = date_merged.merge(
            group[["symbol", "future_return"]].drop_duplicates(), on="symbol"
        )

        if len(date_merged) < 30 or not lib_cols:
            continue

        # OLS: target ~ library_factors, get residual
        X = date_merged[lib_cols].values
        y = date_merged["target"].values
        try:
            coeffs, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
            residual = y - X @ coeffs
            corr, _ = spearmanr(residual, date_merged["future_return"].values)
            daily_residual_ics.append(corr)
        except (np.linalg.LinAlgError, ValueError):
            continue

    if not daily_residual_ics:
        return None, None
    ics = np.array(daily_residual_ics)
    return float(np.mean(ics)), float(np.mean(ics) / np.std(ics)) if np.std(ics) > 0 else 0.0
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/xinzhan/.openclaw/workspace/quant_factor_system && PYTHONPATH=src python3 -m pytest tests/report/analytics/test_uniqueness.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/report/analytics/uniqueness.py tests/report/analytics/test_uniqueness.py
git commit -m "feat(report): add UniquenessAnalyzer with correlation matrix + incremental IC"
```

---

## Task 6: Upgrade DecayAnalyzer (absorb distribution)

**Files:**
- Modify: `src/report/analytics/decay.py`
- Create: `tests/report/analytics/test_decay.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/report/analytics/test_decay.py
"""Tests for upgraded DecayAnalyzer — decay + distribution + tradability."""
import pandas as pd
import numpy as np
import pytest
from report.analytics.decay import DecayAnalyzer
from report.data_prep import merge_factor_price


def _make_data(n_dates=200, n_stocks=50):
    np.random.seed(42)
    dates = pd.bdate_range("2023-01-01", periods=n_dates)
    factor_rows, price_rows = [], []
    for d in dates:
        for s in [f"S{i:03d}" for i in range(n_stocks)]:
            fv = np.random.randn()
            close = 10 + 0.05 * fv + np.random.randn() * 0.3
            factor_rows.append({"time": d, "symbol": s, "value": fv})
            price_rows.append({"time": d, "symbol": s, "close": abs(close)})
    return pd.DataFrame(factor_rows), pd.DataFrame(price_rows)


class TestDecayCompute:
    def test_returns_required_keys(self):
        fdf, pdf = _make_data()
        analyzer = DecayAnalyzer()
        result = analyzer.compute(fdf, pdf)
        assert "ic_by_period" in result
        assert "half_life_days" in result
        assert "optimal_rebalance_days" in result
        assert "autocorrelation" in result
        assert "distribution" in result  # absorbed from DistributionAnalyzer

    def test_includes_2d_period(self):
        fdf, pdf = _make_data()
        analyzer = DecayAnalyzer()
        result = analyzer.compute(fdf, pdf)
        periods = [r["days"] for r in result["ic_by_period"]]
        assert 2 in periods  # New 2-day period

    def test_distribution_stats(self):
        fdf, pdf = _make_data()
        merged = merge_factor_price(fdf, pdf)
        analyzer = DecayAnalyzer()
        result = analyzer.compute(fdf, pdf, split_date="2023-07-01", factor_values_mi=None)
        dist = result["distribution"]
        assert "stats_is" in dist or "stats_all" in dist

    def test_optimal_rebalance(self):
        fdf, pdf = _make_data()
        analyzer = DecayAnalyzer()
        result = analyzer.compute(fdf, pdf)
        assert isinstance(result["optimal_rebalance_days"], int)
        assert result["optimal_rebalance_days"] > 0


class TestDecayCharts:
    def test_all_charts(self):
        fdf, pdf = _make_data()
        analyzer = DecayAnalyzer()
        result = analyzer.compute(fdf, pdf)
        charts = analyzer.generate_charts(result)
        expected = ["ic_decay", "autocorrelation", "distribution", "coverage"]
        for name in expected:
            assert name in charts, f"Missing chart: {name}"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/xinzhan/.openclaw/workspace/quant_factor_system && PYTHONPATH=src python3 -m pytest tests/report/analytics/test_decay.py -v`
Expected: FAIL

- [ ] **Step 3: Upgrade DecayAnalyzer**

Modify `src/report/analytics/decay.py`. New unified `compute()` method:

```python
def compute(
    self,
    factor_df: pd.DataFrame,    # flat [time, symbol, value]
    price_df: pd.DataFrame,      # flat [time, symbol, close]
    split_date=None,
    periods: list[int] | None = None,
) -> dict:
    """Compute decay, autocorrelation, and distribution in one call.

    Args:
        factor_df: Flat factor values [time, symbol, value]
        price_df: Price data [time, symbol, close]
        split_date: IS/OOS cutoff for distribution stats (optional)
        periods: IC holding periods (default: [1, 2, 5, 10, 20, 60])

    Returns:
        dict with ic_by_period, half_life_days, optimal_rebalance_days,
              autocorrelation, distribution (stats_is, stats_oos or stats_all)
    """
    periods = periods or [1, 2, 5, 10, 20, 60]

    # 1. IC decay: for each period, compute cross-sectional IC with N-day forward return
    ic_by_period = self._compute_ic_decay(factor_df, price_df, periods)

    # 2. Half-life and optimal rebalance
    half_life = self._compute_half_life(ic_by_period)
    optimal_rebal = self._compute_optimal_rebalance(ic_by_period)

    # 3. Autocorrelation: pivot factor_df to wide format, compute per-stock lag corr
    autocorr = self._compute_autocorrelation(factor_df)

    # 4. Distribution stats (absorbed from DistributionAnalyzer)
    dist = self._compute_distribution(factor_df, split_date)

    return {
        "ic_by_period": ic_by_period,
        "half_life_days": half_life,
        "optimal_rebalance_days": optimal_rebal,
        "autocorrelation": autocorr,
        "distribution": dist,
    }
```

Key implementation details:
- `_compute_ic_decay`: For each period N, compute N-day forward return per stock, then daily cross-sectional Spearman correlation
- `_compute_optimal_rebalance`: First period where IC ratio < 0.7, or half_life if exists, or max period
- `_compute_autocorrelation`: Sample up to 50 dates, compute cross-sectional correlation between factor at date t and date t-lag
- `_compute_distribution`: Use `scipy.stats.skew/kurtosis`, compute coverage as `1 - nan_ratio` per date. If `split_date` provided, compute `stats_is` and `stats_oos` separately; otherwise `stats_all`
- Absorb `plot_distribution` and `plot_coverage` from old `DistributionAnalyzer`

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/xinzhan/.openclaw/workspace/quant_factor_system && PYTHONPATH=src python3 -m pytest tests/report/analytics/test_decay.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/report/analytics/decay.py tests/report/analytics/test_decay.py
git commit -m "feat(report): upgrade DecayAnalyzer with 2d period, rebalance rec, absorbed distribution"
```

---

## Task 7: Rewrite CompositeScorer

**Files:**
- Rewrite: `src/report/scorer.py`
- Rewrite: `tests/report/test_scorer.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/report/test_scorer.py
"""Tests for 7-dimension S-curve CompositeScorer."""
import math
import pytest
from report.scorer import CompositeScorer, s_curve_score, robustness_score


class TestSCurveScore:
    def test_midpoint_gives_50(self):
        assert abs(s_curve_score(0.03, midpoint=0.03, k=92) - 50) < 1

    def test_high_value_near_100(self):
        score = s_curve_score(0.08, midpoint=0.03, k=92)
        assert score > 98

    def test_zero_value_near_0(self):
        score = s_curve_score(0.0, midpoint=0.03, k=92)
        assert score < 10

    def test_negative_input(self):
        score = s_curve_score(-0.05, midpoint=0.03, k=92)
        assert score < 1


class TestRobustnessScore:
    def test_no_drift(self):
        assert robustness_score(0.05, 0.05) == 100.0

    def test_50_percent_drift(self):
        score = robustness_score(0.06, 0.03)
        assert abs(score - 50) < 1

    def test_100_percent_drift(self):
        score = robustness_score(0.05, 0.0)
        assert score == 0

    def test_ic_is_near_zero_returns_neutral(self):
        score = robustness_score(0.005, 0.03)
        assert score == 50.0  # |IC_IS| < 0.01 -> neutral


class TestCompositeScorer:
    def test_seven_dimensions(self):
        scorer = CompositeScorer()
        result = scorer.compute(
            rank_ic_oos=0.05,
            icir_oos=0.4,
            ls_sharpe=0.8,
            monotonicity=0.8,
            ic_is=0.05,
            ic_oos=0.04,
            max_corr=0.3,
            ic_1d=0.05,
            ic_20d=0.04,
        )
        assert len(result["dimensions"]) == 7
        assert "composite_score" in result
        assert "composite_grade" in result

    def test_grade_scale(self):
        scorer = CompositeScorer()
        assert scorer.score_to_grade(95) == "S"
        assert scorer.score_to_grade(80) == "A"
        assert scorer.score_to_grade(65) == "B"
        assert scorer.score_to_grade(50) == "C"
        assert scorer.score_to_grade(30) == "D"

    def test_missing_data_uses_neutral(self):
        scorer = CompositeScorer()
        result = scorer.compute(
            rank_ic_oos=0.05,
            icir_oos=0.4,
            ls_sharpe=0.8,
            monotonicity=0.8,
            ic_is=0.05,
            ic_oos=0.04,
            max_corr=None,  # data missing
            ic_1d=0.05,
            ic_20d=0.04,
        )
        # Uniqueness dimension should use score 50
        uniqueness_dim = [d for d in result["dimensions"] if d["name"] == "Uniqueness"][0]
        assert uniqueness_dim["score"] == 50
        assert uniqueness_dim["data_available"] is False

    def test_radar_chart(self):
        scorer = CompositeScorer()
        result = scorer.compute(
            rank_ic_oos=0.05, icir_oos=0.4, ls_sharpe=0.8,
            monotonicity=0.8, ic_is=0.05, ic_oos=0.04,
            max_corr=0.3, ic_1d=0.05, ic_20d=0.04,
        )
        charts = scorer.generate_charts(result)
        assert "radar" in charts

    def test_weights_sum_to_1(self):
        scorer = CompositeScorer()
        total = sum(w for _, w in scorer.WEIGHTS)
        assert abs(total - 1.0) < 0.001
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/xinzhan/.openclaw/workspace/quant_factor_system && PYTHONPATH=src python3 -m pytest tests/report/test_scorer.py -v`
Expected: FAIL

- [ ] **Step 3: Rewrite CompositeScorer**

Rewrite `src/report/scorer.py`:

```python
"""CompositeScorer — 7-dimension S-curve factor scoring."""
from __future__ import annotations
import math
import plotly.graph_objects as go
from report.charts.theme import apply_theme


def s_curve_score(x: float, midpoint: float, k: float) -> float:
    """Sigmoid scoring: ≈50 at midpoint, approaches 0/100 at extremes."""
    return 100.0 / (1.0 + math.exp(-k * (x - midpoint)))


def robustness_score(ic_is: float, ic_oos: float) -> float:
    """OOS robustness: lower IC drift = higher score."""
    if abs(ic_is) < 0.01:
        return 50.0  # neutral when IC_IS near zero
    drift = abs(ic_oos - ic_is) / abs(ic_is)
    return max(0.0, 100.0 * (1.0 - drift))


class CompositeScorer:
    # (dimension_name, weight)
    WEIGHTS = [
        ("Predictive Power", 0.25),
        ("Signal Stability", 0.20),
        ("Profitability", 0.15),
        ("Monotonicity", 0.10),
        ("OOS Robustness", 0.15),
        ("Uniqueness", 0.10),
        ("Decay Resistance", 0.05),
    ]

    _GRADE_SCALE = [(90, "S"), (75, "A"), (60, "B"), (45, "C"), (0, "D")]

    @staticmethod
    def score_to_grade(score: float) -> str:
        for threshold, grade in CompositeScorer._GRADE_SCALE:
            if score >= threshold:
                return grade
        return "D"

    def compute(self, *, rank_ic_oos, icir_oos, ls_sharpe, monotonicity,
                ic_is, ic_oos, max_corr, ic_1d, ic_20d) -> dict:
        dimensions = []

        # 1. Predictive Power
        dimensions.append(self._dim("Predictive Power",
            s_curve_score(abs(rank_ic_oos), midpoint=0.03, k=92),
            data_available=rank_ic_oos is not None))

        # 2. Signal Stability
        dimensions.append(self._dim("Signal Stability",
            s_curve_score(abs(icir_oos), midpoint=0.3, k=9.2),
            data_available=icir_oos is not None))

        # 3. Profitability
        dimensions.append(self._dim("Profitability",
            s_curve_score(ls_sharpe, midpoint=0.5, k=4.6) if ls_sharpe is not None else 50,
            data_available=ls_sharpe is not None))

        # 4. Monotonicity
        mono_score = min(100, abs(monotonicity) * 100) if monotonicity is not None else 50
        dimensions.append(self._dim("Monotonicity", mono_score,
            data_available=monotonicity is not None))

        # 5. OOS Robustness
        rob = robustness_score(ic_is, ic_oos) if (ic_is is not None and ic_oos is not None) else 50
        dimensions.append(self._dim("OOS Robustness", rob,
            data_available=(ic_is is not None and ic_oos is not None)))

        # 6. Uniqueness: score = max(0, 100 * (1 - max_corr / 0.7))
        if max_corr is not None:
            uniq = max(0.0, min(100.0, 100.0 * (1.0 - max_corr / 0.7)))
        else:
            uniq = 50.0
        dimensions.append(self._dim("Uniqueness", uniq, data_available=max_corr is not None))

        # 7. Decay Resistance: linear 0->0, 0.7+->100
        if ic_1d is not None and ic_20d is not None and abs(ic_1d) > 0.001:
            ratio = abs(ic_20d) / abs(ic_1d)
            decay = min(100.0, ratio / 0.7 * 100)
        else:
            decay = 50.0
        dimensions.append(self._dim("Decay Resistance", decay,
            data_available=(ic_1d is not None and ic_20d is not None)))

        # Weighted composite
        composite = sum(d["score"] * w for d, (_, w) in zip(dimensions, self.WEIGHTS))

        return {
            "dimensions": dimensions,
            "composite_score": round(composite, 1),
            "composite_grade": self.score_to_grade(composite),
            "library_rank": None,   # populated by builder after scoring all factors
            "library_total": None,  # populated by builder after scoring all factors
        }

    def _dim(self, name, score, data_available=True):
        return {
            "name": name,
            "score": round(score if data_available else 50.0, 1),
            "data_available": data_available,
        }

    def generate_charts(self, result: dict) -> dict:
        """Generate radar chart."""
        dims = result["dimensions"]
        names = [d["name"] for d in dims]
        scores = [d["score"] for d in dims]
        available = [d["data_available"] for d in dims]

        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=scores + [scores[0]],
            theta=names + [names[0]],
            fill="toself",
            name="Score",
        ))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])))
        apply_theme(fig)
        return {"radar": fig}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/xinzhan/.openclaw/workspace/quant_factor_system && PYTHONPATH=src python3 -m pytest tests/report/test_scorer.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/report/scorer.py tests/report/test_scorer.py
git commit -m "feat(report): rewrite CompositeScorer with 7-dim S-curve scoring"
```

---

## Task 8: Rewrite ReportDataBuilder (Integration)

**Files:**
- Rewrite: `src/report/builder.py`
- Modify: `src/report/analytics/__init__.py`
- Modify: `src/report/__init__.py`
- Delete: `src/report/analytics/distribution.py` (absorbed into decay)
- Create: `tests/report/test_builder.py`

- [ ] **Step 1: Update analytics/__init__.py exports**

```python
# src/report/analytics/__init__.py
from .ic import ICAnalyzer
from .profit import ProfitAnalyzer
from .conditional import ConditionalAnalyzer
from .decay import DecayAnalyzer
from .uniqueness import UniquenessAnalyzer

__all__ = [
    "ICAnalyzer",
    "ProfitAnalyzer",
    "ConditionalAnalyzer",
    "DecayAnalyzer",
    "UniquenessAnalyzer",
]
```

- [ ] **Step 2: Update report/__init__.py exports**

```python
# src/report/__init__.py
from .analytics import (
    ICAnalyzer, ProfitAnalyzer, ConditionalAnalyzer,
    DecayAnalyzer, UniquenessAnalyzer,
)
from .scorer import CompositeScorer
from .builder import ReportDataBuilder
from .renderer import ReportRenderer  # deprecated but kept for backward compat

__all__ = [
    "ICAnalyzer", "ProfitAnalyzer", "ConditionalAnalyzer",
    "DecayAnalyzer", "UniquenessAnalyzer",
    "CompositeScorer", "ReportDataBuilder", "ReportRenderer",
]
```

Note: `ReportRenderer` is deprecated (uses old schema) but kept in exports because `dashboard/pages/Factors.py` and `mining/publisher.py` may import it. It will produce broken output with the new schema but won't crash on import.

- [ ] **Step 3: Delete distribution.py**

```bash
rm src/report/analytics/distribution.py
rm tests/report/analytics/test_distribution.py
```

- [ ] **Step 4: Write builder integration test**

```python
# tests/report/test_builder.py
"""Integration test for ReportDataBuilder — mocked DB."""
import pandas as pd
import numpy as np
import pytest
from unittest.mock import patch, MagicMock
from report.builder import ReportDataBuilder


def _mock_factor_metadata():
    return {
        "id": "001", "name": "test_factor",
        "expression": "Std($close, 20)",
        "category": "volatility", "batch": "test_batch",
        "admitted_at": "2026-01-01",
    }


def _mock_db_data(n_dates=200, n_stocks=50):
    """Returns flat DataFrames matching the new _load_data_from_db() format."""
    np.random.seed(42)
    dates = pd.bdate_range("2022-01-01", periods=n_dates)
    factor_rows, price_rows = [], []
    for d in dates:
        for s in [f"S{i:03d}" for i in range(n_stocks)]:
            fv = np.random.randn()
            close = 10 + 0.05 * fv + np.random.randn() * 0.3
            factor_rows.append({"time": d, "symbol": s, "value": fv})
            price_rows.append({"time": d, "symbol": s, "close": abs(close)})
    return pd.DataFrame(factor_rows), pd.DataFrame(price_rows)  # flat format


class TestReportDataBuilder:
    @patch.object(ReportDataBuilder, "_load_factor_metadata")
    @patch.object(ReportDataBuilder, "_load_data_from_db")
    @patch.object(ReportDataBuilder, "_load_library_factors")
    def test_build_returns_new_schema(self, mock_lib, mock_db, mock_meta):
        mock_meta.return_value = _mock_factor_metadata()
        fdf, pdf = _mock_db_data()
        mock_db.return_value = (fdf, pdf)
        mock_lib.return_value = {}

        builder = ReportDataBuilder("001")
        result = builder.build()

        # New schema keys
        assert "factor" in result
        assert "predictive_power" in result
        assert "profitability" in result
        assert "risk_attribution" in result  # null at L0
        assert "conditional" in result
        assert "decay_tradability" in result
        assert "uniqueness" in result
        assert "composite" in result

    @patch.object(ReportDataBuilder, "_load_factor_metadata")
    @patch.object(ReportDataBuilder, "_load_data_from_db")
    @patch.object(ReportDataBuilder, "_load_library_factors")
    def test_risk_attribution_null_at_l0(self, mock_lib, mock_db, mock_meta):
        mock_meta.return_value = _mock_factor_metadata()
        fdf, pdf = _mock_db_data()
        mock_db.return_value = (fdf, pdf)
        mock_lib.return_value = {}

        builder = ReportDataBuilder("001")
        result = builder.build()
        assert result["risk_attribution"] is None  # No L1 data

    @patch.object(ReportDataBuilder, "_load_factor_metadata")
    @patch.object(ReportDataBuilder, "_load_data_from_db")
    @patch.object(ReportDataBuilder, "_load_library_factors")
    def test_composite_has_seven_dimensions(self, mock_lib, mock_db, mock_meta):
        mock_meta.return_value = _mock_factor_metadata()
        fdf, pdf = _mock_db_data()
        mock_db.return_value = (fdf, pdf)
        mock_lib.return_value = {}

        builder = ReportDataBuilder("001")
        result = builder.build()
        assert len(result["composite"]["dimensions"]) == 7
```

- [ ] **Step 5: Run tests to verify they fail**

Run: `cd /Users/xinzhan/.openclaw/workspace/quant_factor_system && PYTHONPATH=src python3 -m pytest tests/report/test_builder.py -v`
Expected: FAIL

- [ ] **Step 6: Rewrite ReportDataBuilder**

Rewrite `src/report/builder.py`. Key changes:

1. **New orchestration flow** in `build()`:
   ```python
   def build(self, vault_dir=None):
       meta = self._load_factor_metadata()
       factor_df, price_df = self._load_data_from_db()
       library_factors = self._load_library_factors()

       merged = merge_factor_price(factor_df, price_df)
       split_date = self.config.test_start
       is_df, oos_df = split_is_oos(merged, split_date)

       # Ch1: Predictive Power
       ic_analyzer = ICAnalyzer()
       ic_result = ic_analyzer.compute(merged, split_date)
       ic_charts = ic_analyzer.generate_charts(ic_result)

       # Ch2: Profitability
       profit_analyzer = ProfitAnalyzer()
       profit_result = profit_analyzer.compute(merged, split_date)
       profit_charts = profit_analyzer.generate_charts(profit_result)

       # Ch3: Risk Attribution (null at L0)
       risk_result = None

       # Ch4: Conditional
       cond_analyzer = ConditionalAnalyzer()
       cond_result = cond_analyzer.compute(merged, price_df)
       cond_charts = cond_analyzer.generate_charts(cond_result)

       # Ch5: Decay & Tradability
       decay_analyzer = DecayAnalyzer()
       decay_result = decay_analyzer.compute(factor_df, price_df, split_date)
       decay_charts = decay_analyzer.generate_charts(decay_result)

       # Ch6: Uniqueness
       uniq_analyzer = UniquenessAnalyzer()
       uniq_result = uniq_analyzer.compute(factor_df, library_factors, merged)
       uniq_charts = uniq_analyzer.generate_charts(uniq_result)

       # Ch7: Composite Score
       scorer = CompositeScorer()
       composite = scorer.compute(
           rank_ic_oos=ic_result["summary"]["oos"]["rank_ic_mean"],
           icir_oos=ic_result["summary"]["oos"]["icir"],
           ls_sharpe=profit_result["ls_stats"]["sharpe"],
           monotonicity=profit_result["monotonicity"],
           ic_is=ic_result["summary"]["is"]["rank_ic_mean"],
           ic_oos=ic_result["summary"]["oos"]["rank_ic_mean"],
           max_corr=uniq_result["max_corr"] if uniq_result["max_corr"] > 0 else None,
           ic_1d=self._get_ic_at_period(decay_result, 1),
           ic_20d=self._get_ic_at_period(decay_result, 20),
       )
       score_charts = scorer.generate_charts(composite)

       # Export charts if vault_dir
       all_charts = {}
       for chart_dict in [ic_charts, profit_charts, cond_charts, decay_charts, uniq_charts, score_charts]:
           for name, fig in chart_dict.items():
               all_charts[name] = self._export_fig(fig, name) if vault_dir else name

       # Assemble report_data
       return {
           "factor": {**meta, "data_level": "L0"},
           "predictive_power": {**ic_result, "charts": {k: all_charts[k] for k in ic_charts}},
           "profitability": {**profit_result, "charts": {k: all_charts[k] for k in profit_charts}},
           "risk_attribution": risk_result,
           "conditional": {**cond_result, "charts": {k: all_charts[k] for k in cond_charts}},
           "decay_tradability": {**decay_result, "charts": {k: all_charts[k] for k in decay_charts}},
           "uniqueness": {**uniq_result, "charts": {k: all_charts[k] for k in uniq_charts}},
           "composite": {**composite, "charts": {k: all_charts[k] for k in score_charts}},
       }
   ```

2. **New `_load_library_factors()`**: Query DB for all admitted factors' values, return dict of factor_id → DataFrame.

3. **Update `_load_data_from_db()`** — change to return flat DataFrames directly: `(factor_df[time,symbol,value], price_df[time,symbol,close])`. Move `_to_flat_df()` conversion inside the method. This simplifies all downstream analyzer calls.

4. **Keep `_export_fig()` and `save_for_vault()`** — chart export logic is sound.

5. **Keep CLI `__main__` block** at bottom of file.

6. **Merge regime labels** into `predictive_power.annual`: After computing both IC and conditional results, merge `ConditionalAnalyzer`'s regime labels into IC annual entries:
   ```python
   regime_map = {a["year"]: a["regime"] for a in cond_result.get("annual_ic", [])}
   for entry in ic_result.get("annual", []):
       entry["regime"] = regime_map.get(entry["year"], "unknown")
   ```

7. **Populate `library_rank`/`library_total`**: After scoring, load existing factor scores from library YAML and compute rank position.

8. **ICAnalyzer backward compat**: Add `compute_ic()` wrapper in rewritten ICAnalyzer for `dashboard/pages/Factors.py` compatibility:
   ```python
   def compute_ic(self, factor_df, price_df, split_date=None, method="spearman"):
       """Backward-compatible wrapper for dashboard."""
       from report.data_prep import merge_factor_price
       merged = merge_factor_price(factor_df, price_df)
       return self.compute(merged, split_date)
   ```

9. **New `_load_library_factors()`**: Query DB for all admitted factors' values, return `dict[str, pd.DataFrame]`.

- [ ] **Step 7: Run all tests**

Run: `cd /Users/xinzhan/.openclaw/workspace/quant_factor_system && PYTHONPATH=src python3 -m pytest tests/report/ -v`
Expected: All PASS

- [ ] **Step 8: Commit**

```bash
git add src/report/builder.py src/report/__init__.py src/report/analytics/__init__.py tests/report/test_builder.py
git rm src/report/analytics/distribution.py src/report/analytics/groups.py
git rm -f tests/report/analytics/test_distribution.py
git commit -m "feat(report): rewrite ReportDataBuilder with 6-analyzer pipeline + new schema"
```

---

## Task 9: End-to-End Verification

**Files:** No new files — integration testing against real DB.

- [ ] **Step 1: Run all unit tests**

Run: `cd /Users/xinzhan/.openclaw/workspace/quant_factor_system && PYTHONPATH=src python3 -m pytest tests/report/ tests/core/test_metrics.py -v`
Expected: All PASS

- [ ] **Step 2: Generate report for F011 (best factor)**

Run: `cd /Users/xinzhan/.openclaw/workspace/quant_factor_system && PYTHONPATH=src python3 -m report.builder --factor-id 011 --vault`
Expected: Creates `storage/vault/assets/F011/report_data.json` + 18 PNG files

- [ ] **Step 3: Verify report_data.json schema**

Run: `cd /Users/xinzhan/.openclaw/workspace/quant_factor_system && python3 -c "
import json
with open('storage/vault/assets/F011/report_data.json') as f:
    data = json.load(f)
required = ['factor', 'predictive_power', 'profitability', 'risk_attribution', 'conditional', 'decay_tradability', 'uniqueness', 'composite']
for k in required:
    assert k in data, f'Missing: {k}'
assert data['risk_attribution'] is None  # L0
assert len(data['composite']['dimensions']) == 7
print('Schema OK')
print(f'Grade: {data[\"composite\"][\"composite_grade\"]}')
print(f'Score: {data[\"composite\"][\"composite_score\"]}')
"`
Expected: `Schema OK` + grade/score output

- [ ] **Step 4: Generate report for F001 (verify different factor)**

Run: `cd /Users/xinzhan/.openclaw/workspace/quant_factor_system && PYTHONPATH=src python3 -m report.builder --factor-id 001 --vault`
Expected: Success

- [ ] **Step 5: Commit any fixes from E2E testing**

```bash
git add -u
git commit -m "fix(report): address issues found in E2E verification"
```

---

## Task 10: Update factor-report Skill

**Files:**
- Modify: `.claude/skills/factor-report/skill.md` (or the skill directory)

- [ ] **Step 1: Read current skill definition**

Read the current skill file to understand the template structure that needs updating.

- [ ] **Step 2: Update skill with new 7-chapter structure**

Update the skill's Markdown template to match the new report structure:
- New frontmatter schema (add `data_level`, `composite_score`, update metric names)
- 7 analysis chapters with decision question headers
- Per-chapter narrative task/constraint from spec
- Updated chart wikilink list (20 charts, organized by chapter)
- Data-missing callout patterns
- Per-chapter verdict lines

Key sections in the updated skill:
```markdown
## KPI 摘要
| 指标 | IS | OOS |
|------|----|----|
| RankIC (Spearman) | {{rank_ic_is}} | {{rank_ic_oos}} |
| IC (Pearson) | {{ic_is}} | {{ic_oos}} |
| ICIR | {{icir_is}} | {{icir_oos}} |
| t-statistic | {{t_stat_is}} (p={{p_is}}) | {{t_stat_oos}} (p={{p_oos}}) |
| 多空 Sharpe | — | {{ls_sharpe}} |
| 单调性 | — | {{monotonicity}} |
| 综合评分 | — | {{composite_score}} ({{composite_grade}}) |

## 1. 预测能力 — "这个信号有多强？"
![[FXXX/ic_timeseries.png]]
![[FXXX/ic_distribution.png]]
![[FXXX/rolling_ic.png]]
![[FXXX/cumulative_ic.png]]
![[FXXX/monthly_heatmap.png]]
[LLM narrative: task + constraint from spec]
**结论**: [one-line verdict]

## 2. 盈利能力 — "信号能稳定赚钱吗？"
...
```

- [ ] **Step 3: Verify skill loads correctly**

Test by running `/factor-report 011` (or reviewing that the skill file parses without errors).

- [ ] **Step 4: Commit**

```bash
git add .claude/skills/factor-report/
git commit -m "feat(report): update factor-report skill for 7-chapter structure"
```

---

## Dependency Graph

```
Task 1 (Foundation) ──┬──> Task 2 (ICAnalyzer)
                      ├──> Task 3 (ProfitAnalyzer)
                      ├──> Task 4 (ConditionalAnalyzer)
                      ├──> Task 5 (UniquenessAnalyzer)
                      ├──> Task 6 (DecayAnalyzer)
                      └──> Task 7 (CompositeScorer)
                              │
Tasks 2-7 ──────────────────> Task 8 (Builder Integration)
                              │
Task 8 ─────────────────────> Task 9 (E2E Verification)
                              │
Task 9 ─────────────────────> Task 10 (Skill Update)
```

**Parallelizable**: Tasks 2, 3, 4, 5, 6, 7 can run in parallel after Task 1 completes.
