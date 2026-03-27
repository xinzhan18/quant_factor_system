# Report Module Refactor — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extract report code from `mining/report/` and `visualization/` into a standalone top-level `report/` module with clear layer separation.

**Architecture:** Four layers — analytics (pure compute+chart, zero IO), scorer (pure Python scoring), builder (thin IO+orchestration), renderer (Jinja2 HTML). The `visualization/` directory is fully absorbed; `mining/report/` is deleted.

**Tech Stack:** Python, pandas, numpy, scipy, plotly, jinja2

**Spec:** `docs/superpowers/specs/2026-03-28-report-module-refactor-design.md`

---

### Task 1: Create report/analytics/ic.py — ICAnalyzer

**Files:**
- Create: `report/__init__.py`, `report/analytics/__init__.py`, `report/analytics/ic.py`
- Source: `visualization/ic_analyzer.py` (all methods), `mining/report/builder.py:263-313` (compute_ic_summary, compute_annual_breakdown, compute_monthly_heatmap_data), `mining/report/builder.py:23-27` (_REGIME_LOOKUP), `mining/report/builder.py:456-475` (cumulative IC + monthly heatmap charts)
- Test: `tests/report/__init__.py`, `tests/report/analytics/__init__.py`, `tests/report/analytics/test_ic.py`

- [ ] **Step 1: Create directory structure and empty `__init__.py` files**

```bash
mkdir -p report/analytics tests/report/analytics
touch report/__init__.py report/analytics/__init__.py tests/report/__init__.py tests/report/analytics/__init__.py
```

- [ ] **Step 2: Write tests for ICAnalyzer**

Create `tests/report/analytics/test_ic.py` with tests migrated from `tests/mining/report/test_builder.py` (TestAnnualICBreakdown, TestMonthlyHeatmap) plus new tests for compute_ic and compute_ic_summary. Tests call `ICAnalyzer` methods directly (not builder private methods).

- [ ] **Step 3: Run tests — expect FAIL (ICAnalyzer doesn't exist)**

```bash
pytest tests/report/analytics/test_ic.py -v
```

- [ ] **Step 4: Implement report/analytics/ic.py**

Merge from `visualization/ic_analyzer.py` (full class: compute_ic, plot_ic_timeseries, plot_ic_distribution, plot_rolling_ic_comparison, compute_ic_statistics). Add methods extracted from builder: `compute_ic_summary`, `compute_annual_breakdown`, `compute_monthly_heatmap_data` (converted from private to public). Add new chart methods: `plot_cumulative_ic`, `plot_monthly_heatmap`. Include `_REGIME_LOOKUP` dict at module level.

- [ ] **Step 5: Run tests — expect PASS**

```bash
pytest tests/report/analytics/test_ic.py -v
```

- [ ] **Step 6: Commit**

```bash
git add report/ tests/report/
git commit -m "feat(report): add ICAnalyzer to report/analytics/ic.py"
```

---

### Task 2: Create report/analytics/groups.py — GroupReturnsAnalyzer

**Files:**
- Create: `report/analytics/groups.py`
- Source: `visualization/group_returns.py` (all methods except plot_returns_decay), `mining/report/builder.py:317-371` (compute_quintile_detailed_stats, compute_monotonicity), `mining/report/builder.py:493-498` (IS vs OOS bar chart)
- Test: `tests/report/analytics/test_groups.py`

- [ ] **Step 1: Write tests for GroupReturnsAnalyzer**

Create `tests/report/analytics/test_groups.py` with tests for compute_group_returns, compute_monotonicity, compute_quintile_detailed_stats.

- [ ] **Step 2: Run tests — expect FAIL**

- [ ] **Step 3: Implement report/analytics/groups.py**

Merge from `visualization/group_returns.py` (compute_group_returns, plot_group_returns_bar, plot_cumulative_returns, plot_long_short, compute_group_statistics). Add: `compute_quintile_detailed_stats`, `compute_monotonicity`, `plot_is_vs_oos_bar`. Do NOT include `plot_returns_decay` (goes to DecayAnalyzer).

- [ ] **Step 4: Run tests — expect PASS**

- [ ] **Step 5: Commit**

```bash
git add report/analytics/groups.py tests/report/analytics/test_groups.py
git commit -m "feat(report): add GroupReturnsAnalyzer to report/analytics/groups.py"
```

---

### Task 3: Create report/analytics/decay.py — DecayAnalyzer

**Files:**
- Create: `report/analytics/decay.py`
- Source: `mining/report/builder.py:375-425` (compute_decay, compute_autocorrelation), `mining/report/builder.py:532-548` (plot_ic_decay, plot_autocorrelation), `visualization/group_returns.py:293-358` (plot_returns_decay)
- Test: `tests/report/analytics/test_decay.py`

- [ ] **Step 1: Write tests**
- [ ] **Step 2: Run tests — expect FAIL**
- [ ] **Step 3: Implement report/analytics/decay.py**
- [ ] **Step 4: Run tests — expect PASS**
- [ ] **Step 5: Commit**

```bash
git add report/analytics/decay.py tests/report/analytics/test_decay.py
git commit -m "feat(report): add DecayAnalyzer to report/analytics/decay.py"
```

---

### Task 4: Create report/analytics/distribution.py — DistributionAnalyzer

**Files:**
- Create: `report/analytics/distribution.py`
- Source: `mining/report/builder.py:246-259` (compute_stats), `mining/report/builder.py:503-527` (plot_distribution, plot_coverage)
- Test: `tests/report/analytics/test_distribution.py`

- [ ] **Step 1: Write tests**

Migrate `TestDistributionStats` from `tests/mining/report/test_builder.py` — change to call `DistributionAnalyzer.compute_stats()`.

- [ ] **Step 2: Run tests — expect FAIL**
- [ ] **Step 3: Implement report/analytics/distribution.py**
- [ ] **Step 4: Run tests — expect PASS**
- [ ] **Step 5: Commit**

```bash
git add report/analytics/distribution.py tests/report/analytics/test_distribution.py
git commit -m "feat(report): add DistributionAnalyzer to report/analytics/distribution.py"
```

---

### Task 5: Move report/scorer.py

**Files:**
- Create: `report/scorer.py`
- Source: `mining/report/scorer.py` (move as-is, no changes)
- Test: `tests/report/test_scorer.py`

- [ ] **Step 1: Copy scorer.py to report/scorer.py**
- [ ] **Step 2: Move test — copy `tests/mining/report/test_scorer.py` to `tests/report/test_scorer.py`, update import from `mining.report.scorer` to `report.scorer`**
- [ ] **Step 3: Run tests — expect PASS**

```bash
pytest tests/report/test_scorer.py -v
```

- [ ] **Step 4: Commit**

```bash
git add report/scorer.py tests/report/test_scorer.py
git commit -m "feat(report): move CompositeScorer to report/scorer.py"
```

---

### Task 6: Move report/renderer.py + templates/

**Files:**
- Create: `report/renderer.py`, `report/templates/factor_report.html.j2`
- Source: `mining/report/renderer.py`, `mining/report/templates/factor_report.html.j2`
- Test: `tests/report/test_renderer.py`

- [ ] **Step 1: Copy renderer.py and templates/**
- [ ] **Step 2: Update template path in renderer.py** — `os.path.dirname(__file__)` already works, just verify
- [ ] **Step 3: Move test — copy `tests/mining/report/test_renderer.py` to `tests/report/test_renderer.py`, update import**
- [ ] **Step 4: Run tests — expect PASS**

```bash
pytest tests/report/test_renderer.py -v
```

- [ ] **Step 5: Commit**

```bash
git add report/renderer.py report/templates/ tests/report/test_renderer.py
git commit -m "feat(report): move ReportRenderer and templates to report/"
```

---

### Task 7: Rewrite report/builder.py — thin orchestrator

**Files:**
- Create: `report/builder.py`
- Source: `mining/report/builder.py` (rewrite — keep IO methods, replace compute with analytics calls)
- Test: `tests/report/test_builder.py`

- [ ] **Step 1: Write integration test for builder**

Create `tests/report/test_builder.py` — test that `ReportDataBuilder` imports from `report.builder` and its `build()` method assembles data correctly (mock DB). Keep it focused on orchestration, not analytics logic.

- [ ] **Step 2: Implement report/builder.py**

Keep: `__init__`, `build`, `_load_factor_metadata`, `_load_data_from_db`, `_to_flat_df`, `_get_max_library_correlation`, `_fig_to_html`, `save`, `main`.

Replace all `_compute_*` calls with analytics imports:
```python
from report.analytics.ic import ICAnalyzer
from report.analytics.groups import GroupReturnsAnalyzer
from report.analytics.decay import DecayAnalyzer
from report.analytics.distribution import DistributionAnalyzer
from report.scorer import CompositeScorer
```

Replace all `_generate_*_charts` with direct calls to analyzer `plot_*` methods. Keep the radar chart inline (CompositeScorer stays pure).

Target: ~200 lines.

- [ ] **Step 3: Run all report tests**

```bash
pytest tests/report/ -v
```

- [ ] **Step 4: Commit**

```bash
git add report/builder.py tests/report/test_builder.py
git commit -m "feat(report): rewrite ReportDataBuilder as thin orchestrator"
```

---

### Task 8: Update report/__init__.py with public API

**Files:**
- Modify: `report/__init__.py`

- [ ] **Step 1: Write public exports**

```python
from report.analytics.ic import ICAnalyzer
from report.analytics.groups import GroupReturnsAnalyzer
from report.analytics.decay import DecayAnalyzer
from report.analytics.distribution import DistributionAnalyzer
from report.scorer import CompositeScorer
from report.builder import ReportDataBuilder
from report.renderer import ReportRenderer
```

- [ ] **Step 2: Commit**

```bash
git add report/__init__.py
git commit -m "feat(report): export public API from report/__init__.py"
```

---

### Task 9: Update consumers

**Files:**
- Modify: `mining/publisher.py:226-227`
- Modify: `dashboard/pages/Factors.py:19`
- Modify: `quant_factor_system/__init__.py:12`
- Modify: `.claude/skills/factor-report.md:23,93`

- [ ] **Step 1: Update mining/publisher.py**

```python
# Line 226-227: change
from mining.report.builder import ReportDataBuilder
from mining.report.renderer import ReportRenderer
# to
from report.builder import ReportDataBuilder
from report.renderer import ReportRenderer
```

Also update the report_dir path at line 229 — currently `os.path.join(os.path.dirname(self.config.library_dir), "reports")`.

- [ ] **Step 2: Update dashboard/pages/Factors.py**

```python
# Line 19: change
from quant_factor_system.visualization import ICAnalyzer
# to
from report.analytics.ic import ICAnalyzer
```

- [ ] **Step 3: Update quant_factor_system/__init__.py**

Update docstring line 12 from `from quant_factor_system.visualization import ICAnalyzer` to `from report.analytics.ic import ICAnalyzer`.

- [ ] **Step 4: Update .claude/skills/factor-report.md**

```
# Line 23: change
python3 -m mining.report.builder --factor-id FACTOR_ID --output-dir ...
# to
python3 -m report.builder --factor-id FACTOR_ID --output-dir ...

# Line 93: change
python3 -m mining.report.renderer --input-dir ... --output-dir mining/reports/
# to
python3 -m report.renderer --input-dir ... --output-dir mining/reports/
```

- [ ] **Step 5: Run existing publisher tests**

```bash
pytest tests/mining/test_publisher.py -v
```

- [ ] **Step 6: Commit**

```bash
git add mining/publisher.py dashboard/pages/Factors.py __init__.py .claude/skills/factor-report.md
git commit -m "refactor: update all consumers to use report/ module"
```

---

### Task 10: Delete old directories

**Files:**
- Delete: `visualization/` (entire directory)
- Delete: `mining/report/` (entire directory)
- Delete: `tests/visualization/` (entire directory)
- Delete: `tests/mining/report/` (entire directory)

- [ ] **Step 1: Verify no remaining imports reference old paths**

```bash
grep -r "from visualization" --include="*.py" . | grep -v __pycache__ | grep -v _archive
grep -r "from mining.report" --include="*.py" . | grep -v __pycache__ | grep -v _archive
```

- [ ] **Step 2: Delete old directories**

```bash
rm -rf visualization/
rm -rf mining/report/
rm -rf tests/visualization/
rm -rf tests/mining/report/
```

- [ ] **Step 3: Run full test suite**

```bash
pytest tests/report/ tests/mining/ -v
```

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "refactor: delete visualization/ and mining/report/ — fully replaced by report/"
```
