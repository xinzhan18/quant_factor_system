# CLAUDE.md

Guidance for Claude Code working with this repo.

## Commands

```bash
# Tests (pytest.ini sets pythonpath=src)
pytest
pytest tests/research/compute/test_vectorized_ic.py -v

# Research CLI (all commands need PYTHONPATH=src)
PYTHONPATH=src python3 -m research mine --once --direction bootstrap
PYTHONPATH=src python3 -m research audit mt-budget

# Data sync
PYTHONPATH=src python3 scripts/sync_index_constituents.py --all
PYTHONPATH=src python3 scripts/resync_qlib.py   # TimescaleDB → Qlib binary

# DB / install
./scripts/db.sh start|stop|shell
pip install -e .
```

## Architecture

### System Constitution (R1-R8)

| Rule | Summary |
|---|---|
| **R1** Rule A/B | YAML = Python-consumed; Markdown = LLM-consumed |
| **R2** LLM 主驾 | LLM decides direction/candidates/judgment/reports; Python does compute/validate/state/commit |
| **R3** Single data source | Each data lives at one canonical location; one pre-packed input per LLM step |
| **R4** No recomputation | Phase 4 consumes Phase 2 result.yaml; never re-runs IC/Barra |
| **R5** Full vectorization | No row/date/symbol for-loops; use groupby/broadcasting/einsum/pinv |
| **R6** Code minimal | No backward compat, no adapter shims, no speculative abstractions |
| **R7** Autonomous + auditable | LLM runs autonomously; every decision leaves git provenance |
| **R8** DSL first | Default = Qlib DSL; Python escape hatch (AST-whitelisted) only when DSL can't express |

### Source Layout (`src/`)

`package_dir={"": "src"}` with bare imports. Four modules:

- **`core/`** — pure-function math (`factor_stats`, `metrics`, `constants`)
- **`research/`** — 5-phase factor mining pipeline (see below)
- **`report/`** — report analytics v2 + chart rendering (consumes result.yaml, no recomputation)
- **`data/`** — TimescaleDB storage, Qlib sync, RiceQuant API, loaders

### Research Module

5-phase loop: `START → EXECUTE → JUDGE → ARCHIVE → (CONSOLIDATION)`

| Subpackage | Role |
|---|---|
| `cli/` | `mine` loop, `audit mt-budget`, state management |
| `compute/` | 6 vectorized metric modules, sha256 parquet cache, MAD+zscore preprocess, python_runner (R8) |
| `domain/` | frozen dataclasses for evidence/verdicts/sample policy |
| `checkpoints/` | `hard_gates` (CP01), `mt_budget` (§7.MT), `generator` (pre-pack), `audit` (6 structural checks) |
| `phases/` | phase1_start..phase5_consolidate |
| `memory/` | vault ops: `direction_updater`, `index_refresher` |
| `archive/` | `factor_writer` (F{id} alloc), `python_archiver`, `report_packer`, `commit` |
| `storage/` | `yaml_io` (safe/unsafe), `paths` (StoragePaths), `state` (phase DAG) |

### Data Flow

```
RiceQuant → TimescaleDB (Docker, :5432) → Qlib binary (~/.qlib/) → Phase 2 compute
                                                                   ↓
    manifest.yaml → result.yaml → judge_packet.md → judge.md (LLM) → audit → factor.yaml + git commit
    (Phase 1)       (Phase 2)      (Phase 3 prep)   (Phase 3)                 (Phase 4)
```

DB tables: `market_daily` (11M), `factor_values` (147M, derived cache), `index_constituents` (2.7M).

### Storage Layout

```
storage/
  state.yaml / config.yaml              ← system state + thresholds/mt_budget/consolidation
  vault/                                ← Obsidian root (everything LLM-visible)
    INDEX.md                            ← MOC: upper=LLM narrative, lower=Python auto-stats
    lessons.md                          ← system-level hard-won facts
    directions/{tag}.md                 ← per-direction hypothesis + threads
    factors/F{id}.{yaml,md}             ← admitted factor metadata + deep report
    batches/batch_{NNN}/                ← immutable archive (manifest/result/judge + _packets/signals)
  cache/                                ← parquet caches (out of vault)
  python_factors/F{id}_{name}.py        ← admitted Python factors
  _holdout_private/ _legacy/            ← LLM forbidden / archived
```

Paths managed by `StoragePaths` in `src/research/storage/paths.py`.

### §7.MT Multiple Testing Budget

Phase 3 pre-pack scans `batches/batch_*/manifest.yaml` (judged-only) for cumulative + per-direction counts. Constants in `config.yaml.thresholds.mt_budget`. CP03 must cite `mt_bucket`; audit enforces. See `src/research/checkpoints/mt_budget.py`.

## Critical Technical Notes

- **Qlib package**: `pip install pyqlib` (NOT `qlib`)
- **Custom operator registration**: `Operators._ops[name] = cls` (NOT `register()`)
- **Multiprocessing**: `C.kernels = 1` — workers don't inherit `_ops`
- **`D.instruments('all')`** returns dict, not list
- **DB**: TimescaleDB in Docker on `:5432`. Do NOT run Homebrew PostgreSQL simultaneously — it shadows the port.
- **Unavailable Qlib ops**: `Neg`, `SMA` (use `Mul($x, -1)`). `TsRank/TsMax/TsMin` are custom-registered.
- **`$vwap`** is zero in current data — forbidden in precheck whitelist. **`$amount`** has data.
- **Factor metadata**: `vault/factors/F{id}.yaml` is truth; DB `factor_meta` is derived cache.
- **YAML safety**: result files may contain DataFrames → use `load_yaml_unsafe()`. Config/state/manifest → `load_yaml()`.
- **Qlib binary format**: `[start_index:f32][data:f32×N]` — data starts at `start_index`, no leading NaNs.
- **Barra OLS**: `vectorized_barra.py` uses `pinv + einsum` on 3D tensor — 6× faster than per-date lstsq.

## Autonomous Mining Mode

`/factor-mine` 循环进入全自主模式：不停下问确认，候选失败自动跳下一个，冻结/admit/reserve/reject 按 6 CP + §7.MT 自行裁决，admitted 自动启动 report subagent，一轮结束检查 consolidation 触发。**只在系统级错误时停下**（DB 断、文件损坏、Python 崩溃）。

## Environment

- Python 3.8+ (conda env `quantfactor`)
- TimescaleDB `:5432`, `.env` from `.env.example`
- Qlib data: `~/.qlib/qlib_data/cn_data_1d`
- pytest with `--import-mode=importlib`
