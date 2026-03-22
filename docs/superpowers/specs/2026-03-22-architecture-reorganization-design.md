# Architecture Reorganization: Mining-Centric Design

**Date**: 2026-03-22
**Status**: Approved
**Goal**: Reorganize quant_factor_system around the automated factor mining pipeline, eliminating duplication and archiving unused modules.

## Context

The project (v4.1, 134 Python files) grew organically with multiple parallel systems:
- `factors/` — manual factor computation with CSV registry and custom evaluator
- `mining/` — automated factor mining with Qlib, YAML library, and multi-stage evaluator
- `backtest/` — backtesting engine (no longer in use)
- Two separate evaluation systems, three registration mechanisms

The user has confirmed:
- **Mining is the primary workflow** going forward
- **Qlib** remains the expression/data engine
- `data/`, `dashboard/`, and `factors/visualization/` are still in use
- `backtest/` is no longer used

## Target Structure

```
quant_factor_system/
├── core/                    # Foundation: config, logging, exceptions
│   ├── config.py            # System-wide configuration
│   ├── exceptions.py
│   └── logger.py
│
├── data/                    # Data layer: storage + sources + Qlib sync
│   ├── storage/             # TimescaleDB (unchanged)
│   ├── clean/               # Data validation (unchanged)
│   ├── ricequant_source.py  # RiceQuant data source (unchanged, no rename)
│   ├── qlib_sync.py         # Moved from mining/data_sync.py
│   ├── loaders.py           # Retained
│   ├── data_manager.py      # Retained
│   └── utils/               # Retained
│
├── mining/                  # Core: full factor mining lifecycle
│   ├── expression.py        # Expression validation + safe_wrap
│   ├── operators.py         # Custom Qlib operators (15 ops)
│   ├── evaluator.py         # Multi-stage evaluation (sole evaluator)
│   ├── library.py           # Factor library (YAML, sole registry)
│   ├── memory.py            # Experience memory
│   ├── config.py            # Mining-specific config (references core config)
│   ├── cli.py               # CLI entry point
│   └── __main__.py
│
├── visualization/           # Extracted from factors/visualization/
│   ├── ic_analyzer.py       # IC analysis charts
│   ├── tearsheet.py         # Factor tearsheets
│   ├── group_returns.py     # Quantile group returns
│   └── report.py            # Report generation
│
├── dashboard/               # Streamlit UI (retained, imports updated)
│   ├── Home.py
│   └── pages/
│
├── _archive/                # Archived unused code (git history as backup)
│   ├── backtest/
│   ├── factors/
│   └── scripts/
│
├── scripts/                 # Minimal operational scripts
│   ├── data.sh
│   ├── db.sh
│   └── stock_list_manager.py
│
└── tests/
    ├── mining/              # Existing tests
    ├── data/                # To be added
    └── visualization/       # To be added
```

## Data Flow

Single clear path through the system:

```
TimescaleDB (raw market data)
    ↓  data/qlib_sync.py
Qlib binary format (~/.qlib/qlib_data/)
    ↓  qlib.data.D.features()
mining/evaluator.py (4-stage pipeline)
    ↓  BatchResult (admitted/rejected/replacements)
mining/library.py (YAML factor library)
    ↓
visualization/ (IC charts, tearsheets)
    ↓
dashboard/ (web display)
```

## Module Responsibilities

### core/
- System-wide configuration (DB connection, Qlib paths)
- Logging setup
- Exception hierarchy
- **Does NOT**: contain business logic

### data/
- TimescaleDB read/write operations
- RiceQuant data source integration
- Qlib data synchronization (TimescaleDB → Qlib binary)
- Data loading utilities
- **Does NOT**: compute factors or evaluate them

### mining/
- Expression validation and safe wrapping
- Custom Qlib operator registration
- Multi-stage factor evaluation (Stage 1 → 1.5 → 2 → 2.5 → 3)
- Factor library management (YAML-based, sole source of truth)
- Experience memory for iterative improvement
- CLI interface
- **Does NOT**: store raw data, generate visualizations

### visualization/
- IC analysis charts
- Factor tearsheets and reports
- Accepts DataFrames as input (no module dependencies)
- **Does NOT**: load data or compute factors

### dashboard/
- Streamlit web pages
- Calls data/, mining/, visualization/ for content
- **Does NOT**: contain business logic

## Migration Steps

**Order matters**: Steps must execute in this sequence to avoid import breakage.

### Step 1: Rewrite `__init__.py` and `setup.py` (do FIRST to prevent import errors)
- Rewrite root `__init__.py` to export only: `data`, `mining`, `visualization`
- Retain `__version__ = "4.1.0"` in root `__init__.py`
- Remove all `backtest` and `factors` imports from root `__init__.py`
- Update `setup.py` packages list and fix version to `"4.1.0"` (currently `"3.0.0"`, inconsistent)

### Step 2: Move data_sync to data layer
- `mining/data_sync.py` → `data/qlib_sync.py`
- Update imports in: `mining/__init__.py`, `mining/cli.py`, `mining/evaluator.py`, `tests/mining/test_data_sync.py`
- `mining/__init__.py` currently re-exports `DataSynchronizer` from `.data_sync` — update to import from `data.qlib_sync` or remove the re-export
- Note: `data/ricequant_source.py` stays in place (no rename, to avoid unnecessary breakage)

### Step 3: Extract visualization
- Move reusable modules only: `ic_analyzer.py`, `tearsheet.py`, `group_returns.py`, `report.py`
- Exclude one-off scripts: `sentiment_overflow_tearsheet.py`, `analyze_ambiguous_amount_ratio.py` → archive
- Remove relative imports to `factors/` internals
- Ensure all functions accept pure DataFrame inputs

### Step 4: Update dashboard imports
Concrete changes required in dashboard files:
- `dashboard/pages/Factors.py`: change `from quant_factor_system.factors.visualization import ICAnalyzer` → `from quant_factor_system.visualization import ICAnalyzer`
- `dashboard/Home.py`: remove `from quant_factor_system.factors import register_all_builtins, list_factors` (replace with mining/library reads or remove unused UI)
- `dashboard/pages/Pipeline.py`: remove `from quant_factor_system.factors import Pipeline, list_factors, register_all_builtins` (Pipeline page needs redesign or removal since the old Pipeline is being archived)
- `dashboard/pages/StrategyConfig.py`: same — remove factors imports, redesign or stub
- `dashboard/components/page_template.py`: this file has a **deferred import** inside `render_factor_selector()` function body (not at module level) — the function must be rewritten to call `mining/library.py` instead
- Decision: dashboard pages that depended on `factors/core/pipeline.py` or `factors/core/registry.py` should either be redesigned to use `mining/library.py` or temporarily stubbed/removed

### Step 5: Delete duplicate evaluator and registry
- Delete `factors/automation/evaluator.py` (replaced by `mining/evaluator.py`)
- Delete `factors/core/registry.py` (replaced by `mining/library.py`)
- Delete `factors/automation/factor_register.py` (DB registration no longer needed)

### Step 6: Archive unused modules
- `backtest/` → `_archive/backtest/`
- `factors/basic/` → `_archive/factors/basic/`
- `factors/core/` → `_archive/factors/core/`
- `factors/processing/` → `_archive/factors/processing/`
- `factors/report/` → `_archive/factors/report/`
- `factors/automation/` (remaining: pdf_parser, code_generator, factor_extractor) → `_archive/factors/automation/`
- `examples/` → `_archive/examples/` (all example scripts import from archived modules)
- Most of `scripts/` → `_archive/scripts/`

### Step 7: Clean up scripts
- Keep: `data.sh`, `db.sh`, `stock_list_manager.py`
- Archive everything else (including `run_pdf_factor.py` which depends on archived `factors/automation`)

### Step 8: Unify configuration
- Add `qlib_data_dir` to `core/config.py` `SystemConfig`
- Update `mining/config.py` `MiningConfig` to reference `SystemConfig`
- Update all code that constructs `MiningConfig` directly, including:
  - `mining/cli.py` `cmd_evaluate()` — constructs `MiningConfig(qlib_data_dir=...)`
  - `mining/config.py` — default value `qlib_data_dir` moves to `SystemConfig`
  - Any test fixtures that construct `MiningConfig`

### Step 9: Update skills and tests
- Update `.claude/skills/` files if they reference moved paths
- Update `tests/mining/test_data_sync.py` import path (if not done in Step 2)
- Verify all existing tests pass

## What Does NOT Change
- `mining/` internal structure (already clean)
- `core/exceptions.py`, `core/logger.py`
- `data/ricequant_source.py` (kept in place, not renamed)
- `data/clean/` (data validation, kept in place)
- `.claude/skills/` (content unchanged, paths may update)
- `tests/mining/` (all existing tests, except test_data_sync.py import path)
- Qlib dependency and usage pattern

## Dashboard Pages That Need Redesign
The following dashboard pages depend on `factors/core/` which is being archived:
- `Pipeline.py` — uses `Pipeline`, `list_factors`, `register_all_builtins` from factors/core
- `StrategyConfig.py` — uses `register_all_builtins`, `list_factors`
- `Home.py` — uses `register_all_builtins`, `list_factors`
- `page_template.py` — uses `list_factors`, `register_all_builtins`

These pages should be redesigned to read from `mining/library.py` instead, or temporarily stubbed until redesign is complete.

## Configuration Unification

Current: two separate config files with no relationship.

Target: hierarchical configuration.

```python
# core/config.py
@dataclass
class SystemConfig:
    db_host: str
    db_port: int
    qlib_data_dir: str
    ...

# mining/config.py
@dataclass
class MiningConfig:
    system: SystemConfig          # References global config
    ic_threshold: float = 0.03
    correlation_threshold: float = 0.5
    ...
```

## Factor Registration Unification

Current: three parallel systems (CSV, YAML, TimescaleDB table).

Target: `mining/library.py` YAML files are the sole source of truth.

```
mining/library/
├── library.yaml          # Index + metadata
└── factors/
    ├── factor_001.yaml   # Individual factor details
    └── ...
```

Dashboard and CLI read directly from this library. No CSV registry, no DB factor_config table for mining factors.

## Risks and Mitigations

| Risk | Mitigation |
|------|-----------|
| Breaking dashboard imports | Update imports before archiving; test dashboard after |
| Losing useful code from factors/ | Archive to `_archive/`, git history preserves everything |
| visualization/ coupling to factors/ | Refactor to accept DataFrames only, no module imports |
| Skills referencing old paths | Update skill files after migration |
