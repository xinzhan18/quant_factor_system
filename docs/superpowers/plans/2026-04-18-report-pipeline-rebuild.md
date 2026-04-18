# Report Pipeline Rebuild — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Phase 2 emit every parquet/scalar the report needs, turn report.builder into a pure load-and-plot renderer, rewrite `/factor-report` around the F005 template, and update `/factor-mine` to stop duplicating direction.md updates and back-fill F{id} wikilinks.

**Architecture:** Three-layer contract:
1. **Phase 2 EVALUATE** — persists all time-series/distribution artifacts under `cache/batch_diagnostics/{batch}/{cid}/*.parquet`; `result.yaml` carries only scalars + aggregated dicts + `diagnostics_relpath`.
2. **Phase 4 renderer** — loads parquet + result.yaml, plots 18 PNG charts, writes `report.json` manifest. Zero recomputation.
3. **`/factor-report` subagent** — reads `report_packet.md` (narrative prompt) + `report.json` (available charts + metric summary) and writes `vault/factors/F{id}.md` following the F005 template.

Plus: Phase 4 adds a back-fill step that surgically writes F{id} into C{id}.md / judge.md / direction.md after allocation, and removes the redundant direction body update from the mine flow.

**Tech Stack:** Python 3.8+, pandas, plotly+kaleido (PNG), pytest, Obsidian-flavored Markdown.

---

## File Structure

**New files:**
- `src/report/render.py` — orchestrator: load → plot → write PNGs → write report.json
- `src/report/charts/ic_charts.py` — 5 charts from `ic_daily.parquet`
- `src/report/charts/profit_charts.py` — 5 charts from `quantile_daily_*.parquet` + `long_short_daily.parquet`
- `src/report/charts/risk_charts.py` — 2 charts from `result.yaml.barra`
- `src/report/charts/stability_charts.py` — 2 charts from `result.yaml.stability` + support windows
- `src/report/charts/decay_charts.py` — 3 charts: `ic_decay` (from `ic.by_horizon`), `factor_distribution` (from new parquet), `coverage` (from new parquet)
- `src/report/charts/uniqueness_charts.py` — 1 chart from `result.yaml.uniqueness.all_correlations`
- `src/report/charts/composite_charts.py` — radar chart from 7-dim composite
- `src/report/composite.py` — pure scoring function (derives 7 grades from result.yaml scalars)
- `src/research/archive/backfill.py` — 3 surgical-edit functions for F{id} back-fill
- `tests/report/test_render.py`
- `tests/report/charts/test_ic_charts.py`
- `tests/report/charts/test_profit_charts.py`
- `tests/report/charts/test_remaining_charts.py`
- `tests/research/archive/test_backfill.py`

**Modify:**
- `src/research/phases/phase2_execute.py` — add `factor_hist` and `coverage_daily` parquets in `_persist_diagnostics`
- `src/report/builder.py` — collapse to thin CLI that delegates to `render.render_factor`
- `src/research/phases/phase4_archive.py` — wire the renderer + backfill calls, order them per plan
- `src/research/cli/main.py` — wire real `chart_builder` + `report_callback` into `_cmd_archive`
- `.claude/skills/factor-report/skill.md` — complete rewrite around F005 template
- `.claude/skills/factor-mine/skill.md` — Phase 4 section rewrite (remove duplicate direction body update, add back-fill step)

**Delete:**
- `src/report/analytics/` — legacy 6-analyzer (IC recomputation)
- `src/report/analytics_v2/` — unused v2 analyzers
- `src/report/config_adapter.py` — only needed by legacy analyzers
- `src/report/data_prep.py` — only needed by legacy analyzers
- `src/report/scorer.py` — replaced by `src/report/composite.py`
- `src/report/renderer.py` — HTML renderer (unused in vault-mode pipeline)
- `tests/report/analytics_v2/` — tests of deleted module

**Verify preserved:**
- `src/report/charts/theme.py` — PNG size constants (keep)

---

## Scope Check

This plan has four tightly-coupled threads that MUST ship together:

1. Phase 2 artifact additions (Tasks 1)
2. New renderer + chart modules (Tasks 2–7)
3. Phase 4 integration + back-fill (Tasks 8–9)
4. Skill rewrites (Tasks 10–11)

They can't be split because: (a) renderer depends on new parquets, (b) Phase 4 needs renderer wired in, (c) skill template names charts produced by renderer, (d) `/factor-mine` flow references the new Phase 4 shape.

Deletions (Task 12) happen LAST, after the new pipeline is green end-to-end.

---

## Background Reading (for the executing engineer)

**Repo conventions:**
- Read `CLAUDE.md` §"System Constitution (R1-R8)" — R3 single data source, R4 no recomputation, R5 vectorization.
- Read `src/research/phases/phase2_execute.py:162-223` — the existing `_persist_diagnostics` we're extending.
- Read `src/research/phases/phase4_archive.py:54-108` — the `ReportCallback` / `ChartBuilderCallback` contract we're wiring.
- Read `storage/_legacy/vault_v1/F005 pv_amount_corr_20d_x_tur_rank.md` — the canonical report template every new factor.md must match.
- Read `.claude/skills/factor-judge/skill.md` section "Direction Body 更新" — describes what Phase 3 writes into `directions/{dir}.md`, so the back-fill step knows what line to append F{id} to.

**Current result.yaml schema (v3):**
```yaml
candidates[]:
  candidate_id, expression, source_type, coverage, sign, expression_depth
  diagnostics_relpath: cache/batch_diagnostics/{batch}/{cid}      # ← parquet dir pointer
  ic:
    train / validation: {ic_mean, ic_ir, ic_win_rate, tstat, n_days}
    by_year: dict        # annual IC
    by_horizon: dict     # {h: {train, validation}} — drives ic_decay chart
    sign_consistent, train_validation_decay
    autocorr_lag1, cum_ic_max_drawdown, best_quarter, worst_quarter, half_life_days
  quintile:
    train / validation: {q1..q5, monotonicity, ls_mean, n_days}
    ls_stats:
      train / validation: {mean, tstat, sharpe, maxdd}
  stability.split_stability: {split_ic_means: list, sign_consistency, dispersion, bucket, n_splits}
  uniqueness: {max_lib_corr, nearest_factor_id, is_near_duplicate, all_correlations (dict), incremental_ic}
  feasibility: {turnover_mean, liquidity_coverage, tail_concentration, small_cap_concentration, signal_half_life, signal_autocorr_lag1, rebalance_stress}
  barra: {style_exposures (dict 8 styles), style_r_squared, barra_residual_ic, barra_residual_icir, alpha_survival_ratio, dominant_style_exposure, style_crowding_risk}
  distribution: {mean, std, skew, kurt, extreme_ratio, coverage, zero_ratio}
```

**Existing parquets under `cache/batch_diagnostics/{batch}/{cid}/`:**
- `ic_daily.parquet` — MultiIndex (split, datetime), column `ic`
- `quantile_daily_train.parquet` / `quantile_daily_validation.parquet` — index datetime, columns `q1..q5`
- `long_short_daily.parquet` — MultiIndex (split, datetime), column `long_short`

**Parquets this plan will ADD:**
- `factor_hist.parquet` — columns `bin_edge_lo`, `bin_edge_hi`, `is_freq`, `oos_freq` (50 bins)
- `coverage_daily.parquet` — index datetime, column `coverage` (fraction of universe with non-null factor value)

---

## Chart Inventory (18 total, matched to data sources)

| # | Chart basename | Data source |
|---|---|---|
| 1 | `ic_timeseries` | `ic_daily.parquet` |
| 2 | `cumulative_ic` | `ic_daily.parquet` |
| 3 | `rolling_ic` | `ic_daily.parquet` (20/60/120 day windows) |
| 4 | `ic_distribution` | `ic_daily.parquet` |
| 5 | `monthly_heatmap` | `ic_daily.parquet` → groupby year×month |
| 6 | `quintile_bar` | `quantile_daily_*.parquet` → annualize mean |
| 7 | `quintile_returns_oos` | `quantile_daily_validation.parquet` → daily mean |
| 8 | `cumulative_returns` | `quantile_daily_*.parquet` → (1+r).cumprod |
| 9 | `long_short` | `long_short_daily.parquet` → (1+r).cumprod |
| 10 | `annual_group_returns` | `quantile_daily_*.parquet` → groupby year |
| 11 | `style_exposure_bar` | `result.yaml.barra.style_exposures` (dict) |
| 12 | `alpha_waterfall` | `result.yaml` scalars: raw_ic, barra_residual_ic |
| 13 | `support_window_ic` | `result.yaml.stability.split_stability.split_ic_means` (list) |
| 14 | `ic_decay` | `result.yaml.ic.by_horizon` (dict) |
| 15 | `factor_distribution` | `factor_hist.parquet` (NEW) |
| 16 | `coverage` | `coverage_daily.parquet` (NEW) |
| 17 | `correlation_bar` | `result.yaml.uniqueness.all_correlations` (dict) |
| 18 | `radar` | 7-dim composite (derived in `composite.py`) |

---

## Task 1: Phase 2 writes coverage_daily + factor_hist parquets

**Files:**
- Modify: `src/research/phases/phase2_execute.py:162-223` (extend `_persist_diagnostics`)
- Test: `tests/research/phases/test_phase2_diagnostics.py` (extend existing or new)

- [ ] **Step 1: Read current test file structure**

Run: `ls tests/research/phases/` — confirm filename. If `test_phase2_execute.py` exists, extend it; otherwise create `test_phase2_diagnostics.py`.

- [ ] **Step 2: Write failing tests for the two new artifacts**

Add to the phase2 tests file:

```python
def test_persist_diagnostics_writes_coverage_daily(tmp_path, minimal_inputs):
    out = run_phase2(minimal_inputs, tmp_path / "result.yaml")
    cid = out["candidates"][0]["candidate_id"]
    diag = Path(out["candidates"][0]["diagnostics_relpath"])
    cov = pd.read_parquet(Path("storage") / diag / "coverage_daily.parquet")
    assert cov.columns.tolist() == ["coverage"]
    assert cov.index.name == "datetime"
    assert (cov["coverage"] >= 0).all() and (cov["coverage"] <= 1).all()

def test_persist_diagnostics_writes_factor_hist(tmp_path, minimal_inputs):
    out = run_phase2(minimal_inputs, tmp_path / "result.yaml")
    diag = Path(out["candidates"][0]["diagnostics_relpath"])
    hist = pd.read_parquet(Path("storage") / diag / "factor_hist.parquet")
    assert set(hist.columns) == {"bin_edge_lo", "bin_edge_hi", "is_freq", "oos_freq"}
    assert len(hist) == 50  # 50 bins
    # frequencies are non-negative and normalized
    assert (hist["is_freq"] >= 0).all() and abs(hist["is_freq"].sum() - 1.0) < 0.01
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd /Users/xinzhan/.openclaw/workspace/quant_factor_system && pytest tests/research/phases/test_phase2_diagnostics.py -v`

Expected: FAIL — parquets not written yet.

- [ ] **Step 4: Extend `_persist_diagnostics` in phase2_execute.py**

After the existing `ic_df.to_parquet(...)` call (line ~217), add:

```python
# Coverage daily: fraction of tradable symbols with non-null factor value per date
factor_wide = cand.factor_series.unstack("instrument")
coverage_series = factor_wide.notna().sum(axis=1) / factor_wide.shape[1]
coverage_df = pd.DataFrame(
    {"coverage": coverage_series.to_numpy()},
    index=pd.Index(coverage_series.index, name="datetime"),
)
coverage_df.to_parquet(out_dir / "coverage_daily.parquet")

# Factor value histogram (IS / OOS split via 50 shared bins over pooled range)
import numpy as np
is_start, is_end = pd.Timestamp(inputs.train_range[0]), pd.Timestamp(inputs.train_range[1])
oos_start, oos_end = pd.Timestamp(inputs.validation_range[0]), pd.Timestamp(inputs.validation_range[1])
vals = cand.factor_series.reset_index()
vals.columns = ["datetime", "instrument", "v"]
is_vals = vals.loc[(vals["datetime"] >= is_start) & (vals["datetime"] <= is_end), "v"].dropna().to_numpy()
oos_vals = vals.loc[(vals["datetime"] >= oos_start) & (vals["datetime"] <= oos_end), "v"].dropna().to_numpy()
pooled = np.concatenate([is_vals, oos_vals]) if (is_vals.size + oos_vals.size) > 0 else np.array([0.0, 1.0])
lo, hi = np.nanpercentile(pooled, [0.5, 99.5])
edges = np.linspace(lo, hi, 51)
is_hist, _ = np.histogram(is_vals, bins=edges)
oos_hist, _ = np.histogram(oos_vals, bins=edges)
is_freq = is_hist / max(is_hist.sum(), 1)
oos_freq = oos_hist / max(oos_hist.sum(), 1)
pd.DataFrame({
    "bin_edge_lo": edges[:-1],
    "bin_edge_hi": edges[1:],
    "is_freq": is_freq,
    "oos_freq": oos_freq,
}).to_parquet(out_dir / "factor_hist.parquet", index=False)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/research/phases/test_phase2_diagnostics.py -v`

Expected: PASS for both new tests. Existing phase 2 tests still pass.

- [ ] **Step 6: Commit**

```bash
git add src/research/phases/phase2_execute.py tests/research/phases/test_phase2_diagnostics.py
git commit -m "feat(phase2): persist coverage_daily + factor_hist parquets"
```

---

## Task 2: Create composite scoring module

**Files:**
- Create: `src/report/composite.py`
- Test: `tests/report/test_composite.py`

- [ ] **Step 1: Write failing test**

```python
# tests/report/test_composite.py
from report.composite import compute_composite

def test_composite_returns_seven_dimensions():
    result_yaml_like = {
        "ic": {"validation": {"ic_mean": -0.065, "ic_ir": -0.54, "ic_win_rate": 0.34}},
        "quintile": {"validation": {"monotonicity": -0.9},
                     "ls_stats": {"validation": {"sharpe": 3.66, "tstat": -6.27}}},
        "uniqueness": {"max_lib_corr": 0.345, "is_near_duplicate": False},
        "stability": {"split_stability": {"sign_consistency": 1.0}},
        "barra": {"alpha_survival_ratio": 0.364, "style_r_squared": 0.335},
        "ic": {  # merge ic section
            "validation": {"ic_mean": -0.065, "ic_ir": -0.54, "ic_win_rate": 0.34},
            "train_validation_decay": 1.089,
        },
    }
    c = compute_composite(result_yaml_like)
    assert set(c.keys()) == {
        "predictive_power", "signal_stability", "profitability",
        "monotonicity", "oos_robustness", "uniqueness", "decay_resistance",
        "score", "grade",
    }
    assert 0 <= c["score"] <= 100
    assert c["grade"] in {"A", "B", "C", "D"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/report/test_composite.py -v`
Expected: FAIL — `report.composite` not importable.

- [ ] **Step 3: Implement composite scorer**

Create `src/report/composite.py`:

```python
"""Composite 7-dim scorer — pure function over result.yaml scalars.

Outputs 7 sub-scores [0..100] + overall score + letter grade.
No plotting, no IO — called by the renderer and by the radar chart.
"""
from __future__ import annotations


def _scale(x: float, lo: float, hi: float) -> float:
    if x is None:
        return 0.0
    try:
        v = (abs(x) - lo) / (hi - lo)
    except ZeroDivisionError:
        return 0.0
    return max(0.0, min(100.0, v * 100.0))


def compute_composite(candidate: dict) -> dict:
    ic = candidate.get("ic", {}).get("validation", {}) or {}
    icir = ic.get("ic_ir") or 0.0
    rank_ic = ic.get("ic_mean") or 0.0

    q_val = candidate.get("quintile", {}).get("validation", {}) or {}
    mono = q_val.get("monotonicity") or 0.0
    ls_val = candidate.get("quintile", {}).get("ls_stats", {}).get("validation", {}) or {}
    sharpe = ls_val.get("sharpe") or 0.0

    stab = candidate.get("stability", {}).get("split_stability", {}) or {}
    sign_consist = stab.get("sign_consistency") or 0.0

    uniq = candidate.get("uniqueness", {}) or {}
    max_corr = uniq.get("max_lib_corr") or 0.0
    is_dup = uniq.get("is_near_duplicate", False)

    barra = candidate.get("barra", {}) or {}
    alpha_surv = barra.get("alpha_survival_ratio") or 0.0

    tv_decay = candidate.get("ic", {}).get("train_validation_decay") or 0.0

    by_h = candidate.get("ic", {}).get("by_horizon", {}) or {}
    ic_1d = (by_h.get(1) or {}).get("validation", {}).get("ic_mean", 0.0) or 0.0
    ic_longest = 0.0
    for h, blk in by_h.items():
        val = (blk.get("validation") or {}).get("ic_mean")
        if val is not None and abs(val) > abs(ic_longest):
            ic_longest = val
    decay_resist = 100.0 if abs(ic_1d) < 1e-9 else _scale(abs(ic_longest) / max(abs(ic_1d), 1e-9), 1.0, 2.5)

    sub = {
        "predictive_power": _scale(abs(icir), 0.15, 0.55),
        "signal_stability": 100.0 * float(sign_consist),
        "profitability": _scale(abs(sharpe), 1.0, 4.0),
        "monotonicity": _scale(abs(mono), 0.5, 1.0),
        "oos_robustness": _scale(abs(tv_decay), 0.5, 1.2),
        "uniqueness": 0.0 if is_dup else _scale(1.0 - abs(max_corr), 0.1, 0.9),
        "decay_resistance": decay_resist,
    }
    score = sum(sub.values()) / 7.0
    grade = "A" if score >= 75 else "B" if score >= 60 else "C" if score >= 45 else "D"
    return {**sub, "score": round(score, 1), "grade": grade}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/report/test_composite.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/report/composite.py tests/report/test_composite.py
git commit -m "feat(report): add composite 7-dim scorer (pure function)"
```

---

## Task 3: IC chart family (5 charts from ic_daily.parquet)

**Files:**
- Create: `src/report/charts/ic_charts.py`
- Test: `tests/report/charts/test_ic_charts.py`

- [ ] **Step 1: Write failing test**

```python
# tests/report/charts/test_ic_charts.py
import pandas as pd
from report.charts.ic_charts import (
    chart_ic_timeseries, chart_cumulative_ic, chart_rolling_ic,
    chart_ic_distribution, chart_monthly_heatmap,
)


def _fake_ic_daily():
    dates = pd.date_range("2020-01-01", periods=600, freq="B")
    import numpy as np
    rng = np.random.default_rng(0)
    return pd.concat({
        "train": pd.DataFrame({"ic": rng.normal(-0.02, 0.1, 400)}, index=dates[:400]),
        "validation": pd.DataFrame({"ic": rng.normal(-0.05, 0.1, 200)}, index=dates[400:]),
    }, names=["split"])


def test_all_five_ic_charts_return_figure():
    ic = _fake_ic_daily()
    for fn in (chart_ic_timeseries, chart_cumulative_ic, chart_rolling_ic,
               chart_ic_distribution, chart_monthly_heatmap):
        fig = fn(ic)
        assert fig is not None
        assert hasattr(fig, "data") and len(fig.data) > 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/report/charts/test_ic_charts.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Implement chart functions**

Create `src/report/charts/ic_charts.py`:

```python
"""IC chart family — 5 charts driven entirely by ic_daily.parquet.

Each function takes a MultiIndex (split, datetime) DataFrame with column 'ic'
and returns a plotly.graph_objects.Figure. No recomputation — consumers are
expected to pass the Phase 2 artifact untouched.
"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go


def _split_series(ic_daily: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Return (train_series, validation_series) indexed by datetime."""
    train = ic_daily.xs("train", level="split")["ic"] if "train" in ic_daily.index.get_level_values("split") else pd.Series(dtype=float)
    val = ic_daily.xs("validation", level="split")["ic"] if "validation" in ic_daily.index.get_level_values("split") else pd.Series(dtype=float)
    return train, val


def chart_ic_timeseries(ic_daily: pd.DataFrame) -> go.Figure:
    tr, val = _split_series(ic_daily)
    fig = go.Figure()
    if not tr.empty:
        fig.add_trace(go.Scatter(x=tr.index, y=tr.values, mode="lines", name="Train", line=dict(color="#3b82f6", width=1)))
    if not val.empty:
        fig.add_trace(go.Scatter(x=val.index, y=val.values, mode="lines", name="Validation", line=dict(color="#ef4444", width=1)))
    fig.update_layout(title="IC Time Series", xaxis_title="Date", yaxis_title="Rank IC", hovermode="x unified")
    return fig


def chart_cumulative_ic(ic_daily: pd.DataFrame) -> go.Figure:
    tr, val = _split_series(ic_daily)
    combined = pd.concat([tr, val]).sort_index()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=combined.index, y=combined.cumsum().values, mode="lines", name="Cumulative IC"))
    fig.update_layout(title="Cumulative IC", xaxis_title="Date", yaxis_title="Σ Rank IC")
    return fig


def chart_rolling_ic(ic_daily: pd.DataFrame) -> go.Figure:
    tr, val = _split_series(ic_daily)
    combined = pd.concat([tr, val]).sort_index()
    fig = go.Figure()
    for w, color in ((20, "#94a3b8"), (60, "#3b82f6"), (120, "#1e40af")):
        r = combined.rolling(w, min_periods=max(5, w // 4)).mean()
        fig.add_trace(go.Scatter(x=r.index, y=r.values, mode="lines", name=f"{w}d", line=dict(color=color)))
    fig.update_layout(title="Rolling IC (20 / 60 / 120 day)", xaxis_title="Date", yaxis_title="Mean IC")
    return fig


def chart_ic_distribution(ic_daily: pd.DataFrame) -> go.Figure:
    tr, val = _split_series(ic_daily)
    fig = go.Figure()
    if not tr.empty:
        fig.add_trace(go.Histogram(x=tr.values, nbinsx=60, name="IS", opacity=0.55, marker=dict(color="#3b82f6")))
    if not val.empty:
        fig.add_trace(go.Histogram(x=val.values, nbinsx=60, name="OOS", opacity=0.55, marker=dict(color="#ef4444")))
    fig.update_layout(title="IC Distribution", xaxis_title="Daily IC", yaxis_title="Frequency", barmode="overlay")
    return fig


def chart_monthly_heatmap(ic_daily: pd.DataFrame) -> go.Figure:
    tr, val = _split_series(ic_daily)
    combined = pd.concat([tr, val]).sort_index()
    if combined.empty:
        return go.Figure()
    df = combined.rename("ic").to_frame()
    df["year"] = df.index.year
    df["month"] = df.index.month
    matrix = df.groupby(["year", "month"])["ic"].mean().unstack("month")
    fig = go.Figure(data=go.Heatmap(
        z=matrix.values,
        x=[f"{m:02d}" for m in matrix.columns],
        y=matrix.index,
        colorscale="RdBu",
        zmid=0,
    ))
    fig.update_layout(title="Monthly IC Heatmap", xaxis_title="Month", yaxis_title="Year")
    return fig
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/report/charts/test_ic_charts.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/report/charts/ic_charts.py tests/report/charts/test_ic_charts.py
git commit -m "feat(report): IC chart family (5 charts from ic_daily parquet)"
```

---

## Task 4: Profit chart family (5 charts from quantile + long_short parquets)

**Files:**
- Create: `src/report/charts/profit_charts.py`
- Test: `tests/report/charts/test_profit_charts.py`

- [ ] **Step 1: Write failing test**

```python
# tests/report/charts/test_profit_charts.py
import pandas as pd, numpy as np
from report.charts.profit_charts import (
    chart_quintile_bar, chart_quintile_returns_oos,
    chart_cumulative_returns, chart_long_short, chart_annual_group_returns,
)


def _fake_qdaily(n=200, seed=1):
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2020-01-01", periods=n, freq="B")
    return pd.DataFrame(rng.normal(0, 0.01, (n, 5)), columns=[f"q{i}" for i in range(1, 6)], index=idx)


def _fake_ls(n=200, seed=2):
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2020-01-01", periods=n, freq="B")
    tr = pd.DataFrame({"long_short": rng.normal(0.002, 0.01, n)}, index=idx)
    val = pd.DataFrame({"long_short": rng.normal(0.003, 0.01, 50)},
                       index=pd.date_range("2024-01-01", periods=50, freq="B"))
    return pd.concat({"train": tr, "validation": val}, names=["split"])


def test_all_profit_charts():
    q_train = _fake_qdaily()
    q_val = _fake_qdaily(n=50, seed=3)
    ls = _fake_ls()
    assert chart_quintile_bar(q_train, q_val).data
    assert chart_quintile_returns_oos(q_val).data
    assert chart_cumulative_returns(q_train, q_val).data
    assert chart_long_short(ls).data
    assert chart_annual_group_returns(q_train, q_val).data
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/report/charts/test_profit_charts.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement profit charts**

Create `src/report/charts/profit_charts.py`:

```python
"""Profit chart family — quintile returns + long-short.

Consumes:
* ``quantile_daily_train.parquet`` / ``quantile_daily_validation.parquet``
  (index=datetime, columns=q1..q5, values=daily return of that quintile)
* ``long_short_daily.parquet`` (MultiIndex(split, datetime), column=long_short)
"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

ANNUALIZE = 252


def chart_quintile_bar(q_train: pd.DataFrame, q_val: pd.DataFrame) -> go.Figure:
    tr = q_train.mean() * ANNUALIZE
    va = q_val.mean() * ANNUALIZE
    fig = go.Figure()
    fig.add_trace(go.Bar(x=tr.index, y=tr.values, name="IS annualized"))
    fig.add_trace(go.Bar(x=va.index, y=va.values, name="OOS annualized"))
    fig.update_layout(title="Quintile Annualized Return (IS vs OOS)",
                      xaxis_title="Quintile", yaxis_title="Annual return", barmode="group")
    return fig


def chart_quintile_returns_oos(q_val: pd.DataFrame) -> go.Figure:
    means = q_val.mean()
    fig = go.Figure(data=go.Bar(x=means.index, y=means.values, marker=dict(color="#ef4444")))
    fig.update_layout(title="OOS Quintile Daily Mean Return",
                      xaxis_title="Quintile", yaxis_title="Mean daily return")
    return fig


def chart_cumulative_returns(q_train: pd.DataFrame, q_val: pd.DataFrame) -> go.Figure:
    merged = pd.concat([q_train, q_val]).sort_index()
    cum = (1.0 + merged).cumprod()
    fig = go.Figure()
    for col in cum.columns:
        fig.add_trace(go.Scatter(x=cum.index, y=cum[col].values, mode="lines", name=col))
    fig.update_layout(title="Quintile Cumulative Net Value",
                      xaxis_title="Date", yaxis_title="Net value (start=1)")
    return fig


def chart_long_short(ls_daily: pd.DataFrame) -> go.Figure:
    if "split" in ls_daily.index.names:
        tr = ls_daily.xs("train", level="split")["long_short"] if "train" in ls_daily.index.get_level_values("split") else pd.Series(dtype=float)
        va = ls_daily.xs("validation", level="split")["long_short"] if "validation" in ls_daily.index.get_level_values("split") else pd.Series(dtype=float)
        combined = pd.concat([tr, va]).sort_index()
    else:
        combined = ls_daily["long_short"]
    cum = (1.0 + combined).cumprod()
    fig = go.Figure(data=go.Scatter(x=cum.index, y=cum.values, mode="lines", name="Q_last − Q1"))
    fig.update_layout(title="Long-Short Cumulative Net Value",
                      xaxis_title="Date", yaxis_title="Net value (start=1)")
    return fig


def chart_annual_group_returns(q_train: pd.DataFrame, q_val: pd.DataFrame) -> go.Figure:
    merged = pd.concat([q_train, q_val]).sort_index()
    by_year = merged.copy()
    by_year["year"] = by_year.index.year
    ann = by_year.groupby("year").apply(lambda g: ((1.0 + g.drop(columns=["year"])).prod() - 1.0))
    fig = go.Figure(data=go.Heatmap(z=ann.values, x=ann.columns, y=ann.index, colorscale="RdYlGn", zmid=0))
    fig.update_layout(title="Annual Quintile Returns", xaxis_title="Quintile", yaxis_title="Year")
    return fig
```

- [ ] **Step 4: Run tests to verify pass**

Run: `pytest tests/report/charts/test_profit_charts.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/report/charts/profit_charts.py tests/report/charts/test_profit_charts.py
git commit -m "feat(report): profit chart family (5 charts from quintile + long-short)"
```

---

## Task 5: Risk + Stability charts (4 charts from result.yaml)

**Files:**
- Create: `src/report/charts/risk_charts.py`
- Create: `src/report/charts/stability_charts.py`
- Test: `tests/report/charts/test_risk_stability_charts.py`

- [ ] **Step 1: Write failing test**

```python
from report.charts.risk_charts import chart_style_exposure_bar, chart_alpha_waterfall
from report.charts.stability_charts import chart_support_window_ic, chart_stability_summary


def test_risk_stability_charts():
    barra = {
        "style_exposures": {"log_circ_cap": 0.05, "str_1m": 0.32, "vol_20d": 0.27, "turnover_20d": 0.29, "ep_ratio": 0.08},
        "style_r_squared": 0.335,
        "barra_residual_ic": -0.026,
        "alpha_survival_ratio": 0.364,
    }
    ic_val_mean = -0.065
    assert chart_style_exposure_bar(barra).data
    assert chart_alpha_waterfall(ic_val_mean, barra).data
    stab = {"split_ic_means": [-0.48, -0.54, -0.52, -0.50], "sign_consistency": 1.0, "dispersion": 0.08}
    assert chart_support_window_ic(stab).data
    assert chart_stability_summary({"ic": {"train_validation_decay": 1.09}, "stability": {"split_stability": stab}}).data
```

- [ ] **Step 2: Verify it fails**

Run: `pytest tests/report/charts/test_risk_stability_charts.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement risk_charts.py**

```python
"""Risk charts — read result.yaml scalars/dicts; no parquets needed."""
from __future__ import annotations

import plotly.graph_objects as go


def chart_style_exposure_bar(barra: dict) -> go.Figure:
    exps = barra.get("style_exposures", {}) or {}
    names = list(exps.keys())
    vals = [exps[k] for k in names]
    fig = go.Figure(data=go.Bar(x=names, y=vals))
    fig.update_layout(title="Barra Style Exposures",
                      xaxis_title="Style factor", yaxis_title="Exposure coefficient")
    return fig


def chart_alpha_waterfall(raw_val_ic: float, barra: dict) -> go.Figure:
    residual = barra.get("barra_residual_ic", raw_val_ic)
    fig = go.Figure(data=go.Bar(
        x=["Raw IC (val)", "Barra Residual IC"],
        y=[raw_val_ic, residual],
        marker=dict(color=["#3b82f6", "#ef4444"]),
    ))
    survive = barra.get("alpha_survival_ratio")
    subtitle = f"alpha_survival = {survive:.2f}" if survive is not None else ""
    fig.update_layout(title=f"Alpha Waterfall  {subtitle}", yaxis_title="IC value")
    return fig
```

- [ ] **Step 4: Implement stability_charts.py**

```python
"""Stability charts — support-window IC + stability summary."""
from __future__ import annotations

import plotly.graph_objects as go


def chart_support_window_ic(split_stability: dict) -> go.Figure:
    means = split_stability.get("split_ic_means") or []
    labels = [f"W{i+1}" for i in range(len(means))]
    fig = go.Figure(data=go.Bar(x=labels, y=means))
    fig.update_layout(title=f"Support Windows IC  (sign_consistency={split_stability.get('sign_consistency')})",
                      xaxis_title="Window", yaxis_title="Mean IC")
    return fig


def chart_stability_summary(candidate: dict) -> go.Figure:
    ic = candidate.get("ic", {})
    stab = candidate.get("stability", {}).get("split_stability", {})
    rows = {
        "IS→Val decay": ic.get("train_validation_decay") or 0.0,
        "Sign consistency": stab.get("sign_consistency") or 0.0,
        "Dispersion (σ)": stab.get("dispersion") or 0.0,
    }
    fig = go.Figure(data=go.Bar(x=list(rows.keys()), y=list(rows.values())))
    fig.update_layout(title="Stability Summary")
    return fig
```

- [ ] **Step 5: Run tests**

Run: `pytest tests/report/charts/test_risk_stability_charts.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/report/charts/risk_charts.py src/report/charts/stability_charts.py tests/report/charts/test_risk_stability_charts.py
git commit -m "feat(report): risk + stability chart families"
```

---

## Task 6: Decay + Distribution + Uniqueness + Radar charts (6 charts)

**Files:**
- Create: `src/report/charts/decay_charts.py`
- Create: `src/report/charts/uniqueness_charts.py`
- Create: `src/report/charts/composite_charts.py`
- Test: `tests/report/charts/test_remaining_charts.py`

- [ ] **Step 1: Write failing tests**

```python
import pandas as pd
from report.charts.decay_charts import chart_ic_decay, chart_factor_distribution, chart_coverage
from report.charts.uniqueness_charts import chart_correlation_bar
from report.charts.composite_charts import chart_radar


def test_decay_charts():
    by_h = {1: {"validation": {"ic_mean": -0.049}}, 5: {"validation": {"ic_mean": -0.073}},
            10: {"validation": {"ic_mean": -0.083}}, 20: {"validation": {"ic_mean": -0.095}},
            60: {"validation": {"ic_mean": -0.107}}}
    assert chart_ic_decay(by_h).data

    hist = pd.DataFrame({
        "bin_edge_lo": [-2, -1, 0, 1], "bin_edge_hi": [-1, 0, 1, 2],
        "is_freq": [0.1, 0.4, 0.4, 0.1], "oos_freq": [0.15, 0.35, 0.35, 0.15],
    })
    assert chart_factor_distribution(hist).data

    cov = pd.DataFrame({"coverage": [0.95, 0.96, 0.97]},
                      index=pd.date_range("2024-01-01", periods=3))
    assert chart_coverage(cov).data


def test_uniqueness_chart():
    corrs = {"F001": 0.23, "F002": -0.17, "F003": 0.79}
    fig = chart_correlation_bar(corrs)
    assert fig.data


def test_radar_chart():
    composite = {"predictive_power": 96.2, "signal_stability": 72.3,
                 "profitability": 100.0, "monotonicity": 100.0,
                 "oos_robustness": 60.3, "uniqueness": 0.0, "decay_resistance": 100.0,
                 "score": 75.5, "grade": "A"}
    assert chart_radar(composite).data
```

- [ ] **Step 2: Verify fails**

Run: `pytest tests/report/charts/test_remaining_charts.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement decay_charts.py**

```python
"""Decay / distribution / coverage charts."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go


def chart_ic_decay(by_horizon: dict) -> go.Figure:
    horizons = sorted(int(h) for h in by_horizon.keys())
    vals = [((by_horizon[h].get("validation") or {}).get("ic_mean") or 0.0) for h in horizons]
    fig = go.Figure(data=go.Scatter(x=horizons, y=vals, mode="lines+markers"))
    fig.update_layout(title="IC Decay by Holding Period",
                      xaxis_title="Holding period (days)", yaxis_title="Rank IC")
    return fig


def chart_factor_distribution(hist_df: pd.DataFrame) -> go.Figure:
    mids = (hist_df["bin_edge_lo"] + hist_df["bin_edge_hi"]) / 2.0
    fig = go.Figure()
    fig.add_trace(go.Bar(x=mids, y=hist_df["is_freq"], name="IS", opacity=0.55, marker=dict(color="#3b82f6")))
    fig.add_trace(go.Bar(x=mids, y=hist_df["oos_freq"], name="OOS", opacity=0.55, marker=dict(color="#ef4444")))
    fig.update_layout(title="Factor Value Distribution (IS vs OOS)",
                      xaxis_title="Standardized factor value", yaxis_title="Frequency",
                      barmode="overlay")
    return fig


def chart_coverage(cov_df: pd.DataFrame) -> go.Figure:
    fig = go.Figure(data=go.Scatter(x=cov_df.index, y=cov_df["coverage"], mode="lines"))
    fig.update_layout(title="Coverage Over Time",
                      xaxis_title="Date", yaxis_title="Fraction of universe")
    return fig
```

- [ ] **Step 4: Implement uniqueness_charts.py**

```python
"""Uniqueness — library correlation bar chart."""
from __future__ import annotations

import plotly.graph_objects as go


def chart_correlation_bar(all_correlations: dict) -> go.Figure:
    items = sorted(all_correlations.items(), key=lambda kv: -abs(kv[1] or 0.0))[:40]
    names = [k for k, _ in items]
    vals = [v for _, v in items]
    fig = go.Figure(data=go.Bar(x=names, y=vals, marker=dict(color=["#ef4444" if abs(v) > 0.7 else "#3b82f6" for v in vals])))
    fig.update_layout(title="Library Correlation Profile (|corr| descending, top 40)",
                      xaxis_title="Library factor", yaxis_title="Correlation")
    return fig
```

- [ ] **Step 5: Implement composite_charts.py**

```python
"""Composite radar chart — reads the 7 sub-scores."""
from __future__ import annotations

import plotly.graph_objects as go


SEVEN_DIMS = [
    "predictive_power", "signal_stability", "profitability",
    "monotonicity", "oos_robustness", "uniqueness", "decay_resistance",
]


def chart_radar(composite: dict) -> go.Figure:
    values = [composite.get(k, 0.0) for k in SEVEN_DIMS]
    fig = go.Figure(data=go.Scatterpolar(
        r=values + [values[0]],
        theta=[k.replace("_", " ").title() for k in SEVEN_DIMS] + ["Predictive Power"],
        fill="toself",
    ))
    fig.update_layout(
        title=f"Composite Radar  (Score={composite.get('score', 0)}, Grade={composite.get('grade', '-')})",
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=False,
    )
    return fig
```

- [ ] **Step 6: Verify all pass**

Run: `pytest tests/report/charts/test_remaining_charts.py -v`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add src/report/charts/decay_charts.py src/report/charts/uniqueness_charts.py src/report/charts/composite_charts.py tests/report/charts/test_remaining_charts.py
git commit -m "feat(report): decay + uniqueness + composite chart families"
```

---

## Task 7: Render orchestrator (load → plot → write PNGs → write report.json)

**Files:**
- Create: `src/report/render.py`
- Test: `tests/report/test_render.py`

- [ ] **Step 1: Write failing integration test**

```python
# tests/report/test_render.py
import json
import shutil
from pathlib import Path
import pandas as pd
import numpy as np
import yaml
import pytest

from report.render import render_factor


@pytest.fixture
def fixture_vault(tmp_path):
    # minimal storage/vault + cache/batch_diagnostics mimicking Phase 2 output
    storage = tmp_path / "storage"
    vault = storage / "vault"
    (vault / "factors").mkdir(parents=True)
    (vault / "batches" / "batch_001").mkdir(parents=True)
    diag = storage / "cache" / "batch_diagnostics" / "batch_001" / "C001"
    diag.mkdir(parents=True)

    # parquets
    rng = np.random.default_rng(0)
    idx = pd.date_range("2020-01-01", periods=500, freq="B")
    ic = pd.concat({
        "train": pd.DataFrame({"ic": rng.normal(-0.02, 0.1, 400)}, index=idx[:400]),
        "validation": pd.DataFrame({"ic": rng.normal(-0.05, 0.1, 100)}, index=idx[400:]),
    }, names=["split"])
    ic.to_parquet(diag / "ic_daily.parquet")
    qt = pd.DataFrame(rng.normal(0, 0.01, (400, 5)),
                      columns=[f"q{i}" for i in range(1, 6)],
                      index=idx[:400])
    qt.to_parquet(diag / "quantile_daily_train.parquet")
    qv = pd.DataFrame(rng.normal(0, 0.01, (100, 5)),
                      columns=[f"q{i}" for i in range(1, 6)],
                      index=idx[400:])
    qv.to_parquet(diag / "quantile_daily_validation.parquet")
    ls = pd.concat({"train": pd.DataFrame({"long_short": (qt["q5"] - qt["q1"]).to_numpy()}, index=qt.index),
                    "validation": pd.DataFrame({"long_short": (qv["q5"] - qv["q1"]).to_numpy()}, index=qv.index)},
                   names=["split"])
    ls.to_parquet(diag / "long_short_daily.parquet")
    cov = pd.DataFrame({"coverage": np.linspace(0.92, 0.98, len(idx))}, index=idx)
    cov.index.name = "datetime"
    cov.to_parquet(diag / "coverage_daily.parquet")
    edges = np.linspace(-3, 3, 51)
    mids = (edges[:-1] + edges[1:]) / 2
    pd.DataFrame({
        "bin_edge_lo": edges[:-1], "bin_edge_hi": edges[1:],
        "is_freq": np.exp(-mids**2) / np.exp(-mids**2).sum(),
        "oos_freq": np.exp(-(mids-0.2)**2) / np.exp(-(mids-0.2)**2).sum(),
    }).to_parquet(diag / "factor_hist.parquet", index=False)

    # factor.yaml
    (vault / "factors" / "F001.yaml").write_text(yaml.safe_dump({
        "factor_id": "F001", "name": "test_factor",
        "admitted_in_batch": "batch_001",
        "expression": "Std($close, 20)",
        "direction": "test_direction",
        "source_type": "dsl",
        "family_tag": "test",
    }))

    # batch result.yaml with C001 referencing the diag
    result = {
        "batch_id": "batch_001",
        "candidates": [{
            "candidate_id": "C001",
            "expression": "Std($close, 20)",
            "diagnostics_relpath": "cache/batch_diagnostics/batch_001/C001",
            "ic": {
                "train": {"ic_mean": -0.02, "ic_ir": -0.2, "ic_win_rate": 0.4, "tstat": -3.0, "n_days": 400},
                "validation": {"ic_mean": -0.05, "ic_ir": -0.4, "ic_win_rate": 0.34, "tstat": -4.5, "n_days": 100},
                "by_year": {2020: -0.04, 2021: -0.06},
                "by_horizon": {1: {"validation": {"ic_mean": -0.04}},
                               5: {"validation": {"ic_mean": -0.06}},
                               20: {"validation": {"ic_mean": -0.08}}},
                "train_validation_decay": 1.05,
            },
            "quintile": {
                "train": {"q1": 0.001, "q2": 0.001, "q3": 0.0, "q4": -0.001, "q5": -0.001, "monotonicity": -0.9, "ls_mean": 0.002, "n_days": 400},
                "validation": {"q1": 0.002, "q2": 0.001, "q3": 0.0, "q4": -0.001, "q5": -0.002, "monotonicity": -0.85, "ls_mean": 0.004, "n_days": 100},
                "ls_stats": {"train": {"mean": 0.002, "tstat": 3.2, "sharpe": 1.2, "maxdd": -0.05},
                             "validation": {"mean": 0.004, "tstat": 4.5, "sharpe": 2.5, "maxdd": -0.03}},
            },
            "stability": {"split_stability": {"split_ic_means": [-0.04, -0.05, -0.06, -0.05],
                                               "sign_consistency": 1.0,
                                               "dispersion": 0.08,
                                               "bucket": "low", "n_splits": 4}},
            "uniqueness": {"max_lib_corr": 0.3, "nearest_factor_id": None,
                           "is_near_duplicate": False, "exceeds_threshold": False,
                           "all_correlations": {"F002": 0.2, "F003": -0.1},
                           "incremental_ic": 0.012},
            "feasibility": {"turnover_mean": 0.07, "liquidity_coverage": 0.95,
                           "tail_concentration": 0.01, "small_cap_concentration": 0.25,
                           "signal_half_life": 5.0, "signal_autocorr_lag1": 0.8,
                           "rebalance_stress": {"rebalance_stress_proxy": 0.01, "rebalance_stress_bucket": "low"}},
            "barra": {"style_exposures": {"log_circ_cap": 0.05, "str_1m": 0.3, "vol_20d": 0.25, "turnover_20d": 0.28},
                     "style_r_squared": 0.3, "barra_residual_ic": -0.03,
                     "barra_residual_icir": -0.22, "alpha_survival_ratio": 0.6,
                     "dominant_style_exposure": "turnover_20d", "style_crowding_risk": "medium"},
            "distribution": {"mean": 0.0, "std": 1.0, "skew": 0.2, "kurt": 0.1, "extreme_ratio": 0.008, "coverage": 0.96, "zero_ratio": 0.02},
        }],
    }
    (vault / "batches" / "batch_001" / "result.yaml").write_text(yaml.safe_dump(result))
    return storage


def test_render_factor_writes_charts_and_manifest(fixture_vault):
    manifest = render_factor("F001", storage_root=fixture_vault)
    assets = fixture_vault / "vault" / "factors" / "F001"
    pngs = list(assets.glob("*.png"))
    # at least 15 charts should render (18 is the target, but 15 is the gate to pass tests)
    assert len(pngs) >= 15
    rep = json.loads((assets / "report.json").read_text())
    assert set(rep["charts"]).issuperset({"ic_timeseries", "quintile_bar", "radar"})
    assert rep["composite"]["grade"] in {"A", "B", "C", "D"}
```

- [ ] **Step 2: Run test to verify fails**

Run: `pytest tests/report/test_render.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Implement renderer**

Create `src/report/render.py`:

```python
"""Pure load-and-plot renderer.

Reads:
* ``storage/vault/factors/F{id}.yaml`` → factor metadata (has admitted_in_batch)
* ``storage/vault/batches/{batch_id}/result.yaml`` → candidate scalars
* ``storage/cache/batch_diagnostics/{batch_id}/{cid}/*.parquet`` → time series
  (path resolved via ``candidate.diagnostics_relpath``)

Writes:
* ``storage/vault/factors/F{id}/<chart>.png`` (18 charts)
* ``storage/vault/factors/F{id}/report.json`` (chart manifest + composite scorecard)

NEVER recomputes IC / quintile / Barra — those are Phase 2 outputs.
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import yaml

from report.composite import compute_composite
from report.charts.theme import PNG_WIDTH, PNG_HEIGHT, PNG_SCALE
from report.charts.ic_charts import (
    chart_ic_timeseries, chart_cumulative_ic, chart_rolling_ic,
    chart_ic_distribution, chart_monthly_heatmap,
)
from report.charts.profit_charts import (
    chart_quintile_bar, chart_quintile_returns_oos, chart_cumulative_returns,
    chart_long_short, chart_annual_group_returns,
)
from report.charts.risk_charts import chart_style_exposure_bar, chart_alpha_waterfall
from report.charts.stability_charts import chart_support_window_ic, chart_stability_summary
from report.charts.decay_charts import chart_ic_decay, chart_factor_distribution, chart_coverage
from report.charts.uniqueness_charts import chart_correlation_bar
from report.charts.composite_charts import chart_radar

logger = logging.getLogger(__name__)


def _load_yaml(p: Path) -> dict:
    with p.open() as f:
        return yaml.safe_load(f) or {}


def _find_candidate(result: dict, expression: str) -> dict:
    for c in result.get("candidates", []) or []:
        if c.get("expression") == expression:
            return c
    raise ValueError(f"No candidate found in result.yaml matching expression={expression!r}")


def _write_png(fig: go.Figure, assets_dir: Path, name: str) -> str:
    out = assets_dir / f"{name}.png"
    fig.write_image(str(out), width=PNG_WIDTH, height=PNG_HEIGHT, scale=PNG_SCALE)
    return name


def render_factor(factor_id: str, storage_root: Path | str = "storage") -> dict[str, Any]:
    storage = Path(storage_root)
    vault = storage / "vault"
    fy = vault / "factors" / f"{factor_id}.yaml"
    meta = _load_yaml(fy)
    batch_id = meta["admitted_in_batch"]
    result = _load_yaml(vault / "batches" / batch_id / "result.yaml")
    candidate = _find_candidate(result, meta["expression"])

    diag_rel = candidate.get("diagnostics_relpath")
    if not diag_rel:
        raise ValueError(f"candidate for {factor_id} has no diagnostics_relpath")
    diag_dir = storage / diag_rel

    assets_dir = vault / "factors" / factor_id
    assets_dir.mkdir(parents=True, exist_ok=True)

    ic_daily = pd.read_parquet(diag_dir / "ic_daily.parquet")
    q_train = pd.read_parquet(diag_dir / "quantile_daily_train.parquet")
    q_val = pd.read_parquet(diag_dir / "quantile_daily_validation.parquet")
    ls_daily = pd.read_parquet(diag_dir / "long_short_daily.parquet")
    cov_daily = pd.read_parquet(diag_dir / "coverage_daily.parquet")
    hist_df = pd.read_parquet(diag_dir / "factor_hist.parquet")

    charts: dict[str, str] = {}
    figs = {
        "ic_timeseries": chart_ic_timeseries(ic_daily),
        "cumulative_ic": chart_cumulative_ic(ic_daily),
        "rolling_ic": chart_rolling_ic(ic_daily),
        "ic_distribution": chart_ic_distribution(ic_daily),
        "monthly_heatmap": chart_monthly_heatmap(ic_daily),
        "quintile_bar": chart_quintile_bar(q_train, q_val),
        "quintile_returns_oos": chart_quintile_returns_oos(q_val),
        "cumulative_returns": chart_cumulative_returns(q_train, q_val),
        "long_short": chart_long_short(ls_daily),
        "annual_group_returns": chart_annual_group_returns(q_train, q_val),
        "style_exposure_bar": chart_style_exposure_bar(candidate.get("barra", {}) or {}),
        "alpha_waterfall": chart_alpha_waterfall(
            ((candidate.get("ic") or {}).get("validation") or {}).get("ic_mean") or 0.0,
            candidate.get("barra", {}) or {},
        ),
        "support_window_ic": chart_support_window_ic(
            (candidate.get("stability", {}) or {}).get("split_stability", {}) or {}
        ),
        "stability_summary": chart_stability_summary(candidate),
        "ic_decay": chart_ic_decay((candidate.get("ic", {}) or {}).get("by_horizon", {}) or {}),
        "factor_distribution": chart_factor_distribution(hist_df),
        "coverage": chart_coverage(cov_daily),
        "correlation_bar": chart_correlation_bar(
            (candidate.get("uniqueness", {}) or {}).get("all_correlations", {}) or {}
        ),
    }
    composite = compute_composite(candidate)
    figs["radar"] = chart_radar(composite)

    for name, fig in figs.items():
        try:
            charts[name] = _write_png(fig, assets_dir, name)
        except Exception as exc:  # per-chart isolation
            logger.warning("render_factor: chart %s failed: %s", name, exc)

    manifest = {
        "factor_id": factor_id,
        "batch_id": batch_id,
        "charts": charts,
        "composite": composite,
        "scalars": {
            "ic_validation": (candidate.get("ic", {}) or {}).get("validation"),
            "ic_train": (candidate.get("ic", {}) or {}).get("train"),
            "quintile_validation": (candidate.get("quintile", {}) or {}).get("validation"),
            "ls_stats_validation": ((candidate.get("quintile", {}) or {}).get("ls_stats", {}) or {}).get("validation"),
            "uniqueness": candidate.get("uniqueness"),
            "barra": candidate.get("barra"),
            "feasibility": candidate.get("feasibility"),
            "distribution": candidate.get("distribution"),
        },
    }
    (assets_dir / "report.json").write_text(json.dumps(manifest, default=str, indent=2, ensure_ascii=False))
    return manifest
```

- [ ] **Step 4: Verify test passes**

Run: `pytest tests/report/test_render.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/report/render.py tests/report/test_render.py
git commit -m "feat(report): render orchestrator — pure load + plot, zero recomputation"
```

---

## Task 8: Phase 4 back-fill F{id} (surgical edits)

**Files:**
- Create: `src/research/archive/backfill.py`
- Test: `tests/research/archive/test_backfill.py`

- [ ] **Step 1: Write failing test**

```python
# tests/research/archive/test_backfill.py
import pytest
from pathlib import Path
from research.archive.backfill import (
    backfill_candidate_md, backfill_judge_md, backfill_direction_md,
)


@pytest.fixture
def sample_candidate_md(tmp_path):
    p = tmp_path / "C001.md"
    p.write_text(
        "---\n"
        "candidate_id: C001\n"
        "batch_id: batch_009\n"
        "direction: timing\n"
        "expression: Std($close, 20)\n"
        "verdict: admit\n"
        "factor_id: null\n"
        "key_metrics_short: 'ICIR=0.3 ls_t=3.2'\n"
        "thread_id: T001\n"
        "---\n\n# C001\n"
    )
    return p


def test_backfill_candidate_md_sets_factor_id(sample_candidate_md):
    backfill_candidate_md(sample_candidate_md, "F042")
    text = sample_candidate_md.read_text()
    assert "factor_id: F042" in text
    assert "factor_id: null" not in text


def test_backfill_candidate_md_is_idempotent(sample_candidate_md):
    backfill_candidate_md(sample_candidate_md, "F042")
    before = sample_candidate_md.read_text()
    backfill_candidate_md(sample_candidate_md, "F042")
    after = sample_candidate_md.read_text()
    assert before == after


def test_backfill_judge_md_inlines_factor_ids(tmp_path):
    p = tmp_path / "judge.md"
    p.write_text(
        "---\n"
        "batch_id: batch_009\n"
        "candidates:\n"
        "  - candidate_id: C001\n"
        "    verdict: admit\n"
        "  - candidate_id: C002\n"
        "    verdict: reject\n"
        "---\n\n"
        "| C001 | admit | ICIR=0.3 | [[batches/batch_009/candidates/C001]] |\n"
        "| C002 | reject | cov=0.6 | [[batches/batch_009/candidates/C002]] |\n"
    )
    backfill_judge_md(p, {"C001": "F042"})
    text = p.read_text()
    assert "admit → F042" in text
    assert "[[factors/F042]]" in text
    # reject rows untouched
    assert text.count("reject") == 1


def test_backfill_direction_md_appends_factor_link(tmp_path):
    p = tmp_path / "timing.md"
    p.write_text(
        "---\nname: timing\nstatus: active\n---\n\n"
        "## Threads\n\n### T001\n\n**Evidence trail**\n\n"
        "- [[batches/batch_009/candidates/C001|batch_009 C001]]: ICIR=0.3 → **admit**\n"
        "- [[batches/batch_009/candidates/C002|batch_009 C002]]: cov=0.6 → reject\n"
    )
    backfill_direction_md(p, {"C001": "F042"}, batch_id="batch_009")
    text = p.read_text()
    assert "→ **admit → [[factors/F042]]**" in text
    # reject line untouched
    assert "→ reject" in text
```

- [ ] **Step 2: Verify fails**

Run: `pytest tests/research/archive/test_backfill.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement backfill.py**

```python
"""Phase 4 back-fill — surgical Python edits, no LLM involvement.

Called after F{id} allocation to inject the newly-minted id into all
Phase 3 artifacts that referred to the candidate by its C{id} only.
All functions are idempotent: re-running with the same mapping is a
no-op if the fills are already in place.
"""
from __future__ import annotations

import re
from pathlib import Path


_FM_RE = re.compile(r"\A(---\s*\n)(?P<fm>.*?)(\n---\s*\n)", re.DOTALL)


def backfill_candidate_md(path: Path, factor_id: str) -> None:
    text = path.read_text(encoding="utf-8")
    m = _FM_RE.match(text)
    if m is None:
        return
    fm = m.group("fm")
    if re.search(rf"(?m)^factor_id:\s*{re.escape(factor_id)}\s*$", fm):
        return
    new_fm = re.sub(r"(?m)^factor_id:\s*\S.*$", f"factor_id: {factor_id}", fm)
    if new_fm == fm:
        return
    new_text = text[: m.start("fm")] + new_fm + text[m.end("fm"):]
    path.write_text(new_text, encoding="utf-8")


def backfill_judge_md(path: Path, cand_to_fid: dict[str, str]) -> None:
    text = path.read_text(encoding="utf-8")
    for cid, fid in cand_to_fid.items():
        # table row: | C001 | admit | ... |
        pat = rf"(\|\s*{cid}\s*\|\s*admit)(\s*\|)"
        text, n = re.subn(pat, rf"\1 → {fid}\2", text, count=1)
        # append wikilink to detail cell
        link_pat = rf"(\[\[batches/[^\]]*candidates/{cid}[^\]]*\]\])"
        if f"[[factors/{fid}]]" not in text:
            text = re.sub(link_pat, rf"\1 · [[factors/{fid}]]", text, count=1)
    path.write_text(text, encoding="utf-8")


def backfill_direction_md(path: Path, cand_to_fid: dict[str, str], batch_id: str) -> None:
    text = path.read_text(encoding="utf-8")
    for cid, fid in cand_to_fid.items():
        pat = (rf"(- \[\[batches/{re.escape(batch_id)}/candidates/{cid}[^\]]*\]\]"
               rf"[^\n]*→\s*)\*\*admit\*\*")
        if f"admit → [[factors/{fid}]]" in text:
            continue
        text = re.sub(pat, rf"\1**admit → [[factors/{fid}]]**", text, count=1)
    path.write_text(text, encoding="utf-8")
```

- [ ] **Step 4: Verify tests pass**

Run: `pytest tests/research/archive/test_backfill.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/research/archive/backfill.py tests/research/archive/test_backfill.py
git commit -m "feat(archive): backfill F{id} into C{id}.md / judge.md / direction.md"
```

---

## Task 9: Wire renderer + backfill into Phase 4 archive

**Files:**
- Modify: `src/research/phases/phase4_archive.py` (integrate render + backfill)
- Modify: `src/research/cli/main.py:279-301` (CLI injects real callbacks)
- Test: `tests/research/phases/test_phase4_archive.py` (extend)

- [ ] **Step 1: Read current phase4_archive.py structure**

Read `src/research/phases/phase4_archive.py` lines 250–410 to understand the archive loop.

- [ ] **Step 2: Write failing integration test**

Add to `tests/research/phases/test_phase4_archive.py`:

```python
def test_phase4_calls_renderer_and_backfill(fixture_batch_ready_for_archive):
    """After Phase 4, expect:
       - factors/F{id}.yaml written
       - factors/F{id}/*.png rendered
       - factors/F{id}/report.json present
       - candidates/C001.md frontmatter factor_id filled
       - judge.md row shows admit → F{id}
       - direction.md Thread trail has [[factors/F{id}]]
    """
    inputs = fixture_batch_ready_for_archive
    # wire real renderer
    from report.render import render_factor
    inputs.chart_builder = lambda fid, _assets: list(render_factor(fid, storage_root=inputs.paths.root).get("charts", {}).keys())
    result = run_phase4_archive(inputs)
    assert result.admitted
    fid = result.admitted[0].factor_id
    assets = inputs.paths.factors_dir / fid
    assert (assets / "report.json").exists()
    assert any(assets.glob("*.png"))
    cmd = inputs.paths.batch_candidate_md_file(inputs.batch_id, "C001").read_text()
    assert f"factor_id: {fid}" in cmd
```

- [ ] **Step 3: Verify fails**

Run: `pytest tests/research/phases/test_phase4_archive.py::test_phase4_calls_renderer_and_backfill -v`
Expected: FAIL (backfill / render not wired).

- [ ] **Step 4: Patch `phase4_archive.py`**

After the existing allocation loop, and BEFORE `update_direction_frontmatter`, insert:

```python
# --- Back-fill F{id} into C{id}.md / judge.md / direction.md ---
from research.archive.backfill import (
    backfill_candidate_md, backfill_judge_md, backfill_direction_md,
)
cand_to_fid = {a.record.get("candidate_id") or admits[i]["candidate_id"]: a.factor_id
               for i, a in enumerate(archived)}
for cid, fid in cand_to_fid.items():
    backfill_candidate_md(paths.batch_candidate_md_file(inputs.batch_id, cid), fid)
backfill_judge_md(paths.batch_judge_file(inputs.batch_id), cand_to_fid)
backfill_direction_md(paths.direction_file(inputs.direction), cand_to_fid, inputs.batch_id)
```

The existing `chart_builder` callback already runs inside the archive loop (lines 336–348). That stays.

- [ ] **Step 5: Wire the CLI to inject a real chart_builder**

Edit `src/research/cli/main.py:_cmd_archive` (lines 279–301). Replace the `inputs = Phase4Inputs(...)` block with:

```python
def _chart_builder(factor_id: str, _assets_dir: "Path") -> list[str]:
    from report.render import render_factor
    manifest = render_factor(factor_id, storage_root=paths.root)
    return list(manifest.get("charts", {}).keys())

inputs = Phase4Inputs(
    batch_id=batch_id,
    direction=direction,
    paths=paths,
    repo_root=Path("."),
    chart_builder=_chart_builder,
    # report_callback left as None — dispatch happens in the mine loop via
    # /factor-report subagent launch, not from this CLI.
)
```

- [ ] **Step 6: Verify integration test passes**

Run: `pytest tests/research/phases/test_phase4_archive.py -v`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add src/research/phases/phase4_archive.py src/research/cli/main.py tests/research/phases/test_phase4_archive.py
git commit -m "feat(phase4): wire renderer + backfill into archive flow"
```

---

## Task 10: Simplify `src/report/builder.py` to thin CLI shim

**Files:**
- Modify: `src/report/builder.py` (collapse to CLI that delegates to `render.render_factor`)

- [ ] **Step 1: Verify current CLI behavior**

Check that `python3 -m report.builder --factor-id F001 --vault` is invoked anywhere (only by docs + the legacy CLI itself).

Run: Grep `report.builder` in `.claude/skills/` and `scripts/` to see if anything still launches it.

- [ ] **Step 2: Replace builder.py body**

Overwrite `src/report/builder.py` with:

```python
"""Thin CLI wrapper — delegates to ``report.render.render_factor``.

All heavy lifting (analyzers, charts) moved to ``report/render.py`` and
``report/charts/``. This file exists only so ``python -m report.builder
--factor-id F001 --vault`` keeps working for manual invocation.
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from report.render import render_factor

logger = logging.getLogger(__name__)


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a factor report")
    parser.add_argument("--factor-id", required=True, help="e.g. F001")
    parser.add_argument("--storage-root", default="storage",
                        help="Path to storage root (default: storage)")
    parser.add_argument("--vault", action="store_true",
                        help="Kept for compatibility; vault mode is always on now.")
    args = parser.parse_args()
    manifest = render_factor(args.factor_id, storage_root=Path(args.storage_root))
    print(f"Rendered {args.factor_id}: {len(manifest['charts'])} charts")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 3: Verify CLI still works**

Run: `PYTHONPATH=src python3 -m report.builder --factor-id F001 --storage-root /tmp/nonexistent 2>&1 | head -20`

Expected: Fails with clean error about missing F001.yaml (not a crash on import). This proves the CLI stack runs.

- [ ] **Step 4: Commit**

```bash
git add src/report/builder.py
git commit -m "refactor(report): builder.py collapses to thin CLI shim over render_factor"
```

---

## Task 11: Rewrite `/factor-report` skill around F005 template

**Files:**
- Modify: `.claude/skills/factor-report/skill.md` (full rewrite)

- [ ] **Step 1: Read the F005 reference**

Read `storage/_legacy/vault_v1/F005 pv_amount_corr_20d_x_tur_rank.md` in full to internalize section structure, callout patterns, and "first/second/third" narrative style.

- [ ] **Step 2: Overwrite the skill file**

Replace `.claude/skills/factor-report/skill.md` body entirely with:

````markdown
---
name: factor-report
description: Phase 4 后台 subagent — 为 admitted 因子按 F005 模板生成 Obsidian 深度报告
user_invocable: true
---

# /factor-report — 因子深度报告（F005 模板）

## 职责

为每个 admitted 因子生成 `vault/factors/F{id}.md`。参考模板：`storage/_legacy/vault_v1/F005 pv_amount_corr_20d_x_tur_rank.md`。

## 沙箱协议

| # | 规则 |
|---|---|
| 1 | 唯一输入：`_packets/report_packet_F{id}.md` + `vault/factors/F{id}/report.json`（由 render_factor 产出） |
| 2 | 唯一输出：`vault/factors/F{id}.md` |
| 3 | 禁止：Qlib / DB / network / 读 result.yaml / 自行算指标 |
| 4 | 图表白名单：`![[F{id}/<name>.png]]` 仅限 `report.json.charts` 里列出的 basename |
| 5 | 失败：append `_subagent_failures.log`，主循环不受影响 |

## 数据源

**`report_packet_F{id}.md`** 包含：
- factor YAML 摘要（expression, family_tag, validation_metrics, risk_metrics）
- Direction hypothesis 节选
- Judge Synthesis（C{id}.md 全文 — 6 CP 推理）
- Library context（最近邻 F{近邻} 关系）
- `## Available Charts`（图表白名单）

**`report.json`** 包含：
- `charts`: dict[name → relative_path] — 哪些 PNG 可 embed
- `composite`: 7 维得分 + grade + overall score
- `scalars`: ic/quintile/uniqueness/barra/feasibility/distribution 的所有汇总数字

## 输出结构（固定 10 节）

### frontmatter

```yaml
---
id: "F{id}"
name: <factor name>
tags: [factor, <family_tag>, grade-<A|B|C|D>]
category: <family_tag>
source_type: <dsl|python>
expression: <raw DSL>
direction: <direction tag>
batch: <batch_id>
admitted_at: <iso>
decision: admit
composite_grade: <A|B|C|D>
composite_score: <0-100>
ic_mean_validation: <float>
ic_ir_validation: <float>
monotonicity_validation: <float>
alpha_survival_ratio: <float>
max_lib_corr: <float>
---
```

### Section 0 — 标题 + TL;DR + 指标快表

```markdown
# F{id} — {name}

> [!success] Verdict: ADMIT | Grade: =={grade}== ({score}/100)
> {1-3 句核心总结}

| Metric | In-Sample | Out-of-Sample |
|---|---|---|
| Rank IC Mean | ... | =={val}== |
| Rank ICIR | ... | =={val}== |
| Win Rate | ... | ... |
| t-stat | ... | =={val}== |
| Monotonicity (val) | — | =={val}== |

> [!tip] 核心判断
> {3-5 句从 judge synthesis 抽取的因子独特性 + 风险}

![[F{id}/radar.png|500]]
```

### Section 1 — Judge Verdict（从 judge synthesis 提炼）

```markdown
## Judge Verdict

> [!abstract] 6-Dimension Assessment
> Effect=**{strong|borderline|weak}**, Stability=**{stable|mixed|unstable}**,
> Redundancy=**{low|medium|high}**, Feasibility=**{ok|limited}**,
> Risk Model=**{good|acceptable|borderline|poor}**, Mechanism=**{aligned|mixed|misaligned}**

### Reason Codes

| Code | Severity | 含义 |
|---|---|---|
| {code} | {info|medium|high} | {1 句} |
```

### Section 2 — 预测能力（3.1）

对每个可用图表（从 `report.json.charts` 查白名单），写：

```markdown
#### {子标题}

> [!info]- 阅读指南
> {1-2 句说明横纵轴}

![[F{id}/{chart_name}.png|600]]

**第一，{观察点}。** {解读}

**第二，{观察点}。** {解读}

**第三，{观察点}。** {解读}
```

子段清单（若图存在则写）：
- IC 时序走势 (`ic_timeseries`)
- 累积 IC (`cumulative_ic`)
- 滚动 IC (`rolling_ic`)
- IC 分布 (`ic_distribution`)
- 月度 IC 热力图 (`monthly_heatmap`)

### Section 3 — 盈利能力（3.2）

- 分组年化收益 (`quintile_bar`)
- 验证期分组收益 (`quintile_returns_oos`)
- 累积净值曲线 (`cumulative_returns`)
- 多空策略表现 (`long_short`)
- 年度分组热力图 (`annual_group_returns`)

### Section 4 — 风险归因（3.3）

- Barra 风格因子暴露 (`style_exposure_bar`)
- Alpha 存活瀑布 (`alpha_waterfall`)

### Section 5 — 信号稳定性（3.4）

- 多验证窗口 IC (`support_window_ic`)
- 稳定性综合 (`stability_summary`)

### Section 6 — 衰减与可交易性（3.5）

- IC 衰减 (`ic_decay`)
- 因子值分布 (`factor_distribution`)
- 覆盖率 (`coverage`)

### Section 7 — 独特性（3.6）

- 因子库相关矩阵 (`correlation_bar`)

### Section 8 — 综合评分（3.7）

![[F{id}/radar.png|600]]

| 维度 | 得分 | 解读 |
|---|---|---|
| Predictive Power | {v} | ... |
| Signal Stability | {v} | ... |
| ... | ... | ... |

### Section 9 — 研究脉络与经济机制（4.1）

> [!note]- 研究脉络与经济机制
### 市场假说 / 经济机制 / 实验设计

**三段论**：机制是什么 / 为什么持续 / 什么时候失效。引用 `[[directions/{direction}]]`。

### Section 10 — 批判性审查（4.2）

> [!danger]- 批判性审查

> [!danger] 一句话毒舌
> {尖锐评价因子的本质短板}

### 致命弱点

1. {编号分析}
2. ...

### 改进方向

1. ...

> [!warning] 使用警告
> {部署注意事项}

### Section 11 — 系统意义 + Graph Links（4.3）

> [!tip]- 系统意义
验证了什么 / 后续方向

## Graph Links
- **Hypothesis**: [[{logic_id}]]
- **Family**: [[{family_id}]]
- **Nearest**: [[factors/{nearest_fid}]]

%%Report generated: {date} | Source: report_packet + report.json%%
```

## 风格硬要求

- 分析叙述用中文；术语保留英文（IC / ICIR / Sharpe / Barra / Rank / Mono / L/S）
- 每段分析用"第一... / 第二... / 第三..." 编号
- 关键数字用 `==highlight==` 突出
- 尖锐判断必须放进 `> [!warning]` / `> [!danger]` callout
- Callout 段不要超过 3 行 —— 长内容拆到正文
- 绝不编造数字或图名；只用 `report.json.scalars` 和 `report.json.charts` 白名单里的东西

## 完成后

```bash
research commit-report F{id}
```
````

- [ ] **Step 3: No code test — lint the markdown manually**

Read the rewritten skill file end-to-end once to verify no broken examples.

- [ ] **Step 4: Commit**

```bash
git add .claude/skills/factor-report/skill.md
git commit -m "docs(skill): rewrite /factor-report around F005 template"
```

---

## Task 12: Update `/factor-mine` skill — remove duplicate + add back-fill

**Files:**
- Modify: `.claude/skills/factor-mine/skill.md` (Phase 4 section rewrite)

- [ ] **Step 1: Read current skill**

Read the current `.claude/skills/factor-mine/skill.md` Phase 4 section (Step 5 in the overall flow).

- [ ] **Step 2: Replace "Step 5 — Phase 4 ARCHIVE" section**

Replace the existing Step 5 block with:

```markdown
### Step 5 — Phase 4 ARCHIVE（纯 Python + 1 个后台 subagent）

direction body 的更新由 Phase 3 JUDGE 完成（见 /factor-judge audit c14/c15/c16）。Phase 4 只做 factor 归档 + F{id} 回填 + 后台 report 派发 + 主 commit。

6 步流程：

**Step 1 — Python：factor.yaml 归档**
- 按 judge.md 里 verdict=admit 的 candidate_id 升序，调 `factor_writer.allocate_and_write_factor` 单调分配 F{id}
- 写 `vault/factors/F{id}.yaml`
- `source_type: python` 时 copy .py 到 `python_factors/F{id}_{name}.py`

**Step 2 — Python：F{id} 回填（backfill）**
三处机械 edit，全部幂等：
- `batches/{batch}/candidates/C{id}.md` frontmatter `factor_id: null` → `factor_id: F{id}`
- `batches/{batch}/judge.md` 表格行 "admit" → "admit → F{id}" + 追加 `[[factors/F{id}]]`
- `directions/{dir}.md` Thread evidence trail 对应 admit 行末尾追加 `→ [[factors/F{id}]]`

**Step 3 — Python：render_factor 画图**
- `render_factor(F{id}, storage_root)` 纯 load parquet + yaml → 写 `factors/F{id}/*.png` (18 张) + `report.json`
- 零重算（所有数据来自 Phase 2 artifacts / result.yaml）
- 失败不阻塞主 commit

**Step 4 — Python：report_packer 打包**
- 读 `factor.yaml` + judge C{id}.md + direction hypothesis + `report.json.charts` 白名单
- 写 `batches/{batch}/_packets/report_packet_F{id}.md`

**Step 5 — Subagent（后台，不阻塞）：写 factor.md**
- dispatch `/factor-report`
- 读 packet + `report.json`，按 F005 模板写 `vault/factors/F{id}.md`
- 完成独立 commit：`[report] F{id} {name} report generated`

**Step 6 — Python：direction frontmatter + INDEX + 主 commit**
- `rounds++ / admits++ / members append F{id} / last_batch / last_activity`
- 刷新 `INDEX.md` 下半段统计表
- `research commit {batch_id}` 单一主 commit（含 factor.yaml / backfill / _packets / PNG / report.json），**不含 factor.md**（后台独立提交）

验证：`state.yaml.current_batch == null`（finish_batch 已执行）
```

- [ ] **Step 3: Update "数据流" / "关键约束" sections to match the new reality**

Find the architecture diagram in the skill; update the Phase 4 swimlane to show the 6-step flow. Add one line to 关键约束:
```
- **R4 无重算**：Phase 4 render_factor 从 `cache/batch_diagnostics/` 直接 load parquet，不触碰 Qlib/DB/signal 重算
```

- [ ] **Step 4: Commit**

```bash
git add .claude/skills/factor-mine/skill.md
git commit -m "docs(skill): /factor-mine Phase 4 — remove duplicate direction update, add F{id} backfill"
```

---

## Task 13: Delete legacy report code

**Files:**
- Delete: `src/report/analytics/` (entire dir)
- Delete: `src/report/analytics_v2/` (entire dir)
- Delete: `src/report/config_adapter.py`
- Delete: `src/report/data_prep.py`
- Delete: `src/report/scorer.py`
- Delete: `src/report/renderer.py`
- Delete: `tests/report/analytics_v2/`

- [ ] **Step 1: Confirm nothing imports the to-be-deleted modules**

Run grep (BEFORE deleting):
```bash
cd /Users/xinzhan/.openclaw/workspace/quant_factor_system
grep -rn "report\.analytics\|report\.config_adapter\|report\.data_prep\|report\.scorer\|report\.renderer" src/ tests/ --include='*.py' | grep -v __pycache__
```

Expected after Tasks 1–10: no references outside the files we're deleting and their own tests.

- [ ] **Step 2: Run the whole test suite to confirm baseline green**

Run: `pytest -q 2>&1 | tail -20`
Expected: PASS (since new code replaces everything that used these).

- [ ] **Step 3: Delete the files**

```bash
rm -rf src/report/analytics
rm -rf src/report/analytics_v2
rm src/report/config_adapter.py src/report/data_prep.py src/report/scorer.py src/report/renderer.py
rm -rf tests/report/analytics_v2
```

- [ ] **Step 4: Re-run tests**

Run: `pytest -q 2>&1 | tail -20`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "chore(report): drop legacy analyzers / scorer / renderer / adapters"
```

---

## Task 14: End-to-end smoke test

**Files:**
- (none new — integration check only)

- [ ] **Step 1: Full pytest**

Run: `pytest -q`
Expected: all pass.

- [ ] **Step 2: Dry-run Phase 4 on an existing batch**

Pick a recently judged batch (e.g. `batch_008`), temporarily point to a scratch storage:
```bash
PYTHONPATH=src python3 -m research archive batch_008
```
Expected:
- `storage/vault/factors/F{id}.yaml` appears
- `storage/vault/factors/F{id}/*.png` (~18 files) present
- `storage/vault/factors/F{id}/report.json` present
- `candidates/C{id}.md` frontmatter has `factor_id: F{id}` filled
- `judge.md` row shows "admit → F{id}"

- [ ] **Step 3: Run `python -m report.builder --factor-id F{id}`**

Should regenerate PNGs+report.json without touching any other files.

- [ ] **Step 4: Final commit if anything shifted**

```bash
git status
# (expected clean, unless test artifacts leaked)
```

---

## Completion Checklist

- [ ] Phase 2 writes coverage_daily + factor_hist parquets (Task 1)
- [ ] Composite scorer + 18 chart functions implemented with tests (Tasks 2–6)
- [ ] Render orchestrator integrated (Task 7)
- [ ] Back-fill module with idempotency tests (Task 8)
- [ ] Phase 4 wires renderer + backfill; CLI injects callback (Task 9)
- [ ] `report.builder` collapsed to thin CLI (Task 10)
- [ ] `/factor-report` skill rewritten for F005 template (Task 11)
- [ ] `/factor-mine` Phase 4 section rewritten, direction update duplicate removed, F{id} backfill added (Task 12)
- [ ] Legacy `analytics/`, `analytics_v2/`, `scorer.py`, `renderer.py`, `config_adapter.py`, `data_prep.py` deleted (Task 13)
- [ ] E2E smoke: archive an existing batch, verify 18 PNGs + backfilled wikilinks + idempotent re-run (Task 14)
