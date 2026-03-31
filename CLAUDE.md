# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run all tests
pytest

# Run a single test file / test case
pytest tests/report/test_builder.py -v
pytest tests/mining/test_evaluator.py::TestEvaluator::test_stage1 -v

# Mining CLI (all commands require PYTHONPATH=src)
PYTHONPATH=src python3 -m mining sync           # Sync TimescaleDB → Qlib binary
PYTHONPATH=src python3 -m mining evaluate "Rank($close)"
PYTHONPATH=src python3 -m mining batch storage/candidates/batch_XXX.yaml --admit
PYTHONPATH=src python3 -m mining probe "Std($close, 20)"
PYTHONPATH=src python3 -m mining library
PYTHONPATH=src python3 -m mining memory

# Report generation
PYTHONPATH=src python3 -m report.builder --factor-id 001 --vault

# Database management
./scripts/db.sh start|stop|shell

# Install (editable)
pip install -e .
```

Note: `pytest` does NOT need `PYTHONPATH=src` — `pytest.ini` sets `pythonpath = src` automatically.

## Architecture

### Source Layout (`src/`)

All source code lives under `src/` with bare imports (e.g., `from mining.config import MiningConfig`). The `package_dir={"": "src"}` in `setup.py` and `pythonpath = src` in `pytest.ini` enable this.

Five modules:

- **`core/`** — Shared utilities: `factor_stats.py` (pure stat functions used by both mining and report), `metrics.py`, `constants.py`
- **`mining/`** — Factor mining pipeline (the "Ralph Loop"). CLI entry via `__main__.py` → `cli.py`. Key classes: `FactorMiningEvaluator` (3-stage IC filtering), `FactorLibrary` (YAML persistence), `ExperienceMemory` (direction-based memory)
- **`report/`** — Factor report generation. Pipeline: 6 analyzers (`analytics/`) → `CompositeScorer` (7-dim S-curve) → `ReportDataBuilder` (thin orchestrator) → Obsidian Markdown + 18 PNG charts
- **`data/`** — Data layer. `storage/timescale_db.py` (DB ops), `qlib_sync.py` (DB → Qlib binary), `loaders.py` (factor/price data loading)
- **`dashboard/`** — Streamlit multi-page app (legacy)

### Data Flow

```
RiceQuant API → TimescaleDB (5432, Docker) → Qlib binary (~/.qlib/) → Mining Evaluator → Factor Library (YAML)
                     ↓                                                         ↑ ↓               ↓
               market_daily (11M rows)                            Stage 2 reads  Stage 3    Report Builder
               factor_values (147M rows)  ─────────────────────► library corr              → Markdown + PNG
               ref_valuation / ref_shares                          from DB
               factor_meta (28 rows)
```

### Storage Layout (`storage/`)

- `storage/library/` — Factor library: `library.yaml` index + `factors/factor_*.yaml` per factor
- `storage/memory/` — Mining memory: `directions.yaml` index + `directions/*.md` per direction
- `storage/candidates/` — Batch YAML files and evaluation results

### Mining Pipeline Stages

1. **Probe** — Lightweight IC-only check on full universe, 1 year
2. **Stage 1** — Fast IC screening on subset (50 stocks)
3. **Stage 2** — Full-universe IC, Sharpe, IC IR
4. **Stage 3** — Out-of-sample IC, quintile returns, long-short return, monotonicity
5. **Judge** — LLM-based admit/reject, direction memory updates

### Report Analyzers

`ICAnalyzer`, `ProfitAnalyzer`, `ConditionalAnalyzer`, `DecayAnalyzer`, `UniquenessAnalyzer` — each returns a section dict. `CompositeScorer` grades S/A/B/C/D across 7 dimensions.

## Critical Technical Notes

- **Qlib package**: Install with `pip install pyqlib` (NOT `pip install qlib`)
- **Custom operator registration**: Use `Operators._ops[name] = cls` (NOT `Operators.register()`)
- **Multiprocessing**: Set `C.kernels = 1` — worker processes don't inherit custom `_ops` registry
- **`D.instruments('all')`** returns a dict, not a list — pass it to `D.features()` then extract instruments from the index
- **`factor_values` DB table** — has 147M+ rows in TimescaleDB (`quant_data` database). Stage 2 loads library factor values from DB via a single batched query. DB is a Docker container: `timescale/timescaledb:latest-pg14` on `localhost:5432`. Do NOT run Homebrew PostgreSQL simultaneously — it will shadow port 5432 and intercept connections.
- **`evaluate_batch()`** returns `BatchResult` but does NOT persist to library — must call `lib.admit()` separately
- **Unavailable Qlib operators**: `Neg`, `TsRank`, `TsMax`, `TsMin`, `SMA` — use alternatives like `Mul($x, -1)` for Neg
- **`$vwap`** field is zero in current data — avoid using it in expressions
- **`$amount`** has data (confirmed)
- **YAML safety**: Result files may contain pandas DataFrames — use `yaml.unsafe_load` when reading them, but always `yaml.safe_load` for config/candidate files

## Environment

- **Python**: 3.8+ (conda env: `quantfactor`)
- **Database**: TimescaleDB on localhost:5432, configured via `.env` (copy from `.env.example`)
- **Qlib data**: `~/.qlib/qlib_data/cn_data_1d` (synced from TimescaleDB)
- **Test framework**: pytest with `--import-mode=importlib`
