# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run all tests
pytest

# Run a single test file / test case
pytest tests/research/compute/test_vectorized_ic.py -v
pytest tests/research/phases/test_phase2_execute.py -v

# Research CLI (all commands require PYTHONPATH=src)
PYTHONPATH=src python3 -m research mine --once --direction bootstrap
PYTHONPATH=src python3 -m research audit mt-budget
PYTHONPATH=src python3 -m research audit mt-budget --direction fundamental_price_divergence
PYTHONPATH=src python3 -m research state set current_batch null
PYTHONPATH=src python3 -m research capabilities

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

### System Constitution (R1-R8)

| Rule | Summary |
|---|---|
| **R1** Rule A/B | YAML = Python-consumed structured data; Markdown = LLM-consumed narrative |
| **R2** LLM 主驾 Python 护栏 | LLM decides direction/candidates/judgment/reports; Python does compute/validate/state/commit |
| **R3** Single data source | Each data lives at one canonical location; LLM gets one pre-packed input file per step |
| **R4** No recomputation | Phase 4 report consumes Phase 2 result.yaml directly, never re-runs IC/Barra |
| **R5** Full vectorization | No for-loop over rows/dates/symbols; use groupby/broadcasting/einsum/pinv |
| **R6** Code minimal | No backward compat, no adapter shims, no speculative abstractions |
| **R7** Autonomous + auditable | LLM runs autonomously; every decision leaves provenance in git |
| **R8** DSL first, Python escape hatch | Default = Qlib DSL; Python only when DSL can't express the idea |

### Source Layout (`src/`)

All source code lives under `src/` with bare imports. `package_dir={"": "src"}` in `setup.py` and `pythonpath = src` in `pytest.ini`.

Four modules:

- **`core/`** — Shared pure-function math: `factor_stats.py` (vectorized IC, quintile, monotonicity), `metrics.py` (Sharpe/Calmar/MDD), `constants.py`
- **`research/`** — Factor research pipeline. 5-phase loop: START → EXECUTE → JUDGE → ARCHIVE → CONSOLIDATION
- **`report/`** — Report analytics v2 (pure extractors consuming result.yaml, no recomputation) + chart rendering
- **`data/`** — Data layer: TimescaleDB storage, Qlib sync, RiceQuant API, loaders

### Research Module (5-Phase Architecture)

| Subpackage | Purpose |
|---|---|
| `cli/` | CLI entry point: `mine.py` (autonomous loop), `audit.py` (mt-budget), state management |
| `compute/` | Factor computation: 6 vectorized metric modules (`vectorized_{ic,quintile,stability,feasibility,redundancy,barra}`), cache (sha256-keyed parquet), preprocess (MAD winsorize + z-score matrix ops), python_runner (R8 escape hatch with AST whitelist) |
| `domain/` | Pure data contracts: frozen dataclasses for evidence, verdicts, sample policy |
| `checkpoints/` | Phase 3 judge infrastructure: `hard_gates.py` (CP01), `mt_budget.py` (§7.MT multiple testing budget), `generator.py` (pre-pack judge_packet.md), `audit.py` (6 structural checks including CP03 mt_bucket citation) |
| `phases/` | 5 phase orchestrators: `phase1_start.py` (DSL whitelist + dedup + manifest freeze), `phase2_execute.py` (vectorized compute → result.yaml), `phase3_judge.py` (hard gates → pre-pack → LLM → audit), `phase4_archive.py` (factor allocation + direction update + INDEX refresh + git commit), `phase5_consolidate.py` (periodic memory md rewrite) |
| `memory/` | Vault operations: `direction_updater.py` (surgical frontmatter update), `index_refresher.py` (auto-section regeneration) |
| `archive/` | Phase 4 helpers: `factor_writer.py` (monotonic F{id} allocation), `python_archiver.py` (copy admitted .py), `report_packer.py` (single-input packet for factor.md subagent), `commit.py` (git commit with hard-fail on hook error) |
| `storage/` | YAML I/O + paths + state: `yaml_io.py` (safe/unsafe load + atomic write), `paths.py` (StoragePaths for vault-first layout), `state.py` (State dataclass + phase DAG enforcement) |

### 5-Phase Loop

```
Phase 1 START+DESIGN → Phase 2 EXECUTE → Phase 3 JUDGE → Phase 4 ARCHIVE → (Phase 5 CONSOLIDATION if triggered)
     ↓                     ↓                  ↓                ↓                     ↓
manifest.yaml          result.yaml        judge.md        factor.yaml           rewritten md
(frozen candidates)    (all metrics)      (6 CP verdicts) (F{id} allocated)     (lessons/dirs/INDEX)
```

### Data Flow

```
RiceQuant API → TimescaleDB (5432, Docker) → Qlib binary (~/.qlib/) → Phase 2 compute → result.yaml
                     ↓                                                      ↓
               market_daily (11M rows)                           Phase 3 judge_packet.md
               factor_values (147M rows)                           → LLM writes judge.md
               index_constituents (2.7M rows)                      → Python audit
                                                                Phase 4 factor.yaml + git commit
```

### Storage Layout (`storage/`)

```
storage/
  state.yaml                            ← system state (current_batch, phase, round)
  config.yaml                           ← system config (sample_policy, thresholds, mt_budget, consolidation)
  vault/                                ← Obsidian vault root — 所有研究产物在此连通
    INDEX.md                            ← MOC: upper=LLM narrative, lower=Python auto-stats
    lessons.md                          ← system-level hard-won facts
    directions/{tag}.md                 ← per-direction hypothesis + threads + narrative log
    factors/F{id}.{yaml,md}             ← admitted factor metadata + deep report
    batches/batch_{NNN}/                ← per-batch immutable archive（vault 内，Obsidian 可见）
      manifest.yaml / result.yaml / judge.md
      _packets/ / signals/ / python_candidates/
    _meta/consolidation_log.md          ← append-only consolidation history
  cache/                                ← parquet caches（vault 外，Obsidian 不需要看）
    market_daily.parquet / barra_factors.parquet
    factor_values/{sha256_key}.parquet
  python_factors/F{id}_{name}.py        ← admitted Python factors
  _holdout_private/                     ← LLM forbidden (holdout review only)
  _legacy/                              ← archived old storage (logic_v1, governance_v1, etc.)
```

All paths managed by `StoragePaths` class in `src/research/storage/paths.py`.

### §7.MT Multiple Testing Budget

Phase 3 pre-pack scans `batches/batch_*/manifest.yaml` (judged-only) to count cumulative candidates + per-direction candidates + validation exposure. Formula constants live in `config.yaml.thresholds.mt_budget`. CP03 numeric_hint includes `mt_score / mt_bucket / search_adjusted_strength`. Audit enforces LLM cites `mt_bucket` in CP03 body. See `src/research/checkpoints/mt_budget.py`.

## Critical Technical Notes

- **Qlib package**: Install with `pip install pyqlib` (NOT `pip install qlib`)
- **Custom operator registration**: Use `Operators._ops[name] = cls` (NOT `Operators.register()`)
- **Multiprocessing**: Set `C.kernels = 1` — worker processes don't inherit custom `_ops` registry
- **`D.instruments('all')`** returns a dict, not a list — pass it to `D.features()` then extract instruments from the index
- **`factor_values` DB table** — has 147M+ rows in TimescaleDB (`quant_data` database). DB is a Docker container: `timescale/timescaledb:latest-pg14` on `localhost:5432`. Do NOT run Homebrew PostgreSQL simultaneously — it will shadow port 5432 and intercept connections.
- **Unavailable Qlib operators**: `Neg`, `SMA` — use alternatives like `Mul($x, -1)` for Neg. Note: `TsRank`, `TsMax`, `TsMin` are custom-registered and available.
- **`$vwap`** field is zero in current data — forbidden in precheck whitelist
- **`$amount`** has data (confirmed)
- **Factor metadata**: `vault/factors/F{id}.yaml` is the source of truth. DB `factor_meta` is a derived cache.
- **YAML safety**: Result files may contain pandas DataFrames — use `load_yaml_unsafe()` from `research.storage.yaml_io`. Config/state/manifest use `load_yaml()` (safe).
- **Qlib binary format**: File = `[start_index:f32][data:f32×N]`. `start_index` is the calendar index; data contains ONLY values from `start_index` onwards (no leading NaNs). Do NOT write full-length arrays with non-zero start_index.
- **`index_constituents` DB table** — daily index membership for `csi300`, `csi500`, `csi1000`
- **Barra OLS**: `vectorized_barra.py` uses `np.linalg.pinv + np.einsum` on a 3D tensor (date × symbol × 8 params) — 6× faster than legacy per-date lstsq loop

## Autonomous Mining Mode

当执行 `/factor-mine` 循环时，进入全自主模式：

- **不要停下来问用户确认**——所有决策自行判断并继续
- 方向选择：读 INDEX → 按优先级自动选取
- 候选验证失败：自动跳过该候选，尝试下一个
- batch 冻结：满足 freeze 条件直接冻结
- judge 裁决：严格按 6 checkpoint + §7.MT 预算执行 admit/reserve/reject
- report：admitted 因子自动启动后台 subagent 生成
- 一轮结束后，检查 consolidation 触发条件，有则自动执行 Phase 5
- **只在系统级错误时停下**：DB 连接失败、文件损坏、Python 异常无法恢复

## Environment

- **Python**: 3.8+ (conda env: `quantfactor`)
- **Database**: TimescaleDB on localhost:5432, configured via `.env` (copy from `.env.example`)
- **Qlib data**: `~/.qlib/qlib_data/cn_data_1d` (synced from TimescaleDB)
- **Test framework**: pytest with `--import-mode=importlib`
