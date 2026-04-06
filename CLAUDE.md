# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run all tests
pytest

# Run a single test file / test case
pytest tests/report/test_builder.py -v
pytest tests/research/execute/test_pipeline.py -v

# Research CLI (all commands require PYTHONPATH=src)
PYTHONPATH=src python3 -m research probe "Std($close, 20)"
PYTHONPATH=src python3 -m research probe "Std($close, 20)" --universe csi1000
PYTHONPATH=src python3 -m research execute storage/batches/batch_001/manifest.yaml
PYTHONPATH=src python3 -m research execute batch.yaml --skip-stage1
PYTHONPATH=src python3 -m research logic list
PYTHONPATH=src python3 -m research logic schedule
PYTHONPATH=src python3 -m research batch list
PYTHONPATH=src python3 -m research batch next-id
PYTHONPATH=src python3 -m research library
PYTHONPATH=src python3 -m research state set current_batch batch_042
PYTHONPATH=src python3 -m research state clear-batch
PYTHONPATH=src python3 -m research state sync-holdout
PYTHONPATH=src python3 -m research capabilities

# Report generation
PYTHONPATH=src python3 -m report.builder --factor-id 001 --vault

# Index constituent sync (RiceQuant API → DB → Qlib instruments file)
PYTHONPATH=src python3 scripts/sync_index_constituents.py csi1000
PYTHONPATH=src python3 scripts/sync_index_constituents.py --all

# Qlib binary resync (TimescaleDB → Qlib binary, ~1 min vectorized)
PYTHONPATH=src python3 scripts/resync_qlib.py

# Database management
./scripts/db.sh start|stop|shell

# Install (editable)
pip install -e .
```

Note: `pytest` does NOT need `PYTHONPATH=src` — `pytest.ini` sets `pythonpath = src` automatically.

## Architecture

### Source Layout (`src/`)

All source code lives under `src/` with bare imports (e.g., `from research.compute.factor_engine import FactorEngine`). The `package_dir={"": "src"}` in `setup.py` and `pythonpath = src` in `pytest.ini` enable this.

Four modules:

- **`core/`** — Shared utilities: `factor_stats.py` (pure stat functions used by both research and report), `metrics.py`, `constants.py`
- **`research/`** — Factor research pipeline (replaces old `mining/`). CLI entry via `__main__.py` → `cli/main.py`. 11 subpackages covering the full lifecycle: hypothesis → evaluation → judgment → governance. See [Research Module](#research-module) below.
- **`report/`** — Factor report generation. Pipeline: 6 analyzers (`analytics/`) → `CompositeScorer` (7-dim S-curve) → `ReportDataBuilder` → Obsidian Markdown + PNG charts
- **`data/`** — Data layer: `storage/timescale_storage.py` (DB ops), `qlib_sync.py` (DB → Qlib binary), `loaders.py` (factor/price data loading), `ricequant_source.py` (API)

### Research Module

The `research/` module is the core factor discovery and evaluation system, organized into 11 subpackages:

| Subpackage | Purpose |
|---|---|
| `cli/` | CLI entry point (7 subcommands: probe, execute, logic, batch, library, state, capabilities) |
| `compute/` | Factor computation engine: Qlib expression evaluation, custom operators, preprocessing, caching |
| `domain/` | Pure data contracts: frozen dataclasses for evidence, verdicts, configs, reason codes, sample policy |
| `execute/` | Evaluation pipeline: precheck → compute → gate → judge_packet. Orchestrator: `ResearchExecutePipeline` |
| `feasibility/` | Proxy portfolio analysis: liquidity coverage, concentration, stress tests, half-life |
| `governance/` | Access control + audit: `GuardedWriter` (level_1/level_2 writes), `WriteAuditLog`, cycle controller |
| `judge/` | 6-dimension structured judgment: mechanism alignment, statistical strength, stability, redundancy, feasibility, risk review |
| `logic/` | Hypothesis lifecycle: LogicCard (proposed→active→warm→productive→saturated→parked→dead), proposals, reviews, scheduler |
| `redundancy/` | Factor overlap analysis: pairwise correlation, family-level overlap, subspace ridge regression |
| `risk/` | Risk model review: Barra/style exposures, cap-neutral IC, residual IC, crowding detection |
| `stats/` | Statistical evidence: effect strength, split/regime stability, reliability (bootstrap, walk-forward), support windows, multiple testing |
| `storage/` | YAML persistence: `StoragePaths` (centralized path registry), stores for state, logic, registry, ledger, packets |

### Skill-Driven Workflow

The research pipeline is operated through 6 Claude Code skills:

1. **`/factor-mine`** — Dual-speed orchestrator: fast loop (working_theme → draft → quick_execute) + formal loop (logic_schedule → /idea → /execute → /judge → /report)
2. **`/factor-idea`** — Candidate generation: consume logic schedule, design routes, probe filter, freeze batch manifest
3. **`/factor-execute`** — Formal evaluation: run `ResearchExecutePipeline` on frozen batch → research_result + judge_packet
4. **`/factor-judge`** — Structured 6-dim judgment: read judge_packet → admit/reserve/reject/replace verdicts via guarded_writer
5. **`/factor-logic`** — Hypothesis management: list, schedule (7-dim priority), propose, review, lifecycle transitions
6. **`/factor-report`** — Obsidian markdown + PNG chart generation for admitted factors

### Data Flow

```
RiceQuant API → TimescaleDB (5432, Docker) → Qlib binary (~/.qlib/) → Research Pipeline → Factor Registry (YAML)
                     ↓                                                       ↓                    ↓
               market_daily (11M rows)                              6-dim evidence          Report Builder
               factor_values (147M rows)                            judge_packet            → Markdown + PNG
               ref_valuation / ref_shares                           → guarded_writer
               index_constituents (2.7M rows)                       → audit log
```

### Multi-Universe Support

Feature binary files (`features/{SYMBOL}/*.bin`) are shared across all universes (5431 stocks). Only `instruments/{universe}.txt` files differ. `--universe` flag on `probe`/`execute` commands flows through config → `D.instruments(universe)`.

**Cross-sectional operators** (`CsRank`, `CsZscore` in `operators.py`) always compute over the full market (`D.instruments("all")`), regardless of the mining universe.

### Storage Layout (`storage/`)

```
storage/
  state/          — research_state.yaml, pending_holdout_queue.yaml
  logic/          — Hypothesis lifecycle
    registry.yaml — All logic IDs + metadata
    cards/        — LogicCard YAML files (L001.yaml, ...)
    proposals/    — Proposal drafts
    reviews/      — Review outcomes
    snapshots/    — latest_schedule_snapshot.yaml
  registry/       — Factor registry (published factors)
    factors/      — index.yaml + per-factor detail YAML
    families/     — family_registry.yaml
  governance/     — research_config.yaml, ledger.yaml, research_lessons.md
  batches/        — Per-batch lifecycle: batch_XXX/{manifest, research_result, judge_packet, ...}
  evidence/       — Derivation layer (deletable, rebuildable)
    vault/        — Obsidian vault: reports + PNG charts
  runtime/        — Ephemeral cache (gitignored)
    cache/        — Factor value + risk exposure caches (.parquet)
```

All paths managed by `StoragePaths` class in `src/research/storage/paths.py`.
Operator/field whitelists: single source of truth in `src/research/execute/precheck.py`. Query via `PYTHONPATH=src python3 -m research capabilities`.

### Research Pipeline Stages

1. **Precheck** — DSL syntax, operator/field whitelist, forbidden pattern validation
2. **Probe** — Lightweight IC-only check on train period
3. **Execute** — Full pipeline: compute → preprocess → 6-dimension evidence (effect strength, stability, reliability, support windows, multiple testing) → redundancy → risk review → feasibility → execution gate → judge_packet
4. **Judge** — 6-dim structured verdict: mechanism alignment, statistical strength, stability, redundancy, feasibility, risk review → admit/reserve/reject/replace
5. **Governance** — Writes via `GuardedWriter` (level_1 immediate / level_2 requires repeated evidence), audit logging

### Report Analyzers

`ICAnalyzer`, `ProfitAnalyzer`, `ConditionalAnalyzer`, `DecayAnalyzer`, `RiskAnalyzer`, `UniquenessAnalyzer` — each returns a section dict. `CompositeScorer` grades S/A/B/C/D across 7 dimensions.

## Critical Technical Notes

- **Qlib package**: Install with `pip install pyqlib` (NOT `pip install qlib`)
- **Custom operator registration**: Use `Operators._ops[name] = cls` (NOT `Operators.register()`)
- **Multiprocessing**: Set `C.kernels = 1` — worker processes don't inherit custom `_ops` registry
- **`D.instruments('all')`** returns a dict, not a list — pass it to `D.features()` then extract instruments from the index
- **`factor_values` DB table** — has 147M+ rows in TimescaleDB (`quant_data` database). DB is a Docker container: `timescale/timescaledb:latest-pg14` on `localhost:5432`. Do NOT run Homebrew PostgreSQL simultaneously — it will shadow port 5432 and intercept connections.
- **Unavailable Qlib operators**: `Neg`, `SMA` — use alternatives like `Mul($x, -1)` for Neg. Note: `TsRank`, `TsMax`, `TsMin` are custom-registered and available.
- **`$vwap`** field is zero in current data — forbidden in precheck
- **`$amount`** has data (confirmed)
- **Registry detail YAML is the metadata truth source** for factor records. DB `factor_meta` is a derived cache. Use `research.storage.registry_store` for factor metadata, not `data/loaders.py`.
- **YAML safety**: Result files may contain pandas DataFrames — use `yaml.unsafe_load` when reading them, but always `yaml.safe_load` for config/candidate files
- **Qlib binary format**: File = `[start_index:f32][data:f32×N]`. `start_index` is the calendar index of the first data point; data contains ONLY values from `start_index` onwards (no leading NaNs). `resync_qlib.py` uses vectorized pivot_table writes (~1 min for 5431 stocks × 17 fields). Do NOT write full-length arrays with non-zero start_index — Qlib will read wrong offsets.
- **`index_constituents` DB table** — stores daily index membership. Available indices: `csi300`, `csi500`, `csi1000`

## Environment

- **Python**: 3.8+ (conda env: `quantfactor`)
- **Database**: TimescaleDB on localhost:5432, configured via `.env` (copy from `.env.example`)
- **Qlib data**: `~/.qlib/qlib_data/cn_data_1d` (synced from TimescaleDB)
- **Test framework**: pytest with `--import-mode=importlib` (79 test files across all modules)
