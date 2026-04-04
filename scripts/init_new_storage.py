#!/usr/bin/env python3
"""Bootstrap the new research storage tree with seed YAML files.

Idempotent — safe to run multiple times.  Existing files are never
overwritten; only missing files are created.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure src/ is importable when running as a standalone script.
_project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_project_root / "src"))

from research.storage.paths import StoragePaths
from research.storage.yaml_io import save_yaml


def _seed(path: Path, data: dict) -> None:
    """Write *data* to *path* only if the file does not yet exist."""
    if path.exists():
        print(f"  [SKIP] {path.relative_to(_project_root)}")
        return
    save_yaml(path, data)
    print(f"  [CREATE] {path.relative_to(_project_root)}")


def main(root: str = "storage") -> None:
    paths = StoragePaths(root=root)
    paths.ensure_dirs()
    print(f"Directories ensured under {paths.root}/")

    # -- state/ --
    _seed(paths.research_state, {
        "current_batch": None,
        "active_logic_ids": [],
        "active_route_ids": [],
        "current_focus": [],
        "current_bottlenecks": [],
        "sample_policy": {
            "train_start": "2015-01-01",
            "train_end": "2023-12-31",
            "oos_start": "2024-01-01",
            "oos_end": "2024-12-31",
            "holdout_start": "2025-01-01",
        },
        "policy_flags": {
            "prefer_dsl": True,
            "python_only_helper_based": True,
            "vectorization_required": True,
        },
        "last_updated_at": None,
    })

    _seed(paths.pending_holdout_queue, {
        "queue": [],
    })

    # -- logic/ --
    _seed(paths.logic_registry, {
        "logics": [],
    })

    # -- registry/ --
    _seed(paths.factor_index, {
        "factors": [],
    })

    _seed(paths.family_registry, {
        "families": [],
    })

    # -- policy/ --
    _seed(paths.capability_registry, {
        "fields": [
            "$open", "$high", "$low", "$close",
            "$volume", "$amount",
            "$pe_ratio", "$pb_ratio", "$ps_ratio",
            "$market_cap", "$circ_market_cap", "$turnover_rate",
        ],
        "unavailable_fields": ["$vwap"],
        "dsl_operators": [
            "Ref", "Mean", "Std", "Corr", "Cov",
            "Rank", "Mul", "Add", "Sub", "Div",
            "Greater", "Less", "If", "Max", "Min",
            "Abs", "Log", "Sign", "Power",
            "TsDecay", "Delta", "Sum", "IdxMax", "IdxMin",
            "Count", "Slope", "Rsquare", "Resi",
            "WMA", "EMA",
        ],
        "unavailable_operators": ["Neg", "TsRank", "TsMax", "TsMin", "SMA"],
    })

    _seed(paths.implementation_policy, {
        "default": {
            "prefer_dsl": True,
            "python_only_helper_based": True,
            "vectorization_required": True,
        },
        "python_allowed_if": [
            "route_requires_multi_stage_pipeline",
            "route_requires_multi_state_logic",
            "dsl_expression_unnatural",
            "route_is_repair_or_decorrelate",
            "helper_backed_complex_logic",
        ],
        "python_discouraged_if": [
            "simple_breakout",
            "simple_reversal",
            "simple_rank_spread",
            "only_window_variation",
        ],
    })

    _seed(paths.failure_taxonomy, {
        "failure_types": [
            "weak_signal",
            "high_overlap",
            "hard_gate_rejected",
            "implementation_blocked",
            "performance_rejected",
            "helper_required",
            "regime_mismatch",
            "unstable_oos",
            "size_drift",
            "style_repackaging",
        ],
    })

    _seed(paths.policy_upgrade_ledger, {
        "entries": [],
    })

    # -- ledger/ --
    _seed(paths.search_ledger, {
        "by_logic": {},
        "by_family": {},
        "by_experiment_tag": {},
        "discovery_candidates": [],
    })

    _seed(paths.batch_usage, {
        "batches": {},
    })

    _seed(paths.holdout_review_ledger, {
        "entries": [],
    })

    _seed(paths.write_audit_log, {
        "entries": [],
    })

    # -- memory/ --
    _seed(paths.forbidden, {
        "forbidden_patterns": [],
    })

    # -- notes/ --
    notes_file = paths.notes_dir / "mining-lessons.md"
    if not notes_file.exists():
        notes_file.write_text(
            "# Mining Lessons\n\nCapture high-level experience and postmortems here.\n",
            encoding="utf-8",
        )
        print(f"  [CREATE] {notes_file.relative_to(_project_root)}")
    else:
        print(f"  [SKIP] {notes_file.relative_to(_project_root)}")

    # -- evaluation_profiles/ --
    eval_profile = paths.evaluation_profiles_dir / "research_eval_v1.yaml"
    _seed(eval_profile, {
        "profile_id": "research_eval_v1",
        "universe": "csi1000",
        "delay": 1,
        "horizon": 5,
        "train_start": "2015-01-01",
        "train_end": "2023-12-31",
        "oos_start": "2024-01-01",
        "oos_end": "2024-12-31",
        "ic_threshold": 0.01,
        "correlation_threshold": 0.7,
    })

    print("\nDone. Storage tree is ready.")


if __name__ == "__main__":
    main()
