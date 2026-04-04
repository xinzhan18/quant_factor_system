# Mining Module Restructure — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restructure `src/mining/` from a flat 18-file module into a well-bounded sub-package architecture with clear separation of CLI, application services, domain rules, evaluation, registry, memory, and logic.

**Architecture:** Seven phases executed incrementally. Each phase produces a working, test-passing codebase. Backward-compatible re-exports in old locations prevent breaking external consumers (`src/report/builder.py`, `src/dashboard/`, `tests/`). Compat shims removed in the final phase.

**Tech Stack:** Python 3.8+, pytest, YAML, Qlib

---

## File Structure — Target State

```
src/mining/
  __init__.py                    # Slim public API (~15 exports via sub-packages)
  __main__.py                    # Unchanged

  cli/
    __init__.py                  # expose main()
    main.py                      # argparse + dispatch (thin)
    commands/
      __init__.py
      sync.py                    # cmd_sync
      evaluate.py                # cmd_evaluate
      batch.py                   # cmd_batch (delegates to batch_service)
      probe.py                   # cmd_probe (delegates to qlib_runtime)
      library.py                 # cmd_library
      memory.py                  # cmd_memory
      logic.py                   # cmd_logic
      forbidden.py               # cmd_forbidden + _forbidden_suggest
      retire.py                  # cmd_retire
      audit.py                   # cmd_audit

  application/
    __init__.py
    batch_service.py             # Batch orchestration (read YAML, eval, save result/cache/history)
    context_service.py           # compose_search_context (moved from memory.py)
    qlib_runtime.py              # Qlib init, universe resolution (shared by batch/probe)

  domain/
    __init__.py
    schema.py                    # FactorRecord, normalize_metrics (moved from mining/schema.py)
    results.py                   # BatchResult (moved from evaluator.py)
    similarity.py                # compute_structural_similarity, check_lookahead_bias
    policies.py                  # _clean_factor_dict, _is_python_candidate, _candidate_cache_key

  evaluation/
    __init__.py
    evaluator.py                 # FactorMiningEvaluator (orchestrator only, ~400 lines)
    gates.py                     # _apply_hard_gates
    sandbox_runner.py            # _compute_factor_python dispatch
    metrics.py                   # Re-export of mining/metrics.py (FactorReportCard, compute_report_card)

  registry/
    __init__.py
    library.py                   # FactorLibrary (facade API)
    publisher.py                 # FactorPublisher (moved from mining/publisher.py)
    history.py                   # Archive logic (extracted from library.replace)
    values_cache.py              # _load_values_cache (extracted from library.py)

  memory/
    __init__.py
    store.py                     # ExperienceMemory (pure YAML store, no compose_search_context)

  logic/
    __init__.py
    library.py                   # MarketLogicLibrary (moved from mining/logic_library.py)
    scheduler.py                 # Scheduler (moved from mining/scheduler.py)

  # Unchanged (stay at mining/ root)
  config.py
  operators.py
  ops_adapter.py
  expression.py
  preprocessing.py
  sandbox.py
  evolution.py
```

### Files NOT moved (stable, clear boundaries already)
- `config.py` (221 lines) — stable anchor, imported everywhere
- `operators.py` (617 lines) — large but self-contained
- `ops_adapter.py` (293 lines) — self-contained
- `expression.py` (222 lines) — self-contained
- `preprocessing.py` (369 lines) — self-contained
- `sandbox.py` (230 lines) — self-contained
- `evolution.py` (236 lines) — self-contained, only imports config
- `metrics.py` (412 lines) — self-contained, only imports config/core

### External consumers (must not break)
- `src/report/builder.py`: `from mining.config import MiningConfig`, `from mining.operators import register_custom_operators`
- `src/dashboard/Home.py`: `from mining import __version__, FactorLibrary, MiningConfig`
- `src/dashboard/pages/StrategyConfig.py`: `from mining import FactorLibrary, MiningConfig`
- `src/dashboard/components/page_template.py`: `from mining import FactorLibrary, MiningConfig`
- `scripts/baseline_eval.py`: `from mining.evaluator import FactorMiningEvaluator, BatchResult`
- `tests/conftest.py`: `from mining.config import MiningConfig`
- 25 test files in `tests/mining/` — various direct imports

### Critical `patch()` targets in tests (must update when modules move)
- `tests/mining/test_cli.py`: 5x `patch("mining.cli.MiningConfig", ...)`
- `tests/mining/test_library.py`: 3x `patch("mining.publisher.FactorPublisher")`
- `tests/mining/test_publisher.py`: 5x `patch("mining.publisher.execute_values")`
- `tests/mining/test_evaluator_preprocessing.py`: 11x `patch("mining.evaluator.*")` — stays at root, no change needed
- `tests/mining/test_evaluator.py`: imports `_clean_factor_dict`, `_is_python_candidate`, `_candidate_cache_key`, `compute_structural_similarity`, `check_lookahead_bias` from `mining.evaluator` — need re-exports

---

## Phase 1: CLI Split (Risk: LOW, Value: HIGH)

Split `cli.py` (505 lines) into `cli/main.py` + `cli/commands/*.py`. No behavior change.

### Task 1.1: Create CLI package skeleton

**Files:**
- Create: `src/mining/cli/__init__.py`
- Create: `src/mining/cli/main.py`
- Create: `src/mining/cli/commands/__init__.py`

- [ ] **Step 1: Create `src/mining/cli/__init__.py`**

```python
"""CLI package for factor mining."""
from .main import main

__all__ = ["main"]
```

- [ ] **Step 2: Create `src/mining/cli/commands/__init__.py`**

```python
"""CLI command implementations."""
```

- [ ] **Step 3: Create `src/mining/cli/main.py` with argparse + dispatch**

Move only the `main()` function (lines 410-505 of old `cli.py`) plus imports needed for argparse setup. Each command handler is imported from `commands/` submodule.

```python
"""CLI entry point — argparse setup and command dispatch."""

from __future__ import annotations

import argparse
import logging
import sys


def main():
    parser = argparse.ArgumentParser(description="FactorMiner CLI")
    sub = parser.add_subparsers(dest="command")

    # sync
    p_sync = sub.add_parser("sync", help="同步数据到 Qlib 格式")
    p_sync.add_argument("--qlib-dir", default="~/.qlib/qlib_data/cn_data_1d")
    p_sync.add_argument("--start", default="2015-01-01")
    p_sync.add_argument("--end", default=None)

    # evaluate
    p_eval = sub.add_parser("evaluate", help="评估单个因子表达式")
    p_eval.add_argument("expression", help="Qlib 表达式, 如 Rank($close)")
    p_eval.add_argument("--qlib-dir", default="~/.qlib/qlib_data/cn_data_1d")
    p_eval.add_argument("--train-start", default="2015-01-01")
    p_eval.add_argument("--train-end", default="2023-12-31")
    p_eval.add_argument("--test-start", default="2024-01-01")
    p_eval.add_argument("--test-end", default="2024-12-31")

    # batch
    p_batch = sub.add_parser("batch", help="评估一个批次的候选因子")
    p_batch.add_argument("batch_file", help="批次 YAML 文件路径")
    p_batch.add_argument("--qlib-dir", default="~/.qlib/qlib_data/cn_data_1d")
    p_batch.add_argument("--train-start", default="2015-01-01")
    p_batch.add_argument("--train-end", default="2023-12-31")
    p_batch.add_argument("--test-start", default="2024-01-01")
    p_batch.add_argument("--test-end", default="2024-12-31")
    p_batch.add_argument("--screening-size", type=int, default=50)
    p_batch.add_argument("--skip-stage1", action="store_true",
                         help="跳过 Stage 1 快筛（候选已通过 Probe 验证时使用）")

    # library
    p_lib = sub.add_parser("library", help="查看因子库状态")
    p_lib.add_argument("--library-dir", default="storage/registry")

    # probe
    p_probe = sub.add_parser("probe", help="Probe a single expression (lightweight IC only)")
    p_probe.add_argument("expression", help="Qlib expression")
    p_probe.add_argument("--qlib-dir", default="~/.qlib/qlib_data/cn_data_1d")
    p_probe.add_argument("--start", default="2022-01-01")
    p_probe.add_argument("--end", default="2023-12-31")

    # memory
    p_mem = sub.add_parser("memory", help="查看挖掘记忆上下文")
    p_mem.add_argument("--memory-dir", default="storage/mining/memory")

    # logic
    p_logic = sub.add_parser("logic", help="Manage and inspect market logics")
    p_logic.add_argument("logic_action", choices=["list", "coverage", "schedule", "create"],
                         help="Action to perform: list, coverage, schedule, or create (stdin YAML)")
    p_logic.add_argument("--status", default=None,
                         help="Filter by status (active, saturated, dead) — used with 'list'")

    # forbidden
    p_forbidden = sub.add_parser("forbidden", help="Manage forbidden expression patterns")
    p_forbidden.add_argument("forbidden_action", choices=["suggest", "apply", "list"],
                             help="suggest: scan results; apply: write to forbidden.yaml; list: current")

    # retire
    p_retire = sub.add_parser("retire", help="Retire a factor from the library")
    p_retire.add_argument("factor_id", help="Factor ID (e.g., 013)")
    p_retire.add_argument("--library-dir", default="storage/registry")

    # audit
    p_audit = sub.add_parser("audit", help="Audit direction states (read-only report)")

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(name)s - %(message)s')

    # Lazy imports — each command module imported only when invoked
    if args.command == "sync":
        from .commands.sync import cmd_sync
        cmd_sync(args)
    elif args.command == "evaluate":
        from .commands.evaluate import cmd_evaluate
        cmd_evaluate(args)
    elif args.command == "batch":
        from .commands.batch import cmd_batch
        cmd_batch(args)
    elif args.command == "library":
        from .commands.library import cmd_library
        cmd_library(args)
    elif args.command == "memory":
        from .commands.memory import cmd_memory
        cmd_memory(args)
    elif args.command == "probe":
        from .commands.probe import cmd_probe
        cmd_probe(args)
    elif args.command == "logic":
        from .commands.logic import cmd_logic
        cmd_logic(args)
    elif args.command == "forbidden":
        from .commands.forbidden import cmd_forbidden
        cmd_forbidden(args)
    elif args.command == "retire":
        from .commands.retire import cmd_retire
        cmd_retire(args)
    elif args.command == "audit":
        from .commands.audit import cmd_audit
        cmd_audit(args)
    else:
        parser.print_help()
```

- [ ] **Step 4: Run tests to confirm nothing breaks yet**

```bash
pytest tests/mining/test_cli.py -v
```

Expected: PASS (old cli.py still exists, tests still import from `mining.cli`)

- [ ] **Step 5: Commit skeleton**

```bash
git add src/mining/cli/
git commit -m "refactor(mining): add CLI package skeleton with main.py dispatch"
```

### Task 1.2: Extract command modules

**Files:**
- Create: `src/mining/cli/commands/sync.py`
- Create: `src/mining/cli/commands/evaluate.py`
- Create: `src/mining/cli/commands/batch.py`
- Create: `src/mining/cli/commands/probe.py`
- Create: `src/mining/cli/commands/library.py`
- Create: `src/mining/cli/commands/memory.py`
- Create: `src/mining/cli/commands/logic.py`
- Create: `src/mining/cli/commands/forbidden.py`
- Create: `src/mining/cli/commands/retire.py`
- Create: `src/mining/cli/commands/audit.py`

- [ ] **Step 1: Create each command file**

Each command file contains exactly one `cmd_*` function moved from the old `cli.py`, with its own imports. Example for `sync.py`:

```python
"""sync command — Sync TimescaleDB data to Qlib format."""
from __future__ import annotations

import sys


def cmd_sync(args):
    """Sync TimescaleDB data to Qlib format."""
    try:
        from data.storage import TimescaleDB
    except ImportError:
        print("Error: data.storage module not found.")
        sys.exit(1)
    from data.qlib_sync import DataSynchronizer
    db = TimescaleDB()
    syncer = DataSynchronizer(db=db, qlib_dir=args.qlib_dir)
    syncer.sync_daily(start=args.start, end=args.end)
    print(f"Sync complete -> {args.qlib_dir}")
```

For `batch.py` — move `cmd_batch()` (lines 73-201 of old cli.py) verbatim, with its imports.
For `forbidden.py` — move `cmd_forbidden()` AND `_forbidden_suggest()` together.
For each other command — straightforward single-function extraction.

- [ ] **Step 2: Run all CLI tests**

```bash
pytest tests/mining/test_cli.py -v
```

Expected: PASS — old `cli.py` still exists, tests import from `mining.cli`

- [ ] **Step 3: Commit command modules**

```bash
git add src/mining/cli/commands/
git commit -m "refactor(mining): extract 10 CLI commands into cli/commands/"
```

### Task 1.3: Replace old cli.py with cli/ package

**Files:**
- Delete: `src/mining/cli.py`
- Modify: `src/mining/__main__.py`
- Modify: `tests/mining/test_cli.py`

`cli.py` and `cli/` cannot coexist as Python module and package. Delete the file; the package takes over.

- [ ] **Step 1: Delete old `src/mining/cli.py`**

- [ ] **Step 2: Keep `src/mining/__main__.py` using relative import (unchanged)**

The existing code already works:
```python
from .cli import main
main()
```
This resolves to `cli/__init__.py` which re-exports `main`. Do NOT switch to absolute import — relative import is more robust when PYTHONPATH varies.

- [ ] **Step 3: Update test imports in `tests/mining/test_cli.py`**

Change line 9:
```python
from mining.cli import cmd_forbidden, cmd_audit, cmd_logic
```
To:
```python
from mining.cli.commands.forbidden import cmd_forbidden
from mining.cli.commands.audit import cmd_audit
from mining.cli.commands.logic import cmd_logic
```

- [ ] **Step 4: Update `patch()` targets in `tests/mining/test_cli.py`**

**CRITICAL:** The 5 `patch("mining.cli.MiningConfig", ...)` calls must be updated to match the module where `MiningConfig` is imported. After the split, each command function looks up `MiningConfig` in its own module namespace.

Update:
- Lines 23, 31: `patch("mining.cli.MiningConfig", ...)` → `patch("mining.cli.commands.forbidden.MiningConfig", ...)`
- Line 41: `patch("mining.cli.MiningConfig", ...)` → `patch("mining.cli.commands.audit.MiningConfig", ...)`
- Lines 51, 63: `patch("mining.cli.MiningConfig", ...)` → `patch("mining.cli.commands.logic.MiningConfig", ...)`

Each patch target must match the module that the command function is defined in — otherwise the patch does nothing silently.

- [ ] **Step 5: Run full test suite**

```bash
pytest tests/mining/ -v
```

Expected: ALL PASS

- [ ] **Step 6: Commit**

```bash
git add -A src/mining/cli.py src/mining/cli/ src/mining/__main__.py tests/mining/test_cli.py
git commit -m "refactor(mining): replace flat cli.py with cli/ package"
```

---

## Phase 2: Application Services (Risk: LOW, Value: HIGH)

Extract batch orchestration and Qlib initialization into `application/`.

### Task 2.1: Create `application/qlib_runtime.py`

**Files:**
- Create: `src/mining/application/__init__.py`
- Create: `src/mining/application/qlib_runtime.py`

- [ ] **Step 1: Create `application/__init__.py`**

```python
"""Application services — orchestration layer."""
```

- [ ] **Step 2: Create `application/qlib_runtime.py`**

Extract the repeated Qlib init + universe resolution from `cmd_batch` and `cmd_probe`:

```python
"""Qlib initialization and universe resolution."""
from __future__ import annotations

import logging
from typing import List

logger = logging.getLogger(__name__)


def init_qlib(qlib_dir: str = "~/.qlib/qlib_data/cn_data_1d") -> None:
    """Initialize Qlib with provider URI. Safe to call multiple times."""
    import qlib
    from qlib.config import REG_CN, C
    qlib.init(provider_uri=qlib_dir, region=REG_CN)
    C.kernels = 1


def resolve_full_universe() -> List[str]:
    """Resolve the full stock universe from Qlib."""
    from qlib.data import D
    inst_dict = D.instruments('all')
    df_temp = D.features(
        instruments=inst_dict, fields=['$close'],
        start_time='2024-06-01', end_time='2024-06-30',
    )
    return df_temp.index.get_level_values('instrument').unique().tolist()
```

- [ ] **Step 3: Update `cli/commands/batch.py` to use `qlib_runtime`**

Replace the inline Qlib init block (lines ~104-116 equivalent) with:

```python
from mining.application.qlib_runtime import init_qlib, resolve_full_universe
init_qlib(args.qlib_dir)
all_instruments = resolve_full_universe()
```

- [ ] **Step 4: Update `cli/commands/probe.py` to use `qlib_runtime`**

Same pattern — replace inline init + universe resolution.

- [ ] **Step 5: Run tests**

```bash
pytest tests/mining/ -v
```

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/mining/application/
git commit -m "refactor(mining): extract Qlib runtime init into application/qlib_runtime.py"
```

### Task 2.2: Create `application/batch_service.py`

**Files:**
- Create: `src/mining/application/batch_service.py`
- Modify: `src/mining/cli/commands/batch.py`

- [ ] **Step 1: Create `application/batch_service.py`**

Move the core batch workflow out of `cmd_batch`. The service handles:
- Read batch YAML
- Build config + evaluator
- Run `evaluate_batch()`
- Save result YAML
- Save values cache (pickle)
- Save eval history

```python
"""Batch evaluation orchestration service."""
from __future__ import annotations

import logging
import pickle
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import yaml

from mining.config import MiningConfig
from mining.evaluator import FactorMiningEvaluator
from mining.memory import ExperienceMemory

logger = logging.getLogger(__name__)


def run_batch(
    batch_path: Path,
    config: MiningConfig,
    skip_stage1: bool = False,
) -> Dict[str, Any]:
    """Execute a full batch evaluation pipeline.

    Returns the result dict (same shape as the YAML output).
    """
    with open(batch_path, 'r', encoding='utf-8') as f:
        batch = yaml.safe_load(f)

    candidates = batch.get('candidates', [])
    batch_id = batch.get('batch_id', batch_path.stem)
    if not candidates:
        raise ValueError("批次文件中没有候选因子")

    logger.info("批次 %s: %d 个候选因子", batch_id, len(candidates))

    evaluator = FactorMiningEvaluator(config)
    result = evaluator.evaluate_batch(candidates, skip_stage1=skip_stage1)

    # Propagate batch_id
    for f in result.screened:
        f["batch"] = batch_id
    for r in result.replacements:
        if "new_factor" in r:
            r["new_factor"]["batch"] = batch_id

    # Log summary
    logger.info("筛选通过: %d, 淘汰: %d, 替换候选: %d",
                len(result.screened), len(result.rejected), len(result.replacements))
    for f in result.screened:
        s3 = f.get('stage3', {})
        rc = f.get('report_card', {})
        logger.info("  通过 %s: IC=%.4f, OOS=%.4f, ICIR=%.2f, 单调性=%.2f",
                     f['name'],
                     s3.get('ic_mean_is', 0) or 0,
                     s3.get('ic_mean_oos', 0) or 0,
                     rc.get('ic_ir', 0) or 0,
                     rc.get('monotonicity_is', 0) or 0)
    for f in result.rejected:
        s1 = f.get('stage1', {})
        logger.info("  淘汰 %s: IC=%s", f['name'], s1.get('ic_mean', '?'))

    # Save values cache
    if result.screened:
        values_cache = {}
        for f in result.screened:
            if "_factor_values" in f and "_factor_values_oos" in f:
                values_cache[f["name"]] = {
                    "is": f["_factor_values"],
                    "oos": f["_factor_values_oos"],
                }
        if values_cache:
            cache_path = batch_path.parent / f"{batch_path.stem}_values.pkl"
            with open(cache_path, "wb") as fp:
                pickle.dump(values_cache, fp)
            logger.info("因子值缓存已保存: %s (%d 个因子)", cache_path, len(values_cache))

    # Save result YAML
    result_path = batch_path.parent / f"{batch_path.stem}_result.yaml"
    output = result.to_dict()
    output['batch_id'] = batch_id
    output['timestamp'] = datetime.now().isoformat()
    with open(result_path, 'w', encoding='utf-8') as fp:
        yaml.dump(output, fp, default_flow_style=False, allow_unicode=True)
    logger.info("结果已保存: %s", result_path)

    # Save eval history
    try:
        mem = ExperienceMemory(config)
        eval_history = {
            "batch_id": batch_id,
            "timestamp": datetime.now().isoformat(),
            "phase": "evaluate",
            "candidates": len(candidates),
            "screened": len(result.screened),
            "rejected": len(result.rejected),
            "replacements": len(result.replacements),
            "hard_gated": len([r for r in result.rejected if "hard_gate_reject" in r]),
            "screened_names": [s["name"] for s in result.screened],
        }
        mem.save_eval_history(batch_id, eval_history)
        logger.info("Eval history saved: %s", batch_id)
    except Exception as e:
        logger.warning("Failed to save eval history: %s", e)

    # Log hard-gated
    for f in result.rejected:
        if "hard_gate_reject" in f:
            logger.warning("Hard-gated %s: %s", f['name'],
                           [r["code"] for r in f['hard_gate_reject']])

    return output
```

- [ ] **Step 2: Slim down `cli/commands/batch.py` to thin wrapper**

```python
"""batch command — Evaluate a batch of candidate factors."""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

from mining.application.qlib_runtime import init_qlib, resolve_full_universe
from mining.application.batch_service import run_batch
from mining.config import MiningConfig


def cmd_batch(args):
    """Evaluate a batch of candidate factors from a YAML file."""
    warnings.filterwarnings('ignore')
    import os
    os.environ['JOBLIB_START_METHOD'] = 'fork'
    import multiprocessing
    try:
        multiprocessing.set_start_method('fork', force=True)
    except RuntimeError:
        pass

    batch_path = Path(args.batch_file)
    if not batch_path.exists():
        print(f"错误：批次文件不存在: {batch_path}")
        sys.exit(1)

    init_qlib(args.qlib_dir)
    all_instruments = resolve_full_universe()

    config = MiningConfig(
        custom_universe=all_instruments,
        train_start=args.train_start,
        train_end=args.train_end,
        test_start=args.test_start,
        test_end=args.test_end,
        fast_screening_universe_size=args.screening_size,
    )
    run_batch(batch_path, config, skip_stage1=args.skip_stage1)
```

- [ ] **Step 3: Run tests**

```bash
pytest tests/mining/ -v
```

- [ ] **Step 4: Commit**

```bash
git add src/mining/application/batch_service.py src/mining/cli/commands/batch.py
git commit -m "refactor(mining): extract batch orchestration into application/batch_service.py"
```

---

## Phase 3: Evaluator Split (Risk: MEDIUM, Value: HIGH)

Split `evaluator.py` (1039 lines) into focused sub-modules under `evaluation/`.

### Task 3.1: Extract `domain/results.py` (BatchResult)

**Files:**
- Create: `src/mining/domain/__init__.py`
- Create: `src/mining/domain/results.py`
- Modify: `src/mining/evaluator.py`

- [ ] **Step 1: Create `domain/__init__.py`**

```python
"""Domain layer — pure data structures and rules, no IO."""
```

- [ ] **Step 2: Create `domain/results.py`**

Move `BatchResult` dataclass (lines 111-145 of evaluator.py) and `_clean_factor_dict` (lines 98-108):

```python
"""Batch evaluation result container."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


def _clean_factor_dict(c: Dict[str, Any]) -> Dict[str, Any]:
    """Extract only serializable fields from a factor dict (whitelist approach)."""
    ALLOWED_KEYS = {
        "name", "expression", "category", "rationale", "batch",
        "stage1", "stage2", "stage3", "full_ic", "report_card",
        "validation_error", "reject_reason",
        "source", "code", "code_path", "type", "params", "param_space",
        "logic_id", "lineage",
    }
    return {k: v for k, v in c.items() if k in ALLOWED_KEYS}


@dataclass
class BatchResult:
    """Result of a batch evaluation."""
    screened: List[Dict[str, Any]] = field(default_factory=list)
    rejected: List[Dict[str, Any]] = field(default_factory=list)
    replacements: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def admitted(self) -> List[Dict[str, Any]]:
        return self.screened

    def to_dict(self) -> Dict[str, Any]:
        clean_replacements = []
        for r in self.replacements:
            if isinstance(r, dict) and "new_factor" in r:
                clean_replacements.append({
                    "new_factor": _clean_factor_dict(r["new_factor"]),
                    "replaces": r.get("replaces"),
                })
            else:
                clean_replacements.append(_clean_factor_dict(r))
        return {
            "screened": [_clean_factor_dict(c) for c in self.screened],
            "rejected": [_clean_factor_dict(c) for c in self.rejected],
            "replacements": clean_replacements,
        }
```

- [ ] **Step 3: Update `evaluator.py` to import from `domain.results`**

Replace the in-file `BatchResult` and `_clean_factor_dict` with:
```python
from .domain.results import BatchResult, _clean_factor_dict
```

**CRITICAL:** These imports in `evaluator.py` also serve as backward-compat re-exports. Tests and external code import `BatchResult` and `_clean_factor_dict` from `mining.evaluator`:
- `tests/mining/test_evaluator.py:13` — `from mining.evaluator import BatchResult`
- `tests/mining/test_evaluator.py:402` — `from mining.evaluator import _clean_factor_dict`
- `tests/mining/test_integration.py:12` — `from mining.evaluator import BatchResult`
- `scripts/baseline_eval.py:31` — `from mining.evaluator import BatchResult`

The import lines above ARE the compat shim — do not remove them.

- [ ] **Step 4: Run tests**

```bash
pytest tests/mining/test_evaluator.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/mining/domain/ src/mining/evaluator.py
git commit -m "refactor(mining): extract BatchResult into domain/results.py"
```

### Task 3.2: Extract `domain/similarity.py`

**Files:**
- Create: `src/mining/domain/similarity.py`
- Modify: `src/mining/evaluator.py`

- [ ] **Step 1: Create `domain/similarity.py`**

Move `compute_structural_similarity` (lines 31-41) and `check_lookahead_bias` (lines 44-75):

```python
"""Structural similarity and static analysis for factor code."""
from __future__ import annotations


def compute_structural_similarity(code1: str, code2: str) -> float:
    """Jaccard similarity of ops call signatures between two Python factors."""
    from mining.expression import ExpressionValidator
    validator = ExpressionValidator()
    ops1 = set(validator.extract_ops_calls(code1))
    ops2 = set(validator.extract_ops_calls(code2))
    if not ops1 and not ops2:
        return 0.0
    if not ops1 or not ops2:
        return 0.0
    return len(ops1 & ops2) / len(ops1 | ops2)


def check_lookahead_bias(code: str) -> bool:
    """Static analysis for common lookahead patterns in Python factor code."""
    import ast
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return False

    for node in ast.walk(tree):
        if (isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "shift"):
            for arg in node.args:
                if isinstance(arg, ast.UnaryOp) and isinstance(arg.op, ast.USub):
                    return True
                if (isinstance(arg, ast.Constant)
                        and isinstance(arg.value, (int, float))
                        and arg.value < 0):
                    return True
    return False
```

- [ ] **Step 2: Update evaluator.py imports**

Replace the in-file definitions with:
```python
from .domain.similarity import compute_structural_similarity, check_lookahead_bias
```

**CRITICAL:** These imports in `evaluator.py` also serve as backward-compat re-exports. Tests import these from `mining.evaluator`:
- `tests/mining/test_lookahead.py:5` — `from mining.evaluator import check_lookahead_bias`
- `tests/mining/test_ast_dedup.py:5` — `from mining.evaluator import compute_structural_similarity`
- `tests/mining/test_python_factor_e2e.py:12` — `from mining.evaluator import check_lookahead_bias, compute_structural_similarity`

The import lines above ARE the compat shim — do not remove them.

- [ ] **Step 3: Run tests**

```bash
pytest tests/mining/test_lookahead.py tests/mining/test_ast_dedup.py tests/mining/test_python_factor_e2e.py -v
```

- [ ] **Step 4: Commit**

```bash
git add src/mining/domain/similarity.py src/mining/evaluator.py
git commit -m "refactor(mining): extract similarity/lookahead into domain/similarity.py"
```

### Task 3.3: Extract `domain/policies.py`

**Files:**
- Create: `src/mining/domain/policies.py`
- Modify: `src/mining/evaluator.py`

- [ ] **Step 1: Create `domain/policies.py`**

Move `_candidate_cache_key`, `_is_python_candidate` (lines 85-95):

```python
"""Factor candidate classification and caching policies."""
from __future__ import annotations

from typing import Any, Dict


def _candidate_cache_key(c: Dict[str, Any]) -> str:
    """Derive a stable cache key for a candidate."""
    if c.get("expression"):
        return c["expression"]
    return c.get("code", "")[:100]


def _is_python_candidate(c: Dict[str, Any]) -> bool:
    """Return True if the candidate represents a Python factor."""
    return c.get("source") == "python" or c.get("type") == "python"
```

- [ ] **Step 2: Update evaluator.py imports**

```python
from .domain.policies import _candidate_cache_key, _is_python_candidate
```

**CRITICAL:** These imports in `evaluator.py` also serve as backward-compat re-exports. Tests import these from `mining.evaluator`:
- `tests/mining/test_evaluator.py:430,436,442` — `from mining.evaluator import _is_python_candidate`
- `tests/mining/test_evaluator.py:447,453,460` — `from mining.evaluator import _candidate_cache_key`

The import lines above ARE the compat shim — do not remove them.

- [ ] **Step 3: Run tests**

```bash
pytest tests/mining/test_evaluator.py -v
```

- [ ] **Step 4: Commit**

```bash
git add src/mining/domain/policies.py src/mining/evaluator.py
git commit -m "refactor(mining): extract candidate policies into domain/policies.py"
```

### Task 3.4: Extract `evaluation/gates.py`

**Files:**
- Create: `src/mining/evaluation/__init__.py`
- Create: `src/mining/evaluation/gates.py`
- Modify: `src/mining/evaluator.py`

- [ ] **Step 1: Create `evaluation/__init__.py`**

```python
"""Evaluation sub-package — factor computation and screening."""
```

- [ ] **Step 2: Create `evaluation/gates.py`**

Extract `_apply_hard_gates` (lines 909-955 of evaluator.py) as a standalone function:

```python
"""Post-Stage3 hard gates — cannot be overridden by LLM or --admit."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Tuple

from mining.config import MiningConfig

logger = logging.getLogger(__name__)


def apply_hard_gates(
    screened: List[Dict[str, Any]],
    config: MiningConfig,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Post-Stage3 hard gates. Returns (passed, gated)."""
    passed, gated = [], []
    for c in screened:
        rc = c.get("report_card", {})
        reasons: List[Dict[str, Any]] = []

        if rc.get("ic_sign_consistent") is False:
            reasons.append({"code": "ic_sign_flip", "value": None})

        decay = rc.get("oos_decay_ratio")
        if decay is not None and decay < config.hard_gate_oos_decay_min:
            reasons.append({"code": "oos_decay_too_low",
                            "value": round(decay, 3),
                            "threshold": config.hard_gate_oos_decay_min})

        cov = rc.get("coverage")
        if cov is not None and cov < config.hard_gate_coverage_min:
            reasons.append({"code": "coverage_too_low",
                            "value": round(cov, 3),
                            "threshold": config.hard_gate_coverage_min})

        mono_is = rc.get("monotonicity_is")
        mono_oos = rc.get("monotonicity_oos")
        if (mono_is is not None and mono_oos is not None
                and mono_is != 0 and mono_oos != 0
                and (mono_is * mono_oos < 0)):
            reasons.append({"code": "mono_sign_flip",
                            "value": {"is": round(mono_is, 2),
                                      "oos": round(mono_oos, 2)}})

        ic_oos_val = rc.get("ic_mean_oos")
        if ic_oos_val is not None and abs(ic_oos_val) < config.hard_gate_ic_oos_min:
            reasons.append({"code": "ic_oos_too_low",
                            "value": round(abs(ic_oos_val), 4),
                            "threshold": config.hard_gate_ic_oos_min})

        if reasons:
            c["hard_gate_reject"] = reasons
            gated.append(c)
            logger.info("Hard gate reject %s: %s",
                        c["name"], [r["code"] for r in reasons])
        else:
            passed.append(c)
    return passed, gated
```

- [ ] **Step 3: Update evaluator.py**

Replace `_apply_hard_gates` method with delegation:

```python
from .evaluation.gates import apply_hard_gates

# In evaluate_batch():
#   screened, hard_gated = self._apply_hard_gates(screened)
# becomes:
#   screened, hard_gated = apply_hard_gates(screened, self.config)
```

Keep the method as a thin wrapper for backward compat if any test calls it directly:

```python
def _apply_hard_gates(self, screened):
    return apply_hard_gates(screened, self.config)
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/mining/test_evaluator.py -v
```

- [ ] **Step 5: Commit**

```bash
git add src/mining/evaluation/ src/mining/evaluator.py
git commit -m "refactor(mining): extract hard gates into evaluation/gates.py"
```

### Task 3.5: Move `schema.py` to `domain/schema.py`

**Files:**
- Create: `src/mining/domain/schema.py` (move from `src/mining/schema.py`)
- Modify: `src/mining/schema.py` → compat re-export

- [ ] **Step 1: Move schema.py content to domain/schema.py**

Copy `src/mining/schema.py` content to `src/mining/domain/schema.py` verbatim.

- [ ] **Step 2: Replace old `schema.py` with compat shim**

```python
"""Backward-compatible re-export — canonical location is domain.schema."""
from .domain.schema import FactorRecord, normalize_metrics, VALID_STATUSES, VALID_SOURCES, METRICS_ALIASES
```

- [ ] **Step 3: Run tests**

```bash
pytest tests/mining/test_schema.py -v
```

- [ ] **Step 4: Commit**

```bash
git add src/mining/domain/schema.py src/mining/schema.py
git commit -m "refactor(mining): move schema.py to domain/schema.py with compat shim"
```

---

## Phase 4: Memory Boundary Cleanup (Risk: MEDIUM, Value: HIGH)

The critical cut: remove `compose_search_context` and `get_lineage_summary` from `ExperienceMemory`. These methods import `FactorLibrary`, `EvolutionEngine`, and `MarketLogicLibrary` — creating reverse dependencies that make `memory` a hidden orchestrator.

### Task 4.1: Create `application/context_service.py`

**Files:**
- Create: `src/mining/application/context_service.py`
- Modify: `src/mining/memory.py`

- [ ] **Step 1: Create `application/context_service.py`**

Move `compose_search_context` and `get_lineage_summary` logic here:

```python
"""Research context composition — reads from memory, logic, registry."""
from __future__ import annotations

import logging
from typing import Any, Dict, List

from mining.config import MiningConfig
from mining.memory import ExperienceMemory

logger = logging.getLogger(__name__)


def compose_search_context(config: MiningConfig) -> str:
    """Compose memory into a prompt-ready string.

    Reads from:
    1. ExperienceMemory (state, directions, forbidden)
    2. MarketLogicLibrary (coverage, active logics)
    3. FactorLibrary + EvolutionEngine (lineage)
    """
    mem = ExperienceMemory(config)
    sections: List[str] = []

    # Section 1: Current library state
    state = mem.read_state()
    lib = state.get("library", {})
    state_lines = ["## Current Mining State", f"Library size: {lib.get('size', 0)}"]
    hint = state.get("next_round_hint")
    if hint:
        state_lines.append(f"\nLast round hint: {hint}")
    sections.append("\n".join(state_lines))

    # Section 2: Direction statuses
    directions = mem.list_directions()
    if directions:
        dir_lines = ["## Direction Statuses"]
        by_status: Dict[str, list] = {}
        for d in directions:
            by_status.setdefault(d["status"], []).append(d)
        for status in ["active", "new", "probing", "exhausted", "blocked", "dead"]:
            if status in by_status:
                names = [
                    f"{d['name']} (IC={d['best_ic']})" if d.get("best_ic") else d["name"]
                    for d in by_status[status]
                ]
                dir_lines.append(f"- **{status}**: {', '.join(names)}")
        sections.append("\n".join(dir_lines))

    # Section 3: Taxonomy coverage map
    logic_lib = None
    try:
        from mining.logic_library import MarketLogicLibrary
        logic_lib = MarketLogicLibrary(config.logic_dir)
        coverage = logic_lib.coverage_map()
        if coverage:
            cov_lines = ["## Taxonomy Coverage"]
            for cat, count in sorted(coverage.items()):
                cov_lines.append(f"  {cat}: {count} active logics")
            sections.append("\n".join(cov_lines))
    except Exception:
        pass

    # Section 4: Forbidden regions
    forbidden = mem.read_forbidden()
    if forbidden:
        forb_lines = ["## Forbidden Regions (DO NOT explore these)"]
        for r in forbidden:
            forb_lines.append(f"  - {r['pattern']} \u2014 {r['reason']}")
        sections.append("\n".join(forb_lines))

    # Section 5: Active logic evidence
    try:
        if logic_lib is None:
            from mining.logic_library import MarketLogicLibrary
            logic_lib = MarketLogicLibrary(config.logic_dir)
        active = logic_lib.list_logics(status="active")
        if active:
            logic_lines = ["## Active Market Logics"]
            for logic in active:
                s = logic.get("stats", {})
                logic_lines.append(
                    f"  {logic['id']} {logic['name']} "
                    f"[gen={s.get('factors_generated', 0)}, "
                    f"adm={s.get('factors_admitted', 0)}, "
                    f"best_ic={s.get('best_ic', 0):.3f}]"
                )
            sections.append("\n".join(logic_lines))
    except Exception:
        pass

    # Section 6: Lineage summary
    lineage_text = _get_lineage_summary(config)
    if lineage_text:
        sections.append(f"## Factor Lineage Tree\n{lineage_text}")

    return "\n\n".join(s for s in sections if s)


def _get_lineage_summary(config: MiningConfig) -> str:
    """Format lineage information from library for prompt context."""
    try:
        from mining.library import FactorLibrary
        lib = FactorLibrary(config)
        factors = lib.list_factors()
        with_lineage = [f for f in factors if f.get("lineage")]
        if not with_lineage:
            return ""
        from mining.evolution import EvolutionEngine
        engine = EvolutionEngine(config)
        return engine.format_lineage_tree(factors)
    except Exception:
        return ""
```

- [ ] **Step 2: Update `memory.py` — remove compose_search_context and get_lineage_summary**

Delete the `compose_search_context` method (lines 126-212) and `get_lineage_summary` method (lines 214-231) from `ExperienceMemory`.

Add a deprecation shim for callers that used `mem.compose_search_context()`:

```python
def compose_search_context(self) -> str:
    """Deprecated — use mining.application.context_service.compose_search_context()."""
    from mining.application.context_service import compose_search_context
    return compose_search_context(self._config)
```

- [ ] **Step 3: Update `cli/commands/memory.py`**

Change from `mem.compose_search_context()` to:
```python
from mining.application.context_service import compose_search_context
ctx = compose_search_context(config)
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/mining/test_memory.py -v
```

- [ ] **Step 5: Commit**

```bash
git add src/mining/application/context_service.py src/mining/memory.py src/mining/cli/commands/memory.py
git commit -m "refactor(mining): move compose_search_context to application/context_service.py"
```

### Task 4.2: Move `memory.py` to `memory/store.py`

**Files:**
- Create: `src/mining/memory/__init__.py`
- Create: `src/mining/memory/store.py` (move from `src/mining/memory.py`)
- Modify: `src/mining/memory.py` → compat re-export

Note: `src/mining/memory.py` and `src/mining/memory/` cannot coexist. We must **delete** the file and create the package.

- [ ] **Step 1: Create `src/mining/memory/store.py`**

Copy `memory.py` content (with compose_search_context already delegating to context_service) to `memory/store.py`.

- [ ] **Step 2: Create `src/mining/memory/__init__.py`**

```python
"""Memory sub-package — experience memory storage."""
from .store import ExperienceMemory

__all__ = ["ExperienceMemory"]
```

- [ ] **Step 3: Delete old `src/mining/memory.py`**

- [ ] **Step 4: Update all imports across the codebase**

Grep for `from mining.memory import` and `from .memory import` — these should now resolve to the package's `__init__.py` which re-exports `ExperienceMemory`. No changes needed if the `__init__.py` re-exports correctly.

Verify: `from mining.memory import ExperienceMemory` still works.

- [ ] **Step 5: Run tests**

```bash
pytest tests/mining/ -v
```

- [ ] **Step 6: Commit**

```bash
git add src/mining/memory/ tests/
git commit -m "refactor(mining): move memory.py to memory/store.py package"
```

---

## Phase 5: Registry Split (Risk: LOW, Value: MEDIUM)

Split `library.py` (245 lines) into focused sub-modules.

### Task 5.1: Extract `registry/values_cache.py` and `registry/history.py`

**Files:**
- Create: `src/mining/registry/__init__.py`
- Create: `src/mining/registry/values_cache.py`
- Create: `src/mining/registry/history.py`
- Create: `src/mining/registry/library.py` (main FactorLibrary)
- Modify: `src/mining/library.py` → compat re-export

- [ ] **Step 1: Create `registry/__init__.py`**

```python
"""Registry sub-package — factor library management."""
from .library import FactorLibrary

__all__ = ["FactorLibrary"]
```

- [ ] **Step 2: Create `registry/values_cache.py`**

Extract `_load_values_cache` method:

```python
"""Factor values cache loading from pickle files."""
from __future__ import annotations

import logging
import pickle
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd

logger = logging.getLogger(__name__)


def load_values_cache(
    factor_name: str,
    candidates_dir: str,
) -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
    """Try to load factor values from pickle cache (saved by evaluate step)."""
    cdir = Path(candidates_dir)
    for pkl in sorted(cdir.glob("*_values.pkl"), reverse=True):
        try:
            with open(pkl, "rb") as f:
                cache = pickle.load(f)
            if factor_name in cache:
                logger.info("Loaded factor values from cache: %s", pkl)
                return cache[factor_name]["is"], cache[factor_name]["oos"]
        except Exception:
            continue
    return None, None
```

- [ ] **Step 3: Create `registry/history.py`**

Extract archive logic from `library.replace`:

```python
"""Factor history archival."""
from __future__ import annotations

import logging
import shutil
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


def archive_detail(factors_dir: Path, factor_id: str) -> None:
    """Archive a factor detail YAML to factors/history/ before overwrite."""
    detail_path = factors_dir / f"factor_{factor_id}.yaml"
    if not detail_path.exists():
        return
    history_dir = factors_dir / "history"
    history_dir.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_name = f"factor_{factor_id}__replaced_{ts}.yaml"
    shutil.copy2(str(detail_path), str(history_dir / archive_name))
    logger.info("Archived %s → history/%s", detail_path.name, archive_name)
```

- [ ] **Step 4: Create `registry/library.py`**

Move `FactorLibrary` class, replacing inline `_load_values_cache` and archive logic with imports from the new modules.

The class itself stays mostly the same but calls:
- `from .values_cache import load_values_cache` instead of the inline method
- `from .history import archive_detail` instead of inline archive logic in `replace()`

- [ ] **Step 5: Replace old `src/mining/library.py` with compat shim**

```python
"""Backward-compatible re-export — canonical location is registry.library."""
from .registry.library import FactorLibrary
```

- [ ] **Step 6: Move `src/mining/publisher.py` to `src/mining/registry/publisher.py`**

Update the import in `registry/library.py`:
```python
from .publisher import FactorPublisher
```

Replace old `publisher.py` with compat shim that re-exports ALL names used by tests:
```python
"""Backward-compatible re-export — canonical location is registry.publisher."""
from .registry.publisher import FactorPublisher
# Re-export execute_values for test patch targets
try:
    from psycopg2.extras import execute_values
except ImportError:
    pass
```

- [ ] **Step 7: Update `patch()` targets in test files**

**CRITICAL:** Tests patch names as they exist in the `mining.publisher` module namespace. After the move, the compat shim must re-export `execute_values` OR tests must update patch targets.

Option A (compat shim re-exports — chosen above): No test changes needed for `test_publisher.py` patches. The shim re-exports `execute_values`.

Option B (update tests — cleaner, do in Phase 7): Update these in `tests/mining/test_publisher.py`:
- `patch("mining.publisher.execute_values")` → `patch("mining.registry.publisher.execute_values")`

And in `tests/mining/test_library.py`:
- `patch("mining.publisher.FactorPublisher")` → `patch("mining.library.FactorPublisher")`

Note: `test_library.py` patches `mining.publisher.FactorPublisher` but `library.py` does `from .publisher import FactorPublisher`. After the move, `registry/library.py` does `from .publisher import FactorPublisher` — so the patch target that matters is `mining.registry.library.FactorPublisher`. However, since old `library.py` is now a compat shim pointing to `registry.library`, and old `publisher.py` is a compat shim pointing to `registry.publisher`, the existing test patches will work AS LONG AS the compat shims re-export the right names.

Verify: After applying compat shims, confirm that `patch("mining.publisher.FactorPublisher")` still intercepts the call in `library._publish()`. If `library.py` is now a compat shim and `registry/library.py` does `from .publisher import FactorPublisher`, the actual lookup path is `mining.registry.publisher.FactorPublisher`. The old patch target `mining.publisher.FactorPublisher` patches the compat shim's re-export — this does NOT affect the import inside `registry/library.py`.

**Therefore:** Update `test_library.py` patch targets:
```python
# Lines 110, 129, 142:
patch("mining.library.FactorPublisher")  →  patch("mining.registry.library.FactorPublisher")
```

- [ ] **Step 8: Run tests**

```bash
pytest tests/mining/test_library.py tests/mining/test_publisher.py -v
```

- [ ] **Step 9: Commit**

```bash
git add src/mining/registry/ src/mining/library.py src/mining/publisher.py tests/mining/test_library.py
git commit -m "refactor(mining): split library into registry/ sub-package"
```

---

## Phase 6: Logic Sub-Package (Risk: LOW, Value: LOW)

### Task 6.1: Move logic files to `logic/` sub-package

**Files:**
- Create: `src/mining/logic/__init__.py`
- Create: `src/mining/logic/library.py` (from `logic_library.py`)
- Create: `src/mining/logic/scheduler.py` (from `scheduler.py`)
- Modify: `src/mining/logic_library.py` → compat re-export
- Modify: `src/mining/scheduler.py` → compat re-export

- [ ] **Step 1: Create `logic/__init__.py`**

```python
"""Logic sub-package — market logic hypotheses management."""
from .library import MarketLogicLibrary
from .scheduler import Scheduler

__all__ = ["MarketLogicLibrary", "Scheduler"]
```

- [ ] **Step 2: Move files**

Copy `logic_library.py` content to `logic/library.py`.
Copy `scheduler.py` content to `logic/scheduler.py`.

- [ ] **Step 3: Replace old files with compat shims**

`logic_library.py`:
```python
from .logic.library import MarketLogicLibrary
```

`scheduler.py`:
```python
from .logic.scheduler import Scheduler
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/mining/test_logic_library.py tests/mining/test_scheduler.py -v
```

- [ ] **Step 5: Commit**

```bash
git add src/mining/logic/ src/mining/logic_library.py src/mining/scheduler.py
git commit -m "refactor(mining): move logic_library + scheduler to logic/ sub-package"
```

---

## Phase 7: Package API Cleanup (Risk: LOW, Value: MEDIUM)

### Task 7.1: Slim `__init__.py` to stable public API

**Files:**
- Modify: `src/mining/__init__.py`

- [ ] **Step 1: Rewrite `__init__.py`**

```python
"""FactorMiner: Automated factor mining with Experience Memory."""

__version__ = "5.0.0"

# Stable public API — import from canonical sub-package locations
from .config import MiningConfig
from .expression import ExpressionValidator, ValidationResult
from .domain.results import BatchResult
from .domain.schema import FactorRecord, normalize_metrics
from .evaluation.gates import apply_hard_gates
from .registry import FactorLibrary
from .memory import ExperienceMemory
from .preprocessing import FactorPreprocessor
from .ops_adapter import OpsAdapter
from .sandbox import run_factor_in_sandbox, SandboxError
from .evolution import EvolutionEngine
from .logic import MarketLogicLibrary, Scheduler

# Evaluator — lazy import recommended for heavy Qlib dependency
from .evaluator import FactorMiningEvaluator

__all__ = [
    "MiningConfig",
    "ExpressionValidator",
    "ValidationResult",
    "FactorMiningEvaluator",
    "BatchResult",
    "FactorRecord",
    "FactorLibrary",
    "ExperienceMemory",
    "FactorPreprocessor",
    "OpsAdapter",
    "run_factor_in_sandbox",
    "SandboxError",
    "EvolutionEngine",
    "MarketLogicLibrary",
    "Scheduler",
]
```

Note: `DataSynchronizer` removed from `__all__` (it's a cross-package import from `data.qlib_sync`, should not be re-exported by mining).

- [ ] **Step 2: Remove compat shims that are no longer needed**

Check if any external code imports from the old flat paths. If all consumers use the `__init__.py` re-exports, the compat shims in `schema.py`, `library.py`, `logic_library.py`, `scheduler.py` can be left as-is (they cost nothing and prevent breakage).

Only remove shims that are confirmed unused.

- [ ] **Step 3: Run full test suite**

```bash
pytest tests/ -v
```

Expected: ALL PASS

- [ ] **Step 4: Commit**

```bash
git add src/mining/__init__.py
git commit -m "refactor(mining): slim __init__.py to stable public API, bump to v5.0.0"
```

### Task 7.2: Update test imports (cleanup pass)

**Files:**
- Modify: various `tests/mining/test_*.py` files

- [ ] **Step 1: Grep for imports that can use canonical locations**

```bash
grep -rn "from mining\." tests/mining/ | grep -v __pycache__
```

- [ ] **Step 2: Update test imports to canonical sub-package paths where beneficial**

Priority updates (high-value, reduce coupling to compat shims):
- `from mining.schema import` → `from mining.domain.schema import`
- `from mining.library import` → `from mining.registry import`
- `from mining.memory import` → `from mining.memory import` (already correct via package)
- `from mining.evaluator import BatchResult` → `from mining.domain.results import BatchResult`

Leave `from mining.evaluator import FactorMiningEvaluator` unchanged — it's the canonical location.

- [ ] **Step 3: Run full test suite**

```bash
pytest tests/ -v
```

- [ ] **Step 4: Commit**

```bash
git add tests/
git commit -m "refactor(tests): update mining test imports to canonical sub-package paths"
```

---

## Risk Notes

1. **Python package vs module conflict:** When `cli.py` and `cli/` coexist, Python prioritizes the package. We handle this by deleting the old `.py` file. Same for `memory.py`/`memory/`.

2. **Compat shims are cheap insurance.** Flat-file re-exports (`library.py → from .registry.library import FactorLibrary`) add zero runtime cost and prevent import breakage. Remove only when confirmed safe.

3. **`evaluator.py` stays at root.** Moving it to `evaluation/evaluator.py` is tempting but would break the most imports for marginal gain. We extract pieces *out* of it but leave the class in its current location. The import-at-top-level lines in `evaluator.py` (e.g., `from .domain.results import BatchResult`) double as backward-compat re-exports — do NOT remove them.

4. **`patch()` targets in tests are the #1 breakage risk.** When a module moves, `unittest.mock.patch("old.path.Name")` silently does nothing. Every phase that moves a module must audit and update patch targets. Key locations:
   - `test_cli.py`: 5x `patch("mining.cli.MiningConfig")` → per-command module paths
   - `test_library.py`: 3x `patch("mining.publisher.FactorPublisher")` → `mining.registry.library.FactorPublisher`
   - `test_publisher.py`: 5x `patch("mining.publisher.execute_values")` → handled by compat shim re-export

5. **Dashboard is an external consumer.** `src/dashboard/` imports `FactorLibrary`, `MiningConfig`, `__version__` from `mining`. These go through `__init__.py` and will continue to work, but should be verified after Phase 7.

6. **Test directory restructuring deferred.** Aligning `tests/mining/` subdirectories to match the new source layout is valuable but is a follow-up concern, not a blocker for this plan.
