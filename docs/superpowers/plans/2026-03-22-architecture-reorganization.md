# Architecture Reorganization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reorganize quant_factor_system around the mining pipeline, eliminating duplicate modules and archiving unused code.

**Architecture:** Mining becomes the core workflow. Data layer gains Qlib sync responsibility. Visualization becomes a standalone module. Backtest and old factors get archived.

**Tech Stack:** Python, Qlib, TimescaleDB, Streamlit, YAML

**Spec:** `docs/superpowers/specs/2026-03-22-architecture-reorganization-design.md`

---

### Task 1: Rewrite root `__init__.py`

**Files:**
- Modify: `__init__.py`

- [ ] **Step 1: Rewrite `__init__.py` to remove backtest and factors imports**

```python
"""
Quant Factor System - 量化因子研究平台

核心工作流: 自动化因子挖掘 (mining)
- 数据层: TimescaleDB存储, RiceQuant数据源, Qlib同步
- 挖掘层: 表达式引擎, 多阶段评估, 因子库, 经验记忆
- 可视化: IC分析, 分组收益, 报告生成

使用:
    from quant_factor_system.data import TimescaleDB
    from quant_factor_system.mining import FactorMiningEvaluator, FactorLibrary
    from quant_factor_system.visualization import ICAnalyzer
"""

__version__ = "4.1.0"

# 数据层
from .data import (
    QuantDataManager,
    RiceQuantSource,
    TimescaleDB,
    DataManager,
)

__all__ = [
    '__version__',
    'QuantDataManager',
    'RiceQuantSource',
    'TimescaleDB',
    'DataManager',
]
```

Note: We only eagerly import `data` here. `mining` and `visualization` are imported on-demand because `mining` requires Qlib (optional dep) and `visualization` requires plotly. Do NOT import from `.backtest` or `.factors`.

- [ ] **Step 2: Verify the package still imports without error**

Run: `cd /Users/xinzhan/.openclaw/workspace/quant_factor_system && python -c "from quant_factor_system import __version__; print(__version__)"`
Expected: `4.1.0`

- [ ] **Step 3: Commit**

```bash
git add __init__.py
git commit -m "refactor: strip backtest/factors from root __init__.py"
```

---

### Task 2: Update `setup.py`

**Files:**
- Modify: `setup.py`

- [ ] **Step 1: Update setup.py version and packages**

```python
from setuptools import setup, find_packages

setup(
    name="quant_factor_system",
    version="4.1.0",
    description="Quantitative Factor Mining and Research Platform",
    author="QuantFactorSystem",
    packages=find_packages(exclude=["_archive", "_archive.*", "examples", "examples.*"]),
    python_requires=">=3.8",
    install_requires=[
        "pandas>=1.5.0",
        "numpy>=1.21.0",
        "scipy>=1.10.0",
        "sqlalchemy>=2.0.0",
        "psycopg2-binary>=2.9.0",
        "matplotlib>=3.5.0",
        "plotly>=5.10.0",
        "streamlit>=1.20.0",
        "python-dateutil>=2.8.0",
        "pytz>=2023.3",
        "pyyaml>=6.0",
    ],
    extras_require={
        "ricequant": ["rqdatac>=1.0.0"],
        "mining": ["qlib>=0.9.0"],
        "dev": [
            "pytest>=7.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "quant-mining=quant_factor_system.mining.cli:main",
        ],
    },
)
```

- [ ] **Step 2: Commit**

```bash
git add setup.py
git commit -m "refactor: update setup.py version to 4.1.0, exclude archive"
```

---

### Task 3: Move `data_sync.py` to data layer

**Files:**
- Move: `mining/data_sync.py` → `data/qlib_sync.py`
- Modify: `mining/__init__.py`
- Modify: `mining/cli.py`
- Modify: `data/__init__.py`
- Modify: `tests/mining/test_data_sync.py`

- [ ] **Step 1: Copy data_sync.py to data/qlib_sync.py**

```bash
cp mining/data_sync.py data/qlib_sync.py
```

- [ ] **Step 2: Update `data/__init__.py` to export DataSynchronizer**

Add at the end of existing imports in `data/__init__.py`, before `__all__`:

```python
from .qlib_sync import DataSynchronizer
```

And add `'DataSynchronizer'` to the `__all__` list.

- [ ] **Step 3: Update `mining/__init__.py`**

Change line 8 from:
```python
from .data_sync import DataSynchronizer
```
to:
```python
from ..data.qlib_sync import DataSynchronizer
```

- [ ] **Step 4: Update `mining/cli.py`**

Change line 14 from:
```python
from .data_sync import DataSynchronizer
```
to:
```python
from ..data.qlib_sync import DataSynchronizer
```

- [ ] **Step 5: Update `tests/mining/test_data_sync.py`**

Change line 10 from:
```python
from mining.data_sync import DataSynchronizer
```
to:
```python
from data.qlib_sync import DataSynchronizer
```

Import style note: `mining/__init__.py` and `mining/cli.py` use **relative imports** (`from ..data.qlib_sync`) because they're inside the package. Tests use **absolute imports** (`from data.qlib_sync`) because they run from the project root. This is the standard Python convention.

Note: `mining/evaluator.py` does NOT import `data_sync` (verified — it imports only `.config` and `.expression`). No update needed there.

- [ ] **Step 6: Run existing tests to verify nothing broke**

Run: `cd /Users/xinzhan/.openclaw/workspace/quant_factor_system && python -m pytest tests/mining/test_data_sync.py -v`
Expected: All tests PASS

- [ ] **Step 7: Delete the original file**

```bash
rm mining/data_sync.py
```

- [ ] **Step 8: Re-run tests**

Run: `python -m pytest tests/mining/test_data_sync.py -v`
Expected: All tests PASS

- [ ] **Step 9: Commit**

```bash
git add data/qlib_sync.py data/__init__.py mining/__init__.py mining/cli.py tests/mining/test_data_sync.py
git rm mining/data_sync.py
git commit -m "refactor: move data_sync to data/qlib_sync (data layer responsibility)"
```

---

### Task 4: Extract visualization module

**Files:**
- Create: `visualization/__init__.py`
- Move: `factors/visualization/ic_analyzer.py` → `visualization/ic_analyzer.py`
- Move: `factors/visualization/group_returns.py` → `visualization/group_returns.py`
- Move: `factors/visualization/report.py` → `visualization/report.py`

- [ ] **Step 1: Create visualization directory and copy files**

```bash
mkdir -p visualization
cp factors/visualization/ic_analyzer.py visualization/ic_analyzer.py
cp factors/visualization/group_returns.py visualization/group_returns.py
cp factors/visualization/report.py visualization/report.py
```

- [ ] **Step 2: Create `visualization/__init__.py`**

```python
"""
Visualization module - Factor analysis charts and reports.

Extracted from factors/visualization/ as a standalone module.
All functions accept pure DataFrames as input.

Usage:
    from quant_factor_system.visualization import ICAnalyzer, GroupReturnsAnalyzer
"""

from .ic_analyzer import ICAnalyzer, create_ic_analyzer
from .group_returns import GroupReturnsAnalyzer, create_group_analyzer
from .report import FactorReportGenerator, create_report_generator

__all__ = [
    'ICAnalyzer',
    'create_ic_analyzer',
    'GroupReturnsAnalyzer',
    'create_group_analyzer',
    'FactorReportGenerator',
    'create_report_generator',
]
```

- [ ] **Step 3: Verify `tearsheet.py` is NOT moved**

`factors/visualization/tearsheet.py` is a one-off script with hardcoded `psycopg2` import and `_PROJECT_ROOT` path hacks. It is NOT a reusable visualization module. It will be archived with the rest of `factors/` in the archive task. Do NOT copy it to `visualization/`.

Similarly, `sentiment_overflow_tearsheet.py` and `analyze_ambiguous_amount_ratio.py` are one-off scripts — they go to archive.

**Spec deviation note**: The spec lists `tearsheet.py` in the target structure, but it has hardcoded DB connections and path hacks that make it unsuitable as a reusable module. This is an intentional deviation — the spec should be updated to reflect this exclusion.

- [ ] **Step 4: Verify visualization module imports work**

Run: `python -c "from visualization.ic_analyzer import ICAnalyzer; print('OK')"`
Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add visualization/
git commit -m "refactor: extract visualization as standalone module"
```

---

### Task 5: Update dashboard imports

**Files:**
- Modify: `dashboard/pages/Factors.py:21`
- Modify: `dashboard/Home.py:10-12`
- Modify: `dashboard/components/page_template.py:82-95`
- Modify: `dashboard/pages/Pipeline.py:14`
- Modify: `dashboard/pages/StrategyConfig.py:8-9`

- [ ] **Step 1: Update `dashboard/pages/Factors.py` line 21**

Change:
```python
from quant_factor_system.factors.visualization import ICAnalyzer
```
to:
```python
from quant_factor_system.visualization import ICAnalyzer
```

- [ ] **Step 2: Update `dashboard/Home.py`**

Change lines 10-12 from:
```python
from quant_factor_system import __version__
from quant_factor_system.data import TimescaleDB
from quant_factor_system.factors import register_all_builtins, list_factors
```
to:
```python
from quant_factor_system import __version__
from quant_factor_system.data import TimescaleDB
from quant_factor_system.mining import FactorLibrary, MiningConfig
```

Then update `get_factor_stats()` function (lines 86-112) to use mining library:

```python
def get_factor_stats() -> dict:
    """获取因子统计信息（从 mining library 读取）"""
    try:
        lib = FactorLibrary(MiningConfig())
        factors = lib.list_factors()
    except Exception:
        factors = []

    result = {
        'total': len(factors),
        'categories': {},
        'top_factors': []
    }

    for f in factors:
        cat = f.get('category', '其他')
        result['categories'][cat] = result['categories'].get(cat, 0) + 1
        ic = f.get('ic_mean')
        if ic is not None:
            result['top_factors'].append({
                'name': f.get('name', ''),
                'ic': ic,
                'type': f.get('category', '未知'),
            })

    result['top_factors'].sort(key=lambda x: abs(x.get('ic', 0)), reverse=True)
    result['top_factors'] = result['top_factors'][:5]

    return result
```

- [ ] **Step 3: Update `dashboard/components/page_template.py` `render_factor_selector` (lines 82-95)**

Replace the function:

```python
def render_factor_selector(key: str = "factor"):
    """
    渲染因子选择器（从 mining library 读取）
    """
    try:
        from quant_factor_system.mining import FactorLibrary, MiningConfig
        lib = FactorLibrary(MiningConfig())
        factors = lib.list_factors()
        factor_names = [f['name'] for f in factors] if factors else []
    except Exception:
        factor_names = []

    return st.selectbox("选择因子", factor_names, key=key)
```

- [ ] **Step 4: Stub `dashboard/pages/Pipeline.py`**

This page depends heavily on `factors.Pipeline` which is being archived. Replace entire import and main with a stub:

Change line 14 from:
```python
from quant_factor_system.factors import Pipeline, list_factors, register_all_builtins
```
to:
```python
# TODO: Redesign to use mining/library workflow
```

In the `main()` function, add at the top after the title:
```python
st.info("Pipeline 页面正在重构中，将整合 mining 工作流。请使用 /factor-mine 技能进行因子挖掘。")
return
```

- [ ] **Step 5: Stub `dashboard/pages/StrategyConfig.py`**

Change lines 8-11 from:
```python
from quant_factor_system.factors import register_all_builtins, list_factors
from quant_factor_system.dashboard.components import (
    factor_selector_form
)
```
to:
```python
from quant_factor_system.mining import FactorLibrary, MiningConfig
```

Note: `factor_selector_form` from `dashboard.components.forms` also depends on the old `factors` module. Remove the import. The function at line 39 (`selected_factors = factor_selector_form(...)`) should be replaced with a simple `st.multiselect`:

```python
selected_factors = st.multiselect("选择因子", get_available_factors(), key='strategy_factors')
```

Update `get_available_factors()` (lines 14-18):
```python
def get_available_factors():
    """获取可用的因子列表"""
    try:
        lib = FactorLibrary(MiningConfig())
        return [f['name'] for f in lib.list_factors()]
    except Exception:
        return []
```

- [ ] **Step 6: Verify dashboard Home.py imports work**

Run: `python -c "import dashboard.Home"`
Expected: No ImportError (may fail on streamlit runtime, but no import errors)

- [ ] **Step 7: Commit**

```bash
git add dashboard/
git commit -m "refactor: update dashboard imports to use mining/visualization"
```

---

### Task 6: Archive unused modules (do BEFORE deleting duplicates)

**Files:**
- Move: `backtest/` → `_archive/backtest/`
- Move: `factors/` → `_archive/factors/`
- Move: `examples/` → `_archive/examples/`

Archive first so no code is lost if something goes wrong mid-step. Git tracks everything, but archiving before deleting is strictly safer.

- [ ] **Step 1: Create archive directory and move modules**

```bash
mkdir -p _archive
git mv backtest _archive/backtest
git mv factors _archive/factors
git mv examples _archive/examples
```

- [ ] **Step 2: Create `_archive/__init__.py` to prevent accidental imports**

```python
"""Archived modules. Not for production use. See git history for context."""
raise ImportError(
    "The _archive package contains archived code. "
    "Use quant_factor_system.mining for factor evaluation, "
    "quant_factor_system.visualization for charts."
)
```

- [ ] **Step 3: Run mining tests to ensure nothing broke**

Run: `python -m pytest tests/mining/ -v`
Expected: All tests PASS

- [ ] **Step 4: Commit**

```bash
git add _archive/
git commit -m "refactor: archive backtest/, factors/, examples/ (no longer in use)"
```

---

### Task 7: Delete duplicate evaluator and registry from archive

**Files:**
- Delete: `_archive/factors/automation/evaluator.py`
- Delete: `_archive/factors/core/registry.py`
- Delete: `_archive/factors/automation/factor_register.py`

These are confirmed duplicates of `mining/evaluator.py` and `mining/library.py`. Remove them from the archive to avoid confusion.

- [ ] **Step 1: Delete the duplicate files from archive**

```bash
git rm _archive/factors/automation/evaluator.py
git rm _archive/factors/core/registry.py
git rm _archive/factors/automation/factor_register.py
```

- [ ] **Step 2: Commit**

```bash
git commit -m "refactor: remove duplicate evaluator and registry from archive"
```

---

### Task 8: Clean up scripts

**Files:**
- Move: most scripts → `_archive/scripts/`
- Keep: `scripts/data.sh`, `scripts/db.sh`, `scripts/stock_list_manager.py`, `scripts/__init__.py`

- [ ] **Step 1: Move non-essential scripts to archive**

```bash
mkdir -p _archive/scripts
for f in scripts/build_ambiguous_amount_ratio.py scripts/check_1min_completeness.py scripts/check_1min_data.py scripts/check_and_pull_1min.py scripts/cli.py scripts/deps.py scripts/fetch_full_market.py scripts/opening_gap_factor.py scripts/pull_1min_data.py scripts/pull_1min_optimized.py scripts/pull_all_years.py scripts/quick_check_1min.py scripts/recompute_factors.py scripts/run_pdf_factor.py scripts/update_industry.py; do
  git mv "$f" _archive/scripts/ 2>/dev/null || true
done
```

- [ ] **Step 2: Commit**

```bash
git add _archive/scripts/ scripts/
git commit -m "refactor: archive unused scripts, keep data.sh/db.sh/stock_list_manager"
```

---

### Task 9: Unify configuration (spec Step 8)

**Files:**
- Modify: `core/config.py`
- Modify: `mining/config.py`
- Modify: `mining/cli.py:37`

- [ ] **Step 1: Add `qlib_data_dir` to `core/config.py` SystemConfig**

Add a new field to the `SystemConfig` dataclass:

```python
qlib_data_dir: str = "~/.qlib/qlib_data/cn_data_1d"
```

- [ ] **Step 2: Update `mining/config.py` MiningConfig to reference SystemConfig**

Add a `system` field to MiningConfig that references `SystemConfig`:

```python
from ..core.config import SystemConfig

@dataclass
class MiningConfig:
    system: SystemConfig = field(default_factory=SystemConfig)
    # qlib_data_dir now delegates to system.qlib_data_dir
    @property
    def qlib_data_dir(self) -> str:
        return self.system.qlib_data_dir
```

Remove the standalone `qlib_data_dir` field from `MiningConfig` and replace it with the property above.

**Backward compatibility note**: Using `@property` means `dataclasses.asdict()` will NOT include `qlib_data_dir`, and `MiningConfig(qlib_data_dir=...)` will raise `TypeError`. This is acceptable since:
- No existing code uses `asdict(config)` on MiningConfig
- All call sites constructing MiningConfig with `qlib_data_dir=` will be updated in Step 3
- If backward compat is needed later, use `__post_init__` instead

- [ ] **Step 3: Update call sites that construct MiningConfig**

In `mining/cli.py` line 37, change:
```python
config = MiningConfig(
    qlib_data_dir=args.qlib_dir,
```
to:
```python
from ..core.config import SystemConfig
system = SystemConfig(qlib_data_dir=args.qlib_dir)
config = MiningConfig(
    system=system,
```

Verified: No existing test fixtures construct `MiningConfig(qlib_data_dir=...)`:
- `tests/conftest.py:28` — uses default MiningConfig (no `qlib_data_dir`)
- `tests/mining/test_config.py` — no `qlib_data_dir`
- `tests/mining/test_evaluator.py` — uses `config` fixture
- `tests/mining/test_integration.py` — uses `config` fixture

No test fixture changes needed.

- [ ] **Step 4: Fix `SystemConfig.version` from `"3.0.0"` to `"4.1.0"`**

In `core/config.py`, line 91, change:
```python
version: str = "3.0.0"
```
to:
```python
version: str = "4.1.0"
```

- [ ] **Step 5: Remove dead config classes from `core/config.py`**

`PipelineConfig` and `FactorConfig` are specific to the archived `factors/` pipeline. Remove them and their references from `SystemConfig`:

Remove the `PipelineConfig` and `FactorConfig` dataclass definitions, and remove these fields from `SystemConfig`:
```python
pipeline: PipelineConfig = field(default_factory=PipelineConfig)
factor: FactorConfig = field(default_factory=FactorConfig)
```

- [ ] **Step 6: Run tests to verify**

Run: `python -m pytest tests/mining/ -v`
Expected: All tests PASS

- [ ] **Step 7: Commit**

```bash
git add core/config.py mining/config.py mining/cli.py
git commit -m "refactor: unify config — MiningConfig references SystemConfig, remove dead configs"
```

---

### Task 10: Add test directory stubs

**Files:**
- Create: `tests/data/__init__.py`
- Create: `tests/data/test_qlib_sync.py`
- Create: `tests/visualization/__init__.py`
- Create: `tests/visualization/test_imports.py`

- [ ] **Step 1: Move existing test and create data test directory**

```bash
mkdir -p tests/data
touch tests/data/__init__.py
```

Move the existing data sync test to its proper location:
```bash
git mv tests/mining/test_data_sync.py tests/data/test_qlib_sync.py
```

Update the import in `tests/data/test_qlib_sync.py` (already updated in Task 3 to `from data.qlib_sync import DataSynchronizer`).

- [ ] **Step 2: Create visualization test stub**

```bash
mkdir -p tests/visualization
touch tests/visualization/__init__.py
```

Create `tests/visualization/test_imports.py`:

```python
"""Smoke test for visualization module imports."""


def test_visualization_imports():
    from visualization.ic_analyzer import ICAnalyzer
    from visualization.group_returns import GroupReturnsAnalyzer
    from visualization.report import FactorReportGenerator
    assert ICAnalyzer is not None
    assert GroupReturnsAnalyzer is not None
    assert FactorReportGenerator is not None
```

- [ ] **Step 3: Run new tests**

Run: `python -m pytest tests/data/ tests/visualization/ -v`
Expected: All tests PASS

- [ ] **Step 4: Commit**

```bash
git add tests/data/ tests/visualization/
git commit -m "test: add data and visualization test directories"
```

---

### Task 11: Update skills

**Files:**
- Modify: `.claude/skills/factor-mine.md`
- Modify: `.claude/skills/factor-evaluate.md`

- [ ] **Step 1: Check if skills reference any moved paths**

The skills reference:
- `mining/evaluator.py` — NOT moved, still valid
- `mining/config.py` — NOT moved, still valid
- `mining/candidates/` — NOT moved, still valid
- `mining/library/` — NOT moved, still valid
- `mining/memory/` — NOT moved, still valid

No changes needed to skill content. The mining module internal paths are unchanged.

- [ ] **Step 2: Verify skills still reference correct paths**

Run: `grep -r "from mining" .claude/skills/`
Run: `grep -r "data_sync" .claude/skills/`

If `data_sync` appears, update the reference to `data.qlib_sync`. Otherwise no action needed.

- [ ] **Step 3: Commit (if changes made)**

```bash
git add .claude/skills/
git commit -m "refactor: update skill paths if needed"
```

---

### Task 12: Run full test suite and verify

**Files:**
- Test: `tests/mining/`

- [ ] **Step 1: Run all mining tests**

Run: `cd /Users/xinzhan/.openclaw/workspace/quant_factor_system && python -m pytest tests/mining/ -v`
Expected: All tests PASS

- [ ] **Step 2: Verify package import**

Run: `python -c "from quant_factor_system import __version__; print(__version__)"`
Expected: `4.1.0`

Run: `python -c "from quant_factor_system.mining import FactorMiningEvaluator, FactorLibrary; print('mining OK')"`
Expected: `mining OK` (may warn about Qlib if not installed)

Run: `python -c "from quant_factor_system.visualization import ICAnalyzer; print('viz OK')"`
Expected: `viz OK`

Run: `python -c "from quant_factor_system.data import TimescaleDB, DataSynchronizer; print('data OK')"`
Expected: `data OK`

- [ ] **Step 3: Verify no imports from archived modules**

Run: `grep -r "from.*backtest" --include="*.py" . | grep -v _archive | grep -v __pycache__ | grep -v .git`
Run: `grep -r "from.*factors" --include="*.py" . | grep -v _archive | grep -v __pycache__ | grep -v .git | grep -v visualization`

Expected: No matches (all references to old modules should be gone)

- [ ] **Step 4: Final commit if any fixes were needed**

```bash
git add -A
git commit -m "refactor: architecture reorganization complete"
```

---

## Summary of Changes

| Before | After | Action |
|--------|-------|--------|
| `mining/data_sync.py` | `data/qlib_sync.py` | Moved |
| `factors/visualization/` | `visualization/` | Extracted |
| `factors/automation/evaluator.py` | (deleted) | Duplicate removed |
| `factors/core/registry.py` | (deleted) | Duplicate removed |
| `factors/automation/factor_register.py` | (deleted) | Duplicate removed |
| `backtest/` | `_archive/backtest/` | Archived |
| `factors/` | `_archive/factors/` | Archived |
| `examples/` | `_archive/examples/` | Archived |
| 15 scripts | `_archive/scripts/` | Archived |
| `__init__.py` (93 lines) | `__init__.py` (~25 lines) | Simplified |
| `setup.py` (version 3.0.0) | `setup.py` (version 4.1.0) | Fixed |
| Dashboard uses factors/ | Dashboard uses mining/library | Updated |

| `core/config.py` | `core/config.py` (+ qlib_data_dir) | Config unified |
| `mining/config.py` | `mining/config.py` (refs SystemConfig) | Config unified |
| `tests/mining/test_data_sync.py` | `tests/data/test_qlib_sync.py` | Moved |
| (none) | `tests/visualization/test_imports.py` | Created |

## Not Changed
- `mining/` internal structure (except config.py references SystemConfig)
- `core/exceptions.py`, `core/logger.py`
- `data/storage/`, `data/clean/`, `data/utils/`
- `.claude/skills/` (mining paths unchanged)
- `tests/mining/` (except test_data_sync moved to tests/data/)
