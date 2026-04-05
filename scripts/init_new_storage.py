#!/usr/bin/env python3
"""Create the new ``storage/`` directory tree with seed YAML files.

Idempotent: directories and seed files are only created if missing.

Usage::

    python scripts/init_new_storage.py                     # default root
    python scripts/init_new_storage.py --root storage_new  # custom root
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow running as a standalone script; add src/ to path for imports.
_project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_project_root / "src"))

from research.storage.paths import StoragePaths  # noqa: E402
from research.storage.yaml_io import save_yaml  # noqa: E402


# ------------------------------------------------------------------
# Seed data: minimal valid content for each YAML file
# ------------------------------------------------------------------

_SEEDS: dict[str, dict] = {
    "research_state": {
        "research_state": {
            "current_batch": None,
            "active_logic_ids": [],
            "current_focus": [],
            "current_bottlenecks": [],
            "policy_flags": {
                "prefer_dsl": True,
                "python_only_helper_based": True,
                "vectorization_required": True,
            },
            "last_updated_at": None,
        }
    },
    "pending_holdout_queue": {"pending": []},
    "logic_registry": {"logics": []},
    "factor_index": {"factors": []},
    "family_registry": {"families": []},
    "capability_registry": {
        "fields": [
            "$open", "$high", "$low", "$close",
            "$volume", "$amount",
            "$pe_ratio", "$pb_ratio", "$ps_ratio",
            "$market_cap", "$circ_market_cap", "$turnover_rate",
        ],
        "unavailable_operators": ["Neg", "TsRank", "TsMax", "TsMin", "SMA"],
        "notes": ["$vwap is zero in current data -- do not use"],
    },
    "implementation_policy": {
        "default": {
            "prefer_dsl": True,
            "python_only_helper_based": True,
            "vectorization_required": True,
        },
        "python_allowed_if": [
            "route_requires_multi_stage_pipeline",
            "route_requires_multi_state_logic",
            "dsl_expression_unnatural",
        ],
        "python_discouraged_if": [
            "simple_breakout",
            "simple_reversal",
            "simple_rank_spread",
            "only_window_variation",
        ],
    },
    "failure_taxonomy": {
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
        ]
    },
    "policy_upgrade_ledger": {"upgrades": []},
    "search_ledger": {
        "by_logic": {},
        "by_family": {},
        "by_experiment_tag": {},
    },
    "batch_usage": {"batches": {}},
    "holdout_review_ledger": {"reviews": []},
    "write_audit_log": {"entries": []},
    "forbidden": {"forbidden_patterns": []},
    "research_eval_v1": {
        "profile_id": "research_eval_v1",
        "universe": "all_a_share",
        "train_end": "2023-12-31",
        "test_start": "2024-01-01",
        "ic_threshold": 0.01,
        "correlation_threshold": 0.7,
    },
}

# Map seed key -> (StoragePaths attribute name for the file path)
_SEED_MAP: dict[str, str] = {
    "research_state": "research_state_file",
    "pending_holdout_queue": "pending_holdout_queue_file",
    "logic_registry": "logic_registry_file",
    "factor_index": "factor_index_file",
    "family_registry": "family_registry_file",
    "capability_registry": "capability_registry_file",
    "implementation_policy": "implementation_policy_file",
    "failure_taxonomy": "failure_taxonomy_file",
    "policy_upgrade_ledger": "policy_upgrade_ledger_file",
    "search_ledger": "search_ledger_file",
    "batch_usage": "batch_usage_file",
    "holdout_review_ledger": "holdout_review_ledger_file",
    "write_audit_log": "write_audit_log_file",
    "forbidden": "forbidden_file",
    "research_eval_v1": "research_eval_v1_file",
}


def init_storage(root: str = "storage") -> None:
    paths = StoragePaths(root)
    paths.ensure_dirs()

    # Write seed files (only if missing)
    for seed_key, attr_name in _SEED_MAP.items():
        file_path = getattr(paths, attr_name)
        if not file_path.exists():
            save_yaml(file_path, _SEEDS[seed_key])
            print(f"  created {file_path}")
        else:
            print(f"  exists  {file_path}")

    # Create notes/mining-lessons.md placeholder
    notes_file = paths.notes_dir / "mining-lessons.md"
    if not notes_file.exists():
        notes_file.write_text("# Mining Lessons\n\nCollected experience notes.\n", encoding="utf-8")
        print(f"  created {notes_file}")
    else:
        print(f"  exists  {notes_file}")

    print(f"\nStorage initialised at: {paths.root.resolve()}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialise the new research storage tree")
    parser.add_argument("--root", default="storage", help="Storage root (default: storage)")
    args = parser.parse_args()
    init_storage(root=args.root)


if __name__ == "__main__":
    main()
