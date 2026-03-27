# Report Module Refactor — Design Spec

## Problem

Report-related code is scattered across three locations with overlapping responsibilities:

| Location | Content | Lines |
|----------|---------|-------|
| `visualization/` | ICAnalyzer, GroupReturnsAnalyzer, FactorReportGenerator | ~750 |
| `mining/report/` | ReportDataBuilder, ReportRenderer, CompositeScorer | ~780 |
| `mining/reports/` | 23 generated HTML files (output artifacts) | — |

Issues:
1. **Wrong location**: Report generation is not "mining" but lives inside `mining/`.
2. **God Object**: `mining/report/builder.py` (589 lines) does data loading, IC analysis, group returns, decay, distribution, and chart generation.
3. **Duplication**: `visualization/` IC/group-return charts overlap with `builder.py` chart methods.
4. **Diamond dependency**: `mining/report/builder.py` imports from `visualization/`; `dashboard/` also imports from `visualization/`.
5. **Ambiguous role**: `visualization/` is simultaneously a compute engine, chart library, and report generator.

## Solution

Create a top-level `report/` module. Merge `visualization/` into it. Delete both `visualization/` and `mining/report/`.

### Package Path Convention

`report/` is a top-level directory alongside `mining/`, `core/`, `data/`, `dashboard/`. The project uses bare imports (`from mining.config import ...`, `from core.config import ...`) because the project root is on `sys.path`. The new module follows the same convention: `from report.builder import ReportDataBuilder`.

The `dashboard/` currently uses installed-package imports (`from quant_factor_system.visualization import ICAnalyzer`). This must change to `from report.analytics.ic import ICAnalyzer` to match the project's bare-import convention. If the dashboard also needs the installed-package path, `quant_factor_system/__init__.py` must re-export from `report.analytics`.

### Target Structure

```
report/
├── __init__.py                 # Public API exports
├── analytics/                  # Analyzers: compute + plot, zero IO
│   ├── __init__.py
│   ├── ic.py                   # ICAnalyzer (merged from visualization/ic_analyzer.py)
│   ├── groups.py               # GroupReturnsAnalyzer (merged from visualization/group_returns.py)
│   ├── decay.py                # DecayAnalyzer (extracted from builder.py)
│   └── distribution.py         # DistributionAnalyzer (extracted from builder.py)
├── scorer.py                   # CompositeScorer (moved as-is from mining/report/scorer.py, stays pure Python)
├── builder.py                  # Thin orchestrator: load data → analytics → scorer → assemble dict
├── renderer.py                 # Jinja2 HTML rendering (moved from mining/report/renderer.py)
└── templates/
    └── factor_report.html.j2   # HTML template (moved as-is)
```

### Layer Responsibilities

**analytics/ — Zero IO, stateless**

Each Analyzer class combines computation and Plotly chart generation. All inputs are DataFrames; all outputs are dicts or Plotly Figures. No file IO, no DB access.

ICAnalyzer (merged from `visualization/ic_analyzer.py` + builder's IC compute/chart methods):
- `compute_ic(factor_df, price_df, split_date)` → dict with rolling_ic, ic_all, etc.
- `compute_ic_statistics(rolling_ic)` → DataFrame
- `compute_annual_breakdown(daily_ic)` → list[dict] (from builder's `_compute_annual_breakdown`)
- `compute_monthly_heatmap_data(daily_ic)` → list (from builder's `_compute_monthly_heatmap_data`)
- `compute_ic_summary(daily_ic, split_date)` → tuple[dict, dict] (from builder's `_compute_ic_summary`)
- `plot_ic_timeseries(rolling_ic, split_date)` → Figure
- `plot_ic_distribution(rolling_ic)` → Figure
- `plot_rolling_ic_comparison(daily_ic, windows)` → Figure
- `plot_cumulative_ic(daily_ic)` → Figure (from builder's inline cumulative IC chart)
- `plot_monthly_heatmap(monthly_data)` → Figure (from builder's inline heatmap chart)

GroupReturnsAnalyzer (merged from `visualization/group_returns.py` + builder's quintile methods):
- `compute_group_returns(factor_df, price_df, n_groups, split_date)` → dict
- `compute_quintile_detailed_stats(gr_result)` → dict (from builder's `_compute_quintile_detailed_stats`)
- `compute_monotonicity(gr_result)` → float (from builder's `_compute_monotonicity`)
- `compute_group_statistics(mean_returns, std_returns, sharpe, cumulative_returns)` → DataFrame
- `plot_group_returns_bar(mean_returns)` → Figure
- `plot_cumulative_returns(cumulative_returns)` → Figure
- `plot_long_short(cumulative_returns)` → Figure
- `plot_is_vs_oos_bar(gr_is, gr_oos)` → Figure (from builder's inline IS/OOS bar chart)

DecayAnalyzer (extracted from builder.py + `visualization/group_returns.py`):
- `compute_decay(flat_factor, price_df, periods)` → dict (from builder's `_compute_decay`)
- `compute_autocorrelation(factor_values)` → list (from builder's `_compute_autocorrelation`)
- `plot_ic_decay(decay_result, name)` → Figure (from builder's `_generate_decay_charts`)
- `plot_autocorrelation(autocorr, name)` → Figure (from builder's `_generate_decay_charts`)
- `plot_returns_decay(factor_df, price_df, holding_periods, name)` → Figure (from `GroupReturnsAnalyzer.plot_returns_decay`)

DistributionAnalyzer (extracted from builder.py):
- `compute_stats(factor_values)` → dict (from builder's `_compute_distribution_stats`)
- `plot_distribution(fv_is, fv_oos, name)` → Figure (from builder's `_generate_distribution_charts`)
- `plot_coverage(factor_values)` → Figure (from builder's `_generate_distribution_charts`)

**scorer.py** — CompositeScorer, moved as-is from `mining/report/scorer.py`. Stays pure Python with zero external dependencies. The radar chart generation (currently in builder's `_generate_score_charts`) stays in `builder.py`'s chart assembly step, not in the scorer.

**builder.py** — The only place that touches IO (DB reads, YAML reads). Also handles the radar chart assembly since it's the only chart that doesn't belong to a specific analyzer.

```
ReportDataBuilder.build(factor_id) -> dict:
    1. Load factor metadata from YAML
    2. Load factor values + price data from DB
    3. Call analytics (ICAnalyzer, GroupReturnsAnalyzer, DecayAnalyzer, DistributionAnalyzer)
    4. Call CompositeScorer
    5. Generate all charts via analyzer plot methods + radar chart inline
    6. Assemble and return report_data dict
```

Target: ~200 lines (down from 589). The builder retains `_load_factor_metadata`, `_load_data_from_db`, `_to_flat_df`, `_get_max_library_correlation` as private helpers (these are IO methods). All compute logic moves to analytics/.

builder.py and renderer.py retain their `if __name__ == "__main__": main()` CLI blocks so they remain invocable as `python -m report.builder` and `python -m report.renderer`.

**renderer.py** — Jinja2 template rendering, moved as-is.

### Migration Plan

| Source | Action | Destination |
|--------|--------|-------------|
| `visualization/ic_analyzer.py` | Merge into | `report/analytics/ic.py` |
| `visualization/group_returns.py` | Merge core into | `report/analytics/groups.py` |
| `visualization/group_returns.py` `plot_returns_decay` | Move to | `report/analytics/decay.py` |
| `visualization/report.py` | **Drop** — superseded by builder.py | Delete (see Dropped Classes) |
| `visualization/__init__.py` | Delete entire `visualization/` | — |
| `mining/report/scorer.py` | Move as-is | `report/scorer.py` |
| `mining/report/builder.py` | Rewrite as thin orchestrator | `report/builder.py` |
| `mining/report/renderer.py` | Move | `report/renderer.py` |
| `mining/report/templates/` | Move | `report/templates/` |
| `mining/report/__init__.py` | Delete entire `mining/report/` | — |
| Builder `_compute_decay`, `_compute_autocorrelation` | Extract to | `report/analytics/decay.py` |
| Builder `_compute_distribution_stats` | Extract to | `report/analytics/distribution.py` |
| Builder `_compute_annual_breakdown`, `_compute_monthly_heatmap_data`, `_compute_ic_summary` | Extract to | `report/analytics/ic.py` |
| Builder `_compute_quintile_detailed_stats`, `_compute_monotonicity` | Extract to | `report/analytics/groups.py` |
| Builder `_generate_*_charts` | Distribute to respective analyzer `plot_*` methods | `report/analytics/*.py` |
| Builder `_generate_score_charts` (radar) | Stays in | `report/builder.py` (inline) |

### Dropped Classes

- **`FactorReportGenerator`** (from `visualization/report.py`): This is an earlier, simpler report generator that is fully superseded by `ReportDataBuilder`. It will be deleted with no replacement. Its test assertion in `tests/visualization/test_imports.py` will be removed.
- **`create_report_generator`**, **`create_ic_analyzer`**, **`create_group_analyzer`** factory functions: Trivial wrappers (`return ICAnalyzer(name)`). Not carried over — callers use constructors directly.

### Consumer Updates

| Consumer | Current Import | New Import |
|----------|---------------|------------|
| `mining/publisher.py` (line 226-227) | `from mining.report.builder import ReportDataBuilder` | `from report.builder import ReportDataBuilder` |
| `mining/publisher.py` (line 227) | `from mining.report.renderer import ReportRenderer` | `from report.renderer import ReportRenderer` |
| `dashboard/pages/Factors.py` (line 19) | `from quant_factor_system.visualization import ICAnalyzer` | `from report.analytics.ic import ICAnalyzer` |
| `quant_factor_system/__init__.py` (line 12) | `from quant_factor_system.visualization import ICAnalyzer` | `from report.analytics.ic import ICAnalyzer` |
| `mining/report/__init__.py` | Re-exports `ReportDataBuilder`, `ReportRenderer`, `CompositeScorer` | Deleted — no code imports via `from mining.report import ...` besides publisher.py which uses direct module imports |
| `.claude/skills/factor-report.md` | `python3 -m mining.report.builder`, `python3 -m mining.report.renderer` | `python3 -m report.builder`, `python3 -m report.renderer` |
| `tests/visualization/test_imports.py` | Asserts `FactorReportGenerator`, `ICAnalyzer`, `GroupReturnsAnalyzer` | Rewrite to test `from report.analytics.ic import ICAnalyzer` etc. Drop `FactorReportGenerator` assertion. |
| `tests/mining/report/test_builder.py` | `from mining.report.builder import ReportDataBuilder` | Split: `TestDistributionStats` → `tests/report/analytics/test_distribution.py` (call `DistributionAnalyzer.compute_stats`); `TestAnnualICBreakdown`, `TestMonthlyHeatmap` → `tests/report/analytics/test_ic.py` (call `ICAnalyzer.compute_annual_breakdown` / `compute_monthly_heatmap_data`); remaining builder integration tests → `tests/report/test_builder.py` |
| `tests/mining/report/test_scorer.py` | `from mining.report.scorer import CompositeScorer` | Move to `tests/report/test_scorer.py`, import from `report.scorer` |
| `tests/mining/report/test_renderer.py` | `from mining.report.renderer import ReportRenderer` | Move to `tests/report/test_renderer.py`, import from `report.renderer` |

### Design Decisions

1. **Compute + plot in same class**: In quant analytics, an ICAnalyzer knowing both "how to compute" and "how to chart" is natural. Splitting adds indirection without clarity.
2. **Builder is the only IO boundary**: analytics/ is stateless and IO-free, making it easy to test and reuse.
3. **No report CLI command**: builder.py and renderer.py keep their `__main__` blocks for ad-hoc invocation, but no new CLI subcommand is added to the mining CLI.
4. **Keep existing chart logic**: The Plotly charts from both visualization/ and builder.py will be merged, preferring the richer version (builder.py's charts have more features like cumulative IC, monthly heatmap).
5. **HTML output location**: Generated reports stay in `mining/reports/` (output artifacts, not code).
6. **Scorer stays pure**: CompositeScorer has no Plotly dependency. The radar chart stays in builder.py.
7. **Bare imports**: `report/` uses the same bare-import convention as `mining/`, `core/`, `data/`.
