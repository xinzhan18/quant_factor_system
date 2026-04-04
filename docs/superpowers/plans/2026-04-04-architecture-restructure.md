# Architecture Restructure: Single Truth Source + 4-Layer System

**Goal:** Transform the quant factor system from a "semi-scripted, semi-prompted" factor mining scaffold into a governed research platform with a single metadata truth source, consistent schema, and clean layer separation.

**Architecture:** 4.5-layer system: Mining (hypothesis + candidates + evaluation + memory), Registry (single metadata truth source for factor records), Evidence (reports/charts — pure derivation, deletable), Runtime (cache/pkl/temp — ephemeral). Governance capabilities (hard gates, judge, forbidden, audit) embedded across Mining + Registry, not a separate layer.

**Truth source scope:**
- Factor **metadata** single source: registry detail YAML (`storage/registry/factors/factor_XXX.yaml`)
- Factor **values and time series** source: DB `factor_values` table (computed, not derivable from YAML)
- Factor **reports and charts**: evidence layer (deletable, rebuildable from metadata + DB)

**Tech Stack:** Python 3.8+, PyYAML, pytest, Qlib, TimescaleDB (psycopg2)

---

## Current Code State (rebased 2026-04-04)

**Already implemented (verify/align only — do NOT reimplement):**
- Hard gates in `evaluator.py:907-949` (ic_sign_flip, oos_decay, coverage, mono_flip, ic_oos)
- `skip_stage1` decoupled from batch dedup — `evaluator.py:1006-1008`
- `logic create/list/coverage/schedule` CLI — `cli.py:274-336`
- `forbidden suggest/apply/list` CLI — `cli.py:338-409`
- `audit` CLI — `cli.py:412-424`
- `eval_history` auto-saved — `cli.py:187-204`
- Time window validation (train_end < test_start) — `config.py:122-134`

**Still broken (must fix):**
- `--admit` flag exists — `cli.py:457`, auto-admit block `cli.py:212-226`
- `_normalize_metrics()` duplicates schema logic — `cli.py:72-87`
- Report builder reads DB first, falls back to hardcoded path — `builder.py:237-285`
- Hardcoded `Path("storage/candidates")` — `library.py:227`
- Hardcoded `Path("storage/library/library.yaml")` — `builder.py:267-269`
- No `status`, `long_leg`, `evaluation_version` in any factor record
- Schema fragmentation: `ic_mean` vs `ic_mean_is`, `max_corr` vs `max_lib_corr`
- `CLAUDE.md:18` still shows `--admit` in example command

**Schema audit (51 detail files):**
| Field | Present | Missing |
|-------|---------|---------|
| `source` | 26 | 25 |
| `status` | 0 | 51 |
| `long_leg` | 0 | 51 |
| `evaluation_version` | 0 | 51 |
| `metrics.ic_mean` (canonical) | 35 | 16 (use `ic_mean_is`) |
| `metrics.max_corr` (canonical) | 12 | 39 (5 use `max_lib_corr`) |
| `metrics.monotonicity_is` (canonical) | 5 | 46 (27 use bare `monotonicity`) |

---

## Phase Structure

| Phase | Focus | Risk | Pre-conditions |
|-------|-------|------|----------------|
| **Phase 0** | Schema definition + inventory snapshot | LOW — additive, no mutations | None |
| **Phase 0.5** | Code integration (wire schema into library/CLI, remove `--admit`) | MED — behavioral change in admit path | Phase 0 tests pass |
| **Phase 1** | Execute schema migration on 51 factor files | **MED** — mutates main assets | Inventory snapshot exists, `--dry-run` reviewed |
| **Phase 2** | Report + path consolidation + docs | MED — touches report/config/skills | Phase 1 complete |
| **Phase 3** | Storage directory restructure (copy → verify → cutover) | MED — file moves | Phase 2 complete, all tests pass |

**Constraint:** Each phase is independently shippable. Tests must pass after every commit.

---

## Status and evaluation_version Semantics

### `status` — factor lifecycle state

| Status | Meaning | Participates in Stage 2 corr blocking? | Used in portfolio? |
|--------|---------|----------------------------------------|--------------------|
| `active` | Current production factor, validated under stable pipeline | Yes | Yes |
| `legacy` | Admitted under earlier pipeline version, not yet re-validated | Yes (still represents a known signal cluster) | No (until promoted) |
| `retired` | Explicitly removed from use (replaced, weak, or redundant) | **Yes** by default (prevents re-mining same signal) | No |

**Key rule:** All statuses participate in correlation blocking by default. Retired/legacy factors still represent known signal clusters — removing them from Stage 2 would allow re-mining identical signals. To truly exclude a factor from blocking, delete its detail YAML.

### `evaluation_version` — pipeline version tag

| Version | Meaning |
|---------|---------|
| `v1` | Admitted before pipeline stabilization. May have: overlapping train/test, no hard gates, dedup bugs, no OOS metrics |
| `v2` | Admitted under current stable pipeline (hard gates, dedup fix, train≤2023/test=2024) |

**Assignment rule:** All existing 51 factors get `v1`. Only factors admitted after this migration through the new pipeline get `v2`. No date-based guessing.

### Migration default

All existing factors with no `status` field → `status: "legacy"` (not `"active"`).
Promotion to `active` is a separate, deliberate step (manual or batch re-certification).

---

## Phase 0: Schema Definition + Inventory

### Task 0.1: Define canonical factor schema

**Files:**
- Create: `src/mining/schema.py`
- Test: `tests/mining/test_schema.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/mining/test_schema.py
"""Tests for canonical factor record schema."""
import pytest
from mining.schema import FactorRecord, normalize_metrics, METRICS_ALIASES


class TestFactorRecord:
    def test_migration_defaults(self):
        """Raw FactorRecord defaults to legacy/v1 for migration safety."""
        rec = FactorRecord(
            id="001", name="test_factor", expression="Std($close, 20)",
            category="volatility", batch="batch_001",
        )
        assert rec.status == "legacy"
        assert rec.evaluation_version == "v1"
        assert rec.source == "dsl"

    def test_for_new_admission_factory(self):
        """for_new_admission() produces active/v2."""
        rec = FactorRecord.for_new_admission(
            id="001", name="test", expression="X",
            category="c", batch="b", metrics={"ic_mean": -0.02},
        )
        assert rec.status == "active"
        assert rec.evaluation_version == "v2"

    def test_for_migration_factory(self):
        """for_migration() produces legacy/v1."""
        rec = FactorRecord.for_migration(
            id="001", name="test", expression="X",
            category="c", batch="b",
        )
        assert rec.status == "legacy"
        assert rec.evaluation_version == "v1"

    def test_long_leg_from_ic(self):
        rec = FactorRecord(
            id="001", name="x", expression="X", category="c", batch="b",
            metrics={"ic_mean": -0.05},
        )
        assert rec.long_leg == "low"

        rec2 = FactorRecord(
            id="002", name="x", expression="X", category="c", batch="b",
            metrics={"ic_mean": 0.03},
        )
        assert rec2.long_leg == "high"

    def test_status_values(self):
        with pytest.raises(ValueError, match="status"):
            FactorRecord(
                id="001", name="x", expression="X", category="c", batch="b",
                status="invalid",
            )

    def test_active_status_accepted(self):
        rec = FactorRecord(
            id="001", name="x", expression="X", category="c", batch="b",
            status="active", evaluation_version="v2",
        )
        assert rec.status == "active"

    def test_retired_status_accepted(self):
        rec = FactorRecord(
            id="001", name="x", expression="X", category="c", batch="b",
            status="retired",
        )
        assert rec.status == "retired"


class TestNormalizeMetrics:
    def test_ic_mean_is_aliased(self):
        raw = {"ic_mean_is": -0.05, "ic_ir_is": -0.4}
        norm = normalize_metrics(raw)
        assert norm["ic_mean"] == -0.05
        assert norm["ic_ir"] == -0.4
        assert "ic_mean_is" not in norm

    def test_max_lib_corr_aliased(self):
        raw = {"max_lib_corr": 0.5, "max_corr_factor": "009"}
        norm = normalize_metrics(raw)
        assert norm["max_corr"] == 0.5
        assert "max_lib_corr" not in norm

    def test_both_present_prefers_canonical(self):
        raw = {"ic_mean": -0.05, "ic_mean_is": -0.03}
        norm = normalize_metrics(raw)
        assert norm["ic_mean"] == -0.05

    def test_monotonicity_renamed(self):
        raw = {"monotonicity": -0.9}
        norm = normalize_metrics(raw)
        assert norm["monotonicity_is"] == -0.9
        assert "monotonicity" not in norm

    def test_passthrough_unknown_keys(self):
        raw = {"ic_mean_oos": -0.04, "custom_metric": 42}
        norm = normalize_metrics(raw)
        assert norm["ic_mean_oos"] == -0.04
        assert norm["custom_metric"] == 42
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/mining/test_schema.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'mining.schema'`

- [ ] **Step 3: Write the implementation**

```python
# src/mining/schema.py
"""Canonical factor record schema — single metadata truth definition.

All factor records in the system (library YAML, DB, evaluator output)
must conform to this schema. The normalize_metrics() function handles
legacy alias resolution.

SCOPE: normalize_metrics() applies ONLY to factor record metrics
(library/registry storage). It must NOT be applied to intermediate
evaluator/analyzer result dicts, which use their own naming.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

VALID_STATUSES = {"active", "legacy", "retired"}
VALID_SOURCES = {"dsl", "python"}

# Maps legacy/variant metric keys → canonical key.
# When both alias and canonical are present, canonical wins.
METRICS_ALIASES: Dict[str, str] = {
    "ic_mean_is": "ic_mean",
    "ic_ir_is": "ic_ir",
    "max_lib_corr": "max_corr",
    "monotonicity": "monotonicity_is",
}


def normalize_metrics(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Resolve legacy metric aliases to canonical names for library storage.

    SCOPE: Only for factor record metrics persisted in registry YAML.
    Do NOT apply to intermediate evaluator/analyzer result dicts.

    Rules:
    - If canonical key already present, keep it (alias is dropped).
    - If only alias present, rename to canonical.
    - Unknown keys pass through unchanged.
    """
    result = {}
    for k, v in raw.items():
        canonical = METRICS_ALIASES.get(k)
        if canonical:
            if canonical not in raw and canonical not in result:
                result[canonical] = v
        else:
            result[k] = v
    return result


@dataclass
class FactorRecord:
    """Canonical factor record — the single metadata truth definition.

    Not persisted directly (we use YAML dicts). Serves as schema contract:
    validation, defaults, and long_leg inference.
    """
    # Required
    id: str
    name: str
    expression: Optional[str]  # None for Python factors
    category: str
    batch: str

    # Defaults — "legacy" and "v1" for migration safety
    source: str = "dsl"
    status: str = "legacy"
    evaluation_version: str = "v1"
    admitted_at: Optional[str] = None
    logic_id: Optional[str] = None
    lineage: Optional[Dict[str, Any]] = None
    code_path: Optional[str] = None
    replaces: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    long_leg: Optional[str] = None

    def __post_init__(self):
        if self.status not in VALID_STATUSES:
            raise ValueError(
                f"Invalid status {self.status!r}, must be one of {VALID_STATUSES}"
            )
        if self.source not in VALID_SOURCES:
            raise ValueError(
                f"Invalid source {self.source!r}, must be one of {VALID_SOURCES}"
            )
        if self.metrics:
            self.metrics = normalize_metrics(self.metrics)
        if self.long_leg is None and self.metrics:
            ic = self.metrics.get("ic_mean")
            if ic is not None:
                self.long_leg = "high" if ic >= 0 else "low"

    @classmethod
    def for_new_admission(cls, **kwargs) -> "FactorRecord":
        """Factory for new pipeline admissions (active/v2)."""
        kwargs.setdefault("status", "active")
        kwargs.setdefault("evaluation_version", "v2")
        return cls(**kwargs)

    @classmethod
    def for_migration(cls, **kwargs) -> "FactorRecord":
        """Factory for migrating legacy records (legacy/v1)."""
        kwargs.setdefault("status", "legacy")
        kwargs.setdefault("evaluation_version", "v1")
        return cls(**kwargs)

    def to_detail_dict(self) -> Dict[str, Any]:
        """Export as dict for detail YAML (factor_XXX.yaml)."""
        d: Dict[str, Any] = {
            "id": self.id,
            "name": self.name,
            "expression": self.expression,
            "source": self.source,
            "status": self.status,
            "evaluation_version": self.evaluation_version,
            "category": self.category,
            "batch": self.batch,
            "admitted_at": self.admitted_at,
            "long_leg": self.long_leg,
            "metrics": self.metrics,
        }
        if self.logic_id:
            d["logic_id"] = self.logic_id
        if self.lineage:
            d["lineage"] = self.lineage
        if self.code_path:
            d["code_path"] = self.code_path
        if self.replaces:
            d["replaces"] = self.replaces
        return d

    def to_index_dict(self) -> Dict[str, Any]:
        """Export as dict for library index (library.yaml factors list)."""
        return {
            "id": self.id,
            "name": self.name,
            "expression": self.expression,
            "source": self.source,
            "category": self.category,
            "status": self.status,
            "ic_mean": self.metrics.get("ic_mean"),
            "long_leg": self.long_leg,
            "evaluation_version": self.evaluation_version,
        }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/mining/test_schema.py -v`
Expected: PASS (all tests)

- [ ] **Step 5: Commit**

```bash
git add src/mining/schema.py tests/mining/test_schema.py
git commit -m "feat(schema): add canonical FactorRecord + normalize_metrics

Defaults: status=legacy, evaluation_version=v1 (safe for migration).
normalize_metrics scoped to library storage only."
```

---

### Task 0.2: Generate inventory snapshot

**Files:**
- Create: `scripts/inventory.py`

This script reads all factor files and outputs a report without modifying anything. It is a prerequisite for Phase 1 migration.

- [ ] **Step 1: Write the inventory script**

```python
#!/usr/bin/env python3
"""Generate inventory snapshot of all factor records.

Reads all factor_*.yaml files and outputs:
1. Total count
2. Schema field coverage
3. Per-factor summary (id, name, status, ic, schema gaps)
4. Category distribution

Does NOT modify any files.

Usage:
    PYTHONPATH=src python3 scripts/inventory.py
    PYTHONPATH=src python3 scripts/inventory.py --output docs/migration/inventory_snapshot.yaml
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import yaml
from mining.schema import normalize_metrics


def main():
    parser = argparse.ArgumentParser(description="Factor inventory snapshot")
    parser.add_argument("--library-dir", default="storage/library")
    parser.add_argument("--output", default=None, help="Save snapshot to YAML file")
    args = parser.parse_args()

    factors_dir = Path(args.library_dir) / "factors"
    if not factors_dir.exists():
        print(f"ERROR: {factors_dir} does not exist")
        sys.exit(1)

    factor_files = sorted(factors_dir.glob("factor_*.yaml"))
    print(f"Found {len(factor_files)} factor detail files\n")

    # Schema field coverage
    EXPECTED_FIELDS = [
        "id", "name", "expression", "source", "status",
        "evaluation_version", "category", "batch", "admitted_at",
        "long_leg", "metrics",
    ]
    EXPECTED_METRICS = [
        "ic_mean", "ic_ir", "ic_mean_oos", "ic_ir_oos",
        "ic_win_rate", "monotonicity_is", "ls_return", "max_corr",
    ]

    field_counts = {f: 0 for f in EXPECTED_FIELDS}
    metric_counts = {f: 0 for f in EXPECTED_METRICS}
    category_counts = {}
    factors = []
    schema_gaps = []

    for p in factor_files:
        with open(p, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        fid = str(data.get("id", "?"))
        name = data.get("name", "?")
        metrics = data.get("metrics", {})
        norm = normalize_metrics(metrics)
        ic = norm.get("ic_mean")

        # Track field presence
        for field in EXPECTED_FIELDS:
            if field in data and data[field] is not None:
                field_counts[field] += 1

        # Track metric presence (after normalization)
        for mk in EXPECTED_METRICS:
            if mk in norm and norm[mk] is not None:
                metric_counts[mk] += 1

        # Track categories
        cat = data.get("category", "unknown")
        category_counts[cat] = category_counts.get(cat, 0) + 1

        # Compute gaps
        missing = [f for f in EXPECTED_FIELDS if f not in data or data[f] is None]
        missing_metrics = [m for m in EXPECTED_METRICS if m not in norm or norm[m] is None]

        factors.append({
            "id": fid,
            "name": name,
            "category": cat,
            "ic_mean": round(ic, 4) if ic is not None else None,
            "has_status": "status" in data,
            "has_eval_version": "evaluation_version" in data,
            "has_long_leg": "long_leg" in data,
            "missing_fields": missing,
            "missing_metrics": missing_metrics,
        })

    # Print report
    total = len(factor_files)
    print("=== Schema Field Coverage ===")
    for f in EXPECTED_FIELDS:
        pct = field_counts[f] / total * 100
        print(f"  {f:25s} {field_counts[f]:3d}/{total}  ({pct:.0f}%)")

    print("\n=== Metrics Coverage (after alias normalization) ===")
    for m in EXPECTED_METRICS:
        pct = metric_counts[m] / total * 100
        print(f"  {m:25s} {metric_counts[m]:3d}/{total}  ({pct:.0f}%)")

    print("\n=== Category Distribution ===")
    for cat, count in sorted(category_counts.items(), key=lambda x: -x[1]):
        print(f"  {cat:25s} {count:3d}")

    print("\n=== Factors with Most Schema Gaps ===")
    gapped = sorted(factors, key=lambda f: len(f["missing_fields"]) + len(f["missing_metrics"]), reverse=True)
    for f in gapped[:10]:
        gap_count = len(f["missing_fields"]) + len(f["missing_metrics"])
        print(f"  [{f['id']}] {f['name']:30s}  gaps={gap_count}  "
              f"fields={f['missing_fields']}")

    # Save snapshot
    if args.output:
        snapshot = {
            "timestamp": str(__import__("datetime").datetime.now().isoformat()),
            "total_factors": total,
            "field_coverage": field_counts,
            "metric_coverage": metric_counts,
            "category_distribution": category_counts,
            "factors": factors,
        }
        with open(args.output, "w", encoding="utf-8") as f:
            yaml.dump(snapshot, f, default_flow_style=False, allow_unicode=True)
        print(f"\nSnapshot saved to {args.output}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run inventory**

Run: `mkdir -p docs/migration && PYTHONPATH=src python3 scripts/inventory.py --output docs/migration/inventory_snapshot.yaml`
Expected: Prints coverage report, saves snapshot to `docs/migration/`. No factor files modified.

- [ ] **Step 3: Commit**

```bash
git add scripts/inventory.py docs/migration/inventory_snapshot.yaml
git commit -m "feat: add inventory snapshot script — prerequisite for schema migration"
```

---

## Admission Path Definition

With `--admit` removed, the system has exactly **one** formal admission path:

```
evaluate_batch() → BatchResult.screened → /judge skill (LLM review)
    → mem.save_admission_history() → lib.admit() / lib.replace()
```

**Rules:**
- `lib.admit()` is the only write entry point to the registry. It always produces `status=active, evaluation_version=v2`.
- `lib.replace(old_id, new_factor)` keeps the same ID, writes a new `status=active, evaluation_version=v2` record, sets `replaces: old_id`. Old detail YAML is archived before overwrite.
- **`save_admission_history()` is mandatory before `admit()`/`replace()`.** The `/judge` skill must call `mem.save_admission_history(batch_id, {...})` with the admission decision (admitted/rejected names, reasons) before writing to the registry. This is already partially implemented (`cli.py:187` saves eval history); the `/judge` skill must do the same for admission decisions. This rule must be enforced in the skill, not optional.
- No CLI command calls `admit()` directly. Admission is always mediated by `/judge` skill calling the Python API.
- For testing/automation, call `lib.admit()` programmatically (e.g., in a script or test). There is no non-interactive CLI admission command by design — this prevents bypassing the judge.

## replace() Lifecycle Semantics

| Aspect | Behavior |
|--------|----------|
| ID | Preserved (same `old_id`) |
| New record | `status=active`, `evaluation_version=v2`, `replaces=old_id` |
| Old detail YAML | Overwritten (same file path `factor_{old_id}.yaml`) |
| Old evidence | Archived before overwrite (see below) |
| Index | Old entry removed, new entry appended |
| DB publish | Re-published under same factor_id |

**Archival on replace:** Before `replace()` overwrites the detail YAML and evidence:
1. **Detail YAML:** `library.replace()` copies the old `factor_{id}.yaml` to `factors/history/factor_{id}__replaced_YYYYMMDD_HHMMSS.yaml` before writing the new record. This preserves the full metadata audit trail in the registry layer.
2. **Evidence:** The `/report` skill renames the old evidence directory (e.g., `F013/` → `F013__replaced_YYYYMMDD_HHMMSS/`) before generating new reports. If no old evidence exists, this is a no-op.

---

## Phase 0.5: Code Integration

Wire `FactorRecord` and `normalize_metrics` into library/CLI code. Remove `--admit`. This phase changes code behavior but does NOT yet touch existing factor YAML files.

### Task 0.5.1: Remove `--admit` flag and `_normalize_metrics` from CLI

**Files:**
- Modify: `src/mining/cli.py`
- Modify: `CLAUDE.md` (line 18)
- Test: `tests/mining/test_cli.py`

**Why:** `--admit` bypasses LLM judge and caused multiple Grade D admissions. `_normalize_metrics()` duplicates schema logic that now lives in `normalize_metrics()`.

- [ ] **Step 1: Remove from cli.py**

1. Delete `_normalize_metrics()` function (lines 72-87)
2. Delete `--admit` argparse line (line 457)
3. Delete auto-admit block (lines 212-226)
4. Remove `args.admit` reference

- [ ] **Step 2: Fix CLAUDE.md**

Line 18: change `PYTHONPATH=src python3 -m mining batch storage/candidates/batch_XXX.yaml --admit`
to: `PYTHONPATH=src python3 -m mining batch storage/candidates/batch_XXX.yaml --skip-stage1`

- [ ] **Step 3: Run tests**

Run: `pytest tests/mining/test_cli.py -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add src/mining/cli.py CLAUDE.md tests/mining/test_cli.py
git commit -m "fix(cli): remove --admit flag and _normalize_metrics

--admit bypassed LLM judge, caused Grade D admissions.
_normalize_metrics duplicated schema logic now in mining.schema."
```

---

### Task 0.5.2: Wire FactorRecord into library.py

**Files:**
- Modify: `src/mining/library.py`
- Test: `tests/mining/test_library.py`

- [ ] **Step 1: Write tests for new behavior**

```python
# Add to tests/mining/test_library.py

class TestLibrarySchemaIntegration:
    def test_admit_normalizes_metrics(self, tmp_path):
        config = MiningConfig(library_dir=str(tmp_path / "library"))
        lib = FactorLibrary(config)
        factor = {
            "name": "test", "expression": "Std($close, 20)",
            "category": "volatility", "batch": "test_batch",
            "metrics": {"ic_mean_is": -0.05, "ic_ir_is": -0.3, "max_lib_corr": 0.4},
        }
        fid = lib.admit(factor)
        detail = lib.load_factor(fid)
        assert detail["metrics"]["ic_mean"] == -0.05
        assert detail["metrics"]["ic_ir"] == -0.3
        assert detail["metrics"]["max_corr"] == 0.4
        assert "ic_mean_is" not in detail["metrics"]

    def test_admit_sets_long_leg(self, tmp_path):
        config = MiningConfig(library_dir=str(tmp_path / "library"))
        lib = FactorLibrary(config)
        factor = {
            "name": "test_pos", "expression": "Mean($close, 20)",
            "category": "momentum", "batch": "test_batch",
            "metrics": {"ic_mean": 0.03},
        }
        fid = lib.admit(factor)
        detail = lib.load_factor(fid)
        assert detail["long_leg"] == "high"

    def test_admit_sets_status_and_version(self, tmp_path):
        config = MiningConfig(library_dir=str(tmp_path / "library"))
        lib = FactorLibrary(config)
        factor = {
            "name": "test", "expression": "X", "category": "c",
            "batch": "b", "metrics": {"ic_mean": -0.02},
        }
        fid = lib.admit(factor)
        detail = lib.load_factor(fid)
        # New admissions get active + v2 (migration defaults are legacy + v1)
        assert detail["status"] == "active"
        assert detail["evaluation_version"] == "v2"

    def test_index_has_full_schema(self, tmp_path):
        config = MiningConfig(library_dir=str(tmp_path / "library"))
        lib = FactorLibrary(config)
        factor = {
            "name": "test", "expression": "X", "category": "c",
            "batch": "b", "metrics": {"ic_mean": -0.02},
        }
        lib.admit(factor)
        entry = lib.list_factors()[0]
        assert "status" in entry
        assert "long_leg" in entry
        assert "evaluation_version" in entry
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/mining/test_library.py::TestLibrarySchemaIntegration -v`
Expected: FAIL — missing fields in detail/index

- [ ] **Step 3: Modify library.py**

1. Import `FactorRecord`, `normalize_metrics` from `mining.schema`
2. Rewrite `admit()` to use `FactorRecord` instead of manual dict construction (current code builds dicts inline with ad-hoc long_leg/ic fallback logic — replace all of it):

```python
def admit(self, factor: Dict[str, Any]) -> str:
    index = self._read_index()
    factor_id = self._next_id(index)
    source = factor.get("source", "dsl")
    name = factor.get("name", f"factor_{factor_id}")
    metrics = factor.get("metrics", {})

    code_path = None
    if source == "python":
        code_path = self._persist_python_factor(factor_id, factor)

    record = FactorRecord.for_new_admission(
        id=factor_id,
        name=name,
        expression=factor.get("expression") if source == "dsl" else None,
        source=source,
        category=factor.get("category", "other"),
        batch=factor.get("batch", "unknown"),
        admitted_at=str(date.today()),
        logic_id=factor.get("logic_id"),
        lineage=factor.get("lineage"),
        code_path=code_path,
        metrics=metrics,  # FactorRecord.__post_init__ normalizes
    )

    detail_path = self._factors_dir / f"factor_{factor_id}.yaml"
    with open(detail_path, "w", encoding="utf-8") as f:
        yaml.dump(record.to_detail_dict(), f,
                  default_flow_style=False, allow_unicode=True, sort_keys=False)
    index.setdefault("factors", []).append(record.to_index_dict())
    self._write_index(index)

    # ... publisher logic unchanged ...
```

4. Rewrite `replace()` using `FactorRecord.for_new_admission()`:
   - Keep same `old_id`
   - New record: `status=active`, `evaluation_version=v2`, `replaces=old_id`
   - Remove old entry from index, append new entry
   - Publisher logic unchanged

- [ ] **Step 4: Run all tests**

Run: `pytest tests/mining/ -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/mining/library.py tests/mining/test_library.py
git commit -m "refactor(library): use FactorRecord for admit/replace

New admissions: status=active, evaluation_version=v2.
Replaces inline dict construction with FactorRecord. Normalizes metrics via schema."
```

---

### Task 0.5.3: Add `retire()` and status-filtered `list_factors()`

**Files:**
- Modify: `src/mining/library.py`
- Test: `tests/mining/test_library.py`

- [ ] **Step 1: Write the failing test**

```python
class TestFactorLifecycle:
    def test_retire_factor(self, tmp_path):
        config = MiningConfig(library_dir=str(tmp_path / "library"))
        lib = FactorLibrary(config)
        fid = lib.admit({
            "name": "x", "expression": "X", "category": "c",
            "batch": "b", "metrics": {"ic_mean": -0.02},
        })
        lib.retire(fid)
        detail = lib.load_factor(fid)
        assert detail["status"] == "retired"
        entry = next(f for f in lib.list_factors() if f["id"] == fid)
        assert entry["status"] == "retired"

    def test_list_active_only(self, tmp_path):
        config = MiningConfig(library_dir=str(tmp_path / "library"))
        lib = FactorLibrary(config)
        lib.admit({"name": "a", "expression": "A", "category": "c",
                    "batch": "b", "metrics": {"ic_mean": -0.01}})
        fid2 = lib.admit({"name": "b", "expression": "B", "category": "c",
                           "batch": "b", "metrics": {"ic_mean": -0.02}})
        lib.retire(fid2)
        active = lib.list_factors(status="active")
        assert len(active) == 1
        assert active[0]["name"] == "a"

    def test_get_all_expressions_includes_all_statuses(self, tmp_path):
        """Retired/legacy factors still participate in corr blocking."""
        config = MiningConfig(library_dir=str(tmp_path / "library"))
        lib = FactorLibrary(config)
        fid1 = lib.admit({"name": "a", "expression": "A", "category": "c",
                           "batch": "b", "metrics": {"ic_mean": -0.01}})
        fid2 = lib.admit({"name": "b", "expression": "B", "category": "c",
                           "batch": "b", "metrics": {"ic_mean": -0.02}})
        lib.retire(fid2)
        exprs = lib.get_all_expressions()
        # Both active AND retired participate in blocking
        assert fid1 in exprs
        assert fid2 in exprs
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/mining/test_library.py::TestFactorLifecycle -v`
Expected: FAIL — `AttributeError: 'FactorLibrary' has no attribute 'retire'`

- [ ] **Step 3: Implement**

```python
def retire(self, factor_id: str) -> None:
    """Mark a factor as retired in both detail and index."""
    self._set_status(factor_id, "retired")

def _set_status(self, factor_id: str, status: str) -> None:
    detail_path = self._factors_dir / f"factor_{factor_id}.yaml"
    if not detail_path.exists():
        raise FileNotFoundError(f"Factor {factor_id} not found")
    with open(detail_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    data["status"] = status
    with open(detail_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    index = self._read_index()
    for entry in index.get("factors", []):
        if str(entry["id"]) == str(factor_id):
            entry["status"] = status
            break
    self._write_index(index)
    logger.info("Factor %s status → %s", factor_id, status)

def list_factors(self, status: str | None = None) -> list[dict]:
    factors = self._read_index().get("factors", [])
    if status:
        factors = [f for f in factors if f.get("status") == status]
    return factors
```

**Note:** `get_all_expressions()` is NOT modified — it returns all factors regardless of status, because retired/legacy factors still represent known signal clusters and must participate in Stage 2 correlation blocking.

- [ ] **Step 4: Run tests**

Run: `pytest tests/mining/test_library.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/mining/library.py tests/mining/test_library.py
git commit -m "feat(library): add retire() and status-filtered list_factors()

get_all_expressions() unchanged — all statuses participate in corr blocking."
```

---

### Task 0.5.4: Add `retire` CLI command

**Files:**
- Modify: `src/mining/cli.py`

- [ ] **Step 1: Add CLI subcommand**

```python
def cmd_retire(args):
    config = MiningConfig(library_dir=args.library_dir)
    lib = FactorLibrary(config)
    lib.retire(args.factor_id)
    print(f"Factor {args.factor_id} retired")

# In main():
p_retire = sub.add_parser("retire", help="Retire a factor from the library")
p_retire.add_argument("factor_id", help="Factor ID (e.g., 013)")
p_retire.add_argument("--library-dir", default="storage/library")

# In dispatch:
elif args.command == "retire":
    cmd_retire(args)
```

- [ ] **Step 2: Run tests**

Run: `pytest tests/mining/test_cli.py -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add src/mining/cli.py
git commit -m "feat(cli): add 'mining retire <id>' command"
```

---

### Task 0.5.5: Normalize metrics in evaluator output

**Files:**
- Modify: `src/mining/evaluator.py`
- Test: `tests/mining/test_evaluator.py`

**Why:** `evaluate_batch()` returns raw `stage3` dicts with `ic_mean_is` keys. The `/judge` skill does its own normalization. Centralizing this in the evaluator means downstream consumers get canonical names.

**CRITICAL BOUNDARY:** Only create `f['metrics']` — do NOT modify `f['stage3']` or `f['full_ic']`. Those are used for logging, display, and result YAML serialization.

- [ ] **Step 1: Write test**

```python
# Add to tests/mining/test_evaluator.py (or test_schema.py)

def test_normalize_metrics_for_library():
    """normalize_metrics resolves aliases for library storage only."""
    from mining.schema import normalize_metrics
    raw = {
        "ic_mean_is": -0.05, "ic_ir_is": -0.3,
        "ic_mean_oos": -0.04, "monotonicity": -0.9,
        "max_lib_corr": 0.5,
    }
    norm = normalize_metrics(raw)
    assert norm["ic_mean"] == -0.05
    assert norm["ic_ir"] == -0.3
    assert norm["monotonicity_is"] == -0.9
    assert norm["max_corr"] == 0.5
    assert "ic_mean_is" not in norm
    assert norm["ic_mean_oos"] == -0.04  # passthrough
```

- [ ] **Step 2: Add normalization at end of evaluate_batch()**

At the end of `evaluate_batch()`, after Stage 3 and hard gates, before returning `BatchResult`:

```python
from .schema import normalize_metrics

# Build library-bound metrics for screened factors AND replacements.
# f['stage3'] and f['full_ic'] are preserved as-is for logging.
for f in screened:
    raw = {**f.get('full_ic', {}), **f.get('stage3', {})}
    f['metrics'] = normalize_metrics(raw)
for r in replacements:
    nf = r.get('new_factor', r)
    raw = {**nf.get('full_ic', {}), **nf.get('stage3', {})}
    nf['metrics'] = normalize_metrics(raw)
```

**Ownership rule:** All objects entering `library.admit()` or `library.replace()` MUST have canonical `metrics`. The evaluator is responsible for producing this. `FactorRecord.__post_init__` will also normalize as a safety net, but the evaluator should not rely on that.

- [ ] **Step 3: Run tests**

Run: `pytest tests/mining/test_evaluator.py tests/mining/test_schema.py -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add src/mining/evaluator.py tests/mining/test_evaluator.py
git commit -m "refactor: evaluator produces normalized metrics for library storage

f['metrics'] uses canonical names. f['stage3'] and f['full_ic'] unchanged."
```

---

### Task 0.5.6: Propagate batch_id to screened factors

**Files:**
- Modify: `src/mining/cli.py`

- [ ] **Step 1: In cmd_batch(), after evaluate_batch returns:**

```python
for f in result.screened:
    f["batch"] = batch_id
for r in result.replacements:
    if "new_factor" in r:
        r["new_factor"]["batch"] = batch_id
```

- [ ] **Step 2: Run tests**

Run: `pytest tests/mining/ -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add src/mining/cli.py
git commit -m "fix: propagate batch_id to screened factors before admission"
```

---

### Task 0.5.7: Implement replace() detail archival + mandatory admission history

**Files:**
- Modify: `src/mining/library.py` (replace() archives old detail before overwrite)
- Modify: `.claude/skills/factor-judge/skill.md` (enforce save_admission_history before admit/replace)
- Test: `tests/mining/test_library.py`

**Why:** The admission path and replace() lifecycle are defined as rules above. This task makes them executable code + enforced skill steps.

- [ ] **Step 1: Write failing tests**

```python
# Add to tests/mining/test_library.py

class TestReplaceArchival:
    def test_replace_archives_old_detail(self, tmp_path):
        """replace() copies old detail YAML to factors/history/ before overwrite."""
        config = MiningConfig(library_dir=str(tmp_path / "library"))
        lib = FactorLibrary(config)
        fid = lib.admit({
            "name": "old_factor", "expression": "A", "category": "c",
            "batch": "b", "metrics": {"ic_mean": -0.01},
        })
        lib.replace(fid, {
            "name": "new_factor", "expression": "B", "category": "c",
            "batch": "b2", "metrics": {"ic_mean": -0.05},
        })
        # Old detail archived
        history_dir = tmp_path / "library" / "factors" / "history"
        archived = list(history_dir.glob(f"factor_{fid}__replaced_*.yaml"))
        assert len(archived) == 1
        # New detail has new name
        detail = lib.load_factor(fid)
        assert detail["name"] == "new_factor"
        assert detail["replaces"] == fid

    def test_replace_preserves_same_id(self, tmp_path):
        config = MiningConfig(library_dir=str(tmp_path / "library"))
        lib = FactorLibrary(config)
        fid = lib.admit({
            "name": "old", "expression": "A", "category": "c",
            "batch": "b", "metrics": {"ic_mean": -0.01},
        })
        returned_id = lib.replace(fid, {
            "name": "new", "expression": "B", "category": "c",
            "batch": "b2", "metrics": {"ic_mean": -0.05},
        })
        assert returned_id == fid

    def test_replace_keeps_single_index_entry_per_id(self, tmp_path):
        """After replace, index must have exactly one entry for this id."""
        config = MiningConfig(library_dir=str(tmp_path / "library"))
        lib = FactorLibrary(config)
        fid = lib.admit({
            "name": "old", "expression": "A", "category": "c",
            "batch": "b", "metrics": {"ic_mean": -0.01},
        })
        lib.replace(fid, {
            "name": "new", "expression": "B", "category": "c",
            "batch": "b2", "metrics": {"ic_mean": -0.05},
        })
        entries = [f for f in lib.list_factors() if f["id"] == fid]
        assert len(entries) == 1
        assert entries[0]["name"] == "new"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/mining/test_library.py::TestReplaceArchival -v`
Expected: FAIL — no `history/` directory created, archive not implemented

- [ ] **Step 3: Implement archival in replace()**

In `library.py`, at the start of `replace()`, before writing the new record:

```python
import shutil
from datetime import datetime

def replace(self, old_id: str, new_factor: Dict[str, Any]) -> str:
    # Archive old detail YAML before overwrite (timestamp avoids same-day collisions)
    old_detail = self._factors_dir / f"factor_{old_id}.yaml"
    if old_detail.exists():
        history_dir = self._factors_dir / "history"
        history_dir.mkdir(exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_name = f"factor_{old_id}__replaced_{ts}.yaml"
        shutil.copy2(str(old_detail), str(history_dir / archive_name))
        logger.info("Archived %s → history/%s", old_detail.name, archive_name)

    # ... rest of replace logic using FactorRecord.for_new_admission() ...
```

- [ ] **Step 4: Update factor-judge skill**

In `.claude/skills/factor-judge/skill.md`, add as a mandatory step before `lib.admit()`:

```markdown
## 强制步骤：录取前写 admission_history

在调用 `lib.admit()` 或 `lib.replace()` 之前，必须先执行：

mem.save_admission_history(batch_id, {
    "batch_id": batch_id,
    "timestamp": datetime.now().isoformat(),
    "phase": "admission",
    "admitted": [{"name": ..., "id": ...}],
    "rejected": [{"name": ..., "reason": ...}],
    "replaced": [{"old_id": ..., "new_name": ...}],
})

此步骤不可跳过。
```

- [ ] **Step 5: Run tests**

Run: `pytest tests/mining/test_library.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/mining/library.py .claude/skills/factor-judge/skill.md tests/mining/test_library.py
git commit -m "feat: replace() archives old detail YAML + mandatory admission history

replace() copies old factor_XXX.yaml to factors/history/ before overwrite.
/judge skill now requires save_admission_history() before admit/replace."
```

---

## Phase 1: Execute Schema Migration

This phase mutates the 51 existing factor YAML files. Requires Phase 0 (schema) and Phase 0.5 (code integration) to be complete and tested.

### Task 1.0: Create physical backup of main assets

**Pre-condition:** This step MUST run before any migration writes.

- [ ] **Step 1: Backup storage/library**

```bash
mkdir -p docs/migration
tar -czf docs/migration/library_backup_$(date +%Y%m%d_%H%M%S).tar.gz storage/library
```

- [ ] **Step 2: Verify backup**

```bash
tar -tzf docs/migration/library_backup_*.tar.gz | head -5
# Expected: storage/library/library.yaml, storage/library/factors/factor_001.yaml, ...
```

This backup is the rollback path if migration produces unexpected results. Do NOT delete until Phase 1 is verified.

---

### Task 1.1: Write migration script

**Files:**
- Create: `scripts/migrate_schema.py`

- [ ] **Step 1: Write the script**

```python
#!/usr/bin/env python3
"""Migrate existing factor records to canonical schema.

Default mode is --dry-run (report only). Explicit --apply to mutate.

Changes per factor:
- Normalize metric aliases (ic_mean_is → ic_mean, etc.)
- Fill source=dsl if missing
- Fill status=legacy if missing (NOT active — deliberate)
- Fill evaluation_version=v1 (all existing factors)
- Infer long_leg from ic_mean sign
- Zero-pad IDs (9 → 009)

Then rebuilds library.yaml index from detail files.

Usage:
    PYTHONPATH=src python3 scripts/migrate_schema.py            # dry-run (default)
    PYTHONPATH=src python3 scripts/migrate_schema.py --apply    # mutate files
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import yaml
from mining.schema import FactorRecord, normalize_metrics


def migrate_factor(data: dict, path: Path) -> tuple[dict, list[str]]:
    """Normalize a single factor detail record. Returns (data, changes)."""
    changes = []

    # 1. Zero-pad ID
    raw_id = data.get("id", "")
    padded_id = f"{int(raw_id):03d}"
    if str(raw_id) != padded_id:
        data["id"] = padded_id
        changes.append(f"id: {raw_id} → {padded_id}")

    # 2. Normalize metrics
    raw_metrics = data.get("metrics", {})
    norm_metrics = normalize_metrics(raw_metrics)
    if norm_metrics != raw_metrics:
        changes.append(f"metrics aliases resolved")
        data["metrics"] = norm_metrics

    # 3. Fill missing source
    if "source" not in data:
        data["source"] = "dsl"
        changes.append("added source=dsl")

    # 4. Fill missing status — LEGACY, not active
    if "status" not in data:
        data["status"] = "legacy"
        changes.append("added status=legacy")

    # 5. All existing factors are v1
    if "evaluation_version" not in data:
        data["evaluation_version"] = "v1"
        changes.append("added evaluation_version=v1")

    # 6. Infer long_leg
    if "long_leg" not in data:
        ic = data["metrics"].get("ic_mean")
        if ic is not None:
            data["long_leg"] = "high" if ic >= 0 else "low"
            changes.append(f"inferred long_leg={data['long_leg']}")

    # 7. Verify filename matches ID
    expected_name = f"factor_{data['id']}.yaml"
    if path.name != expected_name:
        changes.append(f"WARNING: filename {path.name} != expected {expected_name}")

    return data, changes


def rebuild_index(factors_dir: Path, index_path: Path, dry_run: bool) -> None:
    """Rebuild library.yaml index from detail files (detail = truth source)."""
    # Preserve existing thresholds
    existing = {}
    if index_path.exists():
        with open(index_path, "r", encoding="utf-8") as f:
            existing = yaml.safe_load(f) or {}

    entries = []
    for p in sorted(factors_dir.glob("factor_*.yaml")):
        with open(p, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        rec = FactorRecord.for_migration(
            id=f"{int(data['id']):03d}",
            name=data["name"],
            expression=data.get("expression"),
            category=data.get("category", "other"),
            batch=data.get("batch", "unknown"),
            source=data.get("source", "dsl"),
            status=data.get("status", "legacy"),
            evaluation_version=data.get("evaluation_version", "v1"),
            long_leg=data.get("long_leg"),
            metrics=data.get("metrics", {}),
        )
        entries.append(rec.to_index_dict())

    index_data = {
        "thresholds": existing.get("thresholds", {}),
        "factors": entries,
    }

    if dry_run:
        statuses = {}
        for e in entries:
            s = e.get("status", "?")
            statuses[s] = statuses.get(s, 0) + 1
        print(f"\nIndex would have {len(entries)} entries: {statuses}")
    else:
        with open(index_path, "w", encoding="utf-8") as f:
            yaml.dump(index_data, f, default_flow_style=False,
                      allow_unicode=True, sort_keys=False)
        print(f"\nRebuilt {index_path}: {len(entries)} factors")


def main():
    parser = argparse.ArgumentParser(description="Migrate factor records to canonical schema")
    parser.add_argument("--apply", action="store_true",
                        help="Apply changes (default is dry-run)")
    parser.add_argument("--library-dir", default="storage/library")
    args = parser.parse_args()
    dry_run = not args.apply

    if dry_run:
        print("=== DRY RUN (no files will be modified) ===\n")
    else:
        print("=== APPLYING MIGRATION ===\n")

    lib_dir = Path(args.library_dir)
    factors_dir = lib_dir / "factors"
    index_path = lib_dir / "library.yaml"

    if not factors_dir.exists():
        print(f"ERROR: {factors_dir} does not exist")
        sys.exit(1)

    factor_files = sorted(factors_dir.glob("factor_*.yaml"))
    print(f"Found {len(factor_files)} factor files\n")

    total_changes = 0
    for p in factor_files:
        with open(p, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        data, changes = migrate_factor(data, p)
        if changes:
            total_changes += len(changes)
            print(f"  {p.name}: {', '.join(changes)}")
            if not dry_run:
                # Rename file if filename doesn't match padded ID
                expected_name = f"factor_{data['id']}.yaml"
                if p.name != expected_name:
                    new_path = p.parent / expected_name
                    p.rename(new_path)
                    print(f"    RENAMED {p.name} → {expected_name}")
                    p = new_path
                with open(p, "w", encoding="utf-8") as f:
                    yaml.dump(data, f, default_flow_style=False,
                              allow_unicode=True, sort_keys=False)

    print(f"\nTotal changes: {total_changes}")
    rebuild_index(factors_dir, index_path, dry_run)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Dry-run migration**

Run: `PYTHONPATH=src python3 scripts/migrate_schema.py`
Expected: Report of all changes per factor. No files modified.

- [ ] **Step 3: Audit index consumers before migration**

The new index schema drops `batch` and `admitted_at` from index entries. Verify no code depends on these fields from library.yaml:

```bash
# Find all library.yaml readers
grep -rn "library.yaml\|list_factors\|_read_index" src/ --include='*.py'
# For each hit, check if it reads batch or admitted_at from index entries
```

If any consumer needs `batch` or `admitted_at` from the index, add those fields to `to_index_dict()` before proceeding.

- [ ] **Step 4: Review dry-run output**

Verify:
- All factors get `status=legacy`, not `active`
- All factors get `evaluation_version=v1`
- Metric aliases resolve correctly
- ID zero-padding is correct
- Filename-vs-ID consistency (no warnings)
- Index rebuild preserves thresholds

- [ ] **Step 5: Apply migration**

Run: `PYTHONPATH=src python3 scripts/migrate_schema.py --apply`
Expected: All factor files updated, library.yaml rebuilt.

- [ ] **Step 6: Run inventory to verify**

Run: `PYTHONPATH=src python3 scripts/inventory.py`
Expected: All fields at 51/51 coverage. All statuses = `legacy`.

- [ ] **Step 7: Run tests**

Run: `pytest tests/mining/test_library.py tests/mining/test_config.py -v`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add scripts/migrate_schema.py storage/library/
git commit -m "feat(migration): normalize 51 factor records to canonical schema

All factors: status=legacy, evaluation_version=v1.
Metrics: ic_mean_is→ic_mean, max_lib_corr→max_corr, monotonicity→monotonicity_is.
Index rebuilt from detail files (detail = truth source)."
```

---

## Phase 2: Report + Path Consolidation

**Boundary note:** Phase 2 implements registry-first semantics (metadata reads from `config.library_dir` instead of DB-first). The physical path is still `storage/library` at this point. Phase 3 is where the default physical path changes to `storage/registry`. Do not conflate "registry semantics" (Phase 2) with "registry directory" (Phase 3).

### Task 2.1: Inject all paths via config

**Files:**
- Modify: `src/mining/config.py` (add `vault_dir`)
- Modify: `src/report/builder.py` (remove hardcoded paths)
- Modify: `src/mining/library.py` (line 227)

- [ ] **Step 1: Add `vault_dir` to MiningConfig**

In `config.py`, after `report_dir`:
```python
vault_dir: str = "storage/vault"
```

- [ ] **Step 2: Fix report builder hardcoded path**

In `builder.py` `_load_factor_metadata()`, replace lines 265-269:
```python
# Fallback: read from library.yaml via config path
import yaml
lib_path = Path(self.config.library_dir) / "library.yaml"
```

- [ ] **Step 3: Fix library.py hardcoded path**

In `library.py` `_load_values_cache()`, replace line 227:
```python
candidates_dir = Path(self._config.candidates_dir)
```

- [ ] **Step 4: Fix report builder vault_dir default**

```python
def save_for_vault(self, vault_dir: str | None = None) -> str:
    if vault_dir is None:
        vault_dir = self.config.vault_dir
```

And in CLI: `parser.add_argument("--vault-dir", default=None)`, resolve in code.

- [ ] **Step 5: Run tests**

Run: `pytest tests/report/test_builder.py tests/mining/test_library.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/mining/config.py src/report/builder.py src/mining/library.py
git commit -m "fix: eliminate hardcoded path fallbacks — all paths via MiningConfig"
```

---

### Task 2.2: Report builder reads metadata from registry first

**Files:**
- Modify: `src/report/builder.py` (`_load_factor_metadata`)
- Test: `tests/report/test_builder.py`

**Why:** Report builder currently tries DB first. But registry (detail YAML) is the metadata truth source. DB is a derived cache for factor values.

- [ ] **Step 1: Write the test**

```python
def test_metadata_from_library_yaml(tmp_path):
    factors_dir = tmp_path / "library" / "factors"
    factors_dir.mkdir(parents=True)
    import yaml
    with open(factors_dir / "factor_099.yaml", "w") as f:
        yaml.dump({
            "id": "099", "name": "test_factor",
            "expression": "Std($close, 20)", "category": "volatility",
            "batch": "batch_test", "admitted_at": "2026-04-01",
        }, f)
    config = MiningConfig(library_dir=str(tmp_path / "library"))
    builder = ReportDataBuilder("099", config=config)
    meta = builder._load_factor_metadata()
    assert meta["name"] == "test_factor"
```

- [ ] **Step 2: Rewrite `_load_factor_metadata`**

Primary: read detail YAML from `config.library_dir`. Fallback: DB `factor_meta`.

```python
def _load_factor_metadata(self) -> dict:
    # Primary: registry detail YAML (metadata truth source)
    detail_path = Path(self.config.library_dir) / "factors" / f"factor_{self.factor_id}.yaml"
    if detail_path.exists():
        import yaml
        with open(detail_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return {
            "id": data["id"],
            "name": data.get("name", f"factor_{data['id']}"),
            "expression": data.get("expression", ""),
            "category": data.get("category", "other"),
            "batch": data.get("batch", ""),
            "admitted_at": data.get("admitted_at", ""),
        }
    # Fallback: DB factor_meta (for factors not yet in registry)
    try:
        import psycopg2
        conn = psycopg2.connect(self.config.system.database.connection_string)
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT factor_id, name, expression, category, batch_id, admitted_at "
                    "FROM factor_meta WHERE factor_id = %s", (self.factor_id,))
                row = cur.fetchone()
            if row:
                return {"id": row[0], "name": row[1], "expression": row[2],
                        "category": row[3] or "other", "batch": row[4] or "",
                        "admitted_at": str(row[5] or "")}
        finally:
            conn.close()
    except Exception:
        pass
    raise ValueError(f"Factor {self.factor_id!r} not found")
```

- [ ] **Step 3: Run tests**

Run: `pytest tests/report/test_builder.py -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add src/report/builder.py tests/report/test_builder.py
git commit -m "fix(report): read metadata from registry YAML first, DB as fallback

Registry detail YAML is the metadata truth source. DB stores factor
values (time series), not the authoritative metadata."
```

---

### Task 2.3: Semantic alignment of CLAUDE.md and ALL skills

**Scope:** Semantic correctness only (thresholds, `--admit`, truth source roles, neutralize_mode). Physical path updates (`storage/library` → `storage/registry`) are deferred to Phase 3 Task 3.2 to avoid editing the same files twice.

**Files:**
- Modify: `CLAUDE.md`
- Modify: `.claude/skills/factor-execute/skill.md`
- Modify: `.claude/skills/factor-judge/skill.md`
- Modify: `.claude/skills/factor-idea/skill.md`
- Modify: `.claude/skills/factor-mine/skill.md`
- Modify: `.claude/skills/factor-report/skill.md`

- [ ] **Step 1: Remove threshold duplication from skills**

Replace hardcoded threshold values in factor-execute and factor-judge skills with:
```
阈值由 `src/mining/config.py` MiningConfig 定义，不在 skill 中重复维护。
```

- [ ] **Step 2: Fix neutralize_mode error in factor-execute skill**

Remove incorrect claim that `neutralize_mode` defaults to `"none"`. Config says `"market_cap"`.

- [ ] **Step 3: Fix factor-mine skill**

- Remove `--admit` from example command at skill.md:116
- Clarify that `lib.admit()` now produces `status=active, evaluation_version=v2` records
- Note: admission only via `/judge` skill, no CLI admission path

- [ ] **Step 4: Fix factor-report skill**

- Update `factor_meta` DB-first assumption — registry YAML is now primary metadata source

- [ ] **Step 5: Update CLAUDE.md semantics**

- Remove all `--admit` references from example commands and notes
- Add note: registry detail YAML is metadata truth source, DB is factor values truth source
- Note `src/data/loaders.py` as legacy metadata consumer

- [ ] **Step 6: Commit**

```bash
git add CLAUDE.md .claude/skills/
git commit -m "docs: semantic alignment — --admit removal, truth sources, threshold dedup"
```

---

## Phase 3: Storage Directory Restructure

**Strategy:** Copy → Verify → Cutover → Cleanup. NOT move.

### Task 3.1: Copy storage to new layout

**Files:**
- Create: `scripts/migrate_storage.py`
- Modify: `src/mining/config.py`

**Target layout:**
```
storage/
  registry/              # single metadata truth source (copy of library/)
    library.yaml
    factors/
      history/           # archived detail YAMLs from replace()
  mining/                # pipeline artifacts
    candidates/
    memory/
      history/
        eval/            # per-batch evaluation history
        admission/       # per-batch admission decisions
    logic/
    python_factors/
  evidence/              # pure derivation, deletable
    vault/
    reports/
  runtime/               # ephemeral, gitignored
    cache/
```

- [ ] **Step 1: Write copy-based migration script**

```python
#!/usr/bin/env python3
"""Copy storage to new layout (non-destructive).

Old directories are NOT deleted — they remain as backup until
manual cleanup after verification.

Usage:
    python3 scripts/migrate_storage.py --dry-run
    python3 scripts/migrate_storage.py --apply
"""
import argparse
import shutil
from pathlib import Path

COPIES = [
    ("storage/library", "storage/registry"),
    ("storage/candidates", "storage/mining/candidates"),
    ("storage/memory", "storage/mining/memory"),
    ("storage/logic", "storage/mining/logic"),
    ("storage/python_factors", "storage/mining/python_factors"),
    ("storage/vault", "storage/evidence/vault"),
    ("storage/reports", "storage/evidence/reports"),
    ("storage/cache", "storage/runtime/cache"),
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    dry_run = not args.apply

    if dry_run:
        print("=== DRY RUN ===\n")

    for old, new in COPIES:
        old_p, new_p = Path(old), Path(new)
        if not old_p.exists():
            print(f"  SKIP {old} (not found)")
            continue
        if new_p.exists():
            print(f"  SKIP {old} → {new} (destination exists)")
            continue
        if dry_run:
            print(f"  WOULD COPY {old} → {new}")
        else:
            new_p.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(str(old_p), str(new_p))
            print(f"  COPIED {old} → {new}")

    if not dry_run:
        Path("storage/runtime/.gitkeep").touch()
        print("\nDone. Old directories preserved as backup.")
        print("After verification, manually delete old dirs.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Dry-run**

Run: `python3 scripts/migrate_storage.py --dry-run`
Expected: Lists all copies.

- [ ] **Step 3: Apply copy**

Run: `python3 scripts/migrate_storage.py --apply`
Expected: All directories copied. Old directories still exist.

- [ ] **Step 4: Update config defaults to new paths**

In `src/mining/config.py`:
```python
memory_dir: str = "storage/mining/memory"
library_dir: str = "storage/registry"
candidates_dir: str = "storage/mining/candidates"
report_dir: str = "storage/evidence/reports"
logic_dir: str = "storage/mining/logic"
python_factors_dir: str = "storage/mining/python_factors"
forbidden_file: str = "storage/mining/memory/forbidden.yaml"
lib_cache_dir: str = "storage/runtime/cache/lib_factors"
vault_dir: str = "storage/evidence/vault"
```

**Also update CLI parser defaults** in `src/mining/cli.py`:
```
--library-dir  default="storage/library"  → "storage/registry"    (library, retire commands)
--memory-dir   default="storage/memory"   → "storage/mining/memory" (memory command)
--vault-dir    default=...                → None (resolve via config.vault_dir)
```

And in `src/report/builder.py` CLI:
```
--vault-dir  default="storage/vault"  → None (resolve via config.vault_dir)
```

- [ ] **Step 5: Update script defaults to new paths**

In `scripts/inventory.py` and `scripts/migrate_schema.py`:
```
--library-dir  default="storage/library"  → "storage/registry"
```

- [ ] **Step 6: Add runtime to .gitignore**

```
storage/runtime/
```

- [ ] **Step 7: Run ALL tests**

Run: `pytest -v`
Expected: PASS (tests use tmp_path, not real storage)

- [ ] **Step 8: Verify manually**

```bash
# Verify new paths work
PYTHONPATH=src python3 -m mining library
PYTHONPATH=src python3 -m mining memory

# Verify no hardcoded old paths remain
rg -n "storage/(library|candidates|memory|vault|reports|cache)" src/ --type py \
    --glob '!src/mining/config.py'
# Expected: no matches
```

- [ ] **Step 9: Commit**

```bash
git add scripts/migrate_storage.py scripts/inventory.py scripts/migrate_schema.py src/mining/config.py src/mining/cli.py src/report/builder.py .gitignore storage/registry/ storage/mining/ storage/evidence/
git commit -m "refactor(storage): copy to registry/mining/evidence/runtime layout

Non-destructive: old directories preserved as backup.
Config defaults updated to new paths.
storage/runtime/ gitignored."
```

---

### Task 3.2: Update physical paths in skills and CLAUDE.md

**Scope:** Physical path updates only (semantic changes were done in Phase 2 Task 2.3).

**Files:**
- Modify: `.claude/skills/factor-*` (all 6 skills)
- Modify: `CLAUDE.md`

- [ ] **Step 1: Search-and-replace physical paths in all skills**

```
storage/library        → storage/registry
storage/candidates     → storage/mining/candidates
storage/memory         → storage/mining/memory
storage/logic          → storage/mining/logic
storage/python_factors → storage/mining/python_factors
storage/vault          → storage/evidence/vault
storage/cache          → storage/runtime/cache
```

- [ ] **Step 2: Update CLAUDE.md Storage Layout section**

Replace the current layout diagram with the new `registry/mining/evidence/runtime` structure.

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md .claude/skills/
git commit -m "docs: update all physical paths to new storage layout"
```

---

### Task 3.3: Delete old storage directories (after verification)

**NOT automated.** This is a manual step after verifying the new layout works in production for at least one mining cycle.

```bash
# Only after verification:
rm -rf storage/library storage/candidates storage/memory \
       storage/logic storage/python_factors storage/vault \
       storage/reports storage/cache
```

---

## Verification Checklist

After all phases complete:

```bash
# 1. All tests pass
pytest -v

# 2. Schema coverage — all factors have required fields
python3 -c "
import yaml, sys
from pathlib import Path
for p in ['storage/registry/library.yaml', 'storage/library/library.yaml']:
    if Path(p).exists():
        lib = yaml.safe_load(open(p)); break
else:
    print('ERROR: no library.yaml found'); sys.exit(1)
factors = lib['factors']
for field in ['status', 'long_leg', 'evaluation_version', 'source']:
    count = sum(1 for f in factors if f.get(field) is not None)
    total = len(factors)
    print(f'{field}: {count}/{total}')
# All should be at or near 51/51
"

# 3. Post-Phase-1 check: all 51 migrated factors are legacy/v1
#    (Run immediately after Phase 1, before any new admissions.
#     After new admissions begin, some will be active/v2 — that's expected.)
python3 -c "
import yaml, sys
from pathlib import Path
# Phase 1 = storage/library, Phase 3+ = storage/registry — check both
for p in ['storage/registry/library.yaml', 'storage/library/library.yaml']:
    if Path(p).exists():
        lib = yaml.safe_load(open(p)); break
else:
    print('ERROR: no library.yaml found'); sys.exit(1)
legacy = [f for f in lib['factors'] if f.get('status') == 'legacy']
active = [f for f in lib['factors'] if f.get('status') == 'active']
print(f'legacy={len(legacy)}, active={len(active)}')
# After Phase 1: expect legacy=51, active=0
# After new admissions: active count grows, legacy stays at 51
"

# 4. No hardcoded old storage paths in source (excluding config.py)
rg -n "storage/(library|candidates|memory|vault|reports|cache)" src/ --type py \
    --glob '!src/mining/config.py'
# Expected: no matches (all paths should come from config)

# 5. No --admit flag
grep -rn '\-\-admit' src/ .claude/ CLAUDE.md
# Expected: no matches (except docs/superpowers/ specs which are historical)

# 6. Report builder reads from registry YAML, not DB-first
grep -n 'factor_meta.*WHERE' src/report/builder.py
# Expected: only in fallback block, after YAML check

# 7. Inventory can run clean
PYTHONPATH=src python3 scripts/inventory.py
# Expected: no schema gaps

# 8. Mining CLI works with new paths
PYTHONPATH=src python3 -m mining library
PYTHONPATH=src python3 -m mining memory
```

---

## Known Legacy Metadata Consumers

These modules still read factor metadata from DB (`factor_meta`) instead of registry YAML. They are NOT fixed in this plan but must be migrated in a follow-up:

| Module | Current behavior | Priority |
|--------|-----------------|----------|
| `src/data/loaders.py` | Reads `factor_meta` for admitted factor metadata | Medium — used by dashboard and data layer |
| `src/dashboard/` (multiple files) | Reads via `FactorLibrary.list_factors()` (safe after migration) and may have hardcoded paths | Low — legacy UI |

After Phase 2, `src/data/loaders.py` should be considered deprecated as a metadata source. Future work should route all metadata reads through `FactorLibrary` or directly from registry YAML.

**Rule: No new code may import or call `src/data/loaders.py` for factor metadata after Phase 2.** All new metadata reads must go through `FactorLibrary` or registry YAML. This rule should be added to `CLAUDE.md` in Task 2.3, and enforced via verification:

```bash
# Add to CI or review checklist:
rg "from data.loaders|from data import loaders|import loaders" src/ --glob '!src/data/**'
# Expected: no matches outside src/data/ itself
```

---

## What This Plan Does NOT Cover (Version B / Future)

Explicitly deferred:
- Promoting legacy factors to active (requires re-certification criteria)
- Cluster registry
- Hypothesis registry
- Independent Governance layer/module
- Physical active/legacy/retired directory split
- Full re-evaluation of legacy factors
- DB schema migration (factor_meta table)
- Migrating `src/data/loaders.py` to registry-first metadata reads
- Dashboard updates (may have hardcoded paths — check during Phase 3 verification)
