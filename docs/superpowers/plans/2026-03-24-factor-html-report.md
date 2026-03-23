# Factor HTML Report Generator — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a three-stage pipeline (Python compute → Claude Code narrative → Jinja2 render) that generates publication-quality HTML factor analysis reports with 8 sections.

**Architecture:** `builder.py` computes all metrics and Plotly charts → outputs `report_data.json`. Claude Code skill reads data, writes `narrative.json`. `renderer.py` merges both via Jinja2 template → self-contained HTML. A `/factor-report` skill orchestrates the whole flow.

**Tech Stack:** Python 3, Plotly, Jinja2, pandas, numpy, scipy, psycopg2, YAML

**Spec:** `docs/superpowers/specs/2026-03-24-factor-html-report-design.md`

---

## File Structure

```
mining/
├── report/
│   ├── __init__.py              # Package init, public API
│   ├── builder.py               # ReportDataBuilder: compute metrics + charts → report_data.json
│   ├── renderer.py              # ReportRenderer: Jinja2 + report_data + narrative → HTML
│   ├── scorer.py                # CompositeScorer: 6-dimension scoring → grades
│   └── templates/
│       └── factor_report.html.j2  # Jinja2 HTML template (academic paper style)
tests/
├── mining/
│   └── report/
│       ├── test_scorer.py       # Unit tests for CompositeScorer
│       ├── test_builder.py      # Unit tests for ReportDataBuilder
│       └── test_renderer.py     # Unit tests for ReportRenderer
```

---

### Task 1: Composite Scorer

**Files:**
- Create: `mining/report/__init__.py`
- Create: `mining/report/scorer.py`
- Create: `tests/mining/report/test_scorer.py`

Pure logic, no DB or file dependencies. Easiest to test in isolation.

- [ ] **Step 1: Create package structure**

```bash
mkdir -p mining/report/templates tests/mining/report
touch mining/report/__init__.py tests/mining/__init__.py tests/mining/report/__init__.py
```

- [ ] **Step 2: Write failing tests for scorer**

Create `tests/mining/report/test_scorer.py`:

```python
"""Tests for CompositeScorer."""
import pytest
from mining.report.scorer import CompositeScorer


class TestScoreToGrade:
    def test_grade_a(self):
        assert CompositeScorer.score_to_grade(95) == "A"

    def test_grade_a_minus(self):
        assert CompositeScorer.score_to_grade(85) == "A-"

    def test_grade_b_plus(self):
        assert CompositeScorer.score_to_grade(77) == "B+"

    def test_grade_b(self):
        assert CompositeScorer.score_to_grade(70) == "B"

    def test_grade_c(self):
        assert CompositeScorer.score_to_grade(50) == "C"

    def test_grade_d(self):
        assert CompositeScorer.score_to_grade(20) == "D"

    def test_grade_boundary_90(self):
        assert CompositeScorer.score_to_grade(90) == "A"

    def test_grade_boundary_0(self):
        assert CompositeScorer.score_to_grade(0) == "D"


class TestDimensionScoring:
    def test_predictive_power_high_ic(self):
        s = CompositeScorer()
        score = s._score_predictive_power(0.10)
        assert score >= 80  # A range

    def test_predictive_power_low_ic(self):
        s = CompositeScorer()
        score = s._score_predictive_power(0.02)
        assert score < 35  # D range

    def test_predictive_power_medium_ic(self):
        s = CompositeScorer()
        score = s._score_predictive_power(0.058)
        assert 55 <= score <= 79  # B range

    def test_monotonicity_strong(self):
        s = CompositeScorer()
        score = s._score_monotonicity(-0.9)
        assert score >= 80  # A range

    def test_stability_consistent(self):
        s = CompositeScorer()
        score = s._score_stability(ic_is=-0.058, ic_oos=-0.057)
        assert score >= 80  # A range (delta < 10%)

    def test_stability_divergent(self):
        s = CompositeScorer()
        score = s._score_stability(ic_is=-0.058, ic_oos=-0.01)
        assert score < 35  # D range (delta > 50%)

    def test_decay_resistance_good(self):
        s = CompositeScorer()
        score = s._score_decay_resistance(ic_1d=-0.058, ic_20d=-0.045)
        assert 55 <= score <= 79  # B range (ratio ~0.78)

    def test_capacity_high(self):
        s = CompositeScorer()
        score = s._score_capacity(0.97)
        assert score >= 80  # A range

    def test_uniqueness_low_corr(self):
        s = CompositeScorer()
        score = s._score_uniqueness(0.2)
        assert score >= 80  # A range

    def test_uniqueness_high_corr(self):
        s = CompositeScorer()
        score = s._score_uniqueness(0.8)
        assert score < 35  # D range


class TestCompositeScore:
    def test_compute_returns_all_dimensions(self):
        s = CompositeScorer()
        result = s.compute(
            ic_mean=0.058,
            monotonicity=-0.9,
            ic_is=-0.058,
            ic_oos=-0.057,
            ic_1d=-0.058,
            ic_20d=-0.031,
            coverage=0.962,
            max_library_corr=0.0,
        )
        assert "dimensions" in result
        assert "composite" in result
        assert len(result["dimensions"]) == 6
        assert "score" in result["composite"]
        assert "grade" in result["composite"]

    def test_composite_is_average(self):
        s = CompositeScorer()
        result = s.compute(
            ic_mean=0.058,
            monotonicity=-0.9,
            ic_is=-0.058,
            ic_oos=-0.057,
            ic_1d=-0.058,
            ic_20d=-0.031,
            coverage=0.962,
            max_library_corr=0.0,
        )
        dim_scores = [d["score"] for d in result["dimensions"]]
        expected_avg = sum(dim_scores) / len(dim_scores)
        assert result["composite"]["score"] == pytest.approx(expected_avg, abs=0.5)
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `python3 -m pytest tests/mining/report/test_scorer.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'mining.report.scorer'`

- [ ] **Step 4: Implement scorer.py**

Create `mining/report/scorer.py`:

```python
"""Composite factor scorer — 6-dimension scoring with letter grades."""
from __future__ import annotations


class CompositeScorer:
    """Score a factor across 6 dimensions and compute a composite grade."""

    # Grade scale: score → letter
    _GRADE_SCALE = [
        (90, "A"), (80, "A-"), (75, "B+"), (65, "B"), (60, "B-"),
        (55, "C+"), (45, "C"), (35, "C-"), (0, "D"),
    ]

    @staticmethod
    def score_to_grade(score: float) -> str:
        for threshold, grade in CompositeScorer._GRADE_SCALE:
            if score >= threshold:
                return grade
        return "D"

    @staticmethod
    def _interpolate(value: float, lo: float, hi: float, score_lo: float, score_hi: float) -> float:
        """Linear interpolation of value within [lo, hi] → [score_lo, score_hi], clamped."""
        if hi == lo:
            return score_hi
        t = (value - lo) / (hi - lo)
        t = max(0.0, min(1.0, t))
        return score_lo + t * (score_hi - score_lo)

    def _score_predictive_power(self, ic_mean_abs: float) -> float:
        if ic_mean_abs >= 0.08:
            return self._interpolate(ic_mean_abs, 0.08, 0.15, 80, 100)
        if ic_mean_abs >= 0.05:
            return self._interpolate(ic_mean_abs, 0.05, 0.08, 55, 79)
        if ic_mean_abs >= 0.03:
            return self._interpolate(ic_mean_abs, 0.03, 0.05, 35, 54)
        return self._interpolate(ic_mean_abs, 0.0, 0.03, 0, 34)

    def _score_monotonicity(self, monotonicity: float) -> float:
        m = abs(monotonicity)
        if m >= 0.8:
            return self._interpolate(m, 0.8, 1.0, 80, 100)
        if m >= 0.6:
            return self._interpolate(m, 0.6, 0.8, 55, 79)
        if m >= 0.4:
            return self._interpolate(m, 0.4, 0.6, 35, 54)
        return self._interpolate(m, 0.0, 0.4, 0, 34)

    def _score_stability(self, ic_is: float, ic_oos: float) -> float:
        if ic_is == 0:
            return 0
        delta = abs(ic_is - ic_oos) / abs(ic_is)
        if delta < 0.10:
            return self._interpolate(delta, 0.0, 0.10, 100, 80)
        if delta < 0.25:
            return self._interpolate(delta, 0.10, 0.25, 79, 55)
        if delta < 0.50:
            return self._interpolate(delta, 0.25, 0.50, 54, 35)
        return self._interpolate(delta, 0.50, 1.0, 34, 0)

    def _score_decay_resistance(self, ic_1d: float, ic_20d: float) -> float:
        if ic_1d == 0:
            return 0
        ratio = abs(ic_20d) / abs(ic_1d)
        if ratio >= 0.7:
            return self._interpolate(ratio, 0.7, 1.0, 80, 100)
        if ratio >= 0.5:
            return self._interpolate(ratio, 0.5, 0.7, 55, 79)
        if ratio >= 0.3:
            return self._interpolate(ratio, 0.3, 0.5, 35, 54)
        return self._interpolate(ratio, 0.0, 0.3, 0, 34)

    def _score_capacity(self, coverage: float) -> float:
        if coverage >= 0.95:
            return self._interpolate(coverage, 0.95, 1.0, 80, 100)
        if coverage >= 0.85:
            return self._interpolate(coverage, 0.85, 0.95, 55, 79)
        if coverage >= 0.70:
            return self._interpolate(coverage, 0.70, 0.85, 35, 54)
        return self._interpolate(coverage, 0.0, 0.70, 0, 34)

    def _score_uniqueness(self, max_corr: float) -> float:
        if max_corr < 0.3:
            return self._interpolate(max_corr, 0.0, 0.3, 100, 80)
        if max_corr < 0.5:
            return self._interpolate(max_corr, 0.3, 0.5, 79, 55)
        if max_corr < 0.7:
            return self._interpolate(max_corr, 0.5, 0.7, 54, 35)
        return self._interpolate(max_corr, 0.7, 1.0, 34, 0)

    def compute(
        self,
        ic_mean: float,
        monotonicity: float,
        ic_is: float,
        ic_oos: float,
        ic_1d: float,
        ic_20d: float,
        coverage: float,
        max_library_corr: float,
    ) -> dict:
        dims = [
            {"name": "Predictive Power", "score": round(self._score_predictive_power(abs(ic_mean)), 1)},
            {"name": "Monotonicity", "score": round(self._score_monotonicity(monotonicity), 1)},
            {"name": "Stability", "score": round(self._score_stability(ic_is, ic_oos), 1)},
            {"name": "Decay Resistance", "score": round(self._score_decay_resistance(ic_1d, ic_20d), 1)},
            {"name": "Capacity", "score": round(self._score_capacity(coverage), 1)},
            {"name": "Uniqueness", "score": round(self._score_uniqueness(max_library_corr), 1)},
        ]
        for d in dims:
            d["grade"] = self.score_to_grade(d["score"])
        avg = sum(d["score"] for d in dims) / len(dims)
        return {
            "dimensions": dims,
            "composite": {"score": round(avg, 1), "grade": self.score_to_grade(avg)},
        }
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python3 -m pytest tests/mining/report/test_scorer.py -v`
Expected: All PASS

- [ ] **Step 6: Commit**

```bash
git add mining/report/__init__.py mining/report/scorer.py tests/mining/
git commit -m "feat(report): add CompositeScorer with 6-dimension factor scoring"
```

---

### Task 2: Report Data Builder — Core Data Loading & IC Analysis

**Files:**
- Create: `mining/report/builder.py`
- Create: `tests/mining/report/test_builder.py`

The builder is the largest module. We split it into two tasks: this one covers data loading, factor distribution, IC analysis (sections 3-4). Task 3 covers quintile, decay, scoring, and CLI (sections 5-7).

- [ ] **Step 1: Write failing tests for builder core**

Create `tests/mining/report/test_builder.py`:

```python
"""Tests for ReportDataBuilder — core data loading and IC computation."""
import json
import os
import tempfile

import numpy as np
import pandas as pd
import pytest

from mining.report.builder import ReportDataBuilder


@pytest.fixture
def sample_factor_values():
    """Create sample factor values with MultiIndex (datetime, instrument)."""
    dates = pd.bdate_range("2020-01-02", periods=500)
    symbols = [f"SH60000{i}" for i in range(50)]
    idx = pd.MultiIndex.from_product([dates, symbols], names=["datetime", "instrument"])
    np.random.seed(42)
    values = np.random.randn(len(idx)) * 0.02 + 0.03
    return pd.DataFrame({"factor": values}, index=idx)


@pytest.fixture
def sample_price_df(sample_factor_values):
    """Create matching price data as flat DataFrame."""
    idx = sample_factor_values.index
    dates = idx.get_level_values("datetime")
    symbols = idx.get_level_values("instrument")
    np.random.seed(123)
    close = 10.0 + np.cumsum(np.random.randn(len(idx)) * 0.02)
    return pd.DataFrame({
        "time": dates,
        "symbol": symbols,
        "close": close,
    })


class TestDistributionStats:
    def test_compute_distribution_stats(self, sample_factor_values):
        builder = ReportDataBuilder.__new__(ReportDataBuilder)
        stats = builder._compute_distribution_stats(sample_factor_values)
        assert "mean" in stats
        assert "std" in stats
        assert "skewness" in stats
        assert "kurtosis" in stats
        assert "coverage" in stats
        assert "nan_ratio" in stats
        assert 0 <= stats["coverage"] <= 1

    def test_distribution_with_nans(self):
        dates = pd.bdate_range("2020-01-02", periods=10)
        symbols = ["A", "B"]
        idx = pd.MultiIndex.from_product([dates, symbols], names=["datetime", "instrument"])
        values = [1.0, 2.0, np.nan, 3.0] * 5
        df = pd.DataFrame({"factor": values}, index=idx)
        builder = ReportDataBuilder.__new__(ReportDataBuilder)
        stats = builder._compute_distribution_stats(df)
        assert stats["nan_ratio"] > 0
        assert stats["coverage"] < 1.0


class TestAnnualICBreakdown:
    def test_annual_breakdown_structure(self):
        """Annual breakdown should return list of dicts with year, ic_mean, ic_ir, win_rate, regime."""
        dates = pd.bdate_range("2020-01-02", "2022-12-30")
        np.random.seed(42)
        daily_ic = pd.DataFrame({
            "date": dates,
            "IC": np.random.randn(len(dates)) * 0.1 - 0.05,
        })
        builder = ReportDataBuilder.__new__(ReportDataBuilder)
        result = builder._compute_annual_breakdown(daily_ic)
        assert len(result) >= 2
        first = result[0]
        assert "year" in first
        assert "ic_mean" in first
        assert "ic_ir" in first
        assert "win_rate" in first
        assert "regime" in first
        assert first["regime"] in ("bull", "bear", "sideways")


class TestMonthlyHeatmap:
    def test_monthly_heatmap_data(self):
        dates = pd.bdate_range("2020-01-02", "2021-12-30")
        np.random.seed(42)
        daily_ic = pd.DataFrame({
            "date": dates,
            "IC": np.random.randn(len(dates)) * 0.1 - 0.05,
        })
        builder = ReportDataBuilder.__new__(ReportDataBuilder)
        result = builder._compute_monthly_heatmap_data(daily_ic)
        assert len(result) > 0
        assert len(result[0]) == 3  # [year, month, ic_mean]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/mining/report/test_builder.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement builder.py — data loading, distribution, IC analysis**

Create `mining/report/builder.py`. This is a large file; the key methods are:

```python
"""ReportDataBuilder — compute all metrics and charts for factor reports."""
from __future__ import annotations

import argparse
import json
import logging
import os
from datetime import datetime

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from scipy import stats as sp_stats

from mining.config import MiningConfig
from mining.report.scorer import CompositeScorer

logger = logging.getLogger(__name__)

# Market regime lookup (CSI 300 annual returns)
_REGIME_LOOKUP = {
    2015: "bear", 2016: "sideways", 2017: "bull", 2018: "bear", 2019: "bull",
    2020: "bull", 2021: "sideways", 2022: "bear", 2023: "bear", 2024: "sideways",
    2025: "sideways",
}


class ReportDataBuilder:
    """Compute all metrics and Plotly charts for a factor report.

    Usage:
        builder = ReportDataBuilder(factor_id="001", config=MiningConfig())
        data = builder.build()  # returns dict matching report_data.json schema
    """

    def __init__(self, factor_id: str, config: MiningConfig | None = None):
        self.factor_id = factor_id
        self.config = config or MiningConfig()
        self._conn = None

    def build(self) -> dict:
        """Run full computation pipeline, return report_data dict."""
        factor_meta = self._load_factor_metadata()
        factor_values, price_df = self._load_data_from_db()
        split_date = pd.Timestamp(self.config.test_start)

        # Split IS / OOS
        fv_is = factor_values[factor_values.index.get_level_values("datetime") < split_date]
        fv_oos = factor_values[factor_values.index.get_level_values("datetime") >= split_date]

        # Flatten for ic_analyzer / group_returns compatibility
        flat_factor = self._to_flat_df(factor_values)
        flat_is = self._to_flat_df(fv_is) if len(fv_is) > 0 else pd.DataFrame()
        flat_oos = self._to_flat_df(fv_oos) if len(fv_oos) > 0 else pd.DataFrame()

        # IC analysis (reuse ic_analyzer)
        from visualization.ic_analyzer import ICAnalyzer
        ic = ICAnalyzer(factor_meta["name"])
        ic_result = ic.compute_ic(flat_factor, price_df, split_date)
        daily_ic = ic_result.get("rolling_ic", pd.DataFrame())

        # Distribution stats
        dist_is = self._compute_distribution_stats(fv_is)
        dist_oos = self._compute_distribution_stats(fv_oos) if len(fv_oos) > 100 else None

        # Annual + monthly breakdown
        annual = self._compute_annual_breakdown(daily_ic) if len(daily_ic) > 0 else []
        monthly = self._compute_monthly_heatmap_data(daily_ic) if len(daily_ic) > 0 else []

        # Quintile analysis (reuse group_returns)
        from visualization.group_returns import GroupReturnsAnalyzer
        gr = GroupReturnsAnalyzer(factor_meta["name"])
        gr_result = gr.compute_group_returns(flat_factor, price_df, n_groups=5, split_date=split_date)

        # Quintile detailed stats
        quintile_stats = self._compute_quintile_detailed_stats(gr_result)

        # IS vs OOS quintile
        gr_is = gr.compute_group_returns(flat_is, price_df, n_groups=5) if len(flat_is) > 100 else {}
        gr_oos = gr.compute_group_returns(flat_oos, price_df, n_groups=5) if len(flat_oos) > 100 else {}

        # Decay analysis
        decay = self._compute_decay(flat_factor, price_df)

        # Factor autocorrelation
        autocorr = self._compute_autocorrelation(factor_values)

        # Composite score
        ic_1d = decay["ic_by_period"][0]["ic"] if decay["ic_by_period"] else 0
        ic_20d_entry = next((d for d in decay["ic_by_period"] if d["period"] == 20), None)
        ic_20d = ic_20d_entry["ic"] if ic_20d_entry else ic_1d
        max_lib_corr = self._get_max_library_correlation()

        scorer = CompositeScorer()
        scores = scorer.compute(
            ic_mean=ic_result.get("ic_all", 0),
            monotonicity=gr_result.get("monotonicity", 0) if "monotonicity" in gr_result else self._compute_monotonicity(gr_result),
            ic_is=ic_result.get("ic_train", ic_result.get("ic_all", 0)),
            ic_oos=ic_result.get("ic_test", ic_result.get("ic_all", 0)),
            ic_1d=ic_1d,
            ic_20d=ic_20d,
            coverage=dist_is.get("coverage", 0.9),
            max_library_corr=max_lib_corr,
        )

        # Generate all charts
        charts_ic = self._generate_ic_charts(ic, ic_result, daily_ic, split_date, annual, monthly)
        charts_quintile = self._generate_quintile_charts(gr, gr_result, gr_is, gr_oos)
        charts_dist = self._generate_distribution_charts(fv_is, fv_oos, factor_meta["name"])
        charts_decay = self._generate_decay_charts(decay, autocorr, factor_meta["name"])
        charts_score = self._generate_score_charts(scores, factor_meta["name"])

        # Assemble report_data
        ic_summary_is = {
            "ic_mean": ic_result.get("ic_train", ic_result.get("ic_all", 0)),
            "ic_std": daily_ic[daily_ic.get("period", "train") == "train"]["IC"].std() if "period" in daily_ic.columns else daily_ic["IC"].std(),
            "ic_ir": 0, "win_rate": 0, "ic_significant_rate": 0, "n_days": 0,
        }
        # Compute properly from daily_ic
        if len(daily_ic) > 0:
            ic_summary_is, ic_summary_oos = self._compute_ic_summary(daily_ic, split_date)
        else:
            ic_summary_oos = ic_summary_is.copy()

        return {
            "factor": factor_meta,
            "preprocessing": {
                "filter_suspend": self.config.filter_suspend,
                "filter_limit": self.config.filter_limit,
                "winsorize_method": self.config.winsorize_method,
                "winsorize_n": self.config.winsorize_n,
                "standardize_method": self.config.standardize_method,
                "neutralize_mode": self.config.neutralize_mode,
            },
            "kpi": {
                "ic_mean_is": ic_summary_is["ic_mean"],
                "ic_mean_oos": ic_summary_oos["ic_mean"],
                "ic_ir": ic_summary_is["ic_ir"],
                "ic_win_rate": ic_summary_is["win_rate"],
                "monotonicity": self._compute_monotonicity(gr_result),
                "ls_return": (gr_result.get("mean_returns", pd.Series()).get("Q1", 0) - gr_result.get("mean_returns", pd.Series()).get("Q5", 0)),
                "composite_grade": scores["composite"]["grade"],
            },
            "distribution": {
                "stats_is": dist_is,
                "stats_oos": dist_oos,
                "charts": charts_dist,
            },
            "ic_analysis": {
                "summary": {"is": ic_summary_is, "oos": ic_summary_oos},
                "annual": annual,
                "monthly_heatmap_data": monthly,
                "charts": charts_ic,
            },
            "quintile": {
                "stats": quintile_stats["quintiles"],
                "ls_stats": quintile_stats["ls"],
                "charts": charts_quintile,
            },
            "decay": {
                "ic_by_period": decay["ic_by_period"],
                "autocorrelation": autocorr,
                "half_life_days": decay.get("half_life_days", None),
                "charts": charts_decay,
            },
            "scores": {**scores, "charts": charts_score},
        }

    # ---- Data Loading ----

    def _load_factor_metadata(self) -> dict:
        """Load factor YAML from library."""
        import yaml
        path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "library", "factors", f"factor_{self.factor_id}.yaml",
        )
        with open(path) as f:
            meta = yaml.safe_load(f)
        return {
            "id": meta["id"],
            "name": meta["name"],
            "expression": meta["expression"],
            "category": meta.get("category", "other"),
            "batch": meta.get("batch", ""),
            "admitted_at": str(meta.get("admitted_at", "")),
        }

    def _load_data_from_db(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Load factor values and price data from DB."""
        import psycopg2
        conn = psycopg2.connect(self.config.system.database.connection_string)
        try:
            # Factor values
            fv_sql = "SELECT symbol, trade_date, value FROM mining_factor_values WHERE factor_id = %s ORDER BY trade_date, symbol"
            fv = pd.read_sql(fv_sql, conn, params=[self.factor_id])
            fv["trade_date"] = pd.to_datetime(fv["trade_date"])
            fv = fv.set_index(["trade_date", "symbol"]).rename(columns={"value": "factor"})
            fv.index.names = ["datetime", "instrument"]

            # Price data
            symbols = fv.index.get_level_values("instrument").unique().tolist()
            start = fv.index.get_level_values("datetime").min()
            end = fv.index.get_level_values("datetime").max()
            price_sql = "SELECT symbol, time, close FROM price_daily WHERE symbol = ANY(%s) AND time BETWEEN %s AND %s"
            price_df = pd.read_sql(price_sql, conn, params=[symbols, start, end])
            return fv, price_df
        finally:
            conn.close()

    @staticmethod
    def _to_flat_df(qlib_df: pd.DataFrame) -> pd.DataFrame:
        df = qlib_df.iloc[:, [0]].reset_index()
        df.columns = ["time", "symbol", "value"]
        return df

    # ---- Distribution ----

    def _compute_distribution_stats(self, factor_values: pd.DataFrame) -> dict:
        vals = factor_values.iloc[:, 0]
        total = len(vals)
        non_nan = vals.dropna()
        if len(non_nan) < 10:
            return {"mean": 0, "std": 0, "skewness": 0, "kurtosis": 0, "coverage": 0, "nan_ratio": 1.0}
        return {
            "mean": round(float(non_nan.mean()), 6),
            "std": round(float(non_nan.std()), 6),
            "skewness": round(float(sp_stats.skew(non_nan)), 4),
            "kurtosis": round(float(sp_stats.kurtosis(non_nan)), 4),
            "coverage": round(len(non_nan) / total, 4) if total > 0 else 0,
            "nan_ratio": round(1 - len(non_nan) / total, 4) if total > 0 else 1.0,
        }

    # ---- IC Analysis ----

    def _compute_ic_summary(self, daily_ic: pd.DataFrame, split_date) -> tuple[dict, dict]:
        """Compute IC summary stats for IS and OOS from daily IC DataFrame."""
        def _summarize(ic_series):
            if len(ic_series) < 5:
                return {"ic_mean": 0, "ic_std": 0, "ic_ir": 0, "win_rate": 0, "ic_significant_rate": 0, "n_days": 0}
            m = float(ic_series.mean())
            s = float(ic_series.std())
            return {
                "ic_mean": round(m, 6),
                "ic_std": round(s, 6),
                "ic_ir": round(m / s, 4) if s > 0 else 0,
                "win_rate": round(float((ic_series > 0).mean()), 4),
                "ic_significant_rate": round(float((ic_series.abs() > 0.02).mean()), 4),
                "n_days": len(ic_series),
            }

        if "period" in daily_ic.columns:
            is_ic = daily_ic[daily_ic["period"] == "train"]["IC"]
            oos_ic = daily_ic[daily_ic["period"] == "test"]["IC"]
        else:
            is_ic = daily_ic[daily_ic["date"] < split_date]["IC"]
            oos_ic = daily_ic[daily_ic["date"] >= split_date]["IC"]

        return _summarize(is_ic), _summarize(oos_ic)

    def _compute_annual_breakdown(self, daily_ic: pd.DataFrame) -> list[dict]:
        daily_ic = daily_ic.copy()
        daily_ic["year"] = pd.to_datetime(daily_ic["date"]).dt.year
        result = []
        for year, group in daily_ic.groupby("year"):
            ic = group["IC"]
            if len(ic) < 20:
                continue
            m = float(ic.mean())
            s = float(ic.std())
            result.append({
                "year": int(year),
                "ic_mean": round(m, 4),
                "ic_ir": round(m / s, 4) if s > 0 else 0,
                "win_rate": round(float((ic > 0).mean()), 4),
                "regime": _REGIME_LOOKUP.get(int(year), "sideways"),
            })
        return result

    def _compute_monthly_heatmap_data(self, daily_ic: pd.DataFrame) -> list:
        daily_ic = daily_ic.copy()
        daily_ic["date"] = pd.to_datetime(daily_ic["date"])
        daily_ic["year"] = daily_ic["date"].dt.year
        daily_ic["month"] = daily_ic["date"].dt.month
        grouped = daily_ic.groupby(["year", "month"])["IC"].mean()
        return [[int(y), int(m), round(float(v), 4)] for (y, m), v in grouped.items()]

    # ---- Quintile ----

    def _compute_quintile_detailed_stats(self, gr_result: dict) -> dict:
        """Compute detailed per-quintile stats: ann_return, ann_vol, sharpe, max_dd, calmar, win_days."""
        if "error" in gr_result or "group_returns_pivot" not in gr_result:
            return {"quintiles": [], "ls": {}}
        pivot = gr_result["group_returns_pivot"]
        cum = gr_result["cumulative_returns"]
        quintiles = []
        for q in pivot.columns:
            r = pivot[q]
            ann_ret = float(r.mean() * 252)
            ann_vol = float(r.std() * np.sqrt(252))
            sharpe = ann_ret / ann_vol if ann_vol > 0 else 0
            cum_q = cum[q]
            peak = cum_q.cummax()
            dd = (cum_q - peak).min()
            calmar = ann_ret / abs(dd) if dd != 0 else 0
            win_days = float((r > 0).mean())
            quintiles.append({
                "quintile": str(q),
                "ann_return": round(ann_ret, 6),
                "ann_vol": round(ann_vol, 6),
                "sharpe": round(sharpe, 4),
                "max_dd": round(float(dd), 6),
                "calmar": round(calmar, 4),
                "win_days": round(win_days, 4),
            })
        # LS stats (Q1 - Q5)
        if "Q1" in pivot.columns and "Q5" in pivot.columns:
            ls = pivot["Q1"] - pivot["Q5"]
            ls_cum = (1 + ls).cumprod() - 1
            ann_ret = float(ls.mean() * 252)
            ann_vol = float(ls.std() * np.sqrt(252))
            peak = ls_cum.cummax()
            dd = (ls_cum - peak).min()
            ls_stats = {
                "ann_return": round(ann_ret, 6),
                "ann_vol": round(ann_vol, 6),
                "sharpe": round(ann_ret / ann_vol if ann_vol > 0 else 0, 4),
                "max_dd": round(float(dd), 6),
                "calmar": round(ann_ret / abs(dd) if dd != 0 else 0, 4),
                "win_days": round(float((ls > 0).mean()), 4),
            }
        else:
            ls_stats = {}
        return {"quintiles": quintiles, "ls": ls_stats}

    def _compute_monotonicity(self, gr_result: dict) -> float:
        if "mean_returns" not in gr_result:
            return 0
        mr = gr_result["mean_returns"]
        if len(mr) < 3:
            return 0
        ranks = list(range(1, len(mr) + 1))
        corr, _ = sp_stats.spearmanr(ranks, mr.values)
        return round(float(corr), 4)

    # ---- Decay ----

    def _compute_decay(self, flat_factor: pd.DataFrame, price_df: pd.DataFrame) -> dict:
        merged = pd.merge(flat_factor, price_df, on=["time", "symbol"], how="inner")
        merged = merged.sort_values(["symbol", "time"])
        periods = [1, 5, 10, 20, 60]
        results = []
        base_ic = None
        for period in periods:
            merged[f"ret_{period}"] = merged.groupby("symbol")["close"].pct_change(period).shift(-period)
            valid = merged.dropna(subset=["value", f"ret_{period}"])
            if len(valid) < 100:
                continue
            daily_ic = valid.groupby("time").apply(
                lambda x: x["value"].corr(x[f"ret_{period}"], method="spearman") if len(x) > 3 else np.nan
            ).dropna()
            ic = float(daily_ic.mean())
            if base_ic is None:
                base_ic = ic
            ratio = abs(ic / base_ic) if base_ic != 0 else 0
            results.append({"period": period, "ic": round(ic, 6), "ratio": round(ratio, 4)})
        # Estimate half-life
        half_life = None
        for r in results:
            if r["ratio"] <= 0.5:
                half_life = r["period"]
                break
        return {"ic_by_period": results, "half_life_days": half_life}

    def _compute_autocorrelation(self, factor_values: pd.DataFrame) -> list:
        """Compute factor value autocorrelation at lags 1-20."""
        result = []
        for lag in [1, 2, 3, 5, 10, 15, 20]:
            corrs = []
            for date in factor_values.index.get_level_values("datetime").unique()[lag:]:
                try:
                    current = factor_values.xs(date, level="datetime").iloc[:, 0]
                    prev_date = factor_values.index.get_level_values("datetime").unique()[
                        factor_values.index.get_level_values("datetime").unique().get_loc(date) - lag
                    ]
                    prev = factor_values.xs(prev_date, level="datetime").iloc[:, 0]
                    common = current.index.intersection(prev.index)
                    if len(common) > 10:
                        corrs.append(current[common].corr(prev[common], method="spearman"))
                except (KeyError, IndexError):
                    continue
                if len(corrs) >= 50:
                    break
            if corrs:
                result.append({"lag": lag, "corr": round(float(np.mean(corrs)), 4)})
        return result

    def _get_max_library_correlation(self) -> float:
        """Get max correlation with other library factors. Returns 0 if only factor."""
        import yaml
        lib_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "library", "library.yaml")
        with open(lib_path) as f:
            lib = yaml.safe_load(f)
        factors = lib.get("factors", [])
        if len(factors) <= 1:
            return 0.0
        # For now, return a placeholder. Full computation requires loading all factor values.
        return 0.0

    # ---- Chart Generation (all return HTML div strings) ----

    def _fig_to_html(self, fig: go.Figure) -> str:
        return pio.to_html(fig, full_html=False, include_plotlyjs=False)

    def _generate_ic_charts(self, ic_analyzer, ic_result, daily_ic, split_date, annual, monthly) -> dict:
        charts = {}
        try:
            if "rolling_ic" in ic_result:
                fig = ic_analyzer.plot_ic_timeseries(ic_result["rolling_ic"], split_date)
                charts["ic_timeseries"] = self._fig_to_html(fig)
                fig = ic_analyzer.plot_ic_distribution(ic_result["rolling_ic"])
                charts["ic_distribution"] = self._fig_to_html(fig)
            if len(daily_ic) > 0 and "date" in daily_ic.columns:
                fig = ic_analyzer.plot_rolling_ic_comparison(daily_ic.set_index("date")["IC"])
                charts["rolling_ic"] = self._fig_to_html(fig)
            # Cumulative IC (NEW)
            if len(daily_ic) > 0:
                cum_ic = daily_ic["IC"].cumsum()
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=daily_ic["date"], y=cum_ic, mode="lines", name="Cumulative IC"))
                fig.add_hline(y=0, line_dash="dot", line_color="black")
                fig.update_layout(title="Cumulative IC", template="plotly_white", height=350,
                                  xaxis_title="Date", yaxis_title="Cumulative IC")
                charts["cumulative_ic"] = self._fig_to_html(fig)
            # Monthly heatmap (NEW)
            if monthly:
                years = sorted(set(r[0] for r in monthly))
                months = list(range(1, 13))
                z = [[next((r[2] for r in monthly if r[0] == y and r[1] == m), None) for m in months] for y in years]
                fig = go.Figure(data=go.Heatmap(
                    z=z, x=[str(m) for m in months], y=[str(y) for y in years],
                    colorscale="RdBu_r", zmid=0,
                ))
                fig.update_layout(title="Monthly IC Heatmap", template="plotly_white", height=300,
                                  xaxis_title="Month", yaxis_title="Year")
                charts["monthly_heatmap"] = self._fig_to_html(fig)
        except Exception as e:
            logger.warning("IC chart generation error: %s", e)
        return charts

    def _generate_quintile_charts(self, gr_analyzer, gr_result, gr_is, gr_oos) -> dict:
        charts = {}
        try:
            if "mean_returns" in gr_result:
                fig = gr_analyzer.plot_group_returns_bar(gr_result["mean_returns"])
                charts["quintile_bar"] = self._fig_to_html(fig)
            if "cumulative_returns" in gr_result:
                fig = gr_analyzer.plot_cumulative_returns(gr_result["cumulative_returns"])
                charts["cumulative_returns"] = self._fig_to_html(fig)
                if "Q5" in gr_result["cumulative_returns"].columns and "Q1" in gr_result["cumulative_returns"].columns:
                    fig = gr_analyzer.plot_long_short(gr_result["cumulative_returns"])
                    charts["long_short_curve"] = self._fig_to_html(fig)
            # IS vs OOS bar (NEW)
            if "mean_returns" in gr_is and "mean_returns" in gr_oos:
                fig = go.Figure()
                fig.add_trace(go.Bar(x=gr_is["mean_returns"].index, y=gr_is["mean_returns"].values * 100, name="In-Sample"))
                fig.add_trace(go.Bar(x=gr_oos["mean_returns"].index, y=gr_oos["mean_returns"].values * 100, name="Out-of-Sample"))
                fig.update_layout(title="IS vs OOS Quintile Returns", barmode="group", template="plotly_white", height=350)
                charts["is_vs_oos_bar"] = self._fig_to_html(fig)
        except Exception as e:
            logger.warning("Quintile chart generation error: %s", e)
        return charts

    def _generate_distribution_charts(self, fv_is, fv_oos, name) -> dict:
        charts = {}
        try:
            fig = go.Figure()
            fig.add_trace(go.Histogram(x=fv_is.iloc[:, 0].dropna(), name="In-Sample", opacity=0.6, histnorm="probability density"))
            if len(fv_oos) > 0:
                fig.add_trace(go.Histogram(x=fv_oos.iloc[:, 0].dropna(), name="Out-of-Sample", opacity=0.6, histnorm="probability density"))
            fig.update_layout(title=f"{name} Factor Distribution IS vs OOS", template="plotly_white", height=350, barmode="overlay")
            charts["distribution_overlay"] = self._fig_to_html(fig)

            # Coverage time series
            fv_all = pd.concat([fv_is, fv_oos]) if len(fv_oos) > 0 else fv_is
            coverage = fv_all.groupby(level="datetime").apply(lambda x: x.iloc[:, 0].notna().mean())
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=coverage.index, y=coverage.values, mode="lines", name="Coverage"))
            fig.update_layout(title="Factor Coverage Rate", template="plotly_white", height=300)
            charts["coverage_timeseries"] = self._fig_to_html(fig)
        except Exception as e:
            logger.warning("Distribution chart error: %s", e)
        return charts

    def _generate_decay_charts(self, decay, autocorr, name) -> dict:
        charts = {}
        try:
            if decay["ic_by_period"]:
                periods = [str(d["period"]) + "d" for d in decay["ic_by_period"]]
                ics = [d["ic"] for d in decay["ic_by_period"]]
                fig = go.Figure(data=go.Bar(x=periods, y=ics))
                fig.add_hline(y=0, line_dash="dot")
                fig.update_layout(title=f"{name} IC Decay", template="plotly_white", height=350)
                charts["ic_decay_bar"] = self._fig_to_html(fig)
            if autocorr:
                lags = [a["lag"] for a in autocorr]
                corrs = [a["corr"] for a in autocorr]
                fig = go.Figure(data=go.Scatter(x=lags, y=corrs, mode="lines+markers"))
                fig.update_layout(title=f"{name} Factor Autocorrelation", template="plotly_white", height=350,
                                  xaxis_title="Lag (days)", yaxis_title="Spearman Correlation")
                charts["autocorrelation"] = self._fig_to_html(fig)
        except Exception as e:
            logger.warning("Decay chart error: %s", e)
        return charts

    def _generate_score_charts(self, scores, name) -> dict:
        charts = {}
        try:
            dims = scores["dimensions"]
            names = [d["name"] for d in dims]
            values = [d["score"] for d in dims]
            fig = go.Figure(data=go.Scatterpolar(r=values + [values[0]], theta=names + [names[0]], fill="toself"))
            fig.update_layout(title=f"{name} Composite Score", template="plotly_white", height=400,
                              polar=dict(radialaxis=dict(visible=True, range=[0, 100])))
            charts["radar"] = self._fig_to_html(fig)
        except Exception as e:
            logger.warning("Score chart error: %s", e)
        return charts

    def save(self, output_dir: str) -> str:
        """Build report data and save to JSON."""
        os.makedirs(output_dir, exist_ok=True)
        data = self.build()
        path = os.path.join(output_dir, "report_data.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        logger.info("Report data saved to %s", path)
        return path


def main():
    parser = argparse.ArgumentParser(description="Build factor report data")
    parser.add_argument("--factor-id", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    builder = ReportDataBuilder(args.factor_id)
    builder.save(args.output_dir)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/mining/report/test_builder.py -v`
Expected: All PASS (tests only exercise pure-computation methods, not DB loading)

- [ ] **Step 5: Commit**

```bash
git add mining/report/builder.py tests/mining/report/test_builder.py
git commit -m "feat(report): add ReportDataBuilder with IC, distribution, quintile, decay, chart generation"
```

---

### Task 3: Jinja2 Template

**Files:**
- Create: `mining/report/templates/factor_report.html.j2`

The template is large (~400 lines of HTML/CSS/Jinja2) but is pure markup with no logic beyond `{% if %}` guards. No tests needed for the template itself — it's validated via integration test in Task 5.

- [ ] **Step 1: Create the Jinja2 template**

Create `mining/report/templates/factor_report.html.j2`. The template should match the mockup design from brainstorming (academic paper style, 8 sections). Key structure:

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>Factor Report: {{ factor.name }}</title>
    <script src="https://cdn.plot.ly/plotly-basic-2.35.2.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
    <style>
        /* Academic paper styling: Georgia/Noto Serif SC, white bg, section borders */
        /* ~150 lines of CSS for the full report layout */
    </style>
</head>
<body>
    <!-- Header: factor name, LaTeX formula, KPI strip -->
    <!-- Section 1: Construction Logic (from narrative) -->
    <!-- Section 2: Economic Interpretation (from narrative) -->
    <!-- Section 3: Factor Distribution (charts + narrative) -->
    <!-- Section 4: IC Analysis (charts + tables + narrative) -->
    <!-- Section 5: Quintile Analysis (charts + tables + narrative) -->
    <!-- Section 6: Decay & Persistence (charts + tables + narrative) -->
    <!-- Section 7: Composite Scorecard (radar + table + narrative) -->
    <!-- Section 8: Critical Review (narrative) -->
    <!-- Footer -->
</body>
</html>
```

The full template is ~400 lines. The implementer should build it section by section, following the mockup at `.superpowers/brainstorm/64158-1774285785/report-sections-v2.html` and the spec's visual design guidelines. Each chart is injected via `{{ charts.chart_name | safe }}` with a fallback: `{% if charts.chart_name %}{{ charts.chart_name | safe }}{% else %}<div class="chart-unavailable">Chart unavailable</div>{% endif %}`.

- [ ] **Step 2: Commit**

```bash
git add mining/report/templates/factor_report.html.j2
git commit -m "feat(report): add Jinja2 HTML template for factor reports"
```

---

### Task 4: Report Renderer

**Files:**
- Create: `mining/report/renderer.py`
- Create: `tests/mining/report/test_renderer.py`

- [ ] **Step 1: Write failing tests for renderer**

Create `tests/mining/report/test_renderer.py`:

```python
"""Tests for ReportRenderer."""
import json
import os
import tempfile

import pytest

from mining.report.renderer import ReportRenderer


@pytest.fixture
def minimal_report_data():
    return {
        "factor": {
            "id": "001", "name": "test_factor", "expression": "Std($close, 20)",
            "category": "volatility", "batch": "batch_001", "admitted_at": "2026-03-23",
        },
        "preprocessing": {
            "filter_suspend": True, "filter_limit": True, "winsorize_method": "mad",
            "winsorize_n": 5.0, "standardize_method": "zscore", "neutralize_mode": "none",
        },
        "kpi": {
            "ic_mean_is": -0.058, "ic_mean_oos": -0.057, "ic_ir": -0.304,
            "ic_win_rate": 0.375, "monotonicity": -0.9, "ls_return": -0.22,
            "composite_grade": "C+",
        },
        "distribution": {"stats_is": {"mean": 0.03, "std": 0.02, "skewness": 2.0, "kurtosis": 8.0, "coverage": 0.96, "nan_ratio": 0.04}, "stats_oos": None, "charts": {}},
        "ic_analysis": {"summary": {"is": {"ic_mean": -0.058, "ic_std": 0.19, "ic_ir": -0.304, "win_rate": 0.375, "ic_significant_rate": 0.62, "n_days": 1200}, "oos": {"ic_mean": -0.057, "ic_std": 0.185, "ic_ir": -0.308, "win_rate": 0.382, "ic_significant_rate": 0.64, "n_days": 60}}, "annual": [], "monthly_heatmap_data": [], "charts": {}},
        "quintile": {"stats": [], "ls_stats": {}, "charts": {}},
        "decay": {"ic_by_period": [], "autocorrelation": [], "half_life_days": None, "charts": {}},
        "scores": {"dimensions": [{"name": "Predictive Power", "score": 45, "grade": "C"}], "composite": {"score": 45, "grade": "C"}, "charts": {}},
    }


@pytest.fixture
def minimal_narrative():
    return {
        "factor_metadata": {"name_cn": "测试因子", "expression_latex": "\\sigma_{20}"},
        "construction_logic": {"formula_decomposition": "公式分解...", "parameter_rationale": "参数选择...", "preprocessing_notes": "预处理..."},
        "economic_interpretation": {"theoretical_foundations": "理论基础...", "attribution_angles": [{"title": "角度1", "icon": "📊", "body": "内容..."}], "china_context": "A股特殊性..."},
        "section_interpretations": {"distribution": "分布解读...", "ic_annual": "年度IC...", "ic_monthly": "月度IC...", "quintile": "分层解读...", "decay": "衰减解读...", "composite": "综合评分..."},
        "critical_review": {"one_liner": "一句话总结", "body": "详细批评...", "key_weaknesses": [{"title": "弱点1", "detail": "描述..."}], "improvement_directions": ["建议1"]},
    }


class TestReportRenderer:
    def test_render_produces_html(self, minimal_report_data, minimal_narrative):
        renderer = ReportRenderer()
        html = renderer.render(minimal_report_data, minimal_narrative)
        assert "<!DOCTYPE html>" in html
        assert "测试因子" in html
        assert "test_factor" in html

    def test_render_contains_kpi(self, minimal_report_data, minimal_narrative):
        renderer = ReportRenderer()
        html = renderer.render(minimal_report_data, minimal_narrative)
        assert "-0.058" in html
        assert "C+" in html

    def test_render_contains_narrative(self, minimal_report_data, minimal_narrative):
        renderer = ReportRenderer()
        html = renderer.render(minimal_report_data, minimal_narrative)
        assert "公式分解" in html
        assert "一句话总结" in html

    def test_save_to_file(self, minimal_report_data, minimal_narrative, tmp_path):
        renderer = ReportRenderer()
        path = renderer.render_to_file(minimal_report_data, minimal_narrative, str(tmp_path), "001")
        assert os.path.exists(path)
        assert path.endswith(".html")
        content = open(path, encoding="utf-8").read()
        assert "<!DOCTYPE html>" in content

    def test_render_with_missing_narrative_keys(self, minimal_report_data):
        """Should handle missing narrative gracefully."""
        renderer = ReportRenderer()
        partial_narrative = {
            "factor_metadata": {"name_cn": "测试", "expression_latex": "x"},
        }
        html = renderer.render(minimal_report_data, partial_narrative)
        assert "<!DOCTYPE html>" in html  # Should not crash
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/mining/report/test_renderer.py -v`
Expected: FAIL

- [ ] **Step 3: Implement renderer.py**

Create `mining/report/renderer.py`:

```python
"""ReportRenderer — render report_data + narrative into HTML via Jinja2."""
from __future__ import annotations

import argparse
import json
import logging
import os
from datetime import datetime

from jinja2 import Environment, FileSystemLoader, select_autoescape

logger = logging.getLogger(__name__)


class ReportRenderer:
    """Render factor report HTML from report_data.json and narrative.json."""

    def __init__(self):
        template_dir = os.path.join(os.path.dirname(__file__), "templates")
        self._env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(default=False),
        )

    def render(self, report_data: dict, narrative: dict) -> str:
        """Render HTML string from data and narrative dicts."""
        template = self._env.get_template("factor_report.html.j2")
        # Merge into template context
        ctx = {
            "factor": report_data.get("factor", {}),
            "preprocessing": report_data.get("preprocessing", {}),
            "kpi": report_data.get("kpi", {}),
            "distribution": report_data.get("distribution", {}),
            "ic_analysis": report_data.get("ic_analysis", {}),
            "quintile": report_data.get("quintile", {}),
            "decay": report_data.get("decay", {}),
            "scores": report_data.get("scores", {}),
            "narrative": narrative,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        return template.render(**ctx)

    def render_to_file(self, report_data: dict, narrative: dict, output_dir: str, factor_id: str) -> str:
        """Render and save HTML to output_dir/factor_{id}_report.html."""
        os.makedirs(output_dir, exist_ok=True)
        html = self.render(report_data, narrative)
        path = os.path.join(output_dir, f"factor_{factor_id}_report.html")
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        logger.info("Report saved to %s", path)
        return path


def main():
    parser = argparse.ArgumentParser(description="Render factor report HTML")
    parser.add_argument("--input-dir", required=True, help="Dir containing report_data.json and narrative.json")
    parser.add_argument("--output-dir", required=True, help="Dir to save HTML report")
    args = parser.parse_args()

    with open(os.path.join(args.input_dir, "report_data.json"), encoding="utf-8") as f:
        report_data = json.load(f)
    with open(os.path.join(args.input_dir, "narrative.json"), encoding="utf-8") as f:
        narrative = json.load(f)

    factor_id = report_data["factor"]["id"]
    renderer = ReportRenderer()
    path = renderer.render_to_file(report_data, narrative, args.output_dir, factor_id)
    print(f"Report: {path}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/mining/report/test_renderer.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add mining/report/renderer.py tests/mining/report/test_renderer.py
git commit -m "feat(report): add ReportRenderer with Jinja2 template rendering"
```

---

### Task 5: Integration Test — Generate Real Report for factor_001

**Files:**
- None created — this is a validation task

This task validates the full builder → renderer pipeline end-to-end using real data from the DB. Run this manually (not in CI) since it requires DB connectivity.

- [ ] **Step 1: Test builder with real data**

```bash
cd /Users/xinzhan/.openclaw/workspace/quant_factor_system
python3 -m mining.report.builder --factor-id 001 --output-dir /tmp/factor_report_001
```

Expected: `report_data.json` created at `/tmp/factor_report_001/report_data.json` with all sections populated.

- [ ] **Step 2: Inspect report_data.json**

Read `/tmp/factor_report_001/report_data.json` and verify:
- `factor.name` == "std_returns_20"
- `kpi.ic_mean_is` is a negative float around -0.05 to -0.06
- `distribution.stats_is` has reasonable values
- `ic_analysis.annual` has entries for 2020-2024
- `quintile.stats` has 5 entries (Q1-Q5)
- `scores.composite.grade` is a letter grade
- All `charts` keys contain `<div` HTML strings

- [ ] **Step 3: Create a test narrative.json**

Write a minimal `narrative.json` to `/tmp/factor_report_001/narrative.json` for testing the renderer:

```json
{
  "factor_metadata": {"name_cn": "20日波动率因子", "expression_latex": "\\sigma_{20} = \\text{Std}(r_t, 20)"},
  "construction_logic": {"formula_decomposition": "测试公式分解", "parameter_rationale": "测试参数选择", "preprocessing_notes": "测试预处理"},
  "economic_interpretation": {"theoretical_foundations": "测试理论基础", "attribution_angles": [{"title": "测试角度", "icon": "📊", "body": "测试内容"}], "china_context": "测试A股特殊性"},
  "section_interpretations": {"distribution": "测试分布", "ic_annual": "测试年度IC", "ic_monthly": "测试月度IC", "quintile": "测试分层", "decay": "测试衰减", "composite": "测试综合"},
  "critical_review": {"one_liner": "测试一句话", "body": "测试批评正文", "key_weaknesses": [{"title": "测试弱点", "detail": "测试描述"}], "improvement_directions": ["测试建议"]}
}
```

- [ ] **Step 4: Test renderer with real data**

```bash
python3 -m mining.report.renderer --input-dir /tmp/factor_report_001 --output-dir /tmp/factor_report_001
```

Expected: `factor_001_report.html` created.

- [ ] **Step 5: Open and visually inspect**

```bash
open /tmp/factor_report_001/factor_001_report.html
```

Verify in browser:
- LaTeX formula renders (requires internet for MathJax CDN)
- Plotly charts are interactive (requires internet for plotly CDN)
- All 8 sections visible with proper styling
- KPI strip shows correct numbers
- Tables render with colored values

- [ ] **Step 6: Fix any issues found and commit**

```bash
git add -A
git commit -m "fix(report): address integration test issues"
```

---

### Task 6: `/factor-report` Skill

**Files:**
- Create: Skill file (path depends on skill framework location — check existing skills for convention)

The skill orchestrates the three-stage pipeline. It must be a Claude Code skill file.

- [ ] **Step 1: Check existing skill location convention**

Look at existing skills in the project to determine where to place the new skill file and what format to use. Check `CLAUDE.md` or `.claude/` directory for skill configuration.

- [ ] **Step 2: Create the skill file**

The skill should:
1. Accept a `factor_id` argument (e.g., `/factor-report 001`)
2. Run `python3 -m mining.report.builder --factor-id <id> --output-dir /tmp/factor_report_<id>`
3. Read `/tmp/factor_report_<id>/report_data.json`
4. Instruct Claude Code to write `narrative.json` based on the data, following the narrative schema
5. Run `python3 -m mining.report.renderer --input-dir /tmp/factor_report_<id> --output-dir mining/reports/`
6. Open the report in browser

The skill prompt must include:
- The exact `narrative.json` schema
- Instructions to write as a senior quant analyst
- Requirements for depth: reference specific numbers, provide 3-4 theoretical angles, include A-share context
- Tone for critical review: sharp, witty, data-backed
- Language: Chinese narrative with English technical terms

- [ ] **Step 3: Test the skill**

Run `/factor-report 001` and verify:
- Builder runs successfully
- Claude Code generates narrative with depth
- Renderer produces final HTML
- Report opens in browser with all content

- [ ] **Step 4: Commit**

```bash
git add <skill-file-path>
git commit -m "feat(report): add /factor-report skill for HTML report generation"
```

---

### Task 7: Update publisher.py Integration

**Files:**
- Modify: `mining/publisher.py:215-251` (replace `_generate_report` method)

- [ ] **Step 1: Update publisher to use new report pipeline**

Replace `publisher._generate_report()` to call `mining.report.builder` and `mining.report.renderer` instead of the old `visualization.report.FactorReportGenerator`. Note: the publisher cannot call the LLM narrative step — it only generates the data-driven report without narrative. Narrative-enriched reports are created via the `/factor-report` skill.

```python
def _generate_report(self, factor_id, factor_dict, factor_values):
    """Generate data-only HTML report (no LLM narrative)."""
    from mining.report.builder import ReportDataBuilder
    from mining.report.renderer import ReportRenderer

    report_dir = os.path.join(os.path.dirname(self.config.library_dir), "reports")

    try:
        builder = ReportDataBuilder(factor_id, self.config)
        # Override data loading — we already have factor_values
        data = builder.build()  # uses DB

        # Render with empty narrative (data-only report)
        empty_narrative = {
            "factor_metadata": {"name_cn": "", "expression_latex": factor_dict.get("expression", "")},
        }
        renderer = ReportRenderer()
        path = renderer.render_to_file(data, empty_narrative, report_dir, factor_id)
        return path
    except Exception as e:
        logger.warning("Report generation failed for factor %s: %s", factor_id, e)
        return ""
```

- [ ] **Step 2: Run existing tests**

```bash
python3 -m pytest tests/ -v -k "publisher or report"
```

Expected: All pass

- [ ] **Step 3: Commit**

```bash
git add mining/publisher.py
git commit -m "refactor(publisher): use new report pipeline for HTML generation"
```

---

### Task 8: Update __init__.py and Final Cleanup

**Files:**
- Modify: `mining/report/__init__.py`

- [ ] **Step 1: Update package init with public API**

```python
"""Factor report generation package."""
from mining.report.builder import ReportDataBuilder
from mining.report.renderer import ReportRenderer
from mining.report.scorer import CompositeScorer

__all__ = ["ReportDataBuilder", "ReportRenderer", "CompositeScorer"]
```

- [ ] **Step 2: Run full test suite**

```bash
python3 -m pytest tests/ -v
```

Expected: All pass

- [ ] **Step 3: Generate reports for both admitted factors**

```bash
python3 -m mining.report.builder --factor-id 001 --output-dir /tmp/factor_report_001
python3 -m mining.report.builder --factor-id 002 --output-dir /tmp/factor_report_002
```

- [ ] **Step 4: Final commit**

```bash
git add mining/report/__init__.py
git commit -m "feat(report): finalize report package with public API"
```
